import time
import numpy as np
import pytest
from inference.motion_detector import MotionDetector, ItemState


def test_motion_detector_warmup_and_lifecycle():
    detector = MotionDetector(
        roi_x_bounds=(100, 540),
        roi_y_bounds=(0, 972),
        min_contour_area=500,
        bg_subtractor_threshold=16,
        min_exit_time_sec=0.2,
    )
    detector.min_warmup_frames = 5

    # 1. Warm-up frames should NEVER trigger
    empty_frame = np.zeros((972, 1296, 3), dtype=np.uint8)
    for _ in range(5):
        assert not detector.detect_motion_centered(empty_frame)

    # 2. Frame with centered object (center Y is 486)
    frame_with_box = np.zeros((972, 1296, 3), dtype=np.uint8)
    frame_with_box[436:536, 250:350] = 255

    # Trigger detection
    triggered = detector.detect_motion_centered(frame_with_box)
    assert triggered
    assert detector.state == ItemState.INSPECTING

    # While INSPECTING, cannot trigger again
    assert not detector.detect_motion_centered(frame_with_box)

    # 3. Reset to EXITING
    detector.reset_to_exiting()
    assert detector.state == ItemState.EXITING

    # While in time lock (< min_exit_time_sec), cannot trigger
    assert not detector.detect_motion_centered(frame_with_box)

    # Wait for temporal lock to expire
    time.sleep(0.25)

    # Even after time lock, if object is STILL in center (cy=486), it MUST NOT re-trigger!
    assert not detector.detect_motion_centered(frame_with_box)
    assert detector.state == ItemState.EXITING

    # 4. Now move object away from center (> 60px away, e.g. cy = 486 + 100 = 586)
    frame_moved_away = np.zeros((972, 1296, 3), dtype=np.uint8)
    frame_moved_away[536:636, 250:350] = 255

    # Object has moved away -> state should transition to SEARCHING
    assert not detector.detect_motion_centered(frame_moved_away)
    assert detector.state == ItemState.SEARCHING
