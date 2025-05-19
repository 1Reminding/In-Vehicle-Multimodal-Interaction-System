head_post = HeadPostEstimation()
for res in head_post.classify_pose_in_euler_angles(video=generate_image, poses=HeadPostEstimation.NOD_ACTION | HeadPostEstimation.SHAKE_ACTION):
    print(list(res.keys()))