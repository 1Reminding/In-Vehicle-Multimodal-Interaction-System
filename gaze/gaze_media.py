import cv2
import mediapipe as mp
import time
import numpy as np
from collections import deque
from PIL import Image, ImageDraw, ImageFont
import os

# 添加中文字体支持
font_path = os.path.join(os.environ['SystemRoot'], 'Fonts', 'simhei.ttf')

def draw_chinese_text(img, text, position, font_size=30, text_color=(0, 255, 0)):
    # 创建一个空白的PIL图片，设置背景为透明
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    font = ImageFont.truetype(font_path, font_size)
    
    # 绘制文字
    draw.text(position, text, font=font, fill=text_color[::-1])  # PIL使用RGB而CV2使用BGR
    
    # 转换回OpenCV格式
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

# 初始化
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1,
                                   refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)

# 摄像头
cap = cv2.VideoCapture(0)

# 关键点 - 使用更多眼睛相关的关键点
LEFT_IRIS = 468  # 左眼虹膜中心
RIGHT_IRIS = 473  # 右眼虹膜中心
LEFT_EYE_LEFT = 362  # 左眼左侧
LEFT_EYE_RIGHT = 263  # 左眼右侧
RIGHT_EYE_LEFT = 133  # 右眼左侧
RIGHT_EYE_RIGHT = 33  # 右眼右侧

# 状态与时间记录
status = "Center"
status_start = None
left_time = right_time = blink_time = 0.0
alert_text = ""

# 阈值设定
LEFT_THRESHOLD = 2.0
RIGHT_THRESHOLD = 2.0
BLINK_THRESHOLD = 1.5  # 添加闭眼阈值

# 状态平滑处理 - 使用队列存储最近的状态
status_history = deque(maxlen=10)
status_counts = {"Left": 0, "Right": 0, "Center": 0, "Blink": 0, "Unknown": 0}

# 眼睛闭合检测相关点
LEFT_EYE_TOP = 386
LEFT_EYE_BOTTOM = 374
RIGHT_EYE_TOP = 159
RIGHT_EYE_BOTTOM = 145

# 偏移比例阈值 - 可调整
GAZE_RATIO_THRESHOLD = 0.01  # 进一步降低阈值，提高灵敏度

# 添加字体设置
font = cv2.FONT_HERSHEY_SIMPLEX

# 校准变量
calibration_frames = []
is_calibrated = False
center_ratio = 0.5  # 默认中心比例

# 添加字体设置
font = cv2.FONT_HERSHEY_SIMPLEX

