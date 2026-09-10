import os
from datetime import datetime
import cv2
from .detector import YOLOInference
from .camera import CameraController


class InspectionPipeline:
    def __init__(
        self, model_path: str = "models/best.pt", output_dir: str = "data/defects"
    ):
        self.detector = YOLOInference(model_path=model_path)
        self.camera = CameraController()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def process_trigger(self, lote_id: str = "LOTE_001"):
        """
        Executa um ciclo completo acionado pelo sinal do ESP32-S3.
        """
        # 1. Captura da imagem da esteira
        image = self.camera.capture_frame()

        # 2. Inferência de IA
        result = self.detector.predict(image)

        # 3. Processamento da Decisão de Qualidade
        if result.is_conforme:
            print("[INSPEÇÃO] Item CONFORME. Aguardando próximo sinal.")
            return True

        print(f"[INSPEÇÃO] DEFEITO DETECTADO: {result.defects}")

        # Salva o arquivo de imagem no disco
        now = datetime.now()
        timestamp_str = now.strftime("%Y%m%d_%H%M%S_%f")
        img_filename = f"{lote_id}_{timestamp_str}.jpg"
        img_path = os.path.join(self.output_dir, img_filename)
        cv2.imwrite(img_path, result.annotated_image)

        # Ação 1: Notificar ESP32-S3 via Serial (alerta físico)
        self._send_serial_alert(result.defects)

        # Ação 2: Gravação no Banco de Dados SQLite
        self._save_to_database(
            img_path=img_path,
            timestamp=now,
            lote=lote_id,
            confianca=result.max_confidence,
            tipo_defeito=", ".join(result.defects),
        )
        return False

    def _send_serial_alert(self, defects: list):
        # TODO: Implementar escrita no cabo Serial/UART para o ESP32-S3
        pass

    def _save_to_database(
        self,
        img_path: str,
        timestamp: datetime,
        lote: str,
        confianca: float,
        tipo_defeito: str,
    ):
        # TODO: Implementar inserção da ocorrência e atualização das estatísticas no SQLite via SQLAlchemy
        pass
