from PyQt6.QtWidgets import QDoubleSpinBox

class MQDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event):
        event.ignore()