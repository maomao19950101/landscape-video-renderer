"""全片渲染引擎 — FFmpeg 滤镜链（快速路径）+ Python 逐帧 Bloom（精细路径）"""

import concurrent.futures
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional

import numpy as np
from PIL import Image

_SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPT_DIR))

from focus_detector import compute_ellipse_axes, detect_focus
from presets import get_preset
from preview_generator import (
    apply_style_to_frame,
    get_video_info,
    precompute_vignette_masks,
)


def _process_single_frame(args):
    """并行处理单帧任务。"""
    frame_path, out_path, params, focus, masks = args
    apply_style_to_frame(frame_path, out_path, params, focus, precomputed_masks=masks)
    return out_path


def render_video(
    video_path: str,
    preset_name: str,
    output_path: str,
    focus_hint: Optional[tuple[float, float]] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> dict:
    """
    全片渲染主入口。

    策略选择：
    - 无 Bloom 的预设 → FFmpeg 纯滤镜链（极速路径）
    - 有 Bloom 的预设 → Python 逐帧处理（精细路径）

    Args:
        video_path: 输入视频路径
        preset_name: 预设名称或别名
        output_path: 输出视频路径
        focus_hint: 可选的用户指定焦点 (cx, cy)，0.0~1.0
        progress_callback: 可选的进度回调 (current_frame, total_frames)

    Returns:
        {"output_path": str, "duration_seconds": float, "frames_processed": int}
    """
    start_time = time.time()

    preset = get_preset(preset_name)
    if preset is None:
        raise ValueError(f"Unknown preset: {preset_name}")

    params = preset["params"]
    info = get_video_info(video_path)

    # 检测焦点（用第一帧做检测）
    with tempfile.TemporaryDirectory() as tmpdir:
        first_frame = str(Path(tmpdir) / "first.jpg")
        subprocess.run(
            ["ffmpeg", "-y", "-v", "quiet", "-i", video_path,
             "-frames:v", "1", "-q:v", "2", first_frame],
            check=True,
        )
        focus = detect_focus(first_frame, user_hint=focus_hint)

    if params["bloom_enabled"] and params["bloom_intensity"] > 0:
        frames = _render_framewise(video_path, output_path, params, focus, info, progress_callback)
    else:
        frames = _render_ffmpeg_fast(video_path, output_path, params, focus, info)

    elapsed = time.time() - start_time
    return {
        "output_path": output_path,
        "duration_seconds": round(elapsed, 1),
        "frames_processed": frames,
    }


def _render_ffmpeg_fast(
    video_path: str,
    output_path: str,
    params: dict,
    focus: tuple[float, float],
    info: dict,
) -> int:
    """FFmpeg 纯滤镜链快速渲染（无 Bloom 的预设走此路径）。"""
    w, h = info["width"], info["height"]
    cx, cy = focus
    filters = []

    # 色温偏移：通过 colorbalance 实现
    temp = params["color_temp_shift"]
    if temp != 0:
        rs = max(-1, min(1, temp / 50.0))
        bs = max(-1, min(1, -temp / 50.0))
        filters.append(f"colorbalance=rs={rs:.2f}:bs={bs:.2f}")

    # 画面色彩与明暗调整 (eq 滤镜合并)
    eq_parts = []
    sat = params["saturation_adj"]
    if sat != 0:
        eq_parts.append(f"saturation={1.0 + sat:.2f}")

    contrast = params["contrast_subject"]
    if contrast > 0:
        eq_parts.append(f"contrast={1.0 + contrast:.2f}")

    brightness = params["brightness_subject"]
    if brightness > 0:
        eq_parts.append(f"brightness={brightness * 0.5:.2f}")

    if eq_parts:
        filters.append(f"eq={':'.join(eq_parts)}")

    # 暗角 (直接使用计算好的像素坐标与宽高比)
    vi = params["vignette_intensity"]
    if vi > 0:
        angle = f"PI/{max(2, int(6 - vi * 4))}"
        x0_px = int(cx * w)
        y0_px = int(cy * h)
        aspect_val = f"{w}/{h}"
        filters.append(f"vignette=angle={angle}:x0={x0_px}:y0={y0_px}:aspect={aspect_val}")

    # 胶片颗粒
    grain = params["grain_amount"]
    if grain > 0:
        noise_amount = int(grain * 100)
        filters.append(f"noise=alls={noise_amount}:allf=t")

    filter_chain = ",".join(filters) if filters else "null"

    # 构建 FFmpeg 命令
    cmd = ["ffmpeg", "-y", "-v", "quiet", "-i", video_path]

    if info["has_audio"]:
        cmd += [
            "-filter_complex", f"[0:v]{filter_chain}[vout]",
            "-map", "[vout]", "-map", "0:a?",
            "-c:a", "copy",
        ]
    else:
        cmd += ["-vf", filter_chain]

    cmd += [
        "-c:v", "libx264", "-preset", "medium",
        "-crf", "18", "-pix_fmt", "yuv420p",
        output_path,
    ]

    subprocess.run(cmd, check=True)

    total_frames = int(info["duration"] * info["fps"])
    return total_frames


def _render_framewise(
    video_path: str,
    output_path: str,
    params: dict,
    focus: tuple[float, float],
    info: dict,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> int:
    """Python 逐帧渲染（含 Bloom 的预设走此路径）。"""
    w, h = info["width"], info["height"]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        frames_dir = tmpdir_path / "frames"
        output_frames_dir = tmpdir_path / "rendered"
        frames_dir.mkdir()
        output_frames_dir.mkdir()

        # 解码所有帧
        subprocess.run(
            ["ffmpeg", "-y", "-v", "quiet", "-i", video_path,
             "-q:v", "2", str(frames_dir / "frame_%06d.jpg")],
            check=True,
        )

        # 逐帧渲染（多核并行 + 蒙版预计算）
        frame_files = sorted(frames_dir.glob("frame_*.jpg"))
        actual_count = len(frame_files)
        masks = precompute_vignette_masks(w, h, params, focus)

        frame_tasks = [
            (str(f), str(output_frames_dir / f.name), params, focus, masks)
            for f in frame_files
        ]

        max_workers = min(8, os.cpu_count() or 4)
        chunk = max(1, actual_count // (max_workers * 4))

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            for i, _ in enumerate(executor.map(_process_single_frame, frame_tasks, chunksize=chunk)):
                if progress_callback and (i % 10 == 0 or i == actual_count - 1):
                    progress_callback(i + 1, actual_count)

        # 编码回视频
        encode_cmd = [
            "ffmpeg", "-y", "-v", "quiet",
            "-framerate", str(info["fps"]),
            "-i", str(output_frames_dir / "frame_%06d.jpg"),
        ]

        # 混入音轨
        if info["has_audio"]:
            encode_cmd += ["-i", video_path, "-map", "0:v", "-map", "1:a", "-c:a", "copy"]

        encode_cmd += [
            "-c:v", "libx264", "-preset", "medium",
            "-crf", "18", "-pix_fmt", "yuv420p",
            output_path,
        ]
        subprocess.run(encode_cmd, check=True)

    return actual_count


if __name__ == "__main__":
    """命令行入口：python render_engine.py <input> <preset> <output> [cx cy]"""
    if len(sys.argv) < 4:
        print("Usage: python render_engine.py <input_video> <preset_name> <output_video> [cx cy]")
        sys.exit(1)

    input_path = sys.argv[1]
    preset_name = sys.argv[2]
    output_path = sys.argv[3]
    hint = None
    if len(sys.argv) >= 6:
        hint = (float(sys.argv[4]), float(sys.argv[5]))

    def on_progress(current, total):
        pct = int(current / total * 100)
        print(f"\r渲染进度: {pct}% ({current}/{total})", end="", flush=True)

    print(f"开始渲染: {preset_name}")
    result = render_video(input_path, preset_name, output_path, focus_hint=hint, progress_callback=on_progress)
    print(f"\n✅ 渲染完成！耗时 {result['duration_seconds']}s, 处理 {result['frames_processed']} 帧")
    print(f"   输出: {result['output_path']}")
