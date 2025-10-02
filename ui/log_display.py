"""
日志显示界面
"""

import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPushButton, 
                             QLabel, QHBoxLayout, QFileDialog, QMessageBox, )
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QColor
from handlers.gui_log_handler import GUILogHandler
from PyQt6.QtCore import QThread
from config.config_manager import ConfigManager
import win32com.client  # Windows语音合成
import pythoncom  # COM线程初始化
import os
import re

# 创建后台任务线程
class NotificationWorker(QThread):
    """后台执行通知任务的线程"""
    notification_triggered = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, message):
        super().__init__()
        self.message = message

    def run(self):
        # 发送信号触发弹窗（在主线程中执行）
        self.notification_triggered.emit(self.message)
        # 获取提醒配置
        self.notification_config = ConfigManager.get_notification_settings()
        if "yanxx_voice" not in self.notification_config.keys():
            self.notification_config["yanxx_voice"] = True
        if "yanxx_weixin" not in self.notification_config.keys():
            self.notification_config["yanxx_weixin"] = False
        if "yanxx_weixin_user" not in self.notification_config.keys():
            self.notification_config["yanxx_weixin_user"] = ""

        # 先发微信通知
        if self.notification_config["yanxx_weixin"]:
            import wxauto4
            pass
        

        # 后语音提醒
        if self.notification_config["yanxx_voice"]:
            # 初始化COM线程
            pythoncom.CoInitialize()

            try:
                # 创建语音合成对象
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                            
                # 获取所有可用的语音
                voices = speaker.GetVoices()
                
                # 查找女声语音（根据描述中包含"Female"）
                female_voice = None
                for i in range(voices.Count):
                    voice = voices.Item(i)
                    if "Female" in voice.GetDescription():
                        female_voice = voice
                        break

                # 查找默认女声
                if female_voice is None:
                    # 尝试按名称找
                    known_female_voices = ["Microsoft Huihui", "Microsoft Xiaoxiao"]
                    for i in range(voices.Count):
                        voice = voices.Item(i)
                        description = voice.GetDescription()
                        if any(name in description for name in known_female_voices):
                            female_voice = voice
                            break

                    if female_voice is not None:
                        speaker.Voice = female_voice
                
                # 如果找到女声则设置，否则使用默认语音
                if female_voice:
                    speaker.Voice = female_voice
                
                # 提取课程名称和班号
                course_name = self.extract_course_name(self.message)
                class_number = self.extract_class_number(self.message)
                if "is AVAILABLE" in self.message:
                    if course_name and class_number:
                        speech_text = f"严小希提醒您：{course_name}课程{class_number}班有空余名额啦，快去选课吧！"
                    elif course_name:
                        speech_text = f"严小希提醒您：{course_name}课程有空余名额啦，快去选课吧！"
                    else:
                        speech_text = "严小希提醒您：检测存在课程有空余名额，请及时登录选课网查看！"
                elif "is ELECTED" in self.message:
                    if course_name and class_number:
                        speech_text = f"严小希提醒您：已经选上 {course_name}课程{class_number}班！"
                    elif course_name:
                        speech_text = f"严小希提醒您：已经选上 {course_name}课程！"
                    else:
                        speech_text = "严小希提醒您：检测存在课程已被选上，请及时登录选课网查看！"
                # 朗读文本
                speaker.Speak(speech_text)
            except Exception as e:
                print(f"语音合成失败: {e}")
            finally:
                # 清理COM线程
                pythoncom.CoUninitialize()
        
        # 发送完成信号
        self.finished.emit()


    
    def extract_course_name(self, message):
        """从日志消息中提取课程名称"""
        # 使用正则表达式匹配课程名称
        # 示例日志: [07:56:59][INFO] Course(羽毛球, 5, 体育教研部, 30 / 0) is AVAILABLE now !
        match = re.search(r"Course\(([^,]+),", message)
        if match:
            return match.group(1).strip()
        return None
    
    def extract_class_number(self, message):
        pattern = r'Course\(([^)]+)\)'
        match = re.search(pattern, message)
        
        if match:
            course_content = match.group(1)  # 获取括号内的内容
            parts = [part.strip() for part in course_content.split(',')]
            
            # 确保有足够的部分且第二个部分是数字
            if len(parts) >= 2 and parts[1].isdigit():
                return int(parts[1])  # 返回班号
        
        return None  # 如果提取失败返回None



