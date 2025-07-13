import cv2
import requests
import time

# ESP32 IP address
ESP32_IP = "http://192.168.4.1"  # Update this if needed

# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Warm-up delay for camera
time.sleep(2)

# Load Haar cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Get frame dimensions
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Map function
def map_value(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

# Clamp function (for servo safety)
def clamp(val, min_val, max_val):
    return max(min_val, min(max_val, val))

# Request control timing
last_sent_time = 0
send_interval = 0.2  # seconds

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        # Face center
        cx = x + w // 2
        cy = y + h // 2

        # Reverse pan mapping (flip horizontal direction)
        pan = map_value(cx, 0, frame_width, 180, 0)
        tilt = map_value(cy, 0, frame_height, 0, 180)

        # Clamp values just in case
        pan = clamp(pan, 0, 180)
        tilt = clamp(tilt, 0, 180)

        # Send to ESP32 at controlled rate
        current_time = time.time()
        if current_time - last_sent_time > send_interval:
            try:
                response = requests.get(f"{ESP32_IP}/move?pan={pan}&tilt={tilt}", timeout=0.2)
                if response.status_code != 200:
                    print(f"ESP32 error: {response.status_code}")
                else:
                    print(f"Sent: pan={pan}, tilt={tilt}")
            except requests.RequestException as e:
                print(f"ESP32 request failed: {e}")
            last_sent_time = current_time

        # Draw detection box and face center
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)

    # Show result
    cv2.imshow('Face Tracker', frame)

    # Quit on 'q' or window close
    if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('Face Tracker', cv2.WND_PROP_VISIBLE) < 1:
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()

# Optionally reset servo position to center
try:
    requests.get(f"{ESP32_IP}/move?pan=90&tilt=90", timeout=0.2)
except requests.RequestException:
    pass
