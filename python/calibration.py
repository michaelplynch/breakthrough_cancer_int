import cv2
import json
import numpy as np
from pathlib import Path

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = Path(__file__).parent
CALIB_FILE = BASE_DIR / "calibration.json"

# -----------------------------
# Tissue coordinate system
# (DEFINE ONCE)
# -----------------------------
TISSUE_XMIN = 961.4529
TISSUE_XMAX = 25898.45
TISSUE_YMIN = 2494.565
TISSUE_YMAX = 25790.4

TISSUE_POINTS = [
    [TISSUE_XMIN, TISSUE_YMIN],
    [TISSUE_XMAX, TISSUE_YMIN],
    [TISSUE_XMAX, TISSUE_YMAX],
    [TISSUE_XMIN, TISSUE_YMAX],
]

# -----------------------------
# State
# -----------------------------
clicked = []

def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and len(clicked) < 4:
        clicked.append([x, y])
        print(f"Clicked {len(clicked)}: ({x}, {y})")

# -----------------------------
# Main
# -----------------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Cannot open camera")

cv2.namedWindow("Calibration")
cv2.setMouseCallback("Calibration", on_mouse)

print("Calibration mode")
print("Click 4 points on the floor in order:")
print("1) Top-left")
print("2) Top-right")
print("3) Bottom-right")
print("4) Bottom-left")
print("Press 'r' to reset, 'q' to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # Draw points
    for i, (x, y) in enumerate(clicked):
        cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)
        cv2.putText(
            frame, str(i + 1), (x + 10, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
        )

    cv2.imshow("Calibration", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("r"):
        clicked.clear()
        print("Reset points")
    elif key == ord("q"):
        break
    elif len(clicked) == 4:
        break

cap.release()
cv2.destroyAllWindows()

if len(clicked) != 4:
    print("Calibration aborted")
    exit()

# -----------------------------
# Save calibration
# -----------------------------
calib = {
    "floor_points": clicked,
    "tissue_points": TISSUE_POINTS
}

with open(CALIB_FILE, "w") as f:
    json.dump(calib, f, indent=2)

print("Calibration saved to:", CALIB_FILE.resolve())

# Sanity check
H, _ = cv2.findHomography(
    np.float32(clicked),
    np.float32(TISSUE_POINTS)
)
print("Homography matrix:")
print(H)
