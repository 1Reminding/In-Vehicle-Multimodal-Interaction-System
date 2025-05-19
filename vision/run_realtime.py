import cv2
from init import HeadPostEstimation

def generate_image():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        yield frame
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

def main():
    print("🎯 正在启动：实时摄像头头部姿态识别")
    head_pose = HeadPostEstimation()
    head_pose.frame_window_size = 15

    for res in head_pose.classify_pose_in_euler_angles(
        video=generate_image,
        poses=HeadPostEstimation.NOD_ACTION | HeadPostEstimation.SHAKE_ACTION
    ):
        for action, frames in res.items():
            print(f"[ALERT] 检测到动作: {action}")
            _, frame = frames[-1]
            cv2.putText(frame, f"{action.upper()} DETECTED", (40, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            cv2.imshow("Head Pose Estimation - Realtime", frame)
            cv2.waitKey(1)

if __name__ == "__main__":
    main()
