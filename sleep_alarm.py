import cv2
import time
import os
import sys
import subprocess

# Load cascades
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade  = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# Camera
cap = cv2.VideoCapture(0)
time.sleep(0.5)

# Parameters (tune these)
FPS_ESTIMATE = 20.0
CLOSED_SECONDS_THRESHOLD = 1.5
CLOSED_FRAMES_THRESHOLD = int(FPS_ESTIMATE * CLOSED_SECONDS_THRESHOLD)

# State
eye_closed_frames = 0
alarm_playing = False
ALARM_FILE = 'alarm.wav'  # optional

def play_alarm():
    global alarm_playing
    if alarm_playing: return
    alarm_playing = True
    # Windows
    try:
        import winsound
        if os.path.exists(ALARM_FILE):
            winsound.PlaySound(ALARM_FILE, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            winsound.Beep(2000, 700)
    except Exception:
        # mac/linux fallback using afplay/play (if available)
        if os.path.exists(ALARM_FILE):
            try:
                subprocess.Popen(['afplay', ALARM_FILE])
            except Exception:
                try:
                    subprocess.Popen(['play', ALARM_FILE])
                except Exception:
                    pass

def stop_alarm():
    global alarm_playing
    alarm_playing = False
    try:
        import winsound
        winsound.PlaySound(None, winsound.SND_PURGE)
    except Exception:
        pass

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80,80))

    status_text = "Alert"
    for (x,y,w,h) in faces:
        cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
        roi_gray = gray[y:y+h//2, x:x+w]  # upper half for eyes
        eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=5, minSize=(20,10))

        if len(eyes) == 0:
            eye_closed_frames += 1
        else:
            eye_closed_frames = 0

        # draw eyes
        for (ex,ey,ew,eh) in eyes:
            cv2.rectangle(frame, (x+ex, y+ey), (x+ex+ew, y+ey+eh), (255,0,0), 1)

    # Decide drowsiness
    if eye_closed_frames >= CLOSED_FRAMES_THRESHOLD:
        status_text = "DROWSY!"
        cv2.putText(frame, status_text, (30,60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,0,255), 3)
        play_alarm()
    else:
        cv2.putText(frame, status_text, (30,60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 2)
        stop_alarm()

    cv2.imshow('Drowsiness Detection', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
