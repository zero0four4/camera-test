# camera_test.py
import os
import time
import cv2

# 🔧 设置 ADB 完整路径
ADB_PATH = r"D:\adb\platform-tools\adb.exe"


def capture_and_analyze():
    print("=== 开始 Camera 自动化测试 ===")

    os.makedirs("photo", exist_ok=True)

    input("📱 请在手机上打开「相机」App，然后回到这里按回车继续...")

    print("📸 正在截图保存预览画面...")
    os.system(f'"{ADB_PATH}" shell screencap -p /sdcard/camera_preview.png')
    time.sleep(1.5)

    print("📥 正在拉取截图到本地...")
    result = os.system(f'"{ADB_PATH}" pull /sdcard/camera_preview.png photo/')

    if result == 0:
        img_path = "photo/camera_preview.png"
        img = cv2.imread(img_path)
        if img is not None:
            avg_brightness = img.mean()
            std_brightness = img.std()
            print(f"✅ 图像分析成功！")
            print(f"   平均亮度: {avg_brightness:.1f}")
            print(f"   噪声水平: {std_brightness:.1f}")

            with open("photo/analysis.txt", "w", encoding="utf-8") as f:
                f.write(f"平均亮度: {avg_brightness:.1f}\n")
                f.write(f"噪声水平: {std_brightness:.1f}\n")
            print("📄 分析结果已保存到 photo/analysis.txt")
        else:
            print("❌ 无法读取图像")
    else:
        print("❌ ADB 拉取失败，请检查路径和设备连接")


if __name__ == "__main__":
    capture_and_analyze()