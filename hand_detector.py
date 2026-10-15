from __future__ import annotations

import os
import sys
import time

os.environ.setdefault("GLOG_minloglevel", "2")

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]

FINGER_TIPS = [4, 8, 12, 16, 20]
FINGER_PIPS = [3, 6, 10, 14, 18]

WRIST = 0
THUMB_TIP = 4
INDEX_TIP = 8
MIDDLE_MCP = 9

GESTURE_NONE = "sin mano"
GESTURE_OPEN = "mano abierta"
GESTURE_FIST = "puño"
GESTURE_PINCH = "pinza"
GESTURE_MID = "intermedia"

def resource_path(*parts):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


MODEL_PATH = resource_path("assets", "hand_landmarker.task")


class Detection:

    __slots__ = ("flap", "gesture", "fingers", "hand_visible", "pinch_ratio", "points")

    def __init__(self, flap, gesture, fingers, hand_visible, pinch_ratio, points):
        self.flap = flap
        self.gesture = gesture
        self.fingers = fingers
        self.hand_visible = hand_visible
        self.pinch_ratio = pinch_ratio
        self.points = points


class HandDetector:

    def __init__(
        self,
        model_path=MODEL_PATH,
        max_hands=1,
        mode="pinch",
        detection_confidence=0.6,
        presence_confidence=0.5,
        tracking_confidence=0.5,
        flap_cooldown=0.30,
        pinch_enter=0.25,
        pinch_exit=0.40,
        pinch_index_min=0.50,
    ):
        if mode not in ("pinch", "open", "both"):
            raise ValueError(f"modo de gesto no válido: {mode!r}")
        self.mode = mode
        self.flap_cooldown = flap_cooldown
        self.pinch_enter = pinch_enter
        self.pinch_exit = pinch_exit
        self.pinch_index_min = pinch_index_min

        options = mp_vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=model_path),
            running_mode=mp_vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_hand_presence_confidence=presence_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self._landmarker = mp_vision.HandLandmarker.create_from_options(options)

        self._pinched = False
        self._open = False
        self._last_flap = 0.0

    def process(self, bgr_frame, timestamp_ms):
        rgb = bgr_frame[:, :, ::-1]
        rgb = np.ascontiguousarray(rgb)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        if not result.hand_landmarks:
            self._pinched = False
            self._open = False
            return Detection(False, GESTURE_NONE, 0, False, None, [])

        h, w = bgr_frame.shape[:2]
        landmarks = result.hand_landmarks[0]
        points = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

        fingers = self._count_extended(points)
        is_open = fingers >= 4
        ratio, index_ext = self._pinch_metrics(points)

        below = ratio < (self.pinch_exit if self._pinched else self.pinch_enter)
        pinched = below and index_ext > self.pinch_index_min

        if pinched:
            gesture = GESTURE_PINCH
        elif is_open:
            gesture = GESTURE_OPEN
        elif fingers <= 1:
            gesture = GESTURE_FIST
        else:
            gesture = GESTURE_MID

        flap = self._detect_flap(pinched, is_open)

        self._pinched = pinched
        self._open = is_open
        return Detection(flap, gesture, fingers, True, ratio, points)

    def close(self):
        self._landmarker.close()

    def _detect_flap(self, pinched, is_open):
        triggered = False
        if self.mode in ("pinch", "both"):
            triggered = triggered or (pinched and not self._pinched)
        if self.mode in ("open", "both"):
            triggered = triggered or (is_open and not self._open)
        if not triggered:
            return False
        now = time.time()
        if (now - self._last_flap) < self.flap_cooldown:
            return False
        self._last_flap = now
        return True

    @staticmethod
    def _count_extended(points):
        wrist = np.array(points[WRIST], dtype=float)
        count = 0
        for tip, pip in zip(FINGER_TIPS[1:], FINGER_PIPS[1:]):
            d_tip = np.linalg.norm(np.array(points[tip], dtype=float) - wrist)
            d_pip = np.linalg.norm(np.array(points[pip], dtype=float) - wrist)
            if d_tip > d_pip * 1.1:
                count += 1
        d_tip = np.linalg.norm(np.array(points[THUMB_TIP], dtype=float) - wrist)
        d_mcp = np.linalg.norm(np.array(points[2], dtype=float) - wrist)
        if d_tip > d_mcp * 1.2:
            count += 1
        return count

    @staticmethod
    def _pinch_metrics(points):
        p = np.asarray(points, dtype=float)
        palm = np.linalg.norm(p[WRIST] - p[MIDDLE_MCP])
        if palm < 1e-6:
            return 1.0, 0.0
        pinch = np.linalg.norm(p[THUMB_TIP] - p[INDEX_TIP]) / palm
        index_ext = np.linalg.norm(p[5] - p[INDEX_TIP]) / palm
        return float(pinch), float(index_ext)

    def annotate(self, bgr_frame, detection):
        frame = bgr_frame.copy()
        points = detection.points

        if len(points) == 21:
            for a, b in HAND_CONNECTIONS:
                cv2.line(frame, points[a], points[b], (0, 255, 0), 2)
            for (x, y) in points:
                cv2.circle(frame, (x, y), 4, (0, 0, 255), -1)

            if detection.gesture == GESTURE_PINCH:
                mid = ((points[THUMB_TIP][0] + points[INDEX_TIP][0]) // 2,
                       (points[THUMB_TIP][1] + points[INDEX_TIP][1]) // 2)
                cv2.line(frame, points[THUMB_TIP], points[INDEX_TIP], (0, 215, 255), 3)
                cv2.circle(frame, mid, 12, (0, 215, 255), 2)

        label = f"{detection.gesture}  ({detection.fingers} dedos)"
        if detection.pinch_ratio is not None:
            label += f"  pinza={detection.pinch_ratio:.2f}"
        cv2.putText(frame, label, (12, 32), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame, label, (12, 32), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (255, 255, 255), 2, cv2.LINE_AA)
        return frame
