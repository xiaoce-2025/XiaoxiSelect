@echo off
chcp 65001 >nul
title PKU自动选课程序 - GUI版本

echo ========================================
echo    PKU自动选课程序 - 图形化界面版本
echo ========================================
echo.

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.7+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python环境检查通过
echo.

echo 正在检查依赖包...
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo 正在安装PyQt6...
    pip install PyQt6
    if errorlevel 1 (
        echo 安装失败，尝试使用国内镜像源...
        pip install PyQt6 -i https://pypi.tuna.tsinghua.edu.cn/simple/
    )
)

echo 启动图形化界面...
python run_gui.py

if errorlevel 1 (
    echo.
    echo 程序运行出错，请检查错误信息
    pause
)
