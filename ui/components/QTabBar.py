from PyQt6.QtWidgets import QTabBar, QStyle, QStylePainter, QStyleOptionTab
from PyQt6.QtCore import QRect, Qt, QSize, QPoint
from PyQt6.QtGui import QTransform

class VerticalTabBar(QTabBar):
    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOptionTab()
        
        for index in range(self.count()):
            self.initStyleOption(option, index)
            
            # 保存painter状态
            painter.save()
            
            # 获取标签矩形
            tab_rect = self.tabRect(index)
            
            # 清除默认文本
            option.text = ""
            # 绘制标签形状
            painter.drawControl(QStyle.ControlElement.CE_TabBarTabShape, option)
            
            # 旋转painter以绘制竖向文本
            painter.translate(tab_rect.center())
            painter.rotate(0)  # 旋转90度使文本竖向
            
            # 创建新的文本矩形
            text_rect = QRect(0, 0, tab_rect.height(), tab_rect.width())
            text_rect.moveCenter(QPoint(0, 0))
            
            # 绘制文本
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.tabText(index))
            
            # 恢复painter状态
            painter.restore()

    def tabSizeHint(self, index):
        # 获取默认大小并交换宽高
        size = super().tabSizeHint(index)
        return QSize(size.height(), size.width())