import numpy as np
import pytest

from inference.camera import CameraController


def test_camera_capture_returns_valid_frame():
    """Valida se a câmera retorna uma matriz NumPy válida e não vazia."""
    camera = CameraController(camera_index=0)

    frame = camera.capture_frame()

    assert frame is not None, "O frame capturado não deve ser Nulo."
    assert isinstance(frame, np.ndarray), "O retorno deve ser um ndarray do NumPy."
    assert frame.size > 0, "A imagem capturada não pode estar vazia."
    assert len(frame.shape) == 3, (
        "A imagem deve possuir 3 dimensões (Altura, Largura, Canais)."
    )
    assert frame.shape[2] == 3, (
        "A imagem deve estar no formato de 3 canais de cor (BGR)."
    )


def test_camera_invalid_index():
    """Valida se o controlador lança erro ao tentar acessar um dispositivo inexistente."""
    camera = CameraController(camera_index=99)

    with pytest.raises(RuntimeError):
        camera.capture_frame()
