#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PKU自动选课程序 - 主程序入口
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = MainWindow()
    window.showMaximized()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == '__main__':
    main()