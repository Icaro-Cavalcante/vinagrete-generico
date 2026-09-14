import os

SERIAL_PORT = os.getenv("SERIAL_PORT", "/dev/ttyUSB0")
BAUD_RATE = int(os.getenv("BAUD_RATE", 115200))
MODEL_PATH = os.getenv("MODEL_PATH", "weights/best.pt")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////app/data/vinagrete.db")

# Motion/ROI settings
# Example values, can be overridden by env variables if desired
ROI_X_BOUNDS = (100, 540)
MIN_CONTOUR_AREA = int(os.getenv("MIN_CONTOUR_AREA", 500))
BG_SUBTRACTOR_THRESHOLD = int(os.getenv("BG_SUBTRACTOR_THRESHOLD", 16))

# Câmera
CAMERA_INDEX = 0  
CAMERA_RESOLUTION = (1296, 972)
CAMERA_FRAMERATE = 60