import os
import sys
import time

import serial

from inference.motion_detector import MotionDetector
from inference.pipeline import InspectionPipeline

# Adiciona o diretório raiz ao sys.path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BAUD_RATE, SERIAL_PORT


class SerialCommunicator:
    def __init__(self, port: str = SERIAL_PORT, baudrate: int = BAUD_RATE):
        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=1.0)
        self.ser.reset_input_buffer()

    def send_command(self, cmd: str):
        self.ser.write(cmd.encode("utf-8"))
        self.ser.flush()

    def send_defect_alert(self):
        self.send_command("DEFECT\n")

    def read_line(self) -> str:
        if self.ser.in_waiting > 0:
            return self.ser.readline().decode("utf-8", errors="ignore").strip()
        return ""

    def close(self):
        self.ser.close()


def run_inference_service(port: str = SERIAL_PORT):
    print(f"[SERVIÇO] Iniciando barramento Serial na porta {port}...")
    communicator = SerialCommunicator(port=port)
    pipeline = InspectionPipeline()
    motion_detector = MotionDetector()

    print("[SERVIÇO] Sistema pronto. Aguardando comando SYS_ON do ESP32-S3...")
    sys_on = False

    try:
        while True:
            # Verifica mensagens do ESP32-S3
            command = communicator.read_line()
            if command == "SYS_ON":
                sys_on = True
                print("[SERVIÇO] Sistema ATIVO. Iniciando captura de quadros.")
            elif command == "SYS_OFF":
                sys_on = False
                print("[SERVIÇO] Sistema INATIVO. Aguardando SYS_ON.")

            # Se sistema estiver ativo, captura continuamente
            if sys_on:
                frame = pipeline.camera.capture_frame()
                if frame is not None and motion_detector.detect_motion_centered(frame):
                    print(
                        "[VISÃO] Objeto centralizado detectado na ROI. Parando esteira..."
                    )

                    # 1. Trava o aprendizado do fundo (MOG2) e envia STOP
                    motion_detector.set_belt_moving(False)
                    communicator.send_command("STOP\n")
                    time.sleep(0.3)  # Pequeno atraso para frenagem mecânica

                    # 2 & 3. Processa inferência YOLO e salva no banco de dados
                    is_conforme = pipeline.process_trigger()

                    if not is_conforme:
                        # 4. Envia alerta de defeito
                        communicator.send_defect_alert()
                        print(
                            "[INSPEÇÃO] Reprovado -> Sinal 'DEFECT' enviado ao ESP32-S3."
                        )
                        time.sleep(1.0)
                    else:
                        print("[INSPEÇÃO] Aprovado.")

                    # 5. Envia START, altera estado para EXITING e destrava o MOG2
                    communicator.send_command("START\n")
                    print("[VISÃO] Retomando esteira (START).")

                    motion_detector.reset_to_exiting()
                    motion_detector.set_belt_moving(True)

                    # LIMPEZA DE BUFFER: Descarta os 5 quadros antigos da fila da câmera
                    for _ in range(5):
                        pipeline.camera.capture_frame()
                        time.sleep(0.03)
            else:
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[SERVIÇO] Desconectando hardware e encerrando serviço...")
    finally:
        communicator.close()
        pipeline.close()


if __name__ == "__main__":
    run_inference_service()
