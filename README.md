# 风景视频电影级光影渲染 (landscape-video-renderer)

> **告别繁琐的手动打关键帧！** 专为短视频创作者打造的风景视频光影重塑与电影级调色 Skill / 工具。  
> 自动定位焦点画圈、主体柔光溢出（Bloom）、背景自然暗角、氛围丁达尔光束与电影色调一键成片。

---

## 🌟 核心特性

- 🎯 **智能画圈聚焦**：三级降级策略（自然语言指定 > 画面显著性检测 > 黄金分割重心兜底），无需手动打几十个关键帧做运动跟踪。
- 🦋 **主打 INFP 浪漫梦幻**：莫奈油画色调 + 焦点柔焦 Bloom 漫射 + 仙气微光，抖音/小红书数十亿播放同款治愈系视线美学。
- ⚡ **多核硬件极速引擎**：
  - FFmpeg 底层 C/硬件加速处理色彩与暗角（秒级出片）；
  - Python 多进程并行处理复杂 Bloom 漫射，性能较传统单核提升 10~50 倍。
- 🖼️ **单帧快速预览防翻车**：全片渲染前 1 秒出单帧效果图，支持随时用人话微调（“光圈往右一点”、“柔光再大一点”），满意后再渲染全片。
- 🎵 **音画 100% 同步保真**：采用 FFmpeg 无损 Copy 模式提取并混流原片背景音乐与环境音，杜绝丢音或音画不同步。
- 📱 **横竖屏自适应**：自动根据抖音竖屏（9:16）或单反横屏（16:9）适配椭圆长短轴，暗角绝不畸变变形。

---

## 🎨 9 大电影级预设风格矩阵

| 预设风格 | 核心视觉语言 | 适合场景 |
| :--- | :--- | :--- |
| **🦋 [INFP] 浪漫梦幻** ⭐主打 | 莫奈油画粉紫 · 柔焦 Bloom 仙气漫射 · 温柔暗角 | 花海、湖泊、夕阳微光、微风草地、浪漫旅拍 |
| **🧊 [INTJ] 冷峻秩序** | 冰岛高级灰 · 低饱和冷青 · 锐利线条 · 极简重度暗角 | 雪山峰顶、现代建筑、荒凉公路、极简构图 |
| **🌅 日落金辉** | 强穿透丁达尔金色光束 · 浓郁暖阳 · 深邃聚光 | 海边日落、沙漠晚霞、秋天胡杨林 |
| **🌲 丁达尔晨雾** | 白金柔焦光晕 · 穿透树林圣光 · 仙气水汽感 | 清晨森林、茶园采茶、溪流山涧、古镇云海 |
| **💙 蓝调时刻** | 天空深蓝沉静 · 主体暖黄点缀 · 冷暖绝美撞色 | 日落后暮色、海边微光、城市华灯初上 |
| **💎 极致通透** | 智能去雾 · 高动态范围 · 冷青高光 · 主体锐化立体 | 高原雪山、纯净湖泊、晴空万里 |
| **🌿 宫崎骏夏日** | 青翠鲜亮 · 草木高饱和 · 日系治愈清新 | 夏日草坪、稻田、户外露营、绿意公园 |
| **🎬 富士复古胶片** | 经典 35mm 胶片颗粒 · 暖红调暗角 · 旅途故事感 | 老街古镇、公路旅行、复古绿皮车 Vlog |
| **🎯 极简视线聚焦** | 保留原色 · 纯粹主体打光提亮 + 背景自然压暗 | 任何只想突出主体、保留原片真实色彩的风景 |

---

## 🚀 安装与使用

### 方式 1：作为 Antigravity / Gemini CLI Skill 使用（推荐）

1. 克隆本仓库到你的 Skill 目录：
```bash
git clone git@github.com:maomao19950101/landscape-video-renderer.git ~/.gemini/config/skills/landscape-video-renderer
```

2. 在对话中直接对 AI 说：
> “帮我把这段风景视频渲染一下 `/path/to/video.mp4`”

AI 会自动分析视频画面并提供风格选项，生成单帧预览图供你挑选确认！

---

### 方式 2：作为独立命令行工具使用

本工具使用 `uv` 自动管理 Python 依赖，无需手动安装 pip 包：

#### 1. 生成单帧预览图
```bash
cd ~/.gemini/config/skills/landscape-video-renderer
uv run --with numpy --with Pillow python3 -c "
from scripts.preview_generator import generate_preview
generate_preview('input.mp4', 'infp', 'preview.jpg')
"
```

#### 2. 全片极速渲染
```bash
cd ~/.gemini/config/skills/landscape-video-renderer
uv run --with numpy --with Pillow python3 scripts/render_engine.py input.mp4 infp output.mp4
```

*如果需要指定光圈中心坐标（归一化 0.0 ~ 1.0）：*
```bash
uv run --with numpy --with Pillow python3 scripts/render_engine.py input.mp4 infp output.mp4 0.6 0.4
```

---

## 🛠️ 环境依赖

- **FFmpeg**（必须）：用于音视频编解码与滤镜管线
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt install ffmpeg`
- **Python 3.10+**
- **uv**（推荐）：轻量 Python 运行器

---

## 📄 许可证

MIT License
