"""焦点定位器 — 三级降级策略：用户指定 > 显著性检测 > 黄金分割兜底"""

import sys
from pathlib import Path
from typing import Optional

# 黄金分割比例常量
GOLDEN_RATIO = 0.618


def detect_focus(
    image_path: str,
    user_hint: Optional[tuple[float, float]] = None,
) -> tuple[float, float]:
    """
    检测画面焦点位置，返回归一化坐标 (cx, cy)，范围 0.0~1.0。

    三级降级策略：
    1. 用户指定坐标 → 直接使用
    2. OpenCV 显著性检测 → 自动定位
    3. 黄金分割兜底 → 画面中心偏上（风景片通用构图重心）
    """
    # 第一级：用户指定
    if user_hint is not None:
        cx, cy = user_hint
        cx = max(0.0, min(1.0, cx))
        cy = max(0.0, min(1.0, cy))
        return (cx, cy)

    # 第二级：尝试 OpenCV 显著性检测
    try:
        focus = _saliency_detect(image_path)
        if focus is not None:
            return focus
    except Exception:
        pass  # OpenCV 不可用或检测失败，降级到兜底

    # 第三级：黄金分割兜底
    return _golden_ratio_fallback()


def _saliency_detect(image_path: str) -> Optional[tuple[float, float]]:
    """使用 OpenCV 静态显著性检测定位焦点。"""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None

    img = cv2.imread(image_path)
    if img is None:
        return None

    h, w = img.shape[:2]

    # 使用频谱残差法（Spectral Residual）做显著性检测
    saliency = cv2.saliency.StaticSaliencySpectralResidual_create()
    success, saliency_map = saliency.computeSaliency(img)
    if not success or saliency_map is None:
        return None

    saliency_map = (saliency_map * 255).astype("uint8")

    # 高斯模糊平滑显著性图，避免噪点干扰
    saliency_map = cv2.GaussianBlur(saliency_map, (51, 51), 0)

    # 找到显著性最高的区域中心
    _, max_val, _, max_loc = cv2.minMaxLoc(saliency_map)

    # 显著性太低（画面无明显焦点），返回 None 触发降级
    if max_val < 30:
        return None

    cx = max_loc[0] / w
    cy = max_loc[1] / h

    # 限制在安全范围内（避免焦点过于靠近边缘）
    cx = max(0.2, min(0.8, cx))
    cy = max(0.2, min(0.8, cy))

    return (cx, cy)


def _golden_ratio_fallback() -> tuple[float, float]:
    """黄金分割兜底：画面中心偏上（风景片最通用的构图重心）。"""
    cx = 0.5
    cy = 1.0 - GOLDEN_RATIO  # ≈ 0.382，画面上方约 1/3 处
    return (cx, cy)


def compute_ellipse_axes(
    width: int, height: int, radius: float
) -> tuple[int, int]:
    """
    根据画面宽高比，计算椭圆蒙版的长短轴像素值。
    radius: 占画面短边的比例 (0.3~0.8)。
    返回 (axis_x, axis_y) 像素值。
    """
    short_side = min(width, height)
    base = int(short_side * radius)

    if width > height:
        # 横屏：X 轴拉长
        ratio = width / height
        axis_x = int(base * ratio * 0.8)
        axis_y = base
    elif height > width:
        # 竖屏：Y 轴拉长
        ratio = height / width
        axis_x = base
        axis_y = int(base * ratio * 0.8)
    else:
        axis_x = base
        axis_y = base

    return (axis_x, axis_y)
