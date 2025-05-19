from init import HeadPostEstimation
from load import generate_image

def main():
    # 初始化头部姿态检测器
    head_pose = HeadPostEstimation()
    
    # 设置检测参数（可选）
    head_pose.frame_window_size = 15  # 设置检测窗口大小
    
    # 运行检测
    for res in head_pose.classify_pose_in_euler_angles(
        video=generate_image, 
        poses=HeadPostEstimation.NOD_ACTION | HeadPostEstimation.SHAKE_ACTION
    ):
        # 获取检测结果
        for action, frames in res.items():
            print(f"检测到动作: {action}")

if __name__ == "__main__":
    main()