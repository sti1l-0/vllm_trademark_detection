from skimage.metrics import structural_similarity as ssim
import cv2
import os


def key_frame_image(video_path):
    cap = cv2.VideoCapture(video_path)

    frame_path = frame_folder(video_path)

    ret, frame1 = cap.read()
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    frame_number = 1
    threshold = 0.5

    while True:
        ret, frame2 = cap.read()
        if not ret:
            break

        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        ssim_value = ssim(gray1, gray2)
        if 1 - ssim_value > threshold:
            cv2.imwrite(f"{frame_path}/changed_frame_{frame_number}.jpg", frame2)
        gray1 = gray2
        frame_number += 1

    cap.release()

    return frame_path


def frame_folder(file_path):
    parts = file_path.split("/")
    folder_path = "/".join(parts[:-1]) + "/frames"
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


if __name__ == "__main__":
    print(key_frame_image(r"./demo/pepsi_ad.mp4"))
