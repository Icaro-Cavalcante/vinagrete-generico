import time
import cv2
import numpy as np
from config import CAMERA_FRAMERATE, CAMERA_INDEX, CAMERA_RESOLUTION


class CameraController:
    """Controlador de câmera híbrido para Raspberry Pi.

    Tenta utilizar Picamera2; se não disponível (ambiente Docker/slim),
    utiliza OpenCV V4L2 com warm-up e resiliência a falhas temporárias de frame.
    """

    def __init__(
        self,
        resolution: tuple = CAMERA_RESOLUTION,
        framerate: int = CAMERA_FRAMERATE,
        device_index: int = CAMERA_INDEX,
    ):
        self.use_picam2 = False
        self.picam2 = None
        self.cap = None
        self.consecutive_failures = 0
        self.max_failures = 15  # Tolerância a falhas consecutivas antes de lançar erro

        try:
            from picamera2 import Picamera2

            self.picam2 = Picamera2()
            config = self.picam2.create_video_configuration(
                main={"size": resolution, "format": "RGB888"},
                controls={"FrameRate": framerate},
            )
            self.picam2.configure(config)
            self.picam2.start()
            self.use_picam2 = True
            print("[CÂMERA] Inicializada via Picamera2.")
        except Exception as e:
            print(
                f"[CÂMERA] Picamera2 indisponível ({e}). Tentando OpenCV V4L2 no nó /dev/video{device_index}..."
            )
            self._init_opencv(device_index, resolution, framerate)

    def _init_opencv(self, device_index: int, resolution: tuple, framerate: int):
        if self.cap is not None:
            self.cap.release()

        self.cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        self.cap.set(cv2.CAP_PROP_FPS, framerate)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"Não foi possível abrir /dev/video{device_index} via OpenCV."
            )

        # Warm-up: lê e descarta os primeiros frames até o sensor estabilizar
        print("[CÂMERA] Executando warm-up do sensor...")
        for _ in range(10):
            self.cap.read()
            time.sleep(0.05)

        print(f"[CÂMERA] Inicializada via OpenCV V4L2 (/dev/video{device_index}).")

    def capture_frame(self) -> np.ndarray | None:
        """Captura o frame BGR mais recente.

        Retorna None em falhas pontuais de leitura sem interromper o
        loop.
        """
        if self.use_picam2 and self.picam2:
            rgb_frame = self.picam2.capture_array("main")
            return rgb_frame[:, :, ::-1]

        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.consecutive_failures += 1
            print(
                f"[CÂMERA] Aviso: Falha na leitura do frame ({self.consecutive_failures}/{self.max_failures})."
            )
            if self.consecutive_failures >= self.max_failures:
                raise RuntimeError(
                    "Múltiplas falhas consecutivas na leitura da câmera V4L2."
                )
            return None

        self.consecutive_failures = 0
        return frame

    def close(self):
        if self.use_picam2 and self.picam2:
            self.picam2.stop()
            self.picam2.close()
        elif self.cap and self.cap.isOpened():
            self.cap.release()
        print("[CÂMERA] Dispositivo liberado.")
