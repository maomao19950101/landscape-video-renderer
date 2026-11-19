---
name: landscape-video-renderer
description: Use when the user wants to render landscape or scenic videos with cinematic lighting effects, style presets (INFP dreamy, INTJ moody, sunset glow, etc.), auto-focus vignette, or bloom glow. Also use when the user mentions 抖音风景渲染, 画圈, 视线聚焦, 电影感调色, or MBTI aesthetic video styles.
---

# 风景视频电影级光影渲染

一键为风景视频添加电影级光影效果：自动画圈聚焦主体、柔光漫射、电影色调。

## Overview

解决短视频创作者在剪映/PR中手动做“画圈渲染/视线聚焦/打关键帧”过于繁琐的痛点。
用户提供风景视频 → AI 智能嗅探画面并推荐风格（主打 INFP 浪漫梦幻） → 单帧快速预览确认 → 后台全片渲染出片。

## Checklist

1. **环境自检**：确认系统已安装 `ffmpeg`。若未安装，提示用户 `brew install ffmpeg`，停止。
2. **接收视频**：获取用户传入的视频路径，调用 `preview_generator.get_video_info()` 探测分辨率、长宽比与时长。
3. **推荐风格**：分析画面特征，向用户展示 3~5 个精选推荐风格（见下方推荐话术）。
4. **单帧预览**：用户做出选择或给出指令后，调用 `preview_generator.generate_preview()` 在 1~2 秒内生成单帧预览图，展示给用户确认。
5. **微调循环**：若用户要求微调（移焦点、调大小、调强度、换风格），更新参数并重新生成单帧预览，直到满意。
6. **全片渲染**：用户确认满意后，调用 `render_engine.render_video()` 执行全片渲染，音画无损混流，交付最终成品链接。

## 推荐话术模板

用户发送视频后，分析画面并给出推荐：

```
收到你的风景视频！画面看起来是一段【场景描述】镜头。
你想把它渲染成什么风格？可以直接回复数字或名称：

  1. 🦋 INFP 浪漫梦幻 ⭐推荐 — 莫奈油画 · 柔焦仙气 · 梦幻微光
  2. 🧊 INTJ 冷峻秩序 — 冰岛高级灰 · 锐利线条 · 极简重度暗角
  3. 🌅 日落金辉 — 穿透式金色丁达尔光束 · 浓郁暖调
  4. 🌲 丁达尔晨雾 — 白金柔焦光晕 · 穿透树林圣光
  5. 💙 蓝调时刻 — 深蓝沉静天空 · 暖黄主体点缀
  6. 💎 极致通透 — 强去雾 · 冷青高光 · 主体锐化立体
  7. 🌿 宫崎骏夏日 — 青翠鲜亮 · 日系治愈清新
  8. 🎬 富士复古胶片 — 经典胶片颗粒 · 旅途故事感
  9. 🎯 极简视线聚焦 — 保留原色 · 纯粹主体打光 + 背景压暗

  💡 也可以直接说："把中间的礁石用 INFP 风格渲染，光晕大一点"
```

## 执行脚本与调用方式

所有脚本位于本 Skill 的 `scripts/` 目录。执行时统一通过 `uv run`（自动管理依赖，无需用户预装 Python 包）：

### 1. 探测视频与生成单帧预览
```bash
cd ~/.gemini/config/skills/landscape-video-renderer
uv run --with numpy --with Pillow python3 -c "
from scripts.preview_generator import generate_preview
result = generate_preview(
    video_path='<video_path>',
    preset_name='<preset_name>',
    output_path='<output_preview.jpg>',
    focus_hint=<None 或 (cx, cy)>,
)
print(result)
"
```

### 2. 执行全片渲染
```bash
cd ~/.gemini/config/skills/landscape-video-renderer
uv run --with numpy --with Pillow python3 scripts/render_engine.py <input.mp4> <preset_name> <output.mp4> [cx cy]
```

### 3. 静态超清照片 ➔ 电影感运镜短视频 (Ken Burns 模式)
支持将 8K/4K 超高像素风光照片（如 Ace Pro 2、单反照片）转化为 4K 电影级运镜短视频：
```bash
cd ~/.gemini/config/skills/landscape-video-renderer
uv run --with numpy --with Pillow python3 scripts/ken_burns_generator.py \
  <image.jpg> <output.mp4> \
  --duration 12.0 \
  --fps 30 \
  --audio <optional_ambient_video_or_audio.mp4> \
  --zoom-end 1.25
```

## 自然语言微调映射

用户对预览提出修改要求时，将其自然语言映射到对应参数变更：

| 用户说 | 参数调整 |
|--------|---------|
| "光圈往左/右/上/下移一点" | 更新 `focus_hint` (cx, cy) 坐标 ±0.1 |
| "光圈范围再大/小一点" | 调整 `vignette_radius` ±0.1 |
| "柔光/光晕再强/弱一点" | 调整 `bloom_intensity` ±0.15 |
| "暗角再深/浅一些" | 调整 `vignette_intensity` ±0.1 |
| "换成 INTJ / 通透风格" | 整体切换预设 |

微调后调用 `generate_preview()` 重新出预览图，等待用户再次确认。

## 预估耗时说明

在渲染前可根据视频时长告知用户预估时间：
- 15s 短视频（无 Bloom 风格）：约 3~10 秒
- 15s 短视频（含 Bloom 风格）：约 15~35 秒
- 60s 视频（含 Bloom 风格）：约 1~2 分钟
- 4K 分辨率：耗时约为 1080p 的 2 倍

## 异常与边界防御

- **FFmpeg 缺失**：明确提示用户运行 `brew install ffmpeg`，停止执行。
- **预设名不识别**：列出支持的 9 款预设并让用户重选。
- **无音轨视频**：自动跳过音频提取与混流，安全输出纯视频。
- **横竖屏适配**：脚本已内置自适应椭圆长短轴计算（横屏 16:9 / 竖屏 9:16），暗角均保持自然比例。
