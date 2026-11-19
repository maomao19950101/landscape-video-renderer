"""风景视频电影级光影渲染 — 风格预设参数表"""

from typing import Optional

# 统一参数结构：每个预设是以下 14 个键的字典
PRESET_TEMPLATE = {
    "vignette_intensity": 0.0,    # 画圈暗角强度 0.0~1.0
    "vignette_radius": 0.5,       # 聚光圈半径（占画面短边比例）0.3~0.8
    "vignette_softness": 0.5,     # 羽化柔和度 0.2~0.9
    "brightness_subject": 0.0,    # 主体区域提亮幅度 0.0~0.3
    "contrast_subject": 0.0,      # 主体区域对比度增强 0.0~0.3
    "bloom_enabled": False,       # 是否启用柔光漫射
    "bloom_threshold": 0.7,       # 高光提取亮度门槛 0.5~0.9
    "bloom_intensity": 0.0,       # 柔光叠加强度 0.0~1.0
    "bloom_radius": 15,           # 柔光扩散模糊半径 (px) 5~50
    "color_temp_shift": 0,        # 色温偏移（负冷正暖）-30~+30
    "saturation_adj": 0.0,        # 饱和度调整 -0.3~+0.3
    "tint_shadows": None,         # 暗部着色 hex (如 "#1a1a2e") 或 None
    "tint_highlights": None,      # 高光着色 hex (如 "#ffd4e5") 或 None
    "grain_amount": 0.0,          # 胶片颗粒感 0.0~0.3
}