# 添加校准功能
def calibrate():
    global calibration_frames, is_calibrated, center_ratio
    if len(calibration_frames) > 0:
        # 扩大有效范围，使校准更容易成功
        valid_ratios = [r for r in calibration_frames if 0.3 <= r <= 0.7]
        if valid_ratios:
            # 计算中位数而不是平均值，避免异常值影响
            valid_ratios.sort()
            center_ratio = valid_ratios[len(valid_ratios)//2]
            is_calibrated = True
            print(f"校准完成! 中心比例: {center_ratio:.2f}")
        else:
            print("校准失败，使用默认中心比例: 0.5")
            center_ratio = 0.5
            is_calibrated = True

# 添加偏移角度计算函数
def calculate_gaze_angles(face, h, w):
    try:
        # 计算水平偏移角度，使用加权平均
        left_ratio = (face[LEFT_IRIS].x - face[LEFT_EYE_LEFT].x) / max(0.001, face[LEFT_EYE_RIGHT].x - face[LEFT_EYE_LEFT].x)
        right_ratio = (face[RIGHT_IRIS].x - face[RIGHT_EYE_LEFT].x) / max(0.001, face[RIGHT_EYE_RIGHT].x - face[RIGHT_EYE_LEFT].x)
        
        # 计算垂直偏移角度
        left_v_ratio = (face[LEFT_IRIS].y - face[LEFT_EYE_TOP].y) / max(0.001, face[LEFT_EYE_BOTTOM].y - face[LEFT_EYE_TOP].y)
        right_v_ratio = (face[RIGHT_IRIS].y - face[RIGHT_EYE_TOP].y) / max(0.001, face[RIGHT_EYE_BOTTOM].y - face[RIGHT_EYE_TOP].y)
        
        # 使用加权平均计算最终比例
        h_ratio = left_ratio * 0.6 + right_ratio * 0.4  # 左眼权重更大
        v_ratio = (left_v_ratio + right_v_ratio) / 2
        
        # 应用动态校准的中心点偏移
        if is_calibrated:
            # 计算相对于中心的偏移量，不限制范围以提高灵敏度
            h_offset = h_ratio - center_ratio
            
            # 将偏移量映射到角度范围，增大系数提高灵敏度
            h_angle = h_offset * 90  # 增大角度映射系数
            v_angle = (v_ratio - 0.5) * 60  # 增大垂直方向的灵敏度
        
        return h_angle, v_angle
    except Exception as e:
        print(f"计算视线角度时出错: {e}")
        return 0.0, 0.0

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    h, w, _ = frame.shape
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(frame_rgb)

    current_time = time.time()
    raw_status = "Unknown"

    if results.multi_face_landmarks:
        face = results.multi_face_landmarks[0].landmark
        
        # 提取所有关键点
        left_iris = face[LEFT_IRIS]
        right_iris = face[RIGHT_IRIS]
        left_eye_left = face[LEFT_EYE_LEFT]
        left_eye_right = face[LEFT_EYE_RIGHT]
        right_eye_left = face[RIGHT_EYE_LEFT]
        right_eye_right = face[RIGHT_EYE_RIGHT]
        
        # 计算眼睛宽度和虹膜位置
        left_eye_width = abs(left_eye_right.x - left_eye_left.x) * w
        right_eye_width = abs(right_eye_right.x - right_eye_left.x) * w
        
        try:
            # 计算虹膜相对位置比例，使用更精确的计算方法
            left_ratio = (left_iris.x - left_eye_left.x) / max(0.001, left_eye_right.x - left_eye_left.x)
            right_ratio = (right_iris.x - right_eye_left.x) / max(0.001, right_eye_right.x - right_eye_left.x)
            
            # 限制比例在合理范围内并应用非线性映射增强边缘响应
            left_ratio = max(0.1, min(0.9, left_ratio))
            right_ratio = max(0.1, min(0.9, right_ratio))
            
            # 使用加权平均，给予更大的权重
            avg_ratio = (1.2 * left_ratio + 0.8 * right_ratio) / 2
            
            # 校准过程
            if not is_calibrated and len(calibration_frames) < 30:
                calibration_frames.append(avg_ratio)
                if len(calibration_frames) == 30:
                    calibrate()
            
            # 检测眼睛是否闭合
            left_eye_open = abs(face[LEFT_EYE_TOP].y - face[LEFT_EYE_BOTTOM].y) * h
            right_eye_open = abs(face[RIGHT_EYE_TOP].y - face[RIGHT_EYE_BOTTOM].y) * h
            eye_open_ratio = (left_eye_open + right_eye_open) / 2
            
            # 增强可视化效果
            # 绘制眼睛轮廓
            for pt in [LEFT_EYE_LEFT, LEFT_EYE_RIGHT, RIGHT_EYE_LEFT, RIGHT_EYE_RIGHT]:
                cv2.circle(frame, (int(face[pt].x * w), int(face[pt].y * h)), 3, (0, 255, 0), -1)
            # 突出显示虹膜位置
            for pt in [LEFT_IRIS, RIGHT_IRIS]:
                cv2.circle(frame, (int(face[pt].x * w), int(face[pt].y * h)), 4, (0, 0, 255), -1)
            
            # 绘制虹膜移动轨迹
            left_iris_pos = (int(face[LEFT_IRIS].x * w), int(face[LEFT_IRIS].y * h))
            right_iris_pos = (int(face[RIGHT_IRIS].x * w), int(face[RIGHT_IRIS].y * h))
            
            # 绘制参考线
            cv2.line(frame, (int(face[LEFT_EYE_LEFT].x * w), int(face[LEFT_EYE_LEFT].y * h)), 
                     (int(face[LEFT_EYE_RIGHT].x * w), int(face[LEFT_EYE_RIGHT].y * h)), (255, 255, 0), 1)
            cv2.line(frame, (int(face[RIGHT_EYE_LEFT].x * w), int(face[RIGHT_EYE_LEFT].y * h)), 
                     (int(face[RIGHT_EYE_RIGHT].x * w), int(face[RIGHT_EYE_RIGHT].y * h)), (255, 255, 0), 1)
            
            # 判断眼睛状态
            if eye_open_ratio < 5:  # 眼睛闭合阈值
                raw_status = "Blink"
            else:
                # 计算视线角度
                h_angle, v_angle = calculate_gaze_angles(face, h, w)
                
                # 显示角度信息
                frame = draw_chinese_text(frame, f"水平偏移角: {h_angle:.1f}°", (30, 300), font_size=25, text_color=(255, 255, 255))
                frame = draw_chinese_text(frame, f"垂直偏移角: {v_angle:.1f}°", (30, 330), font_size=25, text_color=(255, 255, 255))
                
                # 根据角度和比例综合判断状态
                if is_calibrated:
                    if abs(h_angle) > 20:
                        raw_status = "Left" if h_angle < 0 else "Right"
                    elif abs(v_angle) > 15:
                        raw_status = "Up" if v_angle < 0 else "Down"
                    else:
                        raw_status = "Center"
                else:
                    raw_status = "Center"  # 校准过程中保持中心状态
                    
            # 显示比例值
            frame = draw_chinese_text(frame, f"视线比例: {avg_ratio:.2f}", (30, 180), font_size=25, text_color=(255, 255, 255))
            frame = draw_chinese_text(frame, f"中心比例: {center_ratio:.2f}", (30, 210), font_size=25, text_color=(255, 255, 255))
            
        except Exception as e:
            print(f"计算比例时出错: {e}")
            raw_status = "Unknown"
    
    # 状态平滑处理
    status_history.append(raw_status)
    status_counts = {k: 0 for k in ["Left", "Right", "Center", "Blink", "Unknown"]}
    for s in status_history:
        status_counts[s] = status_counts.get(s, 0) + 1
    
    # 获取最频繁的状态
    max_count = 0
    new_status = "Unknown"
    for s, count in status_counts.items():
        if count > max_count:
            max_count = count
            new_status = s
    
    # 状态必须占据历史记录的一定比例才算稳定
    if max_count >= len(status_history) * 0.6:  # 60%一致才认为稳定
        if new_status != status:
            status = new_status
            status_start = current_time
    
    # 持续时间计算
    duration = current_time - status_start if status_start else 0.0
    left_time = duration if status == "Left" else 0.0
    right_time = duration if status == "Right" else 0.0
    blink_time = duration if status == "Blink" else 0.0
    
    # 报警逻辑
    alert_text = ""
    if left_time > LEFT_THRESHOLD:
        alert_text = "⚠️ 注视左侧时间过长"
    elif right_time > RIGHT_THRESHOLD:
        alert_text = "⚠️ 注视右侧时间过长"
    elif blink_time > BLINK_THRESHOLD:
        alert_text = "⚠️ 闭眼时间过长"
    
    # 状态变化检测和输出
    if 'last_status' not in locals():
        last_status = status
        last_alert = ""

    # 只在状态发生变化时输出
    if status != last_status:
        print(f"状态变化: {last_status} -> {status} ({duration:.1f}s)")
        last_status = status

    # 警告状态变化时的输出
    if alert_text != last_alert:
        if alert_text:
            print(f"[警告] {alert_text}")
        elif last_alert:
            print(f"[恢复] 异常状态已解除")
        last_alert = alert_text

    # 显示信息
    status_text = {
        "Left": "向左看", 
        "Right": "向右看", 
        "Center": "注视前方",
        "Blink": "眨眼",
        "Unknown": "未检测到"
    }.get(status, status)
    
    # 使用中文显示，确保编码正确
    frame = draw_chinese_text(frame, f"状态: {status_text}", (30, 40), font_size=30, text_color=(0, 255, 0))
    frame = draw_chinese_text(frame, f"左侧注视: {left_time:.1f}s", (30, 80), font_size=25, text_color=(255, 255, 0))
    frame = draw_chinese_text(frame, f"右侧注视: {right_time:.1f}s", (30, 110), font_size=25, text_color=(255, 255, 0))
    frame = draw_chinese_text(frame, f"闭眼时间: {blink_time:.1f}s", (30, 140), font_size=25, text_color=(255, 255, 0))
    
    # 校准状态显示
    if not is_calibrated:
        frame = draw_chinese_text(frame, f"校准中... {len(calibration_frames)}/30", (30, 240), font_size=30, text_color=(0, 165, 255))
    
    if alert_text:
        frame = draw_chinese_text(frame, alert_text, (30, 270), font_size=35, text_color=(0, 0, 255))
    
    # 添加使用说明
    frame = draw_chinese_text(frame, "按ESC退出", (w-150, h-20), font_size=20, text_color=(255, 255, 255))
    
    cv2.imshow("视线追踪监测", frame)
    
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
