"""
Universal Hand Gesture Application
1. When deployed to Cloud (Render): Serves the Web Vision & Controller interface via FastAPI.
2. When run locally (python app.py): Launches the OpenCV Windows Desktop System Controller.
"""

import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# =========================================================================
# FASTAPI WEB APPLICATION (For Render Cloud Deployment)
# =========================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Hand Gesture Camera Cloud Server Live!", flush=True)
    yield
    print("🛑 Hand Gesture Camera Cloud Server Shutting down...", flush=True)

app = FastAPI(
    title="Hand Gesture Camera & Vision Controller",
    description="Real-time Web Camera Gesture Tracking & Assistive Interface",
    version="2.0.0",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.get("/healthz")
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Hand Gesture Camera"}

@app.get("/", response_class=HTMLResponse)
def serve_index(request: Request):
    index_file = os.path.join(TEMPLATES_DIR, "index.html")
    if not os.path.exists(index_file):
        raise HTTPException(status_code=404, detail="index.html not found.")
    return FileResponse(index_file)


# =========================================================================
# LOCAL DESKTOP SYSTEM CONTROLLER (Runs when executing: python app.py)
# =========================================================================
def run_desktop_controller():
    import cv2
    import math
    import time
    import winsound
    import pyautogui
    from datetime import datetime
    from hand_gesture import HandGesture

    # Dedicated Photos Directory on Desktop
    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    photo_save_dir = os.path.join(desktop_dir, "Hand_Gesture_Photos")
    os.makedirs(photo_save_dir, exist_ok=True)

    try:
        from pycaw.pycaw import AudioUtilities
        speakers = AudioUtilities.GetSpeakers()
        volume_interface = speakers.EndpointVolume
        print("✅ Windows Audio Controller: Connected via PyCaw")
    except Exception as e:
        volume_interface = None
        print("⚠️ Windows Audio Controller Warning:", e)

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

    pyautogui.PAUSE = 0.001
    pyautogui.FAILSAFE = False
    screen_width, screen_height = pyautogui.size()

    print(f"🖥️ Detected Screen Size: {screen_width} x {screen_height}")
    print(f"📁 Captured Photos Folder: {photo_save_dir}")
    print("🎥 Starting webcam...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ ERROR: Camera could not be opened.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    print("✅ Webcam Live!")

    hand_detector = HandGesture()

    last_capture = 0
    last_click = 0
    last_volume = 0

    capture_delay = 2.0
    click_delay = 0.5
    volume_delay = 0.12

    previous_x = screen_width // 2
    previous_y = screen_height // 2
    smoothing = 0.40

    notification_text = ""
    notification_timer = 0

    print("=" * 75)
    print("🖐️ HAND GESTURE SYSTEM CONTROLLER IS RUNNING")
    print("👉 INDEX FINGER ONLY: Moves Windows Mouse Cursor")
    print("🤏 PINCH (Thumb + Index tip touching): Left Click")
    print("✌️ TWO FINGERS (Index + Middle Up): Volume UP 🔊")
    print("✊ FIST (All 4 fingers curled down): Volume DOWN 🔉")
    print("👍 THUMBS UP: Takes Photo & Saves to 'Desktop/Hand_Gesture_Photos' 📸")
    print("Press 'Q' to quit.")
    print("=" * 75)

    def dist(p1, p2):
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

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
            index_pip = landmarks[6]
            index_mcp = landmarks[5]

            middle_tip = landmarks[12]
            middle_pip = landmarks[10]
            middle_mcp = landmarks[9]

            ring_tip = landmarks[16]
            ring_pip = landmarks[14]

            pinky_tip = landmarks[20]
            pinky_pip = landmarks[18]

            palm_size = dist(middle_mcp, wrist)
            if palm_size < 1e-4:
                palm_size = 0.20

            # Distance-from-wrist invariant finger extension
            index_extended = dist(index_tip, wrist) > dist(index_pip, wrist) * 1.05
            middle_extended = dist(middle_tip, wrist) > dist(middle_pip, wrist) * 1.05
            ring_extended = dist(ring_tip, wrist) > dist(ring_pip, wrist) * 1.05
            pinky_extended = dist(pinky_tip, wrist) > dist(pinky_pip, wrist) * 1.05
            thumb_extended = dist(thumb_tip, wrist) > dist(thumb_ip, wrist) * 1.05

            pinch_dist = dist(thumb_tip, index_tip) / palm_size
            is_pinch = pinch_dist < 0.38

            # -----------------------------------------------------------------
            # 1. THUMBS UP -> TAKE PHOTO & SAVE TO DEDICATED FOLDER
            # -----------------------------------------------------------------
            if thumb_extended and thumb_tip.y < wrist.y and not index_extended and not middle_extended and not ring_extended and not pinky_extended:
                gesture = "THUMBS UP (Photo Capture)"
                if now - last_capture > capture_delay:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = os.path.join(photo_save_dir, f"hand_photo_{timestamp}.jpg")
                    cv2.imwrite(save_path, frame)
                    print(f"\n📸 PHOTO SAVED TO: {save_path}")
                    try:
                        winsound.MessageBeep(winsound.MB_ICONASTERISK)
                    except Exception:
                        pass
                    notification_text = f"📸 PHOTO SAVED TO 'Hand_Gesture_Photos'"
                    notification_timer = now + 2.0
                    last_capture = now

            # -----------------------------------------------------------------
            # 2. TWO FINGERS (PEACE) -> VOLUME UP
            # -----------------------------------------------------------------
            elif index_extended and middle_extended and not ring_extended and not pinky_extended and not is_pinch:
                gesture = "TWO FINGERS (Volume UP 🔊)"
                if now - last_volume > volume_delay:
                    vol_pct = set_volume_delta(+0.04)
                    if vol_pct is not None:
                        print(f"🔊 Volume Increased -> {vol_pct}%")
                        notification_text = f"🔊 Volume: {vol_pct}%"
                        notification_timer = now + 0.8
                    last_volume = now

            # -----------------------------------------------------------------
            # 3. FIST (CLOSED HAND) -> VOLUME DOWN
            # -----------------------------------------------------------------
            elif not index_extended and not middle_extended and not ring_extended and not pinky_extended:
                gesture = "FIST (Volume DOWN 🔉)"
                if now - last_volume > volume_delay:
                    vol_pct = set_volume_delta(-0.04)
                    if vol_pct is not None:
                        print(f"🔉 Volume Decreased -> {vol_pct}%")
                        notification_text = f"🔉 Volume: {vol_pct}%"
                        notification_timer = now + 0.8
                    last_volume = now

            # -----------------------------------------------------------------
            # 4. PINCH -> LEFT CLICK
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
            # 5. INDEX POINT -> MOVE MOUSE CURSOR
            # -----------------------------------------------------------------
            elif index_extended and not middle_extended and not ring_extended and not pinky_extended:
                gesture = "INDEX POINT (Mouse Cursor 👆)"
                norm_x = max(0.0, min(1.0, (index_tip.x - 0.15) / 0.70))
                norm_y = max(0.0, min(1.0, (index_tip.y - 0.15) / 0.70))

                target_x = int(norm_x * screen_width)
                target_y = int(norm_y * screen_height)

                current_x = previous_x + (target_x - previous_x) * smoothing
                current_y = previous_y + (target_y - previous_y) * smoothing

                pyautogui.moveTo(int(current_x), int(current_y))
                previous_x, previous_y = current_x, current_y

            # -----------------------------------------------------------------
            # 6. OPEN PALM
            # -----------------------------------------------------------------
            elif index_extended and middle_extended and ring_extended and pinky_extended:
                gesture = "OPEN PALM (Standby ✋)"

        # HUD Overlay
        cur_vol = get_current_volume()
        cv2.rectangle(frame, (15, 15), (540, 230), (15, 15, 25), -1)
        cv2.rectangle(frame, (15, 15), (540, 230), (0, 255, 130), 2)

        cv2.putText(frame, f"Gesture: {gesture}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 150), 2)
        cv2.putText(frame, f"System Master Volume: {cur_vol}%", (30, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
        cv2.putText(frame, "👆 INDEX: Move Mouse Cursor", (30, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (240, 240, 240), 1)
        cv2.putText(frame, "🤏 PINCH: Left Click", (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (240, 240, 240), 1)
        cv2.putText(frame, "✌️ TWO FINGERS: Volume UP (+)", (30, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 220, 255), 1)
        cv2.putText(frame, "✊ FIST: Volume DOWN (-)", (30, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 220, 255), 1)
        cv2.putText(frame, "👍 THUMBS UP: Save to Hand_Gesture_Photos", (30, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 100), 1)

        if now < notification_timer and notification_text:
            cv2.rectangle(frame, (w // 2 - 270, h - 70), (w // 2 + 270, h - 20), (0, 180, 80), -1)
            cv2.rectangle(frame, (w // 2 - 270, h - 70), (w // 2 + 270, h - 20), (255, 255, 255), 2)
            cv2.putText(frame, notification_text, (w // 2 - 250, h - 38), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)

        cv2.imshow("Hand Gesture Computer Controller", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\nExiting controller...")
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Camera closed.")


if __name__ == "__main__":
    run_desktop_controller()
