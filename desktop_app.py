"""
Hand Gesture Computer Controller (Windows Desktop Edition)
Controls Windows Master Volume, Mouse Cursor, Left Click, and Photo Snapshots
"""

import cv2
import os
import time
import math
import ctypes
import pyautogui
from datetime import datetime
from hand_gesture import HandGesture

# =====================================================
# SETTINGS & SCREEN CALIBRATION
# =====================================================
pyautogui.PAUSE = 0.001
pyautogui.FAILSAFE = False

screen_width, screen_height = pyautogui.size()
print(f"🖥️ Detected Screen Size: {screen_width} x {screen_height}")

# Windows Native Multimedia Keys (100% Reliable Hardware Volume)
VK_VOLUME_UP = 0xAF
VK_VOLUME_DOWN = 0xAE

def volume_up():
    ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)

def volume_down():
    ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)

# =====================================================
# CAMERA INITIALIZATION
# =====================================================
print("🎥 Starting webcam...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap.release()
    cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ ERROR: Camera could not be opened.")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
print("✅ Camera active!")

hand_detector = HandGesture()

# =====================================================
# TIMERS & STATE
# =====================================================
last_capture = 0
last_click = 0
last_volume = 0

capture_delay = 2.5
click_delay = 0.5
volume_delay = 0.12  # Smooth fast volume stepping

previous_x = screen_width // 2
previous_y = screen_height // 2
smoothing = 0.45  # Exponential moving average for silky smooth cursor

print("=" * 70)
print("🖐️ HAND GESTURE CONTROLLER READY")
print("👉 INDEX FINGER: Move Windows Mouse Cursor")
print("🤏 PINCH (Thumb + Index): Left Click")
print("✌️ TWO FINGERS (Index + Middle): Volume UP 🔊")
print("✊ FIST (Closed Hand): Volume DOWN 🔉")
print("👍 THUMBS UP: Take Photo & Save to Desktop 📸")
print("Press 'Q' on keyboard to exit.")
print("=" * 70)

while True:
    success, frame = cap.read()
    if not success:
        time.sleep(0.02)
        continue

    # Mirror frame for natural interaction
    frame = cv2.flip(frame, 1)
    frame, landmarks = hand_detector.detect_hand(frame)
    gesture = "NO HAND DETECTED"
    now = time.time()

    if landmarks:
        wrist = landmarks[0]
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]

        index_pip = landmarks[6]
        middle_pip = landmarks[10]
        ring_pip = landmarks[14]
        pinky_pip = landmarks[18]

        # Palm scale normalization (distance from wrist to middle finger knuckle)
        palm_size = math.hypot(middle_pip.x - wrist.x, middle_pip.y - wrist.y)
        if palm_size < 1e-4:
            palm_size = 0.20

        # Relative extension checks
        index_up = index_tip.y < index_pip.y
        middle_up = middle_tip.y < middle_pip.y
        ring_up = ring_tip.y < ring_pip.y
        pinky_up = pinky_tip.y < pinky_pip.y
        thumb_up = thumb_tip.y < landmarks[3].y and thumb_tip.y < landmarks[2].y

        # Distance-invariant normalized pinch check
        pinch_dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
        norm_pinch = pinch_dist / palm_size
        is_pinch = norm_pinch < 0.35

        # -------------------------------------------------
        # 1. THUMBS UP -> CAPTURE PHOTO
        # -------------------------------------------------
        if thumb_up and not index_up and not middle_up and not ring_up and not pinky_up and not is_pinch:
            gesture = "THUMBS UP - CAPTURING PHOTO"
            if now - last_capture > capture_delay:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(desktop, f"gesture_photo_{timestamp}.jpg")
                cv2.imwrite(filename, frame)
                print(f"📸 Photo Saved: {filename}")
                last_capture = now

        # -------------------------------------------------
        # 2. TWO FINGERS (INDEX + MIDDLE) -> VOLUME UP
        # -------------------------------------------------
        elif index_up and middle_up and not ring_up and not pinky_up:
            gesture = "TWO FINGERS - VOLUME UP 🔊"
            if now - last_volume > volume_delay:
                volume_up()
                print("🔊 Volume UP (+)")
                last_volume = now

        # -------------------------------------------------
        # 3. FIST (ALL FINGERS CLOSED) -> VOLUME DOWN
        # -------------------------------------------------
        elif not index_up and not middle_up and not ring_up and not pinky_up and not thumb_up:
            gesture = "FIST - VOLUME DOWN 🔉"
            if now - last_volume > volume_delay:
                volume_down()
                print("🔉 Volume DOWN (-)")
                last_volume = now

        # -------------------------------------------------
        # 4. PINCH -> LEFT CLICK
        # -------------------------------------------------
        elif is_pinch:
            gesture = "PINCH - LEFT CLICK 🖱️"
            if now - last_click > click_delay:
                pyautogui.click()
                print("🖱️ Left Click Executed!")
                last_click = now

        # -------------------------------------------------
        # 5. INDEX POINT -> MOUSE CURSOR
        # -------------------------------------------------
        elif index_up and not middle_up and not ring_up and not pinky_up:
            gesture = "INDEX - MOUSE CURSOR 👆"
            
            # Active box calibration (maps 15%-85% camera area to 0%-100% monitor)
            norm_x = max(0.0, min(1.0, (index_tip.x - 0.15) / 0.70))
            norm_y = max(0.0, min(1.0, (index_tip.y - 0.15) / 0.70))

            target_x = int(norm_x * screen_width)
            target_y = int(norm_y * screen_height)

            current_x = previous_x + (target_x - previous_x) * smoothing
            current_y = previous_y + (target_y - previous_y) * smoothing

            pyautogui.moveTo(int(current_x), int(current_y))
            previous_x, previous_y = current_x, current_y

        elif index_up and middle_up and ring_up and pinky_up:
            gesture = "OPEN PALM - STANDBY ✋"

    # =====================================================
    # ON-SCREEN HUD OVERLAY
    # =====================================================
    # Header box
    cv2.rectangle(frame, (10, 10), (480, 200), (20, 20, 30), -1)
    cv2.rectangle(frame, (10, 10), (480, 200), (0, 220, 100), 2)

    cv2.putText(frame, f"Gesture: {gesture}", (25, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 120), 2)
    cv2.putText(frame, "👆 INDEX: Move Mouse", (25, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (240, 240, 240), 1)
    cv2.putText(frame, "🤏 PINCH: Left Click", (25, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (240, 240, 240), 1)
    cv2.putText(frame, "✌️ TWO FINGERS: Volume UP (+)", (25, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (240, 240, 240), 1)
    cv2.putText(frame, "✊ FIST: Volume DOWN (-)", (25, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (240, 240, 240), 1)
    cv2.putText(frame, "👍 THUMBS UP: Take Photo", (25, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (240, 240, 240), 1)

    cv2.imshow("Hand Gesture Computer Controller", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Closing controller...")
        break

cap.release()
cv2.destroyAllWindows()
print("Camera released and closed successfully.")
