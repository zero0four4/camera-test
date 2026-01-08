import os
import cv2
import numpy as np
import time
import subprocess

# ===== 配置区 =====
ADB_PATH = r"D:\adb\platform-tools\adb.exe"  # 你的 ADB 路径
PHOTO_DIR_LOCAL = "photos"  # 本地保存目录
MAX_WAIT_SEC = 5  # 等待拍照完成时间

# 创建本地目录
os.makedirs(PHOTO_DIR_LOCAL, exist_ok=True)


def run_adb(cmd):
    """执行 ADB 命令并返回输出"""
    full_cmd = f'"{ADB_PATH}" {cmd}'
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()


def take_photo():
    """触发拍照 + 获取最新照片"""
    print("📸 正在触发快门...")
    # 方法1: 使用 CAMERA 键 (KEYCODE_CAMERA = 27)
    run_adb("shell input keyevent 27")
    # 如果无效，可尝试音量上键（很多手机设为快门）:
    # run_adb("shell input keyevent 24")

    print(f"⏳ 等待 {MAX_WAIT_SEC} 秒让照片保存...")
    time.sleep(MAX_WAIT_SEC)

    # 获取 DCIM/Camera 下最新照片文件名
    stdout, _ = run_adb('shell "ls -t /sdcard/DCIM/Camera/ | head -n 1"')
    if not stdout:
        raise Exception("❌ 未找到照片！请确认已打开相机App并允许存储权限")

    remote_path = f"/sdcard/DCIM/Camera/{stdout.strip()}"
    local_path = os.path.join(PHOTO_DIR_LOCAL, stdout.strip())

    print(f"📥 正在拉取照片: {remote_path}")
    run_adb(f'pull "{remote_path}" "{local_path}"')

    return local_path


def analyze_image(img_path):
    """分析图像质量"""
    img = cv2.imread(img_path)
    if img is None:
        raise Exception(f"❌ 无法读取图像: {img_path}")

    # 转灰度
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. 平均亮度
    brightness = np.mean(gray)

    # 2. 噪声水平（标准差）
    noise = np.std(gray)

    # 3. 清晰度（Laplacian 方差）
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()

    return {
        "brightness": round(brightness, 2),
        "noise": round(noise, 2),
        "sharpness": round(sharpness, 2)
    }


# ===== 主流程 =====
if __name__ == "__main__":
    try:
        print("📱 请确保手机已打开「相机」App，并停留在拍照界面！")
        input("✅ 准备好后按回车开始测试...")

        # 拍照并拉取
        photo_path = take_photo()
        print(f"✅ 照片已保存至: {photo_path}")

        # 分析
        result = analyze_image(photo_path)
        print("\n📊 图像质量分析结果:")
        print(f"  • 亮度: {result['brightness']}")
        print(f"  • 噪声: {result['noise']}")
        print(f"  • 清晰度: {result['sharpness']}")

        # 保存结果
        with open("analysis_result.txt", "w", encoding="utf-8") as f:
            f.write("Camera Test Report\n")
            f.write("=" * 20 + "\n")
            f.write(f"照片路径: {photo_path}\n")
            f.write(f"亮度: {result['brightness']}\n")
            f.write(f"噪声: {result['noise']}\n")
            f.write(f"清晰度: {result['sharpness']}\n")
        print("\n📄 报告已保存至: analysis_result.txt")

    except Exception as e:
        print(f"💥 错误: {e}")
        input("按回车退出...")