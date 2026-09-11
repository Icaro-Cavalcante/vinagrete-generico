import numpy as np


class CameraController:
    """
    Controlador de câmera otimizado para Raspberry Pi 5 via Picamera2.
    Utiliza modo de vídeo contínuo em RAM para captura instantânea (< 15 ms).
    """

    def __init__(self, resolution: tuple = (1296, 972), framerate: int = 60):
        try:
            from picamera2 import Picamera2
        except ImportError:
            raise RuntimeError("Biblioteca 'picamera2' não encontrada.")

        self.picam2 = Picamera2()

        # Configuração de vídeo para manter o sensor continuamente ativo
        config = self.picam2.create_video_configuration(
            main={"size": resolution, "format": "RGB888"},
            controls={"FrameRate": framerate},
        )
        self.picam2.configure(config)
        self.picam2.start()

    def capture_frame(self) -> np.ndarray:
        """
        Captura o frame mais recente do buffer DMA na memória.
        """
        rgb_frame = self.picam2.capture_array("main")
        # Converte RGB para BGR (padrão OpenCV)
        return rgb_frame[:, :, ::-1]

    def close(self):
        """Encerra a instância da câmera liberando o recurso."""
        self.picam2.stop()
        self.picam2.close()
