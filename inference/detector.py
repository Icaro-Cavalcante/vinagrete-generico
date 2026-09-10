from dataclasses import dataclass
from typing import List

import numpy as np
from ultralytics import YOLO


@dataclass
class DetectionResult:
    is_conforme: bool
    defects: List[str]
    max_confidence: float
    annotated_image: np.ndarray

class YOLOInference:
    def __init__(self, model_path: str = "models/best.pt", conf_threshold: float = 0.5):
        # O arquivo do modelo é versionado via DVC e baixado no caminho especificado
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        # Mapeamento dos nomes de classes de falha esperados
        self.defect_classes = {"etiqueta_ausente", "etiqueta_rasgada", "etiqueta_torta"}

    def predict(self, image: np.ndarray) -> DetectionResult:
        results = self.model(image, conf=self.conf_threshold)[0]
        defects_found = []
        max_conf = 0.0

        for box in results.boxes:
            cls_id = int(box.cls[0])
            class_name = self.model.names[cls_id]
            conf = float(box.conf[0])

            if class_name in self.defect_classes:
                defects_found.append(class_name)
                max_conf = max(max_conf, conf)

        is_conforme = len(defects_found) == 0
        annotated_img = results.plot()

        return DetectionResult(
            is_conforme=is_conforme,
            defects=defects_found,
            max_confidence=max_conf if defects_found else 1.0,
            annotated_image=annotated_img
        )