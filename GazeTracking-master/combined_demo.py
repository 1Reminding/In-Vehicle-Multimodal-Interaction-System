import cv2
import mediapipe as mp
from gaze_tracking import GazeTracking
import time

# 初始化 MediaPipe Hands
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.75,
    min_tracking_confidence=0.75)

def get_y(hand_landmarks, landmark_enum):
    return hand_landmarks.landmark[landmark_enum].y

def get_x(hand_landmarks, landmark_enum):
    return hand_landmarks.landmark[landmark_enum].x

def recognize_gesture(hand_landmarks):
    # 关键点枚举
    lm_thumb_tip = mp_hands.HandLandmark.THUMB_TIP
    lm_thumb_ip = mp_hands.HandLandmark.THUMB_IP
    lm_thumb_mcp = mp_hands.HandLandmark.THUMB_MCP
    
    lm_index_tip = mp_hands.HandLandmark.INDEX_FINGER_TIP
    lm_index_pip = mp_hands.HandLandmark.INDEX_FINGER_PIP
    lm_index_mcp = mp_hands.HandLandmark.INDEX_FINGER_MCP
    
    lm_middle_tip = mp_hands.HandLandmark.MIDDLE_FINGER_TIP
    lm_middle_pip = mp_hands.HandLandmark.MIDDLE_FINGER_PIP
    lm_middle_mcp = mp_hands.HandLandmark.MIDDLE_FINGER_MCP
    
    lm_ring_tip = mp_hands.HandLandmark.RING_FINGER_TIP
    lm_ring_pip = mp_hands.HandLandmark.RING_FINGER_PIP
    lm_ring_mcp = mp_hands.HandLandmark.RING_FINGER_MCP
    
    lm_pinky_tip = mp_hands.HandLandmark.PINKY_TIP
    lm_pinky_pip = mp_hands.HandLandmark.PINKY_PIP
    lm_pinky_mcp = mp_hands.HandLandmark.PINKY_MCP

    # 获取各关键点坐标
    thumb_tip_y, thumb_ip_y, thumb_mcp_y = get_y(hand_landmarks, lm_thumb_tip), get_y(hand_landmarks, lm_thumb_ip), get_y(hand_landmarks, lm_thumb_mcp)
    index_tip_y, index_pip_y, index_mcp_y = get_y(hand_landmarks, lm_index_tip), get_y(hand_landmarks, lm_index_pip), get_y(hand_landmarks, lm_index_mcp)
    middle_tip_y, middle_pip_y, middle_mcp_y = get_y(hand_landmarks, lm_middle_tip), get_y(hand_landmarks, lm_middle_pip), get_y(hand_landmarks, lm_middle_mcp)
    ring_tip_y, ring_pip_y, ring_mcp_y = get_y(hand_landmarks, lm_ring_tip), get_y(hand_landmarks, lm_ring_pip), get_y(hand_landmarks, lm_ring_mcp)
    pinky_tip_y, pinky_pip_y, pinky_mcp_y = get_y(hand_landmarks, lm_pinky_tip), get_y(hand_landmarks, lm_pinky_pip), get_y(hand_landmarks, lm_pinky_mcp)

    # 1. 识别"竖起大拇指"
    thumb_points_up = (thumb_tip_y < thumb_ip_y and thumb_ip_y < thumb_mcp_y)
    other_fingers_curled = (index_tip_y > index_pip_y and
                            middle_tip_y > middle_pip_y and
                            ring_tip_y > ring_pip_y and
                            pinky_tip_y > pinky_pip_y)
    thumb_dominant = thumb_tip_y < index_mcp_y 

    if thumb_points_up and other_fingers_curled and thumb_dominant:
        return "竖起大拇指"

    # 2. 识别"摇手"（张开手掌）
    thumb_extended = (thumb_tip_y < thumb_ip_y and thumb_tip_y < thumb_mcp_y)
    index_extended = (index_tip_y < index_pip_y and index_tip_y < index_mcp_y)
    middle_extended = (middle_tip_y < middle_pip_y and middle_tip_y < middle_mcp_y)
    ring_extended = (ring_tip_y < ring_pip_y and ring_tip_y < ring_mcp_y)
    pinky_extended = (pinky_tip_y < pinky_pip_y and pinky_tip_y < pinky_mcp_y)

    if thumb_extended and index_extended and middle_extended and ring_extended and pinky_extended:
        return "摇手"

    # 3. 识别"握拳"
    index_fist_curled = (index_tip_y > index_pip_y and index_tip_y > index_mcp_y)
    middle_fist_curled = (middle_tip_y > middle_pip_y and middle_tip_y > middle_mcp_y)
    ring_fist_curled = (ring_tip_y > ring_pip_y and ring_tip_y > ring_mcp_y)
    pinky_fist_curled = (pinky_tip_y > pinky_pip_y and pinky_tip_y > pinky_mcp_y)
    thumb_fist_curled = (thumb_tip_y > thumb_ip_y and thumb_tip_y > thumb_mcp_y)

    if index_fist_curled and middle_fist_curled and ring_fist_curled and pinky_fist_curled and thumb_fist_curled:
        return "握拳"
        
    return None

