"""
日志显示界面
"""

import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPushButton, 
                             QLabel, QHBoxLayout, QFileDialog, QMessageBox)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from handlers.gui_log_handler import GUILogHandler

class LogDisplay(QWidget):
    """日志显示界面"""
    
    # 定义信号
    log_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_log_capture()
        
        # 连接信号到槽函数
        self.log_signal.connect(self.add_log)
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("清空日志")
        clear_btn.clicked.connect(self.clear_log)
        save_btn = QPushButton("保存日志")
        save_btn.clicked.connect(self.save_log)
        
        btn_layout.addWidget(clear_btn)
        btn_layout.addWidget(save_btn)
        btn_layout.addStretch()
        
        layout.addWidget(QLabel("程序运行日志:"))
        layout.addWidget(self.log_text)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def setup_log_capture(self):
        """设置日志捕获"""
        # 获取根日志记录器
        root_logger = logging.getLogger()
        
        # 设置日志级别
        root_logger.setLevel(logging.INFO)
        
        # 添加GUI日志处理器
        gui_handler = GUILogHandler(self.log_signal)
        gui_handler.setLevel(logging.INFO)
        
        # 避免重复添加处理器
        for handler in root_logger.handlers:
            if isinstance(handler, GUILogHandler):
                root_logger.removeHandler(handler)
        
        root_logger.addHandler(gui_handler)
        
        # 同时捕获autoelective模块的日志
        autoelective_logger = logging.getLogger('autoelective')
        autoelective_logger.setLevel(logging.INFO)
        autoelective_logger.addHandler(gui_handler)
        
        # 设置其他相关模块的日志级别
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
    
    def add_log(self, message):
        """添加日志消息"""
        # 如果消息已经包含时间戳，直接显示
        if message.startswith('[') and ':' in message:
            # 这是来自日志处理器的格式化消息
            self.log_text.append(message)
        else:
            # 这是手动添加的消息，添加时间戳
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.append(f"[{timestamp}][SYSTEM] {message}")
        
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
        
        # 限制日志行数，避免内存占用过大
        max_lines = 1000
        lines = self.log_text.toPlainText().split('\n')
        if len(lines) > max_lines:
            self.log_text.setPlainText('\n'.join(lines[-max_lines:]))
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
    
    def save_log(self):
        """保存日志到文件"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存日志", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "成功", "日志保存成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存日志失败: {str(e)}")