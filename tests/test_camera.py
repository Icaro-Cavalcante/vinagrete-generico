import time

import numpy as np
import pytest

from inference.camera import CameraController


@pytest.fixture(scope="module")
def camera():
    cam = CameraController(resolution=(1296, 972), framerate=60)
    # Warm-up: descarta os primeiros frames para estabilizar o buffer DMA
    for _ in range(5):
        _ = cam.capture_frame()
        time.sleep(0.01)
    yield cam
    cam.close()


def test_camera_capture_latency(camera):
    """Mede a latência em regime permanente utilizando a mediana (P50)."""
    iterations = 30
    latencies = []

    for _ in range(iterations):
        start_time = time.perf_counter()
        frame = camera.capture_frame()
        end_time = time.perf_counter()

        latencies.append((end_time - start_time) * 1000)
        assert frame is not None

    median_latency = np.median(latencies)
    p95_latency = np.percentile(latencies, 95)
    max_latency = np.max(latencies)

    print(f"\n[BENCHMARK] Capturas: {iterations}")
    print(f"[BENCHMARK] Mediana (P50): {median_latency:.2f} ms")
    print(f"[BENCHMARK] Percentil 95: {p95_latency:.2f} ms")
    print(f"[BENCHMARK] Máxima: {max_latency:.2f} ms")

    # A latência real em regime permanente deve ser menor que 25 ms
    assert median_latency < 25.0, (
        f"Mediana de latência ({median_latency:.2f} ms) excedeu o limite operacional de 25 ms."
    )
