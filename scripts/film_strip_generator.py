"""35mm 复古胶卷底片框与齿孔海报生成器 (Film Strip & Slide Mockup)

将高清风光摄影生成带有真实柯达/富士 35mm 底片质感的高清摄影作品：
- 真实比例的方形齿孔 (Sprocket Holes) 与底片胶片基底边缘
- 柯达/富士经典红橙色底片暗码 (Edge Codes: KODAK PORTRA 400, DX BARCODE, SAFETY FILM)
- 胶卷帧序号与进片标记 (▶ 03A, ▶ 04A, ▶ 05A)
- 90 年代经典数码液晶点阵暖橙色日期戳 ('26 4 6)
- 支持单画幅经典底片与三联幅胶卷连卷 (3-Frame Film Strip)
"""

import math
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFont

_SCRIPT_DIR = Path(__file__).parent


def _get_fonts():
    """获取系统可用字体。"""
    try:
        font_code = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 36)
        font_small = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 24)
        font_date = ImageFont.truetype("/System/Library/Fonts/Courier.dfont", 44)
        font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 38)
    except Exception:
        font_code = font_small = font_date = font_title = ImageFont.load_default()
    return font_code, font_small, font_date, font_title


def create_single_35mm_slide(
    image_path: str,
    output_path: str,
    film_stock: str = "KODAK PORTRA 400",
    frame_number: str = "04A",
    date_stamp: str = "'26  4  6",
    resolution: Tuple[int, int] = (3840, 2160),
) -> str:
    """生成单画幅 35mm 经典复古底片海报。"""
    im = Image.open(image_path).convert("RGB")
    target_w, target_h = resolution

    # 底片边距
    margin_top = int(target_h * 0.14)
    margin_bottom = int(target_h * 0.14)
    margin_left = int(target_w * 0.08)
    margin_right = int(target_w * 0.08)

    inner_w = target_w - margin_left - margin_right
    inner_h = target_h - margin_top - margin_bottom

    # 缩放图像填充内框
    im_fitted = im.resize((inner_w, inner_h), Image.Resampling.LANCZOS)

    # 胶片底基 (极深暗褐黑底，模拟透光负片胶基)
    canvas = Image.new("RGB", (target_w, target_h), (14, 12, 12))
    canvas.paste(im_fitted, (margin_left, margin_top))

    draw = ImageDraw.Draw(canvas)
    font_code, font_small, font_date, _ = _get_fonts()

    # 绘制 35mm 标准方形齿孔
    hole_w = int(target_w * 0.022)
    hole_h = int(target_h * 0.055)
    hole_r = int(hole_w * 0.25)
    gap = int(target_w * 0.048)

    # 顶部齿孔
    top_y = int(target_h * 0.035)
    for x in range(int(target_w * 0.02), target_w - int(target_w * 0.02), gap):
        draw.rounded_rectangle([x, top_y, x + hole_w, top_y + hole_h], radius=hole_r, fill=(2, 2, 2))

    # 底部齿孔
    bottom_y = target_h - top_y - hole_h
    for x in range(int(target_w * 0.02), target_w - int(target_w * 0.02), gap):
        draw.rounded_rectangle([x, bottom_y, x + hole_w, bottom_y + hole_h], radius=hole_r, fill=(2, 2, 2))

    # 胶卷边标印刷 (经典暖橙黄油墨)
    amber = (245, 140, 30)

    # 上边缘暗码
    draw.text((margin_left + 60, top_y + hole_h + 10), f"{film_stock} · 35MM SAFETY FILM", fill=amber, font=font_code)
    draw.text((target_w - margin_right - 350, top_y + hole_h + 10), "EXP 36 · ISO 400", fill=amber, font=font_code)

    # 下边缘暗码与进片标
    draw.text((margin_left + 60, bottom_y - 45), f"▶ {frame_number}", fill=amber, font=font_code)
    draw.text((target_w // 2 - 120, bottom_y - 45), "INSTA360 ACE PRO 2", fill=amber, font=font_code)
    draw.text((target_w - margin_right - 280, bottom_y - 45), "LEICA OPTICS", fill=amber, font=font_code)

    # 画面右下角复古液晶橙黄日期戳
    if date_stamp:
        date_color = (255, 115, 15)
        draw.text((target_w - margin_right - 300, target_h - margin_bottom - 60), date_stamp, fill=date_color, font=font_date)

    canvas.save(output_path, quality=94)
    print(f"✅ 35mm 单画幅底片生成完成: {output_path}")
    return output_path


def create_35mm_film_strip(
    image_paths: list[str],
    output_path: str,
    film_stock: str = "KODAK PORTRA 400",
    start_frame: int = 3,
) -> str:
    """生成经典 3 联幅 35mm 胶卷连卷长画幅底片海报。"""
    canvas_w = 4200
    canvas_h = 1800
    canvas = Image.new("RGB", (canvas_w, canvas_h), (14, 12, 12))
    draw = ImageDraw.Draw(canvas)
    font_code, font_small, font_date, _ = _get_fonts()
    amber = (245, 140, 30)

    # 3 张图按次序排列
    frame_w = 1150
    frame_h = int(frame_w / (16 / 9))
    gap_x = 100
    total_frames_w = len(image_paths) * frame_w + (len(image_paths) - 1) * gap_x
    start_x = (canvas_w - total_frames_w) // 2
    pos_y = (canvas_h - frame_h) // 2

    # 齿孔
    hole_w = 45
    hole_h = 75
    hole_r = 12
    hole_gap = 100
    top_y = 40
    bottom_y = canvas_h - top_y - hole_h

    for x in range(30, canvas_w - 30, hole_gap):
        draw.rounded_rectangle([x, top_y, x + hole_w, top_y + hole_h], radius=hole_r, fill=(2, 2, 2))
        draw.rounded_rectangle([x, bottom_y, x + hole_w, bottom_y + hole_h], radius=hole_r, fill=(2, 2, 2))

    for idx, path in enumerate(image_paths):
        cur_x = start_x + idx * (frame_w + gap_x)
        im = Image.open(path).convert("RGB")
        im_resized = im.resize((frame_w, frame_h), Image.Resampling.LANCZOS)
        canvas.paste(im_resized, (cur_x, pos_y))

        # 帧序号
        frame_code = f"▶ {start_frame + idx:02d}A"
        draw.text((cur_x + 30, bottom_y - 45), frame_code, fill=amber, font=font_code)
        draw.text((cur_x + 30, top_y + hole_h + 10), film_stock, fill=amber, font=font_code)

        # 模拟中间一帧贴日期戳
        if idx == 1:
            draw.text((cur_x + frame_w - 240, pos_y + frame_h - 50), "'26  4  6", fill=(255, 115, 15), font=font_date)

    canvas.save(output_path, quality=94)
    print(f"✅ 35mm 三联卷底片生成完成: {output_path}")
    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="35mm 胶卷底片海报生成器")
    parser.add_argument("input", nargs="+", help="输入图像路径（1张生成单幅，多张生成连卷）")
    parser.add_argument("-o", "--output", required=True, help="输出文件路径")
    parser.add_argument("--stock", default="KODAK PORTRA 400", help="胶卷品牌型号")

    args = parser.parse_args()
    if len(args.input) == 1:
        create_single_35mm_slide(args.input[0], args.output, film_stock=args.stock)
    else:
        create_35mm_film_strip(args.input, args.output, film_stock=args.stock)
