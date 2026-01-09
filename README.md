# 📸 Android 相机自动化测试系统

> 一个轻量级、开源的 **手机相机图像质量（Image Quality, IQ）自动化评估工具**，基于 Python + OpenCV + ADB 实现，支持从拍照到成像质量分析的完整闭环。

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-orange)](LICENSE)

## 🎯 项目目标

将传统的 **主观相机评测** 转化为 **客观、可量化、可重复** 的自动化测试流程，覆盖图像质量核心维度：
- 亮度与曝光合理性
- 噪声水平与信噪比（SNR）
- 清晰度（对焦质量）
- 影调分布（高光/阴影）
- 色温倾向（白平衡）

适用于 Camera 测试实习生、ISP 调优辅助、图像算法验证等场景。

## 🔧 核心功能

| 功能 | 技术实现 | 价值 |
|------|--------|------|
| 📱 自动拍照 | `adb shell input keyevent 27` | 无需人工干预 |
| 📥 自动拉图 | `adb pull` 最新照片 | 支持 JPEG |
| 🖼️ 图像质量分析 | OpenCV + NumPy | 客观量化成像表现 |
| 📊 结构化报告 | 自动生成 `.txt` | 可追溯、可对比 |

### ✨ 支持的图像质量指标

| 指标 | 计算方法 | 意义 |
|------|--------|------|
| **亮度** | 灰度图像均值 | 反映整体曝光水平 |
| **噪声** | 在 Canny 边缘检测后的**均匀区域**计算标准差 | 避免纹理干扰，更准确 |
| **信噪比 (SNR)** | `信号均值 / 噪声标准差` | 值越高，图像越“干净” |
| **清晰度** | Laplacian 算子方差 | 衡量边缘锐度，判断对焦是否准确 |
| **影调** | 灰度直方图分析（高光占比 >15% → 过曝；阴影占比 >15% → 欠曝） | 识别曝光失衡 |
| **色温倾向** | RGB 通道均值比例（红蓝比 >1.1 → 偏暖；<0.9 → 偏冷） | 初步判断白平衡偏差 |

## 📈 示例输出

运行 `python camera_test.py` 后，终端输出如下：
📊 图像质量分析结果:
• 亮度: 102.9
• 噪声 (均匀区): 62.02
• 信噪比 (SNR): 1.65
• 清晰度: 122.8
• 影调: 高光占比 1.08%, 阴影占比 14.72%
• 色温: 红蓝比 = 1.292 (偏暖)

同时生成 `analysis_result.txt` 报告文件，便于存档或批量分析。

## 🛠️ 技术栈

- **语言**: Python 3.7+
- **核心库**: 
  - `opencv-python`（图像处理）
  - `numpy`（数值计算）
  - `subprocess`（ADB 调用）
- **工具**: Android Debug Bridge (ADB)
- **算法**:
  - Canny 边缘检测（选均匀区域）
  - 直方图分析（影调）
  - Laplacian 算子（清晰度）

## 🚀 快速开始

### 前置条件
1. 手机已开启 **开发者模式** 和 **USB 调试**
2. 已安装 [ADB 工具](https://developer.android.com/tools/releases/platform-tools)
3. 手机上已打开 **相机 App**（停留在拍照界面）

### 运行
```bash
git clone https://github.com/zero0four4/camera-test.git
cd camera-test
pip install opencv-python numpy
python camera_test.py
