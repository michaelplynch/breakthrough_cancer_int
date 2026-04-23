import cv2

CAMERA_INDEX = 0  # change to 1, 2, ... if needed

def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print("❌ Could not open camera")
        return

    print("✅ Camera opened successfully")
    print("Press 'q' to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to grab frame")
            break

        # Show resolution on frame
        h, w = frame.shape[:2]
        cv2.putText(
            frame,
            f"{w}x{h}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        cv2.imshow("Camera Test", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("👋 Camera test finished")

if __name__ == "__main__":
    main()
