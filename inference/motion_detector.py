import cv2
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ROI_X_BOUNDS, MIN_CONTOUR_AREA, BG_SUBTRACTOR_THRESHOLD

class MotionDetector:
    def __init__(self, roi_x_bounds=ROI_X_BOUNDS, min_contour_area=MIN_CONTOUR_AREA, bg_subtractor_threshold=BG_SUBTRACTOR_THRESHOLD):
        self.roi_x_start = roi_x_bounds[0]
        self.roi_x_end = roi_x_bounds[1]
        self.min_contour_area = min_contour_area
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=bg_subtractor_threshold, detectShadows=True)
        self.object_in_roi = False

    def detect_motion_centered(self, frame: np.ndarray) -> bool:
        """
        Monitors a Region of Interest (ROI) and detects when an item
        enters the ROI and reaches the geometric center.
        """
        if frame is None:
            return False

        # Ensure ROI bounds are within frame width
        h, w = frame.shape[:2]
        x_start = max(0, min(self.roi_x_start, w))
        x_end = max(0, min(self.roi_x_end, w))
        
        if x_start >= x_end:
            return False
            
        roi = frame[:, x_start:x_end]
        roi_center_x = (x_end - x_start) // 2
        
        fg_mask = self.bg_subtractor.apply(roi)
        _, fg_mask = cv2.threshold(fg_mask, 254, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        centered_item_detected = False
        largest_contour_area = 0
        largest_contour = None
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_contour_area and area > largest_contour_area:
                largest_contour_area = area
                largest_contour = contour
                
        if largest_contour is not None:
            x, y, w_box, h_box = cv2.boundingRect(largest_contour)
            cx = x + w_box // 2
            
            # Use a tolerance for centering
            if abs(cx - roi_center_x) < 20: 
                if not self.object_in_roi:
                    self.object_in_roi = True
                    centered_item_detected = True
            else:
                # Reset if object moves away from center
                if abs(cx - roi_center_x) > 40:
                    self.object_in_roi = False
        else:
            self.object_in_roi = False
            
        return centered_item_detected
