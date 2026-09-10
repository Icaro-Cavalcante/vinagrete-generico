
import time

import numpy as np

from inference.camera import CameraController


def run_benchmark(num_samples: int = 50):
    print("[BENCHMARK] Inicializando Pi Camera 5...")
    cam = CameraController(resolution=(1296, 972))

    # Warm-up
    _ = cam.capture_frame()

    latencies = []
    print(f"[BENCHMARK] Executando {num_samples} capturas sequenciais...")

    for i in range(num_samples):
        t0 = time.perf_counter()
        _ = cam.capture_frame()
        t1 = time.perf_counter()

        elapsed_ms = (t1 - t0) * 1000
        latencies.append(elapsed_ms)

    cam.close()

    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)

    print("-" * 40)
    print(f"Média: {np.mean(latencies):.2f} ms")
    print(f"Mínima: {np.min(latencies):.2f} ms")
    print(f"P50 (Mediana): {p50:.2f} ms")
    print(f"P95: {p95:.2f} ms")
    print(f"Máxima: {np.max(latencies):.2f} ms")
    print("-" * 40)


if __name__ == "__main__":
    run_benchmark()
