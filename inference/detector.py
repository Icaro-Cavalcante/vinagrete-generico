from dataclasses import dataclass

import numpy as np
from ultralytics import YOLO

MODEL_PATH: str = "weights/best.pt"  # Caminho para o modelo YOLO

@dataclass
class DetectionResult:
    is_conforme: bool
    defects: list[str]
    max_confidence: float
    annotated_image: np.ndarray

class YOLOInference:
    """
    Gerenciador de inferência utilizando Ultralytics YOLO.
    """

    def __init__(
        self,
        model_path: str = MODEL_PATH,
        conf_threshold: float = 0.5,
        defect_classes: set[str] | None = None,
    ):
        # Carrega o modelo versionado via DVC baixado no diretório local
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold

        # Classes de falha esperadas no dataset do projeto
        self.defect_classes = defect_classes or {
            "damage",
        }

    def predict(self, image: np.ndarray) -> DetectionResult:
        """
        Executa a inferência em um frame NumPy BGR.
        """
        # verbose=False desativa o log de print a cada frame no console
        results = self.model(image, conf=self.conf_threshold, verbose=False)[0]

        defects_found: list[str] = []
        max_conf: float = 0.0

        if results.boxes is not None and len(results.boxes) > 0:
            for box in results.boxes:
                cls_id = int(box.cls[0])
                class_name = self.model.names[cls_id]
                conf = float(box.conf[0])

                if class_name in self.defect_classes:
                    defects_found.append(class_name)
                    max_conf = max(max_conf, conf)

        is_conforme = len(defects_found) == 0

        # Desenha as bounding boxes e labels na imagem (retorna ndarray BGR)
        annotated_img = results.plot()

        return DetectionResult(
            is_conforme=is_conforme,
            defects=defects_found,
            max_confidence=round(max_conf, 4) if defects_found else 1.0,
            annotated_image=annotated_img,
        )
