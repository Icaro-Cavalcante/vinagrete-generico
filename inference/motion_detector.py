import os
import sys
import time
from enum import Enum

import cv2
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import BG_SUBTRACTOR_THRESHOLD, MIN_CONTOUR_AREA, ROI_DIMENSIONS
except ImportError:
    ROI_DIMENSIONS = (440, 972)
    MIN_CONTOUR_AREA = 500
    BG_SUBTRACTOR_THRESHOLD = 50


class ItemState(Enum):
    SEARCHING = 1  # Aguardando objeto vindo do topo
    INSPECTING = 2  # Objeto no centro (inferência / esteira parada)
    EXITING = 3  # Objeto saindo (bloqueia qualquer re-disparo)


class MotionDetector:
    def __init__(
        self,
        roi_dimensions=ROI_DIMENSIONS,
        min_contour_area=MIN_CONTOUR_AREA,
        bg_subtractor_threshold=BG_SUBTRACTOR_THRESHOLD,
        min_exit_time_sec=1.2,  # Tempo mínimo para ignorar re-disparos na saída
    ):
        self.roi_dimensions = roi_dimensions

        self.min_contour_area = min_contour_area
        self.min_exit_time_sec = min_exit_time_sec

        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=bg_subtractor_threshold, detectShadows=False
        )

        self.state = ItemState.SEARCHING
        self.belt_moving = True
        self.exit_start_time = 0.0
        self.empty_frames_count = 0
        self.warmup_frames = 0
        self.min_warmup_frames = 15

    def set_belt_moving(self, moving: bool):
        self.belt_moving = moving

    def reset_to_exiting(self):
        """Inicia a trava do estado EXITING com temporizador."""
        self.state = ItemState.EXITING
        self.exit_start_time = time.time()
        self.empty_frames_count = 0

    def detect_motion_centered(self, frame: np.ndarray) -> bool:
        if frame is None:
            return False

        h, w = frame.shape[:2]
        
        roi_w, roi_h = self.roi_dimensions
        roi_w = min(roi_w, w)
        roi_h = min(roi_h, h)
        
        x_center, y_center = w // 2, h // 2
        x_start = x_center - roi_w // 2
        x_end = x_start + roi_w
        y_start = y_center - roi_h // 2
        y_end = y_start + roi_h

        if x_start >= x_end or y_start >= y_end:
            return False

        roi = frame[y_start:y_end, x_start:x_end]
        roi_center_y = (y_end - y_start) // 2
        roi_area = (x_end - x_start) * (y_end - y_start)
        max_contour_area = int(roi_area * 0.85)

        # Congela o aprendizado do MOG2 enquanto a esteira estiver parada
        learning_rate = -1 if self.belt_moving else 0
        fg_mask = self.bg_subtractor.apply(roi, learningRate=learning_rate)
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)

        # Período de aquecimento inicial do MOG2 para convergir o modelo de fundo
        if self.warmup_frames < self.min_warmup_frames:
            self.warmup_frames += 1
            return False

        contours, _ = cv2.findContours(
            fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        largest_contour = None
        largest_area = 0
        for c in contours:
            area = cv2.contourArea(c)
            if self.min_contour_area < area < max_contour_area and area > largest_area:
                largest_area = area
                largest_contour = c

        # --- MÁQUINA DE ESTADOS ---

        if self.state == ItemState.EXITING:
            # 1. TRAVA TEMPORAL: Ignora absolutamente qualquer leitura nos primeiros N segundos pós-START
            if time.time() - self.exit_start_time < self.min_exit_time_sec:
                return False

            # 2. Só retorna a SEARCHING se o item se afastou do centro (> 60px) OU sumiu por 5 frames seguidos
            if largest_contour is not None:
                x, y, w_box, h_box = cv2.boundingRect(largest_contour)
                cy = y + h_box // 2
                if abs(cy - roi_center_y) > 60:
                    self.state = ItemState.SEARCHING
                    self.empty_frames_count = 0
            else:
                self.empty_frames_count += 1
                if self.empty_frames_count >= 5:
                    self.state = ItemState.SEARCHING
                    self.empty_frames_count = 0

            return False

        elif self.state == ItemState.INSPECTING:
            return False

        elif self.state == ItemState.SEARCHING:
            if largest_contour is not None:
                x, y, w_box, h_box = cv2.boundingRect(largest_contour)
                cy = y + h_box // 2

                # Gatilho de parada: Objeto atingiu a faixa central (Eixo Y)
                if abs(cy - roi_center_y) < 35:
                    self.state = ItemState.INSPECTING
                    return True

        return False