PRESETS = {
    "infp": {
        "name": "INFP 浪漫梦幻",
        "emoji": "🦋",
        "tagline": "莫奈油画 · 柔焦仙气 · 梦幻微光",
        "scenes": "花海、湖泊、夕阳、微风、雨后",
        "aliases": ["infp", "梦幻", "浪漫", "莫奈", "仙气"],
        "params": {
            "vignette_intensity": 0.45,
            "vignette_radius": 0.55,
            "vignette_softness": 0.85,
            "brightness_subject": 0.08,
            "contrast_subject": 0.08,
            "bloom_enabled": True,
            "bloom_threshold": 0.75,
            "bloom_intensity": 0.35,
            "bloom_radius": 30,
            "color_temp_shift": 12,
            "saturation_adj": 0.05,
            "tint_shadows": "#2d1b4e",
            "tint_highlights": "#ffd4e5",
            "grain_amount": 0.03,
        },
    },
    "intj": {
        "name": "INTJ 冷峻秩序",
        "emoji": "🧊",
        "tagline": "冰岛高级灰 · 锐利线条 · 极简克制聚光",
        "scenes": "雪山、建筑、公路、极简构图",
        "aliases": ["intj", "冷峻", "高级灰", "冰岛"],
        "params": {
            "vignette_intensity": 0.65,
            "vignette_radius": 0.45,
            "vignette_softness": 0.4,
            "brightness_subject": 0.05,
            "contrast_subject": 0.25,
            "bloom_enabled": False,
            "bloom_threshold": 0.8,
            "bloom_intensity": 0.0,
            "bloom_radius": 10,
            "color_temp_shift": -20,
            "saturation_adj": -0.2,
            "tint_shadows": "#0a1628",
            "tint_highlights": "#c0d6e4",
            "grain_amount": 0.0,
        },
    },
    "sunset_gold": {
        "name": "日落金辉",
        "emoji": "🌅",
        "tagline": "穿透式金色丁达尔光束 · 浓郁暖调 · 深邃聚光",
        "scenes": "日落、海边、沙漠、秋景",
        "aliases": ["日落", "金辉", "sunset", "gold"],
        "params": {
            "vignette_intensity": 0.55,
            "vignette_radius": 0.5,
            "vignette_softness": 0.65,
            "brightness_subject": 0.15,
            "contrast_subject": 0.15,
            "bloom_enabled": True,
            "bloom_threshold": 0.55,
            "bloom_intensity": 0.45,
            "bloom_radius": 25,
            "color_temp_shift": 25,
            "saturation_adj": 0.1,
            "tint_shadows": "#1a0a00",
            "tint_highlights": "#ffc966",
            "grain_amount": 0.0,
        },
    },
    "forest_mist": {
        "name": "丁达尔晨雾",
        "emoji": "🌲",
        "tagline": "白金柔焦光晕 · 穿透树林圣光 · 仙气雾感",
        "scenes": "清晨森林、茶园、山涧、古镇",
        "aliases": ["晨雾", "丁达尔", "forest", "mist", "圣光"],
        "params": {
            "vignette_intensity": 0.4,
            "vignette_radius": 0.6,
            "vignette_softness": 0.9,
            "brightness_subject": 0.18,
            "contrast_subject": 0.05,
            "bloom_enabled": True,
            "bloom_threshold": 0.5,
            "bloom_intensity": 0.65,
            "bloom_radius": 40,
            "color_temp_shift": 8,
            "saturation_adj": -0.05,
            "tint_shadows": "#1a2a1a",
            "tint_highlights": "#fffbe6",
            "grain_amount": 0.02,
        },
    },
    "blue_hour": {
        "name": "蓝调时刻",
        "emoji": "💙",
        "tagline": "天空深蓝沉静 · 主体暖黄点缀 · 安静情绪",
        "scenes": "日落后暮色、海边微光、城市黄昏",
        "aliases": ["蓝调", "暮色", "blue", "hour"],
        "params": {
            "vignette_intensity": 0.5,
            "vignette_radius": 0.5,
            "vignette_softness": 0.7,
            "brightness_subject": 0.1,
            "contrast_subject": 0.12,
            "bloom_enabled": True,
            "bloom_threshold": 0.65,
            "bloom_intensity": 0.3,
            "bloom_radius": 20,
            "color_temp_shift": -15,
            "saturation_adj": 0.0,
            "tint_shadows": "#0a1a3a",
            "tint_highlights": "#ffeebb",
            "grain_amount": 0.0,
        },
    },
    "crystal_clear": {
        "name": "极致通透",
        "emoji": "💎",
        "tagline": "强去雾 · 高动态范围 · 冷青高光 · 主体锐化立体",
        "scenes": "雪山、高原、湖泊、蓝天白云",
        "aliases": ["通透", "去雾", "crystal", "clear", "锐化"],
        "params": {
            "vignette_intensity": 0.35,
            "vignette_radius": 0.6,
            "vignette_softness": 0.6,
            "brightness_subject": 0.1,
            "contrast_subject": 0.2,
            "bloom_enabled": False,
            "bloom_threshold": 0.8,
            "bloom_intensity": 0.0,
            "bloom_radius": 10,
            "color_temp_shift": -8,
            "saturation_adj": 0.1,
            "tint_shadows": "#0a1a2a",
            "tint_highlights": "#e0f0ff",
            "grain_amount": 0.0,
        },
    },
    "ghibli_green": {
        "name": "宫崎骏夏日",
        "emoji": "🌿",
        "tagline": "青翠鲜亮 · 草木高饱和 · 日系治愈清新",
        "scenes": "草原、稻田、绿植、露营、夏日",
        "aliases": ["宫崎骏", "夏日", "ghibli", "green", "治愈"],
        "params": {
            "vignette_intensity": 0.3,
            "vignette_radius": 0.65,
            "vignette_softness": 0.8,
            "brightness_subject": 0.12,
            "contrast_subject": 0.08,
            "bloom_enabled": True,
            "bloom_threshold": 0.7,
            "bloom_intensity": 0.25,
            "bloom_radius": 20,
            "color_temp_shift": 5,
            "saturation_adj": 0.18,
            "tint_shadows": "#1a2e1a",
            "tint_highlights": "#f5ffe0",
            "grain_amount": 0.0,
        },
    },
    "film_vintage": {
        "name": "富士复古胶片",
        "emoji": "🎬",
        "tagline": "经典胶片颗粒 · 暖红调暗角 · 旅途故事感",
        "scenes": "公路、乡村、小镇、旅行 Vlog",
        "aliases": ["复古", "胶片", "film", "vintage", "富士"],
        "params": {
            "vignette_intensity": 0.35,
            "vignette_radius": 0.60,
            "vignette_softness": 0.75,
            "brightness_subject": 0.10,
            "contrast_subject": 0.10,
            "bloom_enabled": False,
            "bloom_threshold": 0.7,
            "bloom_intensity": 0.0,
            "bloom_radius": 10,
            "color_temp_shift": 15,
            "saturation_adj": -0.08,
            "tint_shadows": "#2a1a0a",
            "tint_highlights": "#ffe0c0",
            "grain_amount": 0.15,
        },
    },
    "clean_focus": {
        "name": "极简视线聚焦",
        "emoji": "🎯",
        "tagline": "保留原色 · 纯粹主体打光提亮 + 背景自然压暗",
        "scenes": "任何只想突出主体的风景",
        "aliases": ["极简", "聚焦", "clean", "focus", "原色"],
        "params": {
            "vignette_intensity": 0.5,
            "vignette_radius": 0.5,
            "vignette_softness": 0.65,
            "brightness_subject": 0.15,
            "contrast_subject": 0.1,
            "bloom_enabled": False,
            "bloom_threshold": 0.8,
            "bloom_intensity": 0.0,
            "bloom_radius": 10,
            "color_temp_shift": 0,
            "saturation_adj": 0.0,
            "tint_shadows": None,
            "tint_highlights": None,
            "grain_amount": 0.0,
        },
    },
}


def get_preset(name: str) -> Optional[dict]:
    """按预设 ID 或别名查找预设。不区分大小写。"""
    name_lower = name.lower().strip()
    # 先精确匹配 ID
    if name_lower in PRESETS:
        return PRESETS[name_lower]
    # 再匹配别名
    for preset_id, preset in PRESETS.items():
        if name_lower in [a.lower() for a in preset["aliases"]]:
            return preset
    return None


def list_presets() -> list[dict]:
    """返回所有预设的摘要列表。"""
    result = []
    for preset_id, preset in PRESETS.items():
        result.append({
            "id": preset_id,
            "name": preset["name"],
            "emoji": preset["emoji"],
            "tagline": preset["tagline"],
            "scenes": preset["scenes"],
        })
    return result
