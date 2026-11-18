"""单帧预览生成器 — 抽取代表帧 + 应用风格预览"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

# 添加 scripts 目录到 path
_SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPT_DIR))

from focus_detector import compute_ellipse_axes, detect_focus
from presets import get_preset


def get_ffmpeg_bin() -> str:
    """跨平台获取 ffmpeg 可执行文件路径（优先 PATH，备选 bin 目录）。"""
    f = shutil.which("ffmpeg")
    if f:
        return f
    for cand in [
        Path("bin/ffmpeg.exe"), Path("bin/ffmpeg"),
        _SCRIPT_DIR.parent / "bin" / "ffmpeg.exe",
        _SCRIPT_DIR.parent / "bin" / "ffmpeg"
    ]:
        if cand.exists():
            return str(cand.resolve())
    return "ffmpeg"


def get_ffprobe_bin() -> str:
    """跨平台获取 ffprobe 可执行文件路径。"""
    f = shutil.which("ffprobe")
    if f:
        return f
    for cand in [
        Path("bin/ffprobe.exe"), Path("bin/ffprobe"),
        _SCRIPT_DIR.parent / "bin" / "ffprobe.exe",
        _SCRIPT_DIR.parent / "bin" / "ffprobe"
    ]:
        if cand.exists():
            return str(cand.resolve())
    return "ffprobe"


def get_video_info(video_path: str) -> dict:
    """使用 ffprobe 获取视频元数据。"""
    cmd = [
        get_ffprobe_bin(), "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)

    # 找视频流
    video_stream = None
    for s in data.get("streams", []):
        if s.get("codec_type") == "video":
            video_stream = s
            break

    if video_stream is None:
        raise ValueError("No video stream found")

    # 检查是否有音频流
    has_audio = any(
        s.get("codec_type") == "audio" for s in data.get("streams", [])
    )

    width = int(video_stream["width"])
    height = int(video_stream["height"])
    duration = float(data.get("format", {}).get("duration", 0))
    fps_parts = video_stream.get("r_frame_rate", "30/1").split("/")
    fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

    return {
        "width": width,
        "height": height,
        "duration": duration,
        "fps": fps,
        "has_audio": has_audio,
        "orientation": "portrait" if height > width else "landscape",
    }


def extract_representative_frame(video_path: str, output_path: str, duration: float) -> None:
    """抽取视频中间时刻的一帧作为代表帧。"""
    # 取视频 40% 位置的帧（通常比正中间更有代表性）
    seek_time = max(0, duration * 0.4)
    cmd = [
        get_ffmpeg_bin(), "-y", "-v", "quiet",
        "-ss", str(seek_time),
        "-i", video_path,
        "-frames:v", "1",
        "-q:v", "2",
        output_path,
    ]
    subprocess.run(cmd, check=True)


def precompute_vignette_masks(w: int, h: int, params: dict, focus: tuple[float, float]):
    """预计算椭圆画圈蒙版与对比增强矩阵，避免逐帧重复计算。"""
    cx_px = int(focus[0] * w)
    cy_px = int(focus[1] * h)
    ax, ay = compute_ellipse_axes(w, h, params["vignette_radius"])

    y_coords, x_coords = np.mgrid[0:h, 0:w]
    dist = np.sqrt(
        ((x_coords - cx_px) / max(ax, 1)) ** 2
        + ((y_coords - cy_px) / max(ay, 1)) ** 2
    )
    softness = max(params["vignette_softness"], 0.01)
    vignette_mask = np.clip((dist - 0.5) / softness, 0, 1)
    subject_mask = np.clip(1.0 - dist, 0, 1)
    brightness_boost = params["brightness_subject"] * subject_mask
    contrast_boost = params["contrast_subject"] * subject_mask
    return vignette_mask, brightness_boost, contrast_boost


def apply_style_to_frame(
    image_path: str,
    output_path: str,
    params: dict,
    focus: tuple[float, float],
    precomputed_masks=None,
) -> None:
    """对单帧图像应用风格渲染（色彩 + 暗角 + Bloom）。"""
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img, dtype=np.float32) / 255.0
    h, w, _ = arr.shape

    # === 第一层：色彩基底 ===
    # 色温偏移
    temp = params["color_temp_shift"]
    if temp != 0:
        shift = temp / 100.0
        arr[:, :, 0] = np.clip(arr[:, :, 0] + shift * 0.6, 0, 1)   # R
        arr[:, :, 2] = np.clip(arr[:, :, 2] - shift * 0.4, 0, 1)   # B

    # 饱和度调整
    sat = params["saturation_adj"]
    if sat != 0:
        gray = np.mean(arr, axis=2, keepdims=True)
        arr = np.clip(arr + (arr - gray) * sat, 0, 1)

    # 暗部着色
    if params["tint_shadows"]:
        tint = _hex_to_rgb(params["tint_shadows"])
        luminance = np.mean(arr, axis=2, keepdims=True)
        shadow_mask = np.clip(1.0 - luminance * 2.5, 0, 1)
        for c in range(3):
            arr[:, :, c] = np.clip(
                arr[:, :, c] + shadow_mask[:, :, 0] * tint[c] * 0.15, 0, 1
            )

    # 高光着色
    if params["tint_highlights"]:
        tint = _hex_to_rgb(params["tint_highlights"])
        luminance = np.mean(arr, axis=2, keepdims=True)
        highlight_mask = np.clip(luminance * 2.0 - 0.8, 0, 1)
        for c in range(3):
            arr[:, :, c] = np.clip(
                arr[:, :, c] + highlight_mask[:, :, 0] * tint[c] * 0.12, 0, 1
            )

    # === 第二层：画圈视线聚焦（椭圆渐变蒙版）===
    if precomputed_masks is not None:
        vignette_mask, brightness_boost, contrast_boost = precomputed_masks
    else:
        vignette_mask, brightness_boost, contrast_boost = precompute_vignette_masks(w, h, params, focus)

    for c in range(3):
        arr[:, :, c] = np.clip(arr[:, :, c] + brightness_boost, 0, 1)
        arr[:, :, c] = np.clip(
            0.5 + (arr[:, :, c] - 0.5) * (1.0 + contrast_boost), 0, 1
        )

    # 背景压暗
    intensity = params["vignette_intensity"]
    for c in range(3):
        arr[:, :, c] = arr[:, :, c] * (1.0 - vignette_mask * intensity)

    # === 第三层：Bloom 柔光漫射（下采样极速版）===
    if params["bloom_enabled"] and params["bloom_intensity"] > 0:
        luminance = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        bright_mask = np.clip(luminance - params["bloom_threshold"], 0, 1)
        bright_mask = bright_mask[:, :, np.newaxis]

        bloom_layer = arr * bright_mask
        # 降采样优化：若分辨率大于 1080p，先下采样 1/2 计算模糊再放大，速度大幅提升且视觉更柔和自然
        down_scale = 2 if max(w, h) >= 1920 else 1
        if down_scale > 1:
            small_w, small_h = w // down_scale, h // down_scale
            bloom_small = Image.fromarray((bloom_layer * 255).astype(np.uint8)).resize(
                (small_w, small_h), Image.Resampling.BILINEAR
            )
            bloom_blurred = bloom_small.filter(
                ImageFilter.GaussianBlur(radius=params["bloom_radius"] / down_scale)
            )
            bloom_img = bloom_blurred.resize((w, h), Image.Resampling.BILINEAR)
        else:
            bloom_img = Image.fromarray((bloom_layer * 255).astype(np.uint8)).filter(
                ImageFilter.GaussianBlur(radius=params["bloom_radius"])
            )

        bloom_arr = np.array(bloom_img, dtype=np.float32) / 255.0

        # Screen 混合模式
        blend_strength = params["bloom_intensity"]
        arr = np.clip(1.0 - (1.0 - arr) * (1.0 - bloom_arr * blend_strength), 0, 1)

    # === 胶片颗粒 ===
    if params["grain_amount"] > 0:
        noise = np.random.normal(0, params["grain_amount"], arr.shape).astype(np.float32)
        arr = np.clip(arr + noise, 0, 1)

    # 输出
    result = Image.fromarray((arr * 255).astype(np.uint8))
    result.save(output_path, quality=92)


def generate_preview(
    video_path: str,
    preset_name: str,
    output_path: str,
    focus_hint: tuple[float, float] | None = None,
) -> dict:
    """
    完整的预览生成流程：
    1. ffprobe 探测视频信息
    2. 抽取代表帧
    3. 检测焦点
    4. 应用风格渲染
    5. 输出预览 jpg
    """
    # 获取视频信息
    info = get_video_info(video_path)

    # 查找预设
    preset = get_preset(preset_name)
    if preset is None:
        raise ValueError(f"Unknown preset: {preset_name}")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 抽取代表帧
        raw_frame = str(Path(tmpdir) / "frame.jpg")
        extract_representative_frame(video_path, raw_frame, info["duration"])

        # 检测焦点
        focus = detect_focus(raw_frame, user_hint=focus_hint)

        # 应用风格
        apply_style_to_frame(raw_frame, output_path, preset["params"], focus)

    return {
        "preview_path": output_path,
        "focus": focus,
        "preset": preset["name"],
        "video_info": info,
    }


def _hex_to_rgb(hex_str: str) -> tuple[float, float, float]:
    """将 hex 颜色字符串转为 0~1 范围的 RGB 元组。"""
    hex_str = hex_str.lstrip("#")
    return (
        int(hex_str[0:2], 16) / 255.0,
        int(hex_str[2:4], 16) / 255.0,
        int(hex_str[4:6], 16) / 255.0,
    )
