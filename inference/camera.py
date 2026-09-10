import cv2
import numpy as np


class CameraController:
    """
    Abstração para captura da Pi Camera na Raspberry Pi 5.
    """

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index

    def capture_frame(self) -> np.ndarray:
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError("Erro ao conectar à Pi Camera.")

        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise RuntimeError("Falha ao capturar o frame da Pi Camera.")

        return frame
