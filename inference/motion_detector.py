import cv2
import numpy as np
import os
import sys
from enum import Enum

# Adiciona o diretório raiz ao sys.path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import (
        BG_SUBTRACTOR_THRESHOLD,
        MIN_CONTOUR_AREA,
        ROI_X_BOUNDS,
    )
except ImportError:
    ROI_X_BOUNDS = (0, 10000)
    MIN_CONTOUR_AREA = 500
    BG_SUBTRACTOR_THRESHOLD = 50


class ItemState(Enum):
    SEARCHING = 1  # Aguardando objeto vindo do topo da ROI
    INSPECTING = 2  # Objeto no centro (esteira parada / inferência em curso)
    EXITING = 3  # Objeto em movimento de saída (ignora novos disparos)


class MotionDetector:
    def __init__(
        self,
        roi_x_bounds=ROI_X_BOUNDS,
        roi_y_bounds=(0, 10000),
        min_contour_area=MIN_CONTOUR_AREA,
        bg_subtractor_threshold=BG_SUBTRACTOR_THRESHOLD,
    ):
        self.roi_x_start = roi_x_bounds[0]
        self.roi_x_end = roi_x_bounds[1]
        self.roi_y_start = roi_y_bounds[0]
        self.roi_y_end = roi_y_bounds[1]

        self.min_contour_area = min_contour_area
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=bg_subtractor_threshold, detectShadows=True
        )

        self.state = ItemState.SEARCHING
        self.belt_moving = True

    def set_belt_moving(self, moving: bool):
        """Informa o estado da esteira para controlar o aprendizado do MOG2."""
        self.belt_moving = moving

    def reset_to_exiting(self):
        """Define o estado para EXITING logo após religar a esteira."""
        self.state = ItemState.EXITING

    def detect_motion_centered(self, frame: np.ndarray) -> bool:
        """
        Monitora a ROI no sentido de cima para baixo (Eixo Y).
        Retorna True exatamente UMA VEZ por objeto quando este atinge o centro vertical.
        """
        if frame is None:
            return False

        h, w = frame.shape[:2]

        # Limites X (largura)
        x_start = max(0, min(self.roi_x_start, w))
        x_end = max(0, min(self.roi_x_end, w))

        # Limites Y (altura)
        y_start = max(0, min(self.roi_y_start, h))
        y_end = max(0, min(self.roi_y_end, h))

        if x_start >= x_end or y_start >= y_end:
            return False

        roi = frame[y_start:y_end, x_start:x_end]
        roi_center_y = (y_end - y_start) // 2

        # Congela o aprendizado do MOG2 se a esteira estiver parada
        learning_rate = -1 if self.belt_moving else 0

        fg_mask = self.bg_subtractor.apply(roi, learningRate=learning_rate)
        _, fg_mask = cv2.threshold(fg_mask, 254, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(
            fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        largest_contour_area = 0
        largest_contour = None

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_contour_area and area > largest_contour_area:
                largest_contour_area = area
                largest_contour = contour

        centered_item_detected = False

        if largest_contour is not None:
            x, y, w_box, h_box = cv2.boundingRect(largest_contour)
            cy = y + h_box // 2  # Centro do objeto no Eixo Y relativo à ROI

            # --- MÁQUINA DE ESTADOS ---
            if self.state == ItemState.SEARCHING:
                # Se o objeto atingir a linha de centro em Y (tolerância de +/- 30px)
                if abs(cy - roi_center_y) < 30:
                    self.state = ItemState.INSPECTING
                    centered_item_detected = True

            elif self.state == ItemState.INSPECTING:
                # Aguarda o serial_handler processar a inferência
                pass

            # O item está se movendo para baixo (ultrapassou a linha central + margem de saída)
            elif self.state == ItemState.EXITING and cy > (roi_center_y + 50):
                self.state = ItemState.SEARCHING
        else:
            # Sem contornos visíveis na ROI -> pronto para o próximo item
            self.state = ItemState.SEARCHING

        return centered_item_detected
