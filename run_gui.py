#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PKU自动选课程序 - GUI启动脚本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui_main import main
    main()
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装PyQt6: pip install PyQt6")
    input("按回车键退出...")
except Exception as e:
    print(f"程序运行错误: {e}")
    input("按回车键退出...")
