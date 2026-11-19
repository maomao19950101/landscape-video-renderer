"""8K 静态照片电影感运镜生成器 (Ken Burns 动态运镜引擎)

将超高像素（8K/4K）静态风光摄影作品转化为 4K 电影级慢速运镜短视频：
- 支持平滑缓动曲线（Cosine Ease-in-out）
- 支持自定义变焦（Zoom-in / Zoom-out）与多维运镜轨迹（Pan & Tilt）
- 智能画面微光呼吸效应（Breathing Micro-Glow）
- 自动提取并混合环境声音轨（带淡入淡出）
- 跨平台硬件加速编码（macOS VideoToolbox, Windows NVENC, CPU x264）
"""

import math
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image

_SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPT_DIR))

from preview_generator import get_ffmpeg_bin
from render_engine import _get_hw_encoder_args


def _render_frame_worker(args):
    """子进程生成单帧图像数据。"""
    frame_idx, total_frames, img_path, target_size, zoom_range, pan_start, pan_end, breathing = args

    # 缓动函数：平滑加减速
    t = frame_idx / max(1, total_frames - 1)
    ease = (1.0 - math.cos(t * math.pi)) / 2.0

    target_w, target_h = target_size
    z_start, z_end = zoom_range
    current_zoom = z_start + (z_end - z_start) * ease

    cx = pan_start[0] + (pan_end[0] - pan_start[0]) * ease
    cy = pan_start[1] + (pan_end[1] - pan_start[1]) * ease

    # 打开底图进行裁剪
    with Image.open(img_path) as img:
        img_w, img_h = img.size

        # 保持目标画幅比例
        target_aspect = target_w / target_h
        img_aspect = img_w / img_h

        # 计算视窗尺寸
        crop_w = img_w / current_zoom
        crop_h = crop_w / target_aspect

        if crop_h > img_h:
            crop_h = img_h / current_zoom
            crop_w = crop_h * target_aspect

        # 计算视窗左上角坐标（中心点向四周展开）
        x1 = cx * img_w - crop_w / 2.0
        y1 = cy * img_h - crop_h / 2.0

        # 边界约束，避免露黑边
        x1 = max(0.0, min(x1, img_w - crop_w))
        y1 = max(0.0, min(y1, img_h - crop_h))
        x2 = x1 + crop_w
        y2 = y1 + crop_h

        cropped = img.crop((int(x1), int(y1), int(x2), int(y2)))
        resized = cropped.resize((target_w, target_h), Image.Resampling.BILINEAR)

        # 电影感微光呼吸效应（带高光保护，只在中间调与暗部轻微呼吸，绝不让高光过曝）
        if breathing:
            breath_delta = 0.015 * math.sin(t * math.pi * 3.0)
            arr = np.array(resized, dtype=np.float32)
            # 保护因子：亮度越高，呼吸增益越平滑归零 (Soft Knee)
            roll_off = np.clip(1.0 - arr / 255.0, 0, 1) ** 1.5
            arr = np.clip(arr + arr * breath_delta * roll_off, 0, 255).astype(np.uint8)
            return frame_idx, arr.tobytes()

        return frame_idx, resized.tobytes()


