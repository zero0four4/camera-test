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


# =============== 新增：图像质量分析增强函数 ===============
def get_uniform_region_noise(gray):
    """在均匀区域计算噪声，避免纹理干扰"""
    edges = cv2.Canny(gray, threshold1=50, threshold2=150)
    uniform_mask = ~edges.astype(bool)
    if np.sum(uniform_mask) < gray.size * 0.1:  # 均匀区域太少，回退到全图
        uniform_mask = np.ones_like(gray, dtype=bool)
    noise_std = np.std(gray[uniform_mask])
    return noise_std, uniform_mask


def analyze_tone(gray):
    """通过直方图分析影调问题"""
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    total = gray.size
    highlight_ratio = hist[230:].sum() / total
    shadow_ratio = hist[:25].sum() / total
    issues = []
    if highlight_ratio > 0.15:
        issues.append("可能过曝")
    if shadow_ratio > 0.15:
        issues.append("可能欠曝")
    return {
        "highlight_ratio": round(float(highlight_ratio), 4),
        "shadow_ratio": round(float(shadow_ratio), 4),
        "issues": issues
    }


def estimate_snr(gray, uniform_mask):
    """估算信噪比 SNR = 信号 / 噪声"""
    signal = np.mean(gray[uniform_mask])
    noise = np.std(gray[uniform_mask])
    snr = signal / (noise + 1e-6)
    return round(float(snr), 2)


def analyze_color_temperature(img):
    """初步分析色温倾向（红蓝比）"""
    b, g, r = cv2.split(img.astype(np.float32))
    r = np.clip(r, 1, None)
    b = np.clip(b, 1, None)
    rb_ratio = np.mean(r) / np.mean(b)
    if rb_ratio > 1.1:
        tendency = "偏暖"
    elif rb_ratio < 0.9:
        tendency = "偏冷"
    else:
        tendency = "中性"
    return {
        "rb_ratio": round(float(rb_ratio), 3),
        "tendency": tendency
    }


# =======================================================

def analyze_image(img_path):
    """增强版图像质量分析：覆盖亮度、噪声、SNR、影调、色温、清晰度"""
    img = cv2.imread(img_path)
    if img is None:
        raise Exception(f"❌ 无法读取图像: {img_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. 亮度（灰度均值）
    brightness = round(float(np.mean(gray)), 2)

    # 2. 均匀区域噪声 & SNR
    noise_std, uniform_mask = get_uniform_region_noise(gray)
    snr = estimate_snr(gray, uniform_mask)
    noise_std = round(noise_std, 2)

    # 3. 清晰度（Laplacian 方差）
    sharpness = round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 2)

    # 4. 影调分析
    tone_info = analyze_tone(gray)

    # 5. 色温倾向
    color_info = analyze_color_temperature(img)

    return {
        "brightness": brightness,
        "noise_std": noise_std,
        "snr": snr,
        "sharpness": sharpness,
        "tone": tone_info,
        "color_temperature": color_info
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
        print(f" • 亮度: {result['brightness']}")
        print(f" • 噪声 (均匀区): {result['noise_std']}")
        print(f" • 信噪比 (SNR): {result['snr']}")
        print(f" • 清晰度: {result['sharpness']}")

        print(f" • 影调: 高光占比 {result['tone']['highlight_ratio']:.2%}, "
              f"阴影占比 {result['tone']['shadow_ratio']:.2%}")
        if result['tone']['issues']:
            print(f"   ⚠️  {', '.join(result['tone']['issues'])}")

        print(f" • 色温: 红蓝比 = {result['color_temperature']['rb_ratio']} "
              f"({result['color_temperature']['tendency']})")

        # 保存结果
        with open("analysis_result.txt", "w", encoding="utf-8") as f:
            f.write("Camera Test Report\n")
            f.write("=" * 30 + "\n")
            f.write(f"照片路径: {photo_path}\n")
            f.write(f"亮度: {result['brightness']}\n")
            f.write(f"噪声 (均匀区): {result['noise_std']}\n")
            f.write(f"信噪比 (SNR): {result['snr']}\n")
            f.write(f"清晰度: {result['sharpness']}\n")
            f.write(f"影调 - 高光占比: {result['tone']['highlight_ratio']:.4f}\n")
            f.write(f"影调 - 阴影占比: {result['tone']['shadow_ratio']:.4f}\n")
            f.write(f"影调问题: {', '.join(result['tone']['issues']) if result['tone']['issues'] else '无'}\n")
            f.write(f"色温 - 红蓝比: {result['color_temperature']['rb_ratio']}\n")
            f.write(f"色温倾向: {result['color_temperature']['tendency']}\n")

        print("\n📄 报告已保存至: analysis_result.txt")

    except Exception as e:
        print(f"💥 错误: {e}")
        import traceback

        traceback.print_exc()
        input("按回车退出...")