"""抖音 / 小红书 9:16 极简竖屏毛玻璃画中画生成器 (Vertical PiP Generator)

将 16:9 横屏风光摄影或航拍视频一键转化为抖音/小红书爆款 9:16 竖屏模板：
- 全屏沉浸式毛玻璃模糊动态背景（高斯模糊 + 电影级微暗调氛围）
- 中间悬浮 16:9 超清画幅，带精致柔和阴影与极细半透边框
- 顶部自动排版：拍摄地点（普宁·揭阳）、日期时间戳、天气落日标签
- 底部精修排版：极简诗意双语文案、相机 EXIF 胶片标识与原声音乐徽章
- 支持单张 4K 竖屏海报生成，也支持全片 4K 9:16 动态短视频一键直出
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

_SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPT_DIR))

from preview_generator import get_ffmpeg_bin
from render_engine import _get_hw_encoder_args, _get_hwaccel_input_args


def _get_vertical_fonts():
    """加载排版字体。"""
    try:
        font_city = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 64)
        font_sub = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 36)
        font_quote_cn = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 48)
        font_quote_en = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 32)
        font_tag = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 34)
    except Exception:
        font_city = font_sub = font_quote_cn = font_quote_en = font_tag = ImageFont.load_default()
    return font_city, font_sub, font_quote_cn, font_quote_en, font_tag


def create_vertical_pip_poster(
    image_path: str,
    output_path: str,
    city: str = "普宁 · 揭阳",
    date_str: str = "2026.04.06  17:06:45",
    quote_cn: str = "“山川是不卷收的文章，日月为你掌灯伴读。”",
    quote_en: str = "In the silence of sunset, mountains dream.",
    resolution: Tuple[int, int] = (2160, 3840),
) -> str:
    """生成 4K 竖屏 9:16 极简毛玻璃海报。"""
    im = Image.open(image_path).convert("RGB")
    vw, vh = resolution  # 2160, 3840

    # 1. 制作沉浸式毛玻璃背景
    # 保持长边填充并居中裁剪成 9:16
    aspect_im = im.width / im.height
    aspect_target = vw / vh

    if aspect_im > aspect_target:
        # 图更宽，以高为准填充
        bg_h = vh
        bg_w = int(vh * aspect_im)
    else:
        bg_w = vw
        bg_h = int(vw / aspect_im)

    bg_scaled = im.resize((bg_w, bg_h), Image.Resampling.BILINEAR)
    crop_x = (bg_w - vw) // 2
    crop_y = (bg_h - vh) // 2
    bg_cropped = bg_scaled.crop((crop_x, crop_y, crop_x + vw, crop_y + vh))

    # 大半径高斯模糊 + 适度暗化
    bg_blurred = bg_cropped.filter(ImageFilter.GaussianBlur(radius=55))
    bg_arr = np.array(bg_blurred, dtype=np.float32) * 0.65  # 压暗 35% 保证前景可读性
    canvas = Image.fromarray(np.clip(bg_arr, 0, 255).astype(np.uint8))

    # 2. 中间悬浮 16:9 画幅
    fg_w = int(vw * 0.90)  # 占宽度的 90%
    fg_h = int(fg_w / (16 / 9))
    fg_resized = im.resize((fg_w, fg_h), Image.Resampling.LANCZOS)

    fg_x = (vw - fg_w) // 2
    fg_y = int(vh * 0.36)  # 黄金分割视线位置

    # 绘制柔和投影 (Drop shadow)
    shadow_margin = 40
    shadow_w = fg_w + shadow_margin * 2
    shadow_h = fg_h + shadow_margin * 2
    shadow_mask = Image.new("RGBA", (shadow_w, shadow_h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_mask)
    s_draw.rectangle([shadow_margin, shadow_margin, shadow_margin + fg_w, shadow_margin + fg_h], fill=(0, 0, 0, 180))
    shadow_blurred = shadow_mask.filter(ImageFilter.GaussianBlur(radius=30))
    canvas.paste(shadow_blurred, (fg_x - shadow_margin, fg_y - shadow_margin + 15), shadow_blurred)

    # 贴入主体图像
    canvas.paste(fg_resized, (fg_x, fg_y))

    # 绘制前景细白微弱边框
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([fg_x, fg_y, fg_x + fg_w, fg_y + fg_h], outline=(255, 255, 255, 120), width=3)

    # 3. 文艺排版
    font_city, font_sub, font_quote_cn, font_quote_en, font_tag = _get_vertical_fonts()

    # 顶部区域
    # 地点徽标胶囊
    top_y = int(vh * 0.16)
    draw.text(((vw - draw.textbbox((0, 0), city, font=font_city)[2]) // 2, top_y), city, fill=(255, 255, 255), font=font_city)
    draw.text(((vw - draw.textbbox((0, 0), date_str, font=font_sub)[2]) // 2, top_y + 90), date_str, fill=(200, 200, 210), font=font_sub)
    draw.text(((vw - draw.textbbox((0, 0), "✦ GOLDEN HOUR SUNSET · 8K FILM ✦", font=font_sub)[2]) // 2, top_y + 150), "✦ GOLDEN HOUR SUNSET · 8K FILM ✦", fill=(245, 175, 70), font=font_sub)

    # 底部区域
    bottom_y = fg_y + fg_h + 100
    bbox_cn = draw.textbbox((0, 0), quote_cn, font=font_quote_cn)
    draw.text(((vw - bbox_cn[2]) // 2, bottom_y), quote_cn, fill=(245, 245, 250), font=font_quote_cn)

    bbox_en = draw.textbbox((0, 0), quote_en, font=font_quote_en)
    draw.text(((vw - bbox_en[2]) // 2, bottom_y + 75), quote_en, fill=(180, 180, 195), font=font_quote_en)

    # 底部设备认证徽章
    tag_str = "SHOT ON INSTA360 ACE PRO 2  |  LEICA CO-ENGINEERED"
    draw.text(((vw - draw.textbbox((0, 0), tag_str, font=font_tag)[2]) // 2, vh - 220), tag_str, fill=(140, 140, 150), font=font_tag)

    canvas.save(output_path, quality=94)
    print(f"✅ 抖音 9:16 极简竖屏海报生成完成: {output_path}")
    return output_path


def create_vertical_pip_video(
    video_path: str,
    output_path: str,
    overlay_poster_path: Optional[str] = None,
    resolution: Tuple[int, int] = (2160, 3840),
) -> str:
    """使用 FFmpeg 单 Pass 硬件加速直接将 16:9 横屏视频转化为 9:16 毛玻璃竖屏动态视频。"""
    vw, vh = resolution
    fg_w = int(vw * 0.90)
    fg_h = int(fg_w / (16 / 9))
    fg_y = int(vh * 0.36)

    ffmpeg_bin = get_ffmpeg_bin()

    # 构造 FFmpeg 滤镜链：
    # 1. 拆分成背景流与前景流
    # 2. 背景流缩放裁剪填满 9:16 + 高斯模糊 + 调暗
    # 3. 前景流缩放到 90% 宽度的 16:9 画幅
    # 4. 前景覆盖在背景中间偏上
    filter_complex = (
        f"[0:v]split=2[bg_raw][fg_raw];"
        f"[bg_raw]scale={vw}:{vh}:force_original_aspect_ratio=increase,crop={vw}:{vh},boxblur=40:5,eq=brightness=-0.28:saturation=1.1[bg];"
        f"[fg_raw]scale={fg_w}:{fg_h}[fg];"
        f"[bg][fg]overlay=(W-w)/2:{fg_y}[vout]"
    )

    cmd = [ffmpeg_bin, "-y"]
    cmd += _get_hwaccel_input_args()
    cmd += ["-v", "quiet", "-i", video_path]
    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "0:a?",
        "-c:a", "copy",
    ]
    cmd += _get_hw_encoder_args() + [output_path]

    subprocess.run(cmd, check=True)
    print(f"✅ 抖音 9:16 竖屏动态视频生成完成: {output_path}")
    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="抖音 9:16 极简竖屏毛玻璃画中画生成器")
    parser.add_argument("input", help="输入图像或视频文件")
    parser.add_argument("-o", "--output", required=True, help="输出文件路径")
    parser.add_argument("--city", default="普宁 · 揭阳", help="地点标签")
    parser.add_argument("--quote", default="“山川是不卷收的文章，日月为你掌灯伴读。”", help="中文文案")

    args = parser.parse_args()
    ext = Path(args.input).suffix.lower()

    if ext in [".mp4", ".mov", ".mkv", ".ts"]:
        create_vertical_pip_video(args.input, args.output)
    else:
        create_vertical_pip_poster(args.input, args.output, city=args.city, quote_cn=args.quote)