def generate_ken_burns(
    image_path: str,
    output_path: str,
    duration: float = 12.0,
    fps: int = 30,
    resolution: Tuple[int, int] = (3840, 2160),
    zoom_range: Tuple[float, float] = (1.02, 1.25),
    pan_start: Tuple[float, float] = (0.38, 0.32),
    pan_end: Tuple[float, float] = (0.46, 0.44),
    audio_source: Optional[str] = None,
    breathing: bool = True,
    workers: int = 8,
) -> dict:
    """
    生成 4K Ken Burns 运镜短视频。

    Args:
        image_path: 静态大图路径（推荐 8K/4K 构图原底）
        output_path: 导出 MP4 文件路径
        duration: 视频总时长（秒）
        fps: 帧率（默认 30fps）
        resolution: 导出分辨率，默认 4K (3840, 2160)
        zoom_range: 变焦倍率范围，如 (1.02, 1.25) 表示慢速推进
        pan_start: 起始视线中心点 (cx, cy)，0.0~1.0
        pan_end: 终点视线中心点 (cx, cy)，0.0~1.0
        audio_source: 可选的环境声音频源视频或音频文件
        breathing: 是否叠加微光呼吸生命感
        workers: 并行渲染进程数

    Returns:
        {"output_path": str, "duration_seconds": float, "total_frames": int}
    """
    start_time = time.time()
    total_frames = int(duration * fps)
    target_w, target_h = resolution
    ffmpeg_bin = get_ffmpeg_bin()

    print(f"🎬 启动 Ken Burns 运镜生成: {total_frames} 帧 @ {fps}fps, 分辨率 {target_w}x{target_h}")

    # 准备 FFmpeg 编码命令，通过 stdin 接收 rawvideo
    cmd = [
        ffmpeg_bin, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{target_w}x{target_h}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
    ]

    # 音频流处理（如果有音频源，提取对应时长并增加柔和淡入淡出）
    has_audio = False
    if audio_source and os.path.exists(audio_source):
        has_audio = True
        fade_out_start = max(0.5, duration - 1.5)
        afade_filter = f"afade=t=in:ss=0:d=1.0,afade=t=out:st={fade_out_start:.2f}:d=1.5"
        cmd += [
            "-i", audio_source,
            "-t", str(duration),
            "-filter_complex", f"[1:a]{afade_filter}[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:a", "aac",
            "-b:a", "192k",
        ]
    else:
        cmd += ["-map", "0:v"]

    cmd += _get_hw_encoder_args() + [output_path]

    pipe_proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    # 并行分块生成并按帧序送入 FFmpeg 管道
    tasks = [
        (i, total_frames, image_path, resolution, zoom_range, pan_start, pan_end, breathing)
        for i in range(total_frames)
    ]

    # 为避免内存挤压，分批提交执行
    batch_size = workers * 4
    rendered_frames = {}
    next_frame_to_write = 0

    with ProcessPoolExecutor(max_workers=workers) as executor:
        for i in range(0, total_frames, batch_size):
            batch = tasks[i : i + batch_size]
            results = executor.map(_render_frame_worker, batch)
            for frame_idx, raw_bytes in results:
                rendered_frames[frame_idx] = raw_bytes

                # 按次序把连续的帧写入 ffmpeg stdin
                while next_frame_to_write in rendered_frames:
                    pipe_proc.stdin.write(rendered_frames.pop(next_frame_to_write))
                    next_frame_to_write += 1

    pipe_proc.stdin.close()
    pipe_proc.wait()

    if pipe_proc.returncode != 0:
        err = pipe_proc.stderr.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"FFmpeg encoding failed with code {pipe_proc.returncode}: {err}")

    elapsed = time.time() - start_time
    print(f"✅ Ken Burns 运镜生成完成: 耗时 {elapsed:.1f}s, 输出: {output_path}")

    return {
        "output_path": output_path,
        "duration_seconds": round(elapsed, 1),
        "total_frames": total_frames,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="8K 静态照片电影感运镜短视频生成器")
    parser.add_argument("image", help="输入图像文件路径")
    parser.add_argument("output", help="输出视频路径")
    parser.add_argument("--duration", type=float, default=12.0, help="视频时长（秒）")
    parser.add_argument("--fps", type=int, default=30, help="帧率")
    parser.add_argument("--audio", help="可选的环境声音频源")
    parser.add_argument("--zoom-end", type=float, default=1.25, help="终点变焦倍率")

    args = parser.parse_args()
    generate_ken_burns(
        image_path=args.image,
        output_path=args.output,
        duration=args.duration,
        fps=args.fps,
        zoom_range=(1.02, args.zoom_end),
        audio_source=args.audio,
    )
