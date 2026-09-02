# 🖐️ Hand Gesture Camera & Vision Controller
### Real-time Web Camera Gesture Tracking, Virtual Mouse Pointer, & Hands-Free Controller

[![Live Web App](https://img.shields.io/badge/Live%20Demo-Render-00C4B4?style=for-the-badge&logo=render&logoColor=white)](https://hand-gesture-camera-kbgt.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11.9-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-3D%20Vision-00C4B4?style=for-the-badge&logo=google&logoColor=white)](https://mediapipe.dev)

---

## 🌟 Overview

This project provides both a **Live Web Application (ready for Render cloud deployment)** and a **Local Desktop Controller**:

1. **🌐 Web Version (`app.py` + `templates/index.html`)**:
   * Runs in any web browser on any device with a webcam.
   * **Index Finger Mouse Pointer:** Move your index finger to glide the on-screen pointer.
   * **Dwell Auto-Click:** Hover over any button or key for 1.2s to click it automatically.
   * **Touchless Virtual Keyboard:** Type full messages by pointing and hovering over keys.
   * **Hands-Free Photo Capture:** Show **Thumbs Up 👍** to trigger a 3-2-1 photo countdown and save photos to an interactive gallery.
   * **Volume Control:** ✌️ Two Fingers = Volume Up, ✊ Fist = Volume Down.
   * **Text-to-Speech (TTS):** Speaks typed words and assistance phrases aloud.

2. **🖥️ Local Desktop Version (`desktop_app.py`)**:
   * Runs directly on your Windows PC using OpenCV & PyAutoGUI to control your actual operating system cursor and speakers.

---

## 🎯 Gesture Reference

| Gesture | Icon | Action |
| :--- | :---: | :--- |
| **Index Point** | 👆 | Moves the on-screen mouse pointer |
| **Dwell / Hover** | ⏳ | Auto-clicks any key or button after 1.2 seconds |
| **Pinch** | 🤏 | Instant left-click |
| **Thumbs Up** | 👍 | Hands-free photo capture with countdown |
| **Two Fingers** | ✌️ | Increases sound volume / scrolls up |
| **Fist** | ✊ | Decreases sound volume / scrolls down |
| **Open Palm** | ✋ | Emergency alert & voice help |

---

## 🚀 How to Run

### 🌐 1. Run Web App Locally
```powershell
pip install -r requirements.txt
python app.py
```
Open **`http://localhost:8000`** in your browser.

### 🖥️ 2. Run Desktop Controller on Windows
```powershell
python desktop_app.py
```

---

© 2026 **Hand Gesture Camera**.
