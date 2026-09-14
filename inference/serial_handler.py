import time

import serial

from inference.pipeline import InspectionPipeline

import os
import sys

# Adiciona o diretório raiz ao sys.path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SERIAL_PORT, BAUD_RATE

class SerialCommunicator:
    def __init__(self, port: str = SERIAL_PORT, baudrate: int = BAUD_RATE):
        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=1.0)
        self.ser.reset_input_buffer()

    def send_defect_alert(self):
        self.ser.write(b"DEFECT\n")
        self.ser.flush()

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

    print("[SERVIÇO] Sistema pronto. Aguardando sinal 'TRIGGER' do ESP32-S3...")
    try:
        while True:
            command = communicator.read_line()
            if command == "TRIGGER":
                # Executa ciclo completo: captura -> YOLO -> banco de dados
                is_conforme = pipeline.process_trigger()

                if not is_conforme:
                    # Envia resposta imediata para acionar LED/Buzzer no ESP32-S3
                    communicator.send_defect_alert()
                    print("[INSPEÇÃO] Reprovado -> Sinal 'DEFECT' enviado ao ESP32-S3.")
                else:
                    print("[INSPEÇÃO] Aprovado.")

            time.sleep(0.002)  # Ciclo de varredura leve de 2ms
    except KeyboardInterrupt:
        print("\n[SERVIÇO] Desconectando hardware e encerrando serviço...")
    finally:
        communicator.close()
        pipeline.close()


if __name__ == "__main__":
    run_inference_service()
