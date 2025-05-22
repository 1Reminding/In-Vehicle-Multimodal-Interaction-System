import cv2
from gaze_tracking import GazeTracking
import time

def main():
    # 初始化眼神追踪器
    gaze = GazeTracking()
    
    # 打开摄像头 (0表示默认摄像头)
    webcam = cv2.VideoCapture(0)
    
    # 初始化状态跟踪变量
    current_state = "center"
    state_start_time = time.time()
    previous_distracted = False
    
    # 设置分心阈值（秒）
    DISTRACTION_THRESHOLD = {
        "blink": 1.0,  # 闭眼超过1秒判定为分心
        "left": 3.0,   # 看左边超过3秒判定为分心
        "right": 3.0,  # 看右边超过3秒判定为分心
    }

    while True:
        # 从摄像头获取新帧
        _, frame = webcam.read()

        # 将新帧发送给眼神追踪器进行分析
        gaze.refresh(frame)
        
        # 在帧上绘制分析结果
        frame = gaze.annotated_frame()

        # 获取眼睛状态和视线方向
        new_state = ""
        if gaze.is_blinking():
            new_state = "blink"
        elif gaze.is_right():
            new_state = "right"
        elif gaze.is_left():
            new_state = "left"
        elif gaze.is_center():
            new_state = "center"
            
        # 如果状态发生变化，更新开始时间
        if new_state != current_state:
            current_state = new_state
            state_start_time = time.time()
        
        # 计算当前状态持续时间
        duration = time.time() - state_start_time
        
        # 检查是否分心
        is_distracted = False
        if current_state in DISTRACTION_THRESHOLD and duration > DISTRACTION_THRESHOLD[current_state]:
            is_distracted = True
            
        # 只在分心状态变化时打印提示
        if is_distracted != previous_distracted:
            if is_distracted:
                print(f"警告：检测到分心！当前状态: {current_state}")
            else:
                print(f"分心状态已解除。当前状态: {current_state}")
            previous_distracted = is_distracted
            
        # 更新显示文本
        text = f"{current_state} ({duration:.1f}秒)"
        if is_distracted:
            text += " (分心)"

        # 在帧上显示文本
        cv2.putText(frame, text, (90, 60), cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)

        # 显示左右瞳孔位置的比例
        left_pupil = gaze.pupil_left_coords()
        right_pupil = gaze.pupil_right_coords()
        if left_pupil is not None:
            cv2.putText(frame, f"left: {left_pupil}", (90, 130), cv2.FONT_HERSHEY_DUPLEX, 0.9, (147, 58, 31), 1)
        if right_pupil is not None:
            cv2.putText(frame, f"right: {right_pupil}", (90, 165), cv2.FONT_HERSHEY_DUPLEX, 0.9, (147, 58, 31), 1)

        # 显示处理后的帧
        cv2.imshow("眼神追踪演示", frame)

        # 按'q'键退出
        if cv2.waitKey(1) == ord('q'):
            break

    # 释放资源
    webcam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()