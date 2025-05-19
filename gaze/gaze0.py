import cv2
from gaze_tracking import GazeTracking
import time

gaze = GazeTracking()
webcam = cv2.VideoCapture(0)

# 状态记录
left_start = right_start = blink_start = None
left_time = right_time = blink_time = 0.0

# 连续状态阈值（秒）
LEFT_THRESHOLD = 2.0
RIGHT_THRESHOLD = 2.0
BLINK_THRESHOLD = 1.5

def reset_times(exclude=None):
    global left_start, right_start, blink_start
    global left_time, right_time, blink_time
    if exclude != "left":
        left_start = None
        left_time = 0.0
    if exclude != "right":
        right_start = None
        right_time = 0.0
    if exclude != "blink":
        blink_start = None
        blink_time = 0.0

while True:
    _, frame = webcam.read()
    gaze.refresh(frame)
    frame = gaze.annotated_frame()
    now = time.time()
    alert_text = ""
    console_alert = None

    # 状态检测逻辑
    if gaze.is_blinking():
        if blink_start is None:
            blink_start = now
        blink_time = now - blink_start
        reset_times(exclude="blink")
        if blink_time >= BLINK_THRESHOLD:
            alert_text = "⚠️ Eyes closed too long!"
            console_alert = "警告：闭眼超过1.5秒！"

    elif gaze.is_left():
        if left_start is None:
            left_start = now
        left_time = now - left_start
        reset_times(exclude="left")
        if left_time >= LEFT_THRESHOLD:
            alert_text = "⚠️ Looking left too long!"
            console_alert = "警告：向左偏移超过2秒！"

    elif gaze.is_right():
        if right_start is None:
            right_start = now
        right_time = now - right_start
        reset_times(exclude="right")
        if right_time >= RIGHT_THRESHOLD:
            alert_text = "⚠️ Looking right too long!"
            console_alert = "警告：向右偏移超过2秒！"

    elif gaze.is_center():
        reset_times()

    else:
        # unknown 状态也清空
        reset_times()

    # 文字绘制
    cv2.putText(frame, f"Status: {'Blinking' if gaze.is_blinking() else 'Looking left' if gaze.is_left() else 'Looking right' if gaze.is_right() else 'Looking center' if gaze.is_center() else 'Unknown'}",
                (20, 40), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0), 2)

    cv2.putText(frame, f" Left Gaze: {left_time:.1f}s", (20, 80), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 0), 1)
    cv2.putText(frame, f" Right Gaze: {right_time:.1f}s", (20, 110), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 0), 1)
    cv2.putText(frame, f" Blink: {blink_time:.1f}s", (20, 140), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 255), 1)

    if alert_text:
        cv2.putText(frame, alert_text, (20, 180), cv2.FONT_HERSHEY_DUPLEX, 1.1, (0, 0, 255), 2)
        print(f"\n{console_alert}")  # 控制台输出

    cv2.imshow("Driver Gaze Monitor", frame)

    if cv2.waitKey(1) == 27:  # 按 ESC 退出
        break

webcam.release()
cv2.destroyAllWindows()
