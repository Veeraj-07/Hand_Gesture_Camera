"""
Hand Gesture Computer Controller (Windows Desktop Edition)
Controls Windows Master Volume, Mouse Cursor, Left Click, and Photo Snapshots
"""

import cv2
import os
import time
import math
import winsound
import pyautogui
from datetime import datetime
from hand_gesture import HandGesture

# =====================================================
# WINDOWS AUDIO VOLUME (Direct PyCaw Interface)
# =====================================================
try:
    from pycaw.pycaw import AudioUtilities
    speakers = AudioUtilities.GetSpeakers()
    volume_interface = speakers.EndpointVolume
    print("✅ Direct Windows Master Volume: ACTIVE")
except Exception as e:
    volume_interface = None
    print("⚠️ Volume Interface warning:", e)

def set_volume_delta(delta: float):
    if volume_interface:
        try:
            cur = volume_interface.GetMasterVolumeLevelScalar()
            new_v = max(0.0, min(1.0, cur + delta))
            volume_interface.SetMasterVolumeLevelScalar(new_v, None)
            return int(new_v * 100)
        except Exception:
            pass
    return None

def get_current_volume():
    if volume_interface:
        try:
            return int(volume_interface.GetMasterVolumeLevelScalar() * 100)
        except Exception:
            pass
    return 50

# =====================================================
# SETTINGS & SCREEN CALIBRATION
# =====================================================
pyautogui.PAUSE = 0.001
pyautogui.FAILSAFE = False

screen_width, screen_height = pyautogui.size()
print(f"🖥️ Monitor Screen Size: {screen_width} x {screen_height}")

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
print("✅ Webcam Live!")

hand_detector = HandGesture()

# Timers
last_capture = 0
last_click = 0
last_volume = 0

capture_delay = 2.0
click_delay = 0.6
volume_delay = 0.15

previous_x = screen_width // 2
previous_y = screen_height // 2
smoothing = 0.40

# Visual feedback banner timer
notification_text = ""
notification_timer = 0

print("=" * 75)
print("🖐️ HAND GESTURE SYSTEM CONTROLLER IS RUNNING")
print("👉 INDEX FINGER ONLY: Moves Windows Mouse Cursor")
print("🤏 PINCH (Thumb tip + Index tip touching): Left Click")
print("✌️ TWO FINGERS (Index + Middle Up): Volume UP 🔊")
print("✊ FIST (All 4 fingers curled down): Volume DOWN 🔉")
print("👍 THUMBS UP: Takes Photo & Saves directly to your Desktop 📸")
print("Press 'Q' to quit.")
print("=" * 75)

