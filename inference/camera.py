import cv2
import numpy as np


class CameraController:
    """Controlador de câmera híbrido para Raspberry Pi.

    Tenta utilizar Picamera2 (alta performance no Pi 5); se não disponível
    (como no ambiente Docker), faz o fallback automático para OpenCV (V4L2).
    """

    def __init__(
        self,
        resolution: tuple = (1296, 972),
        framerate: int = 60,
        device_index: int = 0,
    ):
        self.use_picam2 = False
        self.picam2 = None
        self.cap = None

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
            print("[CÂMERA] Inicializada com sucesso via Picamera2.")
        except Exception as e:
            print(
                f"[CÂMERA] Picamera2 indisponível ({e}). Alternando para OpenCV V4L2..."
            )
            self.cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, framerate)

            if not self.cap.isOpened():
                raise RuntimeError(
                    f"Não foi possível abrir o dispositivo de vídeo /dev/video{device_index} via OpenCV."
                )
            print(
                f"[CÂMERA] Inicializada com sucesso via OpenCV (/dev/video{device_index})."
            )

    def capture_frame(self) -> np.ndarray:
        """Captura o frame mais recente no formato BGR (padrão OpenCV)."""
        if self.use_picam2 and self.picam2:
            rgb_frame = self.picam2.capture_array("main")
            return rgb_frame[:, :, ::-1]

        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise RuntimeError("Falha ao ler frame do dispositivo de câmera V4L2.")
        return frame

    def close(self):
        """Libera os recursos de captura de vídeo."""
        if self.use_picam2 and self.picam2:
            self.picam2.stop()
            self.picam2.close()
        elif self.cap and self.cap.isOpened():
            self.cap.release()
        print("[CÂMERA] Dispositivo liberado.")
