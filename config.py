import os

SERIAL_PORT = os.getenv("SERIAL_PORT", "/dev/ttyUSB0")
BAUD_RATE = int(os.getenv("BAUD_RATE", 115200))

MODEL_PATH = os.getenv("MODEL_PATH", "weights/best.pt")

# Classes de defeito configuráveis (temos apenas 'good' e 'miscut')
# 'miscut' é considerado defeito; 'good' é considerado conforme
DEFECT_CLASSES = set(
    cls.strip().lower()
    for cls in os.getenv("DEFECT_CLASSES", "miscut").split(",")
    if cls.strip()
)

# Limiar de confiança para considerar defeito
CONF_THRESHOLD = float(os.getenv("CONF_THRESHOLD", "0.5"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////app/data/vinagrete.db")

# Recortar a ROI antes de enviar para inferência no modelo YOLO
CROP_TO_ROI = os.getenv("CROP_TO_ROI", "False").lower() in ("true", "1", "yes")


# Câmera
CAMERA_INDEX = 0
CAMERA_RESOLUTION = (1296, 972)
CAMERA_FRAMERATE = 60

# MotionROI settings
ROI_DIMENSIONS = (400, 400) # (width, height)
MIN_CONTOUR_AREA = int(os.getenv("MIN_CONTOUR_AREA", 500))
BG_SUBTRACTOR_THRESHOLD = int(os.getenv("BG_SUBTRACTOR_THRESHOLD", 16))

# Tamanho da imagem enviada para a inferência/armazenamento quando CROP_TO_ROI for False
INFERENCE_IMAGE_SIZE = (800, 800)  # (width, height)

# Quantidade de falhas consecutivas necessárias para disparar o alerta
DEFECT_ALERT_THRESHOLD = int(os.getenv("DEFECT_ALERT_THRESHOLD", 3))

# Constantes de comunicação serial
CMD_STOP    = "STOP\n"
CMD_START   = "START\n"
CMD_ALERT   = "ALERT\n"
CMD_SYS_ON  = "SYS_ON"
CMD_SYS_OFF = "SYS_OFF"