while True:
    success, frame = cap.read()
    if not success:
        time.sleep(0.02)
        continue

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    frame, landmarks = hand_detector.detect_hand(frame)
    gesture = "NO HAND DETECTED"
    now = time.time()

    if landmarks:
        wrist = landmarks[0]
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]

        index_tip = landmarks[8]
        index_dip = landmarks[7]
        index_pip = landmarks[6]
        index_mcp = landmarks[5]

        middle_tip = landmarks[12]
        middle_pip = landmarks[10]
        middle_mcp = landmarks[9]

        ring_tip = landmarks[16]
        ring_pip = landmarks[14]

        pinky_tip = landmarks[20]
        pinky_pip = landmarks[18]

        # Palm span for distance normalization
        palm_size = math.hypot(middle_mcp.x - wrist.x, middle_mcp.y - wrist.y)
        if palm_size < 1e-4:
            palm_size = 0.20

        # Finger Extension Logic (tip above pip in inverted screen space)
        index_extended = index_tip.y < index_pip.y
        middle_extended = middle_tip.y < middle_pip.y
        ring_extended = ring_tip.y < ring_pip.y
        pinky_extended = pinky_tip.y < pinky_pip.y

        # Thumb Up: thumb tip is significantly higher than thumb joint & index knuckle
        thumb_is_up = (thumb_tip.y < thumb_ip.y - 0.04) and (thumb_tip.y < index_mcp.y - 0.03)

        # Pinch: thumb tip and index tip close together
        pinch_dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y) / palm_size
        is_pinch = pinch_dist < 0.28

        # -----------------------------------------------------------------
        # GESTURE 1: THUMBS UP -> TAKE PHOTO & SAVE TO DESKTOP
        # -----------------------------------------------------------------
        if thumb_is_up and not index_extended and not middle_extended and not ring_extended and not pinky_extended:
            gesture = "THUMBS UP (Photo Capture)"
            if now - last_capture > capture_delay:
                desktop_folder = os.path.join(os.path.expanduser("~"), "Desktop")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(desktop_folder, f"hand_photo_{timestamp}.jpg")
                cv2.imwrite(save_path, frame)
                print(f"\n📸 PHOTO CAPTURED & SAVED TO: {save_path}")
                try:
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
                except Exception:
                    pass
                notification_text = f"📸 PHOTO SAVED: hand_photo_{timestamp}.jpg"
                notification_timer = now + 2.0
                last_capture = now

        # -----------------------------------------------------------------
        # GESTURE 2: TWO FINGERS (PEACE) -> VOLUME UP
        # -----------------------------------------------------------------
        elif index_extended and middle_extended and not ring_extended and not pinky_extended and not is_pinch:
            gesture = "TWO FINGERS (Volume UP 🔊)"
            if now - last_volume > volume_delay:
                vol_pct = set_volume_delta(+0.04)
                if vol_pct is not None:
                    print(f"🔊 Volume Increased -> {vol_pct}%")
                    notification_text = f"🔊 Volume: {vol_pct}%"
                    notification_timer = now + 1.0
                last_volume = now

        # -----------------------------------------------------------------
        # GESTURE 3: FIST (CLOSED HAND) -> VOLUME DOWN
        # -----------------------------------------------------------------
        elif not index_extended and not middle_extended and not ring_extended and not pinky_extended and not thumb_is_up:
            gesture = "FIST (Volume DOWN 🔉)"
            if now - last_volume > volume_delay:
                vol_pct = set_volume_delta(-0.04)
                if vol_pct is not None:
                    print(f"🔉 Volume Decreased -> {vol_pct}%")
                    notification_text = f"🔉 Volume: {vol_pct}%"
                    notification_timer = now + 1.0
                last_volume = now

        # -----------------------------------------------------------------
        # GESTURE 4: PINCH -> LEFT CLICK
        # -----------------------------------------------------------------
        elif is_pinch and not ring_extended and not pinky_extended:
            gesture = "PINCH (Left Click 🖱️)"
            if now - last_click > click_delay:
                pyautogui.click()
                print("🖱️ LEFT CLICK TRIGGERED!")
                try:
                    winsound.MessageBeep(winsound.MB_OK)
                except Exception:
                    pass
                notification_text = "🖱️ CLICK!"
                notification_timer = now + 0.8
                last_click = now

        # -----------------------------------------------------------------
        # GESTURE 5: INDEX POINT -> MOVE MOUSE CURSOR
        # -----------------------------------------------------------------
        elif index_extended and not middle_extended and not ring_extended and not pinky_extended:
            gesture = "INDEX POINT (Mouse Cursor 👆)"
            
            # Map central 15% - 85% of camera frame to 0% - 100% of Windows screen
            norm_x = max(0.0, min(1.0, (index_tip.x - 0.15) / 0.70))
            norm_y = max(0.0, min(1.0, (index_tip.y - 0.15) / 0.70))

            target_x = int(norm_x * screen_width)
            target_y = int(norm_y * screen_height)

            current_x = previous_x + (target_x - previous_x) * smoothing
            current_y = previous_y + (target_y - previous_y) * smoothing

            pyautogui.moveTo(int(current_x), int(current_y))
            previous_x, previous_y = current_x, current_y

        # -----------------------------------------------------------------
        # GESTURE 6: OPEN PALM
        # -----------------------------------------------------------------
        elif index_extended and middle_extended and ring_extended and pinky_extended:
            gesture = "OPEN PALM (Standby ✋)"

    # =====================================================
    # HUD OVERLAY
    # =====================================================
    cur_vol = get_current_volume()
    cv2.rectangle(frame, (15, 15), (540, 230), (15, 15, 25), -1)
    cv2.rectangle(frame, (15, 15), (540, 230), (0, 255, 130), 2)

    cv2.putText(frame, f"Gesture: {gesture}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 150), 2)
    cv2.putText(frame, f"System Master Volume: {cur_vol}%", (30, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
    cv2.putText(frame, "👆 INDEX: Move Mouse Cursor", (30, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (240, 240, 240), 1)
    cv2.putText(frame, "🤏 PINCH: Left Click", (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (240, 240, 240), 1)
    cv2.putText(frame, "✌️ TWO FINGERS: Volume UP (+)", (30, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 220, 255), 1)
    cv2.putText(frame, "✊ FIST: Volume DOWN (-)", (30, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 220, 255), 1)
    cv2.putText(frame, "👍 THUMBS UP: Save Photo to Desktop", (30, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 100), 1)

    # Active notification banner
    if now < notification_timer and notification_text:
        cv2.rectangle(frame, (w // 2 - 250, h - 70), (w // 2 + 250, h - 20), (0, 180, 80), -1)
        cv2.rectangle(frame, (w // 2 - 250, h - 70), (w // 2 + 250, h - 20), (255, 255, 255), 2)
        cv2.putText(frame, notification_text, (w // 2 - 230, h - 38), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    cv2.imshow("Hand Gesture Computer Controller", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\nExiting controller...")
        break

cap.release()
cv2.destroyAllWindows()
print("Camera closed.")
