from PyQt6.QtWidgets import QGroupBox

class MQGroupBox(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            MQGroupBox {
                border: 1px solid transparent;
                border-top: 1px solid #E0E0E0;  /* 浅灰色横线 */
                margin-top: 0.5em;  /* 为标题留出空间 */
                padding-top: 0.5em;  /* 内容区域的内边距 */
            }
            
            MQGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;  /* 标题位置在左上角 */
                left: 10px;  /* 标题左侧偏移 */
                padding: 0 5px 0 5px;  /* 标题内边距 */
            }
        """)