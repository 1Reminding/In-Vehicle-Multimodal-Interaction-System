import cv2

# 打开摄像头
capture = cv2.VideoCapture(0)  # 使用摄像头
fps = 30  # 设置帧率
size = (640, 480)  # 设置分辨率

# 设置摄像头参数
capture.set(cv2.CAP_PROP_FRAME_WIDTH, size[0])
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])
capture.set(cv2.CAP_PROP_FPS, fps)

# 将预测结果写成视频（可选）
video_writer = cv2.VideoWriter('result.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, size)

def generate_image():
    while True:
        ret, frame_rgb = capture.read()
        if not ret:
            print("无法获取摄像头画面")
            break
            
        # 显示实时画面
        cv2.imshow('Camera Feed', frame_rgb)
        
        # 按q键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        yield frame_bgr
        
    capture.release()
    video_writer.release()
    cv2.destroyAllWindows()
