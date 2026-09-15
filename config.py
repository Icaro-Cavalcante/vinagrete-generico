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

# Quantidade de defeitos consecutivos para disparar modo ALERTA (Controle de Danos)
CONSECUTIVE_DEFECTS_ALERT = int(os.getenv("CONSECUTIVE_DEFECTS_ALERT", "3"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////app/data/vinagrete.db")

# Configurações de ROI (Região de Interesse) da esteira
# Na câmera de 1296x972, a esteira centraliza entre X=450 e X=900
ROI_X_BOUNDS = tuple(
    int(x.strip()) for x in os.getenv("ROI_X_BOUNDS", "450,900").split(",")
)
ROI_Y_BOUNDS = tuple(
    int(y.strip()) for y in os.getenv("ROI_Y_BOUNDS", "0,972").split(",")
)

# Área mínima de contorno para acionar detecção (evita disparos falsos com ruído ou esteira vazia)
MIN_CONTOUR_AREA = int(os.getenv("MIN_CONTOUR_AREA", 8000))
BG_SUBTRACTOR_THRESHOLD = int(os.getenv("BG_SUBTRACTOR_THRESHOLD", 16))

# Recortar a ROI antes de enviar para inferência no modelo YOLO
CROP_TO_ROI = os.getenv("CROP_TO_ROI", "True").lower() in ("true", "1", "yes")

# Câmera
CAMERA_INDEX = 0
CAMERA_RESOLUTION = (1296, 972)
CAMERA_FRAMERATE = 60