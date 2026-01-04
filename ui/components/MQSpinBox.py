from PyQt6.QtWidgets import QSpinBox

class MQSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()