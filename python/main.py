import cv2
import numpy as np
import json
import time
from pathlib import Path

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = Path(__file__).parent.parent
SHARED_DIR = BASE_DIR / "shared"
SHARED_DIR.mkdir(exist_ok=True)

PYTHON_DIR = BASE_DIR / 'python'

COORD_FILE = SHARED_DIR / "coords.json"
CALIB_FILE = PYTHON_DIR / "calibration.json"

# -----------------------------
# Load calibration
# -----------------------------
with open(CALIB_FILE) as f:
    calib = json.load(f)

floor_pts = np.float32(calib["floor_points"])
tissue_pts = np.float32(calib["tissue_points"])

H, _ = cv2.findHomography(floor_pts, tissue_pts)

# -----------------------------
# Webcam setup
# -----------------------------
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

time.sleep(1)

# -----------------------------
# Capture background
# -----------------------------
ret, bg = cam.read()
if not ret:
    raise RuntimeError("Failed to read from webcam")

bg_gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
bg_gray = cv2.GaussianBlur(bg_gray, (21, 21), 0)

# -----------------------------
# Foot detection
# -----------------------------
def detect_feet(gray):
    diff = cv2.absdiff(bg_gray, gray)
    thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)

    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    feet = []
    for c in contours:
        if cv2.contourArea(c) > 2000:
            x, y, w, h = cv2.boundingRect(c)
            feet.append((x + w // 2, y + h // 2))
    return feet, thresh

# -----------------------------
# Main loop
# -----------------------------
print("Running foot tracker. Press ESC to quit.")

while True:
    ret, frame = cam.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    feet, mask = detect_feet(gray)

    if feet:
        fx, fy = feet[0]

        # Perspective transform
        pt = np.array([[[fx, fy]]], dtype=np.float32)
        tp = cv2.perspectiveTransform(pt, H)[0][0]
        tx, ty = int(tp[0]), int(tp[1])

        # Write to shared file for R
        data = {
            "timestamp": time.time(),
            "floor_x": fx,
            "floor_y": fy,
            "tissue_x": tx,
            "tissue_y": ty
        }

        with open(COORD_FILE, "w") as f:
            json.dump(data, f)

        # Debug overlay
        cv2.circle(frame, (fx, fy), 10, (0, 0, 255), -1)

    # Debug windows (can be disabled for event)
    cv2.imshow("Webcam", frame)
    cv2.imshow("Mask", mask)

    if cv2.waitKey(10) == 27:
        break

cam.release()
cv2.destroyAllWindows()
