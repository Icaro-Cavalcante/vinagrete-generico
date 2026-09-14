import numpy as np
import pytest
import torch

try:
    import ultralytics.nn.tasks
    torch.serialization.add_safe_globals([
        ultralytics.nn.tasks.ClassificationModel,
        torch.nn.modules.container.Sequential,
    ])
except Exception:
    pass

from inference.detector import DetectionResult, MODEL_PATH, YOLOInference


@pytest.fixture(scope="module")
def detector():
    # Instancia o detector com o modelo compilado em weights/best.pt
    return YOLOInference(model_path=MODEL_PATH, conf_threshold=0.5)


def test_detector_output_structure(detector):
    """Garante que a inferência aceita matrizes NumPy e retorna os tipos corretos."""
    dummy_image = np.zeros((972, 1296, 3), dtype=np.uint8)

    result = detector.predict(dummy_image)

    assert isinstance(result, DetectionResult)
    assert isinstance(result.is_conforme, bool)
    assert isinstance(result.defects, list)
    assert isinstance(result.max_confidence, float)
    assert isinstance(result.annotated_image, np.ndarray)
    assert result.annotated_image.shape == dummy_image.shape
