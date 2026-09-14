import base64
import os
import sys

import cv2
import numpy as np
from sqlalchemy.orm import Session

from backend.crud import registrar_inspecao_com_dados
from backend.database import SessionLocal

from .camera import CameraController
from .detector import YOLOInference

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CROP_TO_ROI, MODEL_PATH, ROI_X_BOUNDS, ROI_Y_BOUNDS


def frame_to_base64(frame: np.ndarray) -> str:
    """Converte matriz NumPy BGR em string Base64 com cabeçalho data:image/jpeg."""
    success, buffer = cv2.imencode(".jpg", frame)
    if not success:
        raise RuntimeError("Falha ao codificar frame para JPEG.")
    encoded = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


class InspectionPipeline:
    def __init__(self, model_path: str = MODEL_PATH):
        self.detector = YOLOInference(model_path=model_path)
        self.camera = CameraController()

    def process_trigger(self) -> bool:
        """
        Executa captura, inferência do YOLO e gravação de estatísticas/defeito no SQLite.
        Retorna True para item Conforme e False para Defeito.
        """
        # 1. Captura rápida via RAM
        image = self.camera.capture_frame()
        if image is None:
            return True

        # 2. Recorta para a ROI da esteira se habilitado (elimina ruídos da mesa/suporte)
        if CROP_TO_ROI:
            h, w = image.shape[:2]
            x1 = max(0, min(ROI_X_BOUNDS[0], w))
            x2 = max(0, min(ROI_X_BOUNDS[1], w))
            y1 = max(0, min(ROI_Y_BOUNDS[0], h))
            y2 = max(0, min(ROI_Y_BOUNDS[1], h))
            if x1 < x2 and y1 < y2:
                inference_img = image[y1:y2, x1:x2]
            else:
                inference_img = image
        else:
            inference_img = image

        # 3. Predição com Ultralytics YOLO
        result = self.detector.predict(inference_img)

        # 4. Codifica imagem anotada apenas em caso de falha para poupar IO/processamento
        imagem_b64 = None
        if not result.is_conforme:
            imagem_b64 = frame_to_base64(result.annotated_image)

        # 5. Transação com o banco SQLite via CRUD
        db: Session = SessionLocal()
        try:
            registrar_inspecao_com_dados(
                db=db,
                possui_defeito=not result.is_conforme,
                tipo_defeito=", ".join(result.defects) if result.defects else None,
                grau_confiabilidade=result.max_confidence
                if not result.is_conforme
                else None,
                imagem=imagem_b64,
            )
        finally:
            db.close()

        return result.is_conforme

    def close(self):
        """Libera o hardware da câmera ao encerrar a aplicação."""
        self.camera.close()