# 日志展示
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

        # 通知队列和工作线程
        self.notification_queue = []
        self.current_worker = None
    
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

    def show_notification(self, message):
        """显示通知弹窗"""
        # 提取课程名称和班号
        course_name = self.extract_course_name(message)
        class_number = self.extract_class_number(message)
        
        if "is AVAILABLE" in message:
            if course_name and class_number:
                display_text = f"课程 {course_name}（班号：{class_number}）有空余名额啦"
            elif course_name:
                display_text = f"课程 {course_name} 有空余名额啦"
            else:
                display_text = "检测到存在课程有空余名额，请及时查看"
        elif "is ELECTED" in message:
            if course_name and class_number:
                display_text = f"课程 {course_name}（班号：{class_number}） 已选上！"
            elif course_name:
                display_text = f"课程 {course_name} 已选上！"
            else:
                display_text = "检测到存在课程已被选上，请及时查看"
            
        QMessageBox.information(
            self,
            "课程可用通知",
            display_text,
            QMessageBox.StandardButton.Ok
        )

    def extract_course_name(self, message):
        """从日志消息中提取课程名称"""
        
        # 使用正则表达式匹配课程名称
        match = re.search(r"Course\(([^,]+),", message)
        if match:
            return match.group(1).strip()
        return None
    
    def extract_class_number(self, message):
        pattern = r'Course\(([^)]+)\)'
        match = re.search(pattern, message)
        
        if match:
            course_content = match.group(1)  # 获取括号内的内容
            parts = [part.strip() for part in course_content.split(',')]
            
            # 确保有足够的部分且第二个部分是数字
            if len(parts) >= 2 and parts[1].isdigit():
                return int(parts[1])  # 返回班号
        
        return None  # 如果提取失败返回None
    
    def add_log(self, message):
        """添加日志消息"""
        # 如果消息已经包含时间戳，直接显示
        if message.startswith('[') and ':' in message:
            # 这是来自日志处理器的格式化消息
            formatted_msg = message
        else:
            # 这是手动添加的消息，添加时间戳
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_msg = f"[{timestamp}][SYSTEM] {message}"
        
        # 创建文本光标并定位到文档末尾
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # 根据关键字设置文本颜色
        text_format = cursor.charFormat()
        
        # 关键字检测
        if "is ELECTED" in formatted_msg.upper():
            text_format.setForeground(QColor("red"))
        elif "is AVAILABLE" in formatted_msg.upper():
            text_format.setForeground(QColor("blue"))
        elif "[DEBUG]" in formatted_msg.upper():
            text_format.setForeground(QColor("gray"))
        elif "[INFO]" in formatted_msg.upper():
            text_format.setForeground(QColor("black"))
        elif "[WARNING]" in formatted_msg.upper():
            text_format.setForeground(QColor("orange"))
        elif "[ERROR]" in formatted_msg.upper():
            text_format.setForeground(QColor("red"))
        elif "[CRITICAL]" in formatted_msg.upper():
            text_format.setForeground(QColor("purple"))
        elif "[SYSTEM]" in formatted_msg.upper():
            text_format.setForeground(QColor("blue"))
        else:
            text_format.setForeground(QColor("black"))
        
        # 插入带格式的文本
        cursor.insertText(formatted_msg + '\n', text_format)
        
        # 自动滚动到底部
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()

        # 检测课程空闲/已选上关键字并触发通知
        if "is AVAILABLE" in formatted_msg.upper() or "is ELECTED" in formatted_msg.upper():
            # 将通知加入队列
            self.notification_queue.append(formatted_msg)
            # 如果没有正在运行的工作线程，启动一个
            if not self.current_worker:
                self.process_next_notification()

        # 测试用（选课网未开放）
        if "目前不是补退选时间，因此不能进行相应操作" in formatted_msg.upper():
            self.notification_queue.append("[07:56:59][INFO] Course(羽毛球, 体育教研部, 30 / 0) is AVAILABLE now !")
            if not self.current_worker:
                self.process_next_notification()
            self.notification_queue.append("[07:56:59][INFO] Course(羽毛球, 体育教研部, 30 / 0) is ELECTED !")
            if not self.current_worker:
                self.process_next_notification()

        # 限制日志行数
        max_lines = 1000
        if self.log_text.document().blockCount() > max_lines:
            cursor.setPosition(0)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()


    def process_next_notification(self):
        """处理队列中的下一个通知"""
        if not self.notification_queue:
            self.current_worker = None
            return
            
        # 从队列中取出下一个通知
        message = self.notification_queue.pop(0)
        
        # 创建并启动通知线程
        self.current_worker = NotificationWorker(message)
        self.current_worker.notification_triggered.connect(self.show_notification)
        self.current_worker.finished.connect(self.on_worker_finished)
        self.current_worker.start()
    
    def on_worker_finished(self):
        """当工作线程完成时调用"""
        self.current_worker = None
        self.process_next_notification()
 
    
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



