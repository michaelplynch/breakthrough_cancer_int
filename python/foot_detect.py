import cv2
import numpy as np
import time

# -------------------------
# Configuration (TUNE THESE)
# -------------------------
CAMERA_INDEX = 0

MIN_FOOT_AREA = 2000        # px^2, depends on camera height
MAX_FOOT_AREA = 50000       # optional sanity limit

BLUR_KERNEL = (7, 7)
THRESH_BLOCK_SIZE = 15      # must be odd
THRESH_C = 3

SMOOTHING_ALPHA = 0.7       # 0 = no smoothing, 0.7 = stable

# -------------------------
# Main
# -------------------------
def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        raise RuntimeError("Could not open camera")

    time.sleep(1.0)
    print("Press 'q' to quit")

    prev_cx, prev_cy = None, None

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        h, w = frame.shape[:2]

        # --- Preprocess ---
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, BLUR_KERNEL, 0)

        thresh = cv2.adaptiveThreshold(
            blur,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            THRESH_BLOCK_SIZE,
            THRESH_C,
        )

        # Morphological cleanup
        kernel = np.ones((5, 5), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        # --- Contours ---
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        detected = False
        cx, cy = None, None

        if contours:
            # Sort by area (largest first)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            for cnt in contours:
                area = cv2.contourArea(cnt)

                if area < MIN_FOOT_AREA or area > MAX_FOOT_AREA:
                    continue

                M = cv2.moments(cnt)
                if M["m00"] == 0:
                    continue

                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                detected = True

                # --- Temporal smoothing ---
                if prev_cx is not None:
                    cx = int(SMOOTHING_ALPHA * prev_cx + (1 - SMOOTHING_ALPHA) * cx)
                    cy = int(SMOOTHING_ALPHA * prev_cy + (1 - SMOOTHING_ALPHA) * cy)

                prev_cx, prev_cy = cx, cy

                # --- Debug draw ---
                cv2.drawContours(frame, [cnt], -1, (0, 255, 0), 2)
                cv2.circle(frame, (cx, cy), 25, (0, 0, 255), -1)


                break  # only take largest valid blob

        if not detected:
            prev_cx, prev_cy = None, None

        # --- Overlay text ---
        status = "DETECTED" if detected else "NO FOOT"
        cv2.putText(
            frame,
            status,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0) if detected else (0, 0, 255),
            2,
        )

        if detected:
            nx = cx / w
            ny = cy / h
            cv2.putText(
                frame,
                f"x={nx:.2f}, y={ny:.2f}",
                (10, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
            )
            print(f"Foot @ floor coords: x={nx:.3f}, y={ny:.3f}")
        else:
            print("No foot detected")

        # --- Show ---
        cv2.imshow("Foot Detection", frame)
        cv2.imshow("Threshold", thresh)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
