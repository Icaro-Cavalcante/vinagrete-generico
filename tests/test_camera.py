import time

import numpy as np
import pytest

from inference.camera import CameraController


@pytest.fixture
def camera():
    cam = CameraController()
    yield cam
    cam.close()


def test_camera_capture_returns_valid_frame(camera):
    """Valida se a câmera retorna uma matriz BGR válida."""
    frame = camera.capture_frame()

    assert frame is not None, "O frame capturado não deve ser Nulo."
    assert isinstance(frame, np.ndarray), "O retorno deve ser um ndarray do NumPy."
    assert frame.size > 0, "A imagem capturada não pode estar vazia."
    assert len(frame.shape) == 3, (
        "A imagem deve possuir 3 dimensões (Altura, Largura, Canais)."
    )
    assert frame.shape[2] == 3, "A imagem deve estar no formato de 3 canais de cor."

def test_camera_capture_latency(camera):
    """Mede a latência de captura individual em múltiplos ciclos."""
    iterations = 20
    latencies = []

    for _ in range(iterations):
        start_time = time.perf_counter()
        frame = camera.capture_frame()
        end_time = time.perf_counter()

        latency_ms = (end_time - start_time) * 1000
        latencies.append(latency_ms)

        assert frame is not None

    avg_latency = np.mean(latencies)
    min_latency = np.min(latencies)
    max_latency = np.max(latencies)

    print(f"\n[BENCHMARK] Capturas: {iterations}")
    print(f"[BENCHMARK] Média: {avg_latency:.2f} ms")
    print(f"[BENCHMARK] Mínima: {min_latency:.2f} ms")
    print(f"[BENCHMARK] Máxima: {max_latency:.2f} ms")

    # Validação de tolerância para operação em tempo real na esteira (meta: < 35 ms)
    assert avg_latency < 35.0, (
        f"Latência média ({avg_latency:.2f} ms) excedeu o limite máximo aceitável de 35 ms."
    )