def main():
    # 初始化眼神追踪器
    gaze = GazeTracking()
    
    # 打开摄像头
    webcam = cv2.VideoCapture(0)
    
    # 初始化状态跟踪变量
    current_state = "center"
    state_start_time = time.time()
    previous_distracted = False
    last_gesture = None
    waiting_for_thumbs_up = False  # 新增：等待竖起大拇指的状态
    is_distracted = False  # 添加这行：初始化分心状态变量
    
    # 设置分心阈值（秒）
    DISTRACTION_THRESHOLD = {
        "blink": 1.0,
        "left": 3.0,
        "right": 3.0,
    }

    while True:
        # 读取摄像头帧
        ret, frame = webcam.read()
        if not ret:
            print("无法读取摄像头帧")
            break

        # 先进行镜面翻转，再处理所有功能
        frame = cv2.flip(frame, 1)

        # 处理眼神追踪
        gaze.refresh(frame)
        frame = gaze.annotated_frame()

        # 处理手势识别
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        # 眼部追踪状态处理
        new_state = ""
        if gaze.is_blinking():
            new_state = "blink"
        elif gaze.is_right():
            new_state = "right"
        elif gaze.is_left():
            new_state = "left"
        elif gaze.is_center():
            new_state = "center"
            
        if new_state != current_state:
            current_state = new_state
            state_start_time = time.time()
        
        duration = time.time() - state_start_time
        
        # 修改分心状态处理逻辑
        if not is_distracted and current_state in DISTRACTION_THRESHOLD and duration > DISTRACTION_THRESHOLD[current_state]:
            is_distracted = True
            waiting_for_thumbs_up = True
            print(f"警告：检测到分心！当前状态: {current_state}")
            print("请竖起大拇指以确认您已恢复注意力")
        
        # 手势识别处理
        current_gesture = None
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                current_gesture = recognize_gesture(hand_landmarks)
                # 检查是否是竖起大拇指来解除分心状态
                if waiting_for_thumbs_up and current_gesture == "竖起大拇指":
                    is_distracted = False
                    waiting_for_thumbs_up = False
                    print("已确认注意力恢复，解除分心状态")
                    last_gesture = current_gesture  # 更新上一次的手势状态
                    
        # 只在手势状态发生变化时输出
        if current_gesture != last_gesture:
            if current_gesture:
                print(f"识别到的手势: {current_gesture}")
            elif last_gesture:  # 只有在之前有手势的情况下才提示手势结束
                print("手势结束")
            last_gesture = current_gesture

        # 在画面上显示信息
        gaze_text = f"{current_state} ({duration:.1f}秒)"
        if is_distracted:
            gaze_text += " (分心 - 请竖起大拇指确认恢复注意力)"
        cv2.putText(frame, gaze_text, (90, 60), cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)

        if current_gesture:
            cv2.putText(frame, f"手势: {current_gesture}", (90, 120), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 255, 0), 2)

        # 显示瞳孔位置
        left_pupil = gaze.pupil_left_coords()
        right_pupil = gaze.pupil_right_coords()
        if left_pupil is not None:
            cv2.putText(frame, f"左瞳孔: {left_pupil}", (90, 180), cv2.FONT_HERSHEY_DUPLEX, 0.9, (147, 58, 31), 1)
        if right_pupil is not None:
            cv2.putText(frame, f"右瞳孔: {right_pupil}", (90, 220), cv2.FONT_HERSHEY_DUPLEX, 0.9, (147, 58, 31), 1)

        # 显示处理后的帧
        cv2.imshow("组合演示", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # 按ESC退出
            break

    webcam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()