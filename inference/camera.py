import numpy as np


class CameraController:
    """
    Controlador de câmera otimizado para Raspberry Pi 5 via Picamera2.
    """

    def __init__(self, resolution: tuple = (1296, 972)):
        try:
            from picamera2 import Picamera2
        except ImportError:
            raise RuntimeError(
                "Biblioteca 'picamera2' não encontrada. "
                "Certifique-se de usar o ambiente com acesso aos pacotes do sistema ou instalar o suporte libcamera."
            )

        self.picam2 = Picamera2()
        config = self.picam2.create_still_configuration(
            main={"size": resolution, "format": "RGB888"}
        )
        self.picam2.configure(config)
        self.picam2.start()

    def capture_frame(self) -> np.ndarray:
        """
        Captura o frame direto do buffer de memória e converte para BGR (padrão OpenCV/YOLO).
        """
        rgb_frame = self.picam2.capture_array()
        # Converte RGB para BGR
        return rgb_frame[:, :, ::-1]

    def close(self):
        """Encerra a instância da câmera liberando o recurso."""
        self.picam2.stop()
        self.picam2.close()
