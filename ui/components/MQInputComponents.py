from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtWidgets import QSpinBox, QDoubleSpinBox

component_height = 26
font_size = 15


class MQDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置无按钮
        self.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)

        # 直接设置固定高度
        self.setFixedHeight(component_height)

        # 调整字体大小
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)

        # 设置样式表，减小上下内边距
        self.setStyleSheet("""
            QDoubleSpinBox {
                padding: 0px 2px;  /* 上/下: 0px, 左/右: 2px */
                margin: 0px;
            }
        """)

    def wheelEvent(self, event):
        event.ignore()


class MQSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置无按钮
        self.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)

        # 直接设置固定高度
        self.setFixedHeight(component_height)

        # 调整字体大小
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)

        # 设置样式表，减小上下内边距
        self.setStyleSheet("""
            QSpinBox {
                padding: 0px 2px;  /* 上/下: 0px, 左/右: 2px */
                margin: 0px;
            }
        """)

    def wheelEvent(self, event):
        event.ignore()


class MQLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 直接设置固定高度
        self.setFixedHeight(component_height)

        # 调整字体大小
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)

        # 设置样式表，减小上下内边距
        self.setStyleSheet("""
            QLineEdit {
                padding: 0px 2px;  /* 上/下: 0px, 左/右: 2px */
                margin: 0px;
            }
        """)
