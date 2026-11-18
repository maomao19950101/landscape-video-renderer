@echo off
chcp 65001 >nul
title 风景视频电影级光影渲染 - Windows 极速版

echo ====================================================================
echo        风景视频电影级光影渲染 (Windows 极速加速版)
echo ====================================================================
echo.

set "VIDEO_PATH=%~1"

if "%VIDEO_PATH%"=="" (
    echo 请将你要渲染的风景视频 (MP4/MOV) 直接拖拽到本 bat 图标上，
    echo 或者在下方输入视频的完整路径：
    echo.
    set /p "VIDEO_PATH=请输入视频路径: "
)

if not exist "%VIDEO_PATH%" (
    echo.
    echo [错误] 找不到视频文件: "%VIDEO_PATH%"
    echo.
    pause
    exit /b 1
)

echo.
echo 当前输入视频: %VIDEO_PATH%
echo.
echo --------------------------------------------------------------------
echo 请选择你想要渲染的风格 (直接输入序号，按回车确认):
echo.
echo   [1] 🦋 INFP 浪漫梦幻 ⭐推荐 (莫奈油画 · 柔焦仙气 · 梦幻微光)
echo   [2] 🧊 INTJ 冷峻秩序 (冰岛高级灰 · 锐利线条 · 极简重暗角)
echo   [3] 🌅 日落金辉     (穿透式金色丁达尔光束 · 浓郁暖阳)
echo   [4] 🌲 丁达尔晨雾   (白金柔焦光晕 · 穿透树林圣光)
echo   [5] 💙 蓝调时刻     (深蓝沉静天空 · 暖黄主体点缀)
echo   [6] 💎 极致通透     (强去雾 · 冷青高光 · 主体锐化立体)
echo   [7] 🌿 宫崎骏夏日   (青翠鲜亮 · 草木高饱和 · 日系治愈)
echo   [8] 🎬 富士复古胶片 (经典胶片颗粒 · 暖红调暗角 · 故事感)
echo   [9] 🎯 极简视线聚焦 (保留原色 · 纯粹主体打光 + 背景自然压暗)
echo.
set "STYLE_CHOICE=1"
set /p "STYLE_CHOICE=请输入风格序号 [1-9] (默认 1): "

set "PRESET_NAME=infp"
if "%STYLE_CHOICE%"=="1" set "PRESET_NAME=infp"
if "%STYLE_CHOICE%"=="2" set "PRESET_NAME=intj"
if "%STYLE_CHOICE%"=="3" set "PRESET_NAME=sunset_gold"
if "%STYLE_CHOICE%"=="4" set "PRESET_NAME=forest_mist"
if "%STYLE_CHOICE%"=="5" set "PRESET_NAME=blue_hour"
if "%STYLE_CHOICE%"=="6" set "PRESET_NAME=crystal_clear"
if "%STYLE_CHOICE%"=="7" set "PRESET_NAME=ghibli_green"
if "%STYLE_CHOICE%"=="8" set "PRESET_NAME=film_vintage"
if "%STYLE_CHOICE%"=="9" set "PRESET_NAME=clean_focus"

for %%F in ("%VIDEO_PATH%") do (
    set "DIR_NAME=%%~dpF"
    set "FILE_NAME=%%~nF"
    set "FILE_EXT=%%~xF"
)

set "OUTPUT_PATH=%DIR_NAME%%FILE_NAME%_%PRESET_NAME%_rendered.mp4"

echo.
echo --------------------------------------------------------------------
echo 开始执行渲染...
echo 选定风格: %PRESET_NAME%
echo 输出路径: %OUTPUT_PATH%
echo (已自动开启 Windows NVIDIA / Intel / AMD 显卡硬件加速)
echo --------------------------------------------------------------------
echo.

cd /d "%~dp0"

where uv >nul 2>nul
if %errorlevel% equ 0 (
    uv run --with numpy --with Pillow python scripts\render_engine.py "%VIDEO_PATH%" "%PRESET_NAME%" "%OUTPUT_PATH%"
) else (
    python scripts\render_engine.py "%VIDEO_PATH%" "%PRESET_NAME%" "%OUTPUT_PATH%"
)

if %errorlevel% equ 0 (
    echo.
    echo ====================================================================
    echo 🎉 渲染完成！成片已保存到：
    echo %OUTPUT_PATH%
    echo ====================================================================
) else (
    echo.
    echo [错误] 渲染过程中断，请确认是否已安装 Python 和 FFmpeg。
)

echo.
pause
