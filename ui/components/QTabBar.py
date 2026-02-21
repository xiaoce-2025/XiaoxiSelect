from PyQt6.QtWidgets import QTabBar, QStyle, QStyleOptionTab
from PyQt6.QtGui import QPainter, QFont, QColor, QCursor
from PyQt6.QtCore import Qt, QSize, QRect

class VerticalTabBar(QTabBar):
    """自定义垂直标签栏"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        self.setExpanding(False)
        
    def tabSizeHint(self, index):
        """重写标签尺寸"""
        # 固定尺寸，交换宽高以实现垂直布局
        return QSize(120, 40)
    
    def paintEvent(self, event):
        """自定义绘制标签"""
        painter = QPainter(self)
        
        for index in range(self.count()):
            # 创建并初始化样式选项
            option = QStyleOptionTab()
            option.initFrom(self)
            option.state = QStyle.StateFlag.State_Active | QStyle.StateFlag.State_Enabled
            
            # 设置当前状态
            if index == self.currentIndex():
                option.state |= QStyle.StateFlag.State_Selected
            if self.tabRect(index).contains(self.mapFromGlobal(QCursor.pos())):
                option.state |= QStyle.StateFlag.State_MouseOver
                
            option.text = self.tabText(index)
            option.rect = self.tabRect(index)
            option.icon = self.tabIcon(index)
            option.shape = self.shape()  # 设置标签形状/方向
            
            rect = option.rect
            
            # 绘制背景
            if option.state & QStyle.StateFlag.State_Selected:
                painter.setBrush(QColor("#4A6572"))  # 选中状态深蓝色
            elif option.state & QStyle.StateFlag.State_MouseOver:
                painter.setBrush(QColor("#344955"))  # 悬停状态深灰色
            else:
                painter.setBrush(QColor("#F9AA33"))  # 默认状态橙色
                
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 5, 5)
            
            # 绘制文字
            painter.setPen(QColor("#FFFFFF"))  # 白色文字
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, option.text)