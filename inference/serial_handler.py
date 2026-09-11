import time

import serial

from inference.pipeline import InspectionPipeline

PORT: str = "/dev/ttyAMA0"  # Porta serial para comunicação com o ESP32-S3


class SerialCommunicator:
    def __init__(self, port: str = PORT, baudrate: int = 115200):
        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=1.0)
        self.ser.reset_input_buffer()

    def send_defect_alert(self):
        """Envia o sinal de falha via UART para o ESP32-S3."""
        self.ser.write(b"DEFECT\n")
        self.ser.flush()

    def read_line(self) -> str:
        if self.ser.in_waiting > 0:
            line = self.ser.readline().decode("utf-8", errors="ignore").strip()
            return line
        return ""

    def close(self):
        self.ser.close()


def run_inference_service(port: str = PORT, lote_id: str = "LOTE_001"):
    print(f"[SERIAL] Conectando na porta {port}...")
    communicator = SerialCommunicator(port=port)
    pipeline = InspectionPipeline()

    print("[SERIAL] Aguardando sinal 'TRIGGER' do ESP32-S3...")
    try:
        while True:
            command = communicator.read_line()
            if command == "TRIGGER":
                print("[SERIAL] Trigger recebido! Executando inferência...")

                # Executa a captura e o modelo de IA
                # Retorna True para Conforme e False para Defeito
                is_conforme = pipeline.process_trigger(lote_id=lote_id)

                if not is_conforme:
                    print("[SERIAL] Enviando sinal 'DEFECT' para o ESP32-S3...")
                    communicator.send_defect_alert()

            time.sleep(0.005)  # Ciclo de polling
    except KeyboardInterrupt:
        print("\n[SERIAL] Encerrando serviço de inspeção.")
    finally:
        communicator.close()


if __name__ == "__main__":
    run_inference_service()
