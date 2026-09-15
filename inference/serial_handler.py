import os
import sys
import time

import serial

from inference.motion_detector import MotionDetector
from inference.pipeline import InspectionPipeline

# Adiciona o diretório raiz ao sys.path para importar config e backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BAUD_RATE, CONSECUTIVE_DEFECTS_ALERT, SERIAL_PORT
from backend.database import SessionLocal
from backend.crud import iniciar_lote, encerrar_lote

# Compatibilidade com scripts de teste
PORT = SERIAL_PORT


class SerialCommunicator:
    def __init__(self, port: str = SERIAL_PORT, baudrate: int = BAUD_RATE):
        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=1.0)
        self.ser.reset_input_buffer()

    def send_command(self, cmd: str):
        try:
            self.ser.write(cmd.encode("utf-8"))
            self.ser.flush()
        except Exception as e:
            print(f"[SERIAL ERRO] Falha ao enviar comando {cmd.strip()}: {e}")

    def send_defect_alert(self):
        self.send_command("DEFECT\n")

    def send_system_alert(self):
        self.send_command("ALERTA\n")

    def read_line(self) -> str:
        try:
            if self.ser.in_waiting > 0:
                return self.ser.readline().decode("utf-8", errors="ignore").strip()
        except Exception as e:
            print(f"[SERIAL ERRO] Falha ao ler serial: {e}")
        return ""

    def close(self):
        try:
            self.ser.close()
        except Exception:
            pass


def run_inference_service(port: str = SERIAL_PORT):
    print(f"[SERVIÇO] Iniciando barramento Serial na porta {port}...")
    communicator = SerialCommunicator(port=port)
    pipeline = InspectionPipeline()
    motion_detector = MotionDetector()

    print("[SERVIÇO] Sistema pronto. Aguardando comando SYS_ON do ESP32-S3...")
    sys_on = False
    in_alert = False
    consecutive_defects = 0

    try:
        while True:
            # Verifica e processa todas as mensagens pendentes do ESP32-S3
            while communicator.ser.in_waiting > 0:
                line = communicator.read_line()
                if not line:
                    break
                if "SYS_ON" in line:
                    if not sys_on:
                        sys_on = True
                        in_alert = False
                        consecutive_defects = 0

                        # Cria novo lote no banco de dados SQLite com ID incremental
                        db = SessionLocal()
                        try:
                            lote = iniciar_lote(db)
                            print(f"[LOTE] Novo lote #{lote.id} iniciado automaticamente no banco.")
                        except Exception as e:
                            print(f"[LOTE ERRO] Falha ao iniciar lote: {e}")
                        finally:
                            db.close()

                        print("[SERVIÇO] Sistema ATIVO. Aguardando estabilização da esteira...")
                        time.sleep(1.0)
                        # Descarta quadros de aceleração inicial da esteira
                        for _ in range(10):
                            pipeline.camera.capture_frame()
                            time.sleep(0.02)
                        print("[SERVIÇO] Esteira estabilizada. Monitorando ROI.")
                elif "SYS_OFF" in line:
                    sys_on = False
                    in_alert = False
                    consecutive_defects = 0

                    # Finaliza lote ativo no banco de dados
                    db = SessionLocal()
                    try:
                        lote = encerrar_lote(db)
                        if lote:
                            print(f"[LOTE] Lote #{lote.id} encerrado com sucesso no banco.")
                    except Exception as e:
                        print(f"[LOTE ERRO] Falha ao encerrar lote: {e}")
                    finally:
                        db.close()

                    print("[SERVIÇO] Sistema INATIVO. Aguardando SYS_ON.")
                else:
                    print(f"[ESP32] {line}")

            # Se sistema estiver ativo e não estiver em modo ALERTA travado
            if sys_on and not in_alert:
                frame = pipeline.camera.capture_frame()
                if frame is not None and motion_detector.detect_motion_centered(frame):
                    print(
                        "[VISÃO] Objeto centralizado detectado na ROI. Parando esteira..."
                    )

                    # 1. Trava o aprendizado do fundo (MOG2) e envia STOP
                    motion_detector.set_belt_moving(False)
                    communicator.send_command("STOP\n")
                    time.sleep(0.3)  # Pequeno atraso para frenagem mecânica

                    # 2 & 3. Processa inferência YOLO e salva no banco de dados (associado ao lote ativo)
                    is_conforme = pipeline.process_trigger()

                    if not is_conforme:
                        consecutive_defects += 1
                        print(
                            f"[INSPEÇÃO] Reprovado ({consecutive_defects}/{CONSECUTIVE_DEFECTS_ALERT} consecutivos)."
                        )

                        # Controle de Danos: se atingir o limiar, entra em ALERTA
                        if consecutive_defects >= CONSECUTIVE_DEFECTS_ALERT:
                            in_alert = True
                            print(
                                f"[ALERTA] Limite de {CONSECUTIVE_DEFECTS_ALERT} defeitos consecutivos atingido! Enviando 'ALERTA' ao ESP32-S3..."
                            )
                            communicator.send_system_alert()
                        else:
                            # Defeito isolado: 1 pulso de 1000 ms no ESP32
                            communicator.send_defect_alert()
                            print(
                                "[INSPEÇÃO] Sinal 'DEFECT' enviado ao ESP32-S3."
                            )
                            time.sleep(1.0)
                    else:
                        consecutive_defects = 0
                        print("[INSPEÇÃO] Aprovado.")

                    # Se não entrou em ALERTA, retoma o movimento da esteira
                    if not in_alert:
                        # 4. Envia START, altera estado para EXITING e destrava o MOG2
                        communicator.send_command("START\n")
                        print("[VISÃO] Retomando esteira (START).")

                        motion_detector.reset_to_exiting()
                        motion_detector.set_belt_moving(True)

                        # Cooldown mecânico: Aguarda a esteira acelerar e retirar a carta (1.2s)
                        time.sleep(1.2)

                        # LIMPEZA DE BUFFER: Descarta quadros residuais da fila da câmera
                        for _ in range(8):
                            pipeline.camera.capture_frame()
                            time.sleep(0.02)
                    else:
                        print(
                            "[ALERTA] Esteira parada permanentemente. Aguardando intervenção do operador na botoeira."
                        )
            else:
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[SERVIÇO] Desconectando hardware e encerrando serviço...")
    finally:
        communicator.close()
        pipeline.close()


if __name__ == "__main__":
    run_inference_service()
