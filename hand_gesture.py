import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_PATH = os.path.join(BASE_DIR, "hand_landmarker.task")

class HandGesture:
    def __init__(self):
        if not os.path.exists(TASK_PATH):
            raise FileNotFoundError(f"Model file not found at: {TASK_PATH}")

        base_options = python.BaseOptions(
            model_asset_path=TASK_PATH
        )

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1,
            min_hand_detection_confidence=0.35,
            min_hand_presence_confidence=0.35,
            min_tracking_confidence=0.35
        )

        self.detector = vision.HandLandmarker.create_from_options(options)

    def detect_hand(self, frame):
        # Keep clean natural lighting
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame = np.ascontiguousarray(rgb_frame)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        result = self.detector.detect(mp_image)
        landmarks = None

        if result.hand_landmarks and len(result.hand_landmarks) > 0:
            landmarks = result.hand_landmarks[0]
            points = []
            h, w, _ = frame.shape

            for lm in landmarks:
                px = int(lm.x * w)
                py = int(lm.y * h)
                points.append((px, py))

            # Hand skeleton connections
            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
                (0, 5), (5, 6), (6, 7), (7, 8),        # Index
                (0, 9), (9, 10), (10, 11), (11, 12),   # Middle
                (0, 13), (13, 14), (14, 15), (15, 16), # Ring
                (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
                (5, 9), (9, 13), (13, 17)              # Palm base
            ]

            # Draw bones
            for start, end in connections:
                if start < len(points) and end < len(points):
                    cv2.line(frame, points[start], points[end], (0, 255, 128), 3)

            # Draw joints
            for idx, (px, py) in enumerate(points):
                # Highlight tips
                if idx in [4, 8, 12, 16, 20]:
                    cv2.circle(frame, (px, py), 9, (255, 0, 128), -1)
                    cv2.circle(frame, (px, py), 9, (255, 255, 255), 2)
                else:
                    cv2.circle(frame, (px, py), 6, (0, 220, 255), -1)
                    cv2.circle(frame, (px, py), 6, (0, 0, 0), 1)

        return frame, landmarks
