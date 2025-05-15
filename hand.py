import cv2
import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# --- 手势识别辅助函数 ---
# 获取关键点y坐标
def get_y(hand_landmarks, landmark_enum):
    return hand_landmarks.landmark[landmark_enum].y

# 获取关键点x坐标
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

    # 获取各关键点坐标 (Y坐标越小，代表在图像中位置越高)
    thumb_tip_y, thumb_ip_y, thumb_mcp_y = get_y(hand_landmarks, lm_thumb_tip), get_y(hand_landmarks, lm_thumb_ip), get_y(hand_landmarks, lm_thumb_mcp)
    index_tip_y, index_pip_y, index_mcp_y = get_y(hand_landmarks, lm_index_tip), get_y(hand_landmarks, lm_index_pip), get_y(hand_landmarks, lm_index_mcp)
    middle_tip_y, middle_pip_y, middle_mcp_y = get_y(hand_landmarks, lm_middle_tip), get_y(hand_landmarks, lm_middle_pip), get_y(hand_landmarks, lm_middle_mcp)
    ring_tip_y, ring_pip_y, ring_mcp_y = get_y(hand_landmarks, lm_ring_tip), get_y(hand_landmarks, lm_ring_pip), get_y(hand_landmarks, lm_ring_mcp)
    pinky_tip_y, pinky_pip_y, pinky_mcp_y = get_y(hand_landmarks, lm_pinky_tip), get_y(hand_landmarks, lm_pinky_pip), get_y(hand_landmarks, lm_pinky_mcp)

    # 1. 识别“竖起大拇指”
    # 大拇指指尖高于IP关节，IP关节高于MCP关节 (大拇指向上)
    thumb_points_up = (thumb_tip_y < thumb_ip_y and thumb_ip_y < thumb_mcp_y)
    # 其他四指弯曲：指尖低于PIP关节
    other_fingers_curled = (index_tip_y > index_pip_y and
                            middle_tip_y > middle_pip_y and
                            ring_tip_y > ring_pip_y and
                            pinky_tip_y > pinky_pip_y)
    # 并且大拇指指尖要高于其他手指的MCP关节（确保大拇指突出）
    thumb_dominant = thumb_tip_y < index_mcp_y 

    if thumb_points_up and other_fingers_curled and thumb_dominant:
        return "竖起大拇指"

    # 2. 识别“摇手”（张开手掌）
    # 所有五指伸直：指尖高于PIP关节，并且指尖高于MCP关节
    thumb_extended = (thumb_tip_y < thumb_ip_y and thumb_tip_y < thumb_mcp_y)
    index_extended = (index_tip_y < index_pip_y and index_tip_y < index_mcp_y)
    middle_extended = (middle_tip_y < middle_pip_y and middle_tip_y < middle_mcp_y)
    ring_extended = (ring_tip_y < ring_pip_y and ring_tip_y < ring_mcp_y)
    pinky_extended = (pinky_tip_y < pinky_pip_y and pinky_tip_y < pinky_mcp_y)

    if thumb_extended and index_extended and middle_extended and ring_extended and pinky_extended:
        return "摇手"

    # 3. 识别“握拳”
    # 四指弯曲：指尖低于PIP关节，并且指尖低于MCP关节
    index_fist_curled = (index_tip_y > index_pip_y and index_tip_y > index_mcp_y)
    middle_fist_curled = (middle_tip_y > middle_pip_y and middle_tip_y > middle_mcp_y)
    ring_fist_curled = (ring_tip_y > ring_pip_y and ring_tip_y > ring_mcp_y)
    pinky_fist_curled = (pinky_tip_y > pinky_pip_y and pinky_tip_y > pinky_mcp_y)
    # 大拇指弯曲：指尖低于IP关节，并且指尖低于MCP关节
    thumb_fist_curled = (thumb_tip_y > thumb_ip_y and thumb_tip_y > thumb_mcp_y)
    
    # （可选）检查大拇指是否覆盖在其他手指上或紧贴手掌
    # thumb_tip_x = get_x(hand_landmarks, lm_thumb_tip)
    # index_mcp_x = get_x(hand_landmarks, lm_index_mcp)
    # thumb_tucked = abs(thumb_tip_x - index_mcp_x) < 0.1 # 阈值需要调整

    if index_fist_curled and middle_fist_curled and ring_fist_curled and pinky_fist_curled and thumb_fist_curled:
        return "握拳"
        
    return None
# --- 辅助函数结束 ---

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.75,
    min_tracking_confidence=0.75)
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        print("无法读取摄像头帧")
        break
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = cv2.flip(frame, 1)
    results = hands.process(frame)   
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    # if results.multi_handedness: # 这部分可以保留或移除，取决于你是否需要左右手信息
    #     for hand_label in results.multi_handedness:
    #         print(hand_label)
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # print('hand_landmarks:', hand_landmarks) # 原始关键点信息，可以注释掉

            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # 进行手势识别
            gesture = recognize_gesture(hand_landmarks)
            if gesture:
                print(f"识别到的手势: {gesture}")
                # 你可以在这里添加将手势名称显示在屏幕上的代码
                cv2.putText(frame, gesture, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    cv2.imshow('MediaPipe Hands', frame)
    if cv2.waitKey(1) & 0xFF == 27: # 按 ESC 退出
        break
cap.release()
cv2.destroyAllWindows()

