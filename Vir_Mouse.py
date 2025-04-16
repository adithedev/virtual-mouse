import cv2
import mediapipe as mp
import pyautogui
import time
import numpy as np
import win32gui
import win32con

# Instructions before starting
print("Welcome to the Virtual Tech Mouse!")
print("Instructions:")
print("1. Move your index finger to move the cursor.")
print("2. Pinch your thumb and index finger to click.")
print("3. Move your middle finger and index finger for scrolling.")
print("4. Press ESC to exit.")
print("\nStarting the program in 5 seconds...")
time.sleep(5)

# Setup
cap = cv2.VideoCapture(0)
hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
draw = mp.solutions.drawing_utils
screen_width, screen_height = pyautogui.size()

# Variables
prev_click_time = 0
click_delay = 0.5
double_click_delay = 1.0
scroll_threshold = 40
mode = "MOVE"
prev_loc_x, prev_loc_y = 0, 0
smoothening = 4
pTime = 0
window_initialized = False

# Colors
glow_color = (0, 255, 0)
click_color = (0, 0, 255)
scroll_color = (255, 255, 0)
font = cv2.FONT_HERSHEY_SIMPLEX

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame_height, frame_width, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    mode = "MOVE"

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            draw.draw_landmarks(frame, hand_landmarks)

            landmarks = hand_landmarks.landmark
            index = landmarks[8]
            thumb = landmarks[4]
            middle = landmarks[12]

            # Position
            x_index, y_index = int(index.x * frame_width), int(index.y * frame_height)
            x_thumb, y_thumb = int(thumb.x * frame_width), int(thumb.y * frame_height)
            x_middle, y_middle = int(middle.x * frame_width), int(middle.y * frame_height)

            # Screen coords
            screen_x = np.interp(x_index, [0, frame_width], [0, screen_width])
            screen_y = np.interp(y_index, [0, frame_height], [0, screen_height])
            curr_x = prev_loc_x + (screen_x - prev_loc_x) / smoothening
            curr_y = prev_loc_y + (screen_y - prev_loc_y) / smoothening
            pyautogui.moveTo(curr_x, curr_y)  # Moves the cursor system-wide
            prev_loc_x, prev_loc_y = curr_x, curr_y

            # Draw pointer
            cv2.circle(frame, (x_index, y_index), 10, glow_color, cv2.FILLED)

            # CLICKING
            index_thumb_dist = np.hypot(x_index - x_thumb, y_index - y_thumb)
            if index_thumb_dist < 30:
                mode = "CLICK"
                cv2.circle(frame, (x_index, y_index), 15, click_color, cv2.FILLED)
                now = time.time()
                if now - prev_click_time > double_click_delay:
                    pyautogui.doubleClick()  # Double click system-wide
                    prev_click_time = now
                elif now - prev_click_time > click_delay:
                    pyautogui.click()  # Click system-wide
                    prev_click_time = now

            # SCROLLING
            index_middle_dist = np.hypot(x_index - x_middle, y_index - y_middle)
            if index_middle_dist < scroll_threshold:
                mode = "SCROLL"
                if y_middle < y_index:
                    pyautogui.scroll(20)  # scroll up
                else:
                    pyautogui.scroll(-20)  # scroll down
                cv2.line(frame, (x_index, y_index), (x_middle, y_middle), scroll_color, 2)

    # FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime + 1e-6)
    pTime = cTime

    # Overlay UI Panel
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame_width, 60), (10, 10, 10), -1)
    alpha = 0.5
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    # UI Text
    cv2.putText(frame, f'MODE: {mode}', (10, 40), font, 1, (0, 255, 255), 2)
    cv2.putText(frame, f'FPS: {int(fps)}', (frame_width - 150, 40), font, 1, (0, 255, 0), 2)

    # Display video in OpenCV window (for debugging only)
    cv2.imshow(' Virtual Tech Mouse', frame)

    # Always on top
    if not window_initialized:
        try:
            hwnd = win32gui.FindWindow(None, '🖱️ Virtual Tech Mouse')
            if hwnd != 0:
                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_TOPMOST,
                    50, 50, 600, 400,
                    win32con.SWP_SHOWWINDOW
                )
                window_initialized = True
        except Exception as e:
            print(f"[!] HWND Error: {e}")

    # Exit
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
