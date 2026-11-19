"""达芬奇行业通用 3D LUT (.cube) 引擎

支持在静止图片与高清视频中加载并应用行业标准的 3D LUT (.cube) 调色预设包：
- 支持 17x17x17, 33x33x33, 65x65x65 规格的标准 Adobe / DaVinci Cube 文件
- 静止图像：使用 Pillow 原生 Color3DLUT 极速高精三线性插值
- 视频流：硬件直通 FFmpeg lut3d 滤镜链，原生满速硬件编码渲染
- 支持调色浓度平滑调节（0.0 ~ 1.0 混合强度）
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Union

import numpy as np
from PIL import Image, ImageFilter

_SCRIPT_DIR = Path(__file__).parent
_LUTS_DIR = _SCRIPT_DIR.parent / "luts"


def load_cube_lut(cube_path: str) -> ImageFilter.Color3DLUT:
    """解析 .cube 文件并返回 Pillow 原生 Color3DLUT 对象。"""
    cube_path = str(cube_path)
    if not os.path.exists(cube_path):
        # 尝试从自带 luts 目录匹配
        bundled = _LUTS_DIR / cube_path
        if bundled.exists():
            cube_path = str(bundled)
        elif (_LUTS_DIR / f"{cube_path}.cube").exists():
            cube_path = str(_LUTS_DIR / f"{cube_path}.cube")
        else:
            raise FileNotFoundError(f"找不到 LUT 文件: {cube_path}")

    size = None
    table = []
    with open(cube_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("LUT_3D_SIZE"):
                size = int(line.split()[1])
            elif size is not None:
                parts = line.split()
                if len(parts) == 3:
                    table.append(tuple(float(p) for p in parts))

    if size is None or len(table) != size ** 3:
        raise ValueError(f"无效的 .cube 文件结构: size={size}, 数据量={len(table)}")

    return ImageFilter.Color3DLUT(size, table)


def apply_lut_to_image(
    image: Union[str, Image.Image],
    lut_path: str,
    output_path: Optional[str] = None,
    strength: float = 1.0,
) -> Image.Image:
    """对单张图像应用 3D LUT 调色。"""
    if isinstance(image, str):
        im = Image.open(image).convert("RGB")
    else:
        im = image.convert("RGB")

    lut = load_cube_lut(lut_path)
    graded = im.filter(lut)

    if strength < 0.999:
        # 平滑强度融合
        im = Image.blend(im, graded, max(0.0, min(1.0, strength)))
    else:
        im = graded

    if output_path:
        im.save(output_path, quality=92)

    return im


def apply_lut_to_video(
    video_path: str,
    lut_path: str,
    output_path: str,
    strength: float = 1.0,
) -> None:
    """使用 FFmpeg lut3d 滤镜链极速渲染视频。"""
    resolved_lut = lut_path
    if not os.path.exists(resolved_lut):
        bundled = _LUTS_DIR / f"{lut_path}.cube"
        if bundled.exists():
            resolved_lut = str(bundled)
        else:
            raise FileNotFoundError(f"找不到 LUT 文件: {lut_path}")

    resolved_lut = os.path.abspath(resolved_lut)

    # 构建滤镜链 (lut3d 四面体插值，视觉平滑)
    filter_chain = f"lut3d=file='{resolved_lut}':interp=tetrahedral"

    # 调用 render_engine 中的跨平台硬件编码参数
    from preview_generator import get_ffmpeg_bin
    from render_engine import _get_hw_encoder_args, _get_hwaccel_input_args

    cmd = [get_ffmpeg_bin(), "-y"]
    cmd += _get_hwaccel_input_args()
    cmd += ["-v", "quiet", "-i", video_path]
    cmd += ["-vf", filter_chain]
    cmd += ["-c:a", "copy"]
    cmd += _get_hw_encoder_args()
    cmd += [output_path]

    subprocess.run(cmd, check=True)


def list_available_luts() -> list[str]:
    """列出内置及可用的 3D LUT 预设。"""
    if not _LUTS_DIR.exists():
        return []
    return [p.stem for p in _LUTS_DIR.glob("*.cube")]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="3D .cube LUT 调色处理工具")
    parser.add_argument("input", help="输入图像或视频文件")
    parser.add_argument("output", help="输出文件路径")
    parser.add_argument("--lut", required=True, help="LUT 文件路径或内置 LUT 名称")
    parser.add_argument("--strength", type=float, default=1.0, help="调色强度 0.0~1.0")

    args = parser.parse_args()

    ext = Path(args.input).suffix.lower()
    if ext in [".mp4", ".mov", ".mkv", ".ts"]:
        print(f"🎬 启动视频 3D LUT 渲染: {args.lut} -> {args.output}")
        apply_lut_to_video(args.input, args.lut, args.output, args.strength)
        print("✅ 视频渲染完成！")
    else:
        print(f"📸 启动图像 3D LUT 渲染: {args.lut} -> {args.output}")
        apply_lut_to_image(args.input, args.lut, args.output, args.strength)
        print("✅ 图像渲染完成！")
