import os
import sys
import time

import serial

from inference.motion_detector import MotionDetector
from inference.pipeline import InspectionPipeline

# Adiciona o diretório raiz ao sys.path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    BAUD_RATE,
    CMD_ALERT,
    CMD_START,
    CMD_STOP,
    CMD_SYS_OFF,
    CMD_SYS_ON,
    DEFECT_ALERT_THRESHOLD,
    SERIAL_PORT,
)


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

    def send_alert(self):
        self.send_command(CMD_ALERT)

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

    print(f"[SERVIÇO] Sistema pronto. Aguardando comando {CMD_SYS_ON} do ESP32-S3...")
    sys_on = False
    consecutive_defects = 0

    try:
        while True:
            # Verifica e processa todas as mensagens pendentes do ESP32-S3
            while communicator.ser.in_waiting > 0:
                line = communicator.read_line()
                if not line:
                    break
                if CMD_SYS_ON in line:
                    if not sys_on:
                        sys_on = True
                        consecutive_defects = 0
                        print(
                            "[SERVIÇO] Sistema ATIVO. Aguardando estabilização da esteira..."
                        )
                        time.sleep(1.0)
                        # Descarta quadros de aceleração inicial da esteira
                        for _ in range(10):
                            pipeline.camera.capture_frame()
                            time.sleep(0.02)
                        print("[SERVIÇO] Esteira estabilizada. Monitorando ROI.")
                elif CMD_SYS_OFF in line:
                    sys_on = False
                    consecutive_defects = 0
                    print(f"[SERVIÇO] Sistema INATIVO. Aguardando {CMD_SYS_ON}.")
                else:
                    print(f"[ESP32] {line}")

            # Se sistema estiver ativo, captura continuamente
            if sys_on:
                frame = pipeline.camera.capture_frame()
                if frame is not None and motion_detector.detect_motion_centered(frame):
                    print(
                        "[VISÃO] Objeto centralizado detectado na ROI. Parando esteira..."
                    )

                    # 1. Trava o aprendizado do fundo (MOG2) e envia STOP
                    motion_detector.set_belt_moving(False)
                    communicator.send_command(CMD_STOP)
                    time.sleep(0.3)  # Pequeno atraso para frenagem mecânica

                    # 2 & 3. Processa inferência YOLO e salva no banco de dados
                    is_conforme = pipeline.process_trigger()

                    if not is_conforme:
                        consecutive_defects += 1
                        print(
                            f"[INSPEÇÃO] Reprovado ({consecutive_defects}/{DEFECT_ALERT_THRESHOLD})."
                        )

                        # Dispara o alerta apenas ao atingir o limite configurado
                        if consecutive_defects >= DEFECT_ALERT_THRESHOLD:
                            communicator.send_alert()
                            print(
                                f"[ALERTA] Limite de {DEFECT_ALERT_THRESHOLD} falhas atingido -> Sinal '{CMD_ALERT.strip()}' enviado ao ESP32-S3."
                            )
                            consecutive_defects = 0

                        time.sleep(1.0)
                    else:
                        consecutive_defects = 0
                        print("[INSPEÇÃO] Aprovado.")

                    # 5. Envia START, altera estado para EXITING e destrava o MOG2
                    communicator.send_command(CMD_START)
                    print(f"[VISÃO] Retomando esteira ({CMD_START.strip()}).")

                    motion_detector.reset_to_exiting()
                    motion_detector.set_belt_moving(True)

                    # Cooldown mecânico: Aguarda a esteira acelerar e retirar a carta (1.0s)
                    time.sleep(1.0)

                    # LIMPEZA DE BUFFER: Descarta quadros residuais da fila da câmera
                    for _ in range(5):
                        pipeline.camera.capture_frame()
                        time.sleep(0.02)
            else:
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[SERVIÇO] Desconectando hardware e encerrando serviço...")
    finally:
        communicator.close()
        pipeline.close()


if __name__ == "__main__":
    run_inference_service()
