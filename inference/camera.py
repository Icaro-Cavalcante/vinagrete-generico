import time
import cv2
import numpy as np
from config import CAMERA_FRAMERATE, CAMERA_INDEX, CAMERA_RESOLUTION, CAMERA_ROTATION


class CameraController:
    """Controlador de câmera híbrido para Raspberry Pi.

    Tenta utilizar Picamera2; se não disponível (ambiente Docker/slim),
    utiliza OpenCV V4L2 com suporte a MJPG, warm-up e auto-reconexão.
    """

    def __init__(
        self,
        resolution: tuple = CAMERA_RESOLUTION,
        framerate: int = CAMERA_FRAMERATE,
        device_index: int = CAMERA_INDEX,
        rotation: int = CAMERA_ROTATION,
    ):
        self.resolution = resolution
        self.framerate = framerate
        self.device_index = device_index
        self.rotation = rotation

        self.use_picam2 = False
        self.picam2 = None
        self.cap = None
        self.consecutive_failures = 0
        self.max_failures = 15

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
            self._init_opencv()

    def _init_opencv(self):
        # Pipeline GStreamer nativa da libcamera na RPi 5
        gst_pipeline = (
            f"libcamerasrc ! "
            f"video/x-raw, width={self.resolution[0]}, height={self.resolution[1]}, framerate={self.framerate}/1 ! "
            f"videoconvert ! appsink"
        )
        self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        
        if not self.cap.isOpened():
            print("[CÂMERA] Erro ao abrir pipeline GStreamer libcamera.")
            return False
        return True

    def capture_frame(self) -> np.ndarray | None:
        """Captura o frame BGR mais recente e aplica a rotação configurada.

        Em caso de falhas consecutivas, tenta reconectar ao hardware em vez de
        encerrar a aplicação.
        """
        frame = None
        if self.use_picam2 and self.picam2:
            rgb_frame = self.picam2.capture_array("main")
            frame = rgb_frame[:, :, ::-1]
        elif self.cap is not None and self.cap.isOpened():
            ret, cap_frame = self.cap.read()
            if not ret or cap_frame is None:
                self.consecutive_failures += 1
                print(
                    f"[CÂMERA] Aviso: Falha na leitura do frame ({self.consecutive_failures}/{self.max_failures})."
                )

                # Tenta reconectar a câmera se ultrapassar o limite de falhas
                if self.consecutive_failures >= self.max_failures:
                    print(
                        "[CÂMERA] Múltiplas falhas detectadas. Reinicializando o driver V4L2..."
                    )
                    self.consecutive_failures = 0
                    self._init_opencv()

                return None

            self.consecutive_failures = 0
            frame = cap_frame
        else:
            self._init_opencv()
            return None

        if frame is not None and self.rotation != 0:
            if self.rotation == 90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif self.rotation == 180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            elif self.rotation == 270:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        return frame

    def close(self):
        if self.use_picam2 and self.picam2:
            self.picam2.stop()
            self.picam2.close()
        elif self.cap and self.cap.isOpened():
            self.cap.release()
        print("[CÂMERA] Dispositivo liberado.")
