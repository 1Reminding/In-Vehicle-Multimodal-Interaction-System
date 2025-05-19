import cv2

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("⚠️ 摄像头帧读取失败")
        continue
    cv2.imshow("Check Frame", frame)
    if cv2.waitKey(1) == 27:
        break
cap.release()
cv2.destroyAllWindows()
