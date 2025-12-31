"""
@Author : xiaoce2025
@File   : console_window.py
@Date   : 2025-12-31
"""

"""Console窗口类"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette


class ConsoleWindow(QMainWindow):
    """Console窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("调试 Console")
        self.setGeometry(200, 200, 800, 600)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowMinimizeButtonHint
        )
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 设置背景色为白色
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
        self.setPalette(palette)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 这里可以添加Console的具体内容
        # 目前是一个空白窗口