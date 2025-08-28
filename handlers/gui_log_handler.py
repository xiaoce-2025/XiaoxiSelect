"""
GUI日志处理器，将日志消息发送到GUI界面
"""

import logging
from PyQt6.QtCore import pyqtSignal

class GUILogHandler(logging.Handler):
    """GUI日志处理器，将日志消息发送到GUI界面"""
    
    def __init__(self, log_signal):
        super().__init__()
        self.log_signal = log_signal
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    def emit(self, record):
        try:
            msg = self.format(record)
            # 使用信号发送日志消息到GUI线程
            self.log_signal.emit(msg)
        except Exception:
            # 如果发送失败，忽略错误避免无限循环
            pass