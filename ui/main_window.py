"""
@Author : xiaoce2025
@File   : main_window.py
@Date   : 2025-08-29
"""

"""主窗口类"""

import logging
import os
import re
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QCheckBox, QTabWidget, QMessageBox,
                             QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment
from PyQt6.QtGui import QIcon, QFont, QColor, QLinearGradient, QBrush, QPalette, QShortcut, QKeySequence
from config.config_manager import ConfigManager
from ui.config_editor import ConfigEditor
from ui.log_display import LogDisplay
from ui.console_window import ConsoleWindow
from utils.weixin_api import create_and_start_active_weixin_api, stop_active_weixin_api

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_auto_elective()
        self.setup_console_window()
        
        # 检查更新
        from version.update_check import check_update
        check_update(self)
    
    def init_ui(self):
        self.setWindowTitle("严小希选课小助手 2026Spring-v1.3.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置应用图标
        self.setWindowIcon(QIcon(":/icons/app_icon.png"))
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 设置主窗口背景
        gradient = QLinearGradient(0, 0, 0, 400)
        gradient.setColorAt(0, QColor("#f0f8ff"))  # 浅蓝色

        gradient.setColorAt(1, QColor("#e6f7ff"))  # 更浅的蓝色
        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(gradient))
        self.setPalette(palette)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # 标题区域
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)

        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(10, 5, 10, 5)

        # 使用HTML创建彩虹色文字
        rainbow_text = """
        <span style="
            font-family: '华文行楷', 'Microsoft YaHei', sans-serif;
            font-size: 36px;
            font-weight: bold;
        ">
            <span style="color: #FF0000;">严</span>
            <span style="color: #FF7F00;">小</span>
            <span style="color: #FFD700;">希</span>
            <span style="color: #00FF00;">选</span>
            <span style="color: #00FFFF;">课</span>
            <span style="color: #0000FF;">小</span>
            <span style="color: #8B00FF;">助</span>
            <span style="color: #FF00FF;">手</span>
        </span>
        """

        title_label = QLabel(rainbow_text)
        title_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(title_label, 0)
        
        # 状态和控制区域
        status_control_frame = QFrame()
        status_control_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        status_control_frame.setMaximumHeight(120)
        
        status_control_layout = QVBoxLayout(status_control_frame)
        status_control_layout.setContentsMargins(10, 5, 10, 5)
        status_control_layout.setSpacing(10)
        
        # 状态显示
        status_layout = QHBoxLayout()
        # 标题
        status_layout.addWidget(title_frame)

        status_title = QLabel("当前运行状态:")
        status_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        status_layout.addWidget(status_title)
        
        self.status_label = QLabel("未启动")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #6c757d;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 15px;
                padding: 5px 15px;
            }
        """)
        # 上面样式表备用方案添加max-height: 30px
        status_layout.addWidget(self.status_label)
        
        # 状态指示灯
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(20, 20)
        self.status_indicator.setStyleSheet("""
            QLabel {
                background-color: #6c757d;
                border-radius: 10px;
            }
        """)
        status_layout.addWidget(self.status_indicator)
        
        status_layout.addStretch()
        
        #status_control_layout.addLayout(status_layout)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)
        
        # 监控开关（已弃用）
        self.monitor_check = QCheckBox("启动监控")
        self.monitor_check.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                padding: 5px;
            }
        """)
        self.monitor_check.hide()
        
        self.start_btn = QPushButton()
        self.start_btn.setIcon(QIcon(":/icons/play_icon.png"))
        self.start_btn.setText("启动选课")
        self.start_btn.clicked.connect(self.start_auto_elective)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        
        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(QIcon(":/icons/stop_icon.png"))
        self.stop_btn.setText("停止选课")
        self.stop_btn.clicked.connect(self.stop_auto_elective)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        
        control_layout.addStretch()
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addStretch()
        
        status_layout.addLayout(control_layout)
        status_control_layout.addLayout(status_layout)
        main_layout.addWidget(status_control_frame)
        
        # 标签页区域
        tab_frame = QFrame()
        tab_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
            }
        """)
        
        tab_layout = QVBoxLayout(tab_frame)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        
        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-top: none;
                border-radius: 0 0 10px 10px;
                background: white;
            }
            
            QTabBar::tab {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 20px;
                margin-right: 2px;
                font-size: 14px;
                color: #6c757d;
            }
            
            QTabBar::tab:selected {
                background: white;
                color: #007bff;
                font-weight: bold;
                border-bottom: 2px solid #007bff;
            }
            
            QTabBar::tab:hover {
                background: #e9ecef;
            }
        """)
        
        # 设置标签页
        self.config_editor = ConfigEditor()
        self.tab_widget.addTab(self.config_editor, QIcon(":/icons/settings_icon.png"), "设置")
        
        # 日志标签页
        self.log_display = LogDisplay()
        self.tab_widget.addTab(self.log_display, QIcon(":/icons/log_icon.png"), "日志")
        
        tab_layout.addWidget(self.tab_widget)
        main_layout.addWidget(tab_frame, 1)  # 添加拉伸因子1使标签页占据剩余空间
        
        # 页脚
        footer_label = QLabel("请不要使用刷课机刷课，否则将受到学校严厉处分！ 本项目仅供学习交流使用，请勿在公开场合传播此项目！ 对于不正当使用本项目所造成的后果，暂时不能给你明确的答复！ 不正当使用过程存在风险，USE AT YOUR OWN RISK，这个需要你自己衡量!")
        footer_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #6c757d;
                text-align: center;
                padding: 5px;
            }
        """)
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer_label)
        
        # 初始化日志系统
        self.setup_logging()
        

    def setup_console_window(self):
        """设置Console窗口和快捷键"""
        # 创建Console窗口（但不立即显示）
        self.console_window = ConsoleWindow(self)
        # 创建快捷键 Ctrl+Shift+I
        self.console_shortcut = QShortcut(QKeySequence("Ctrl+Shift+I"), self)
        self.console_shortcut.activated.connect(self.toggle_console_window)
    
    def toggle_console_window(self):
        """切换Console窗口的显示状态"""
        if self.console_window.isVisible():
            self.console_window.hide()
        else:
            self.console_window.show()
            self.console_window.raise_()  # 将窗口置于最前
            self.console_window.activateWindow()  # 激活窗口
    
    def setup_auto_elective(self):
        """设置自动选课系统"""
        self.elective_process = None
        self._process_stdout_buffer = ""
        self.is_running = False

    def _start_weixin_notification_runtime(self):
        """按配置启动微信监听运行时。"""
        settings = ConfigManager.get_notification_settings()
        if not settings.get("yanxx_weixin", False):
            stop_active_weixin_api()
            return
        create_and_start_active_weixin_api()

    def _stop_weixin_notification_runtime(self):
        """停止微信监听运行时。"""
        stop_active_weixin_api()
    
    def setup_logging(self):
        """设置日志系统"""
        try:
            # 配置日志格式
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[]  # 不添加默认处理器，避免重复输出
            )
            
            # 设置特定模块的日志级别
            logging.getLogger('urllib3').setLevel(logging.WARNING)
            logging.getLogger('requests').setLevel(logging.WARNING)
            logging.getLogger('autoelective').setLevel(logging.INFO)
            
            self.log_display.add_log("日志系统初始化完成")
            
        except Exception as e:
            self.log_display.add_log(f"日志系统初始化失败: {str(e)}")
    
    def start_auto_elective(self):
        """启动自动选课"""
        try:
            # 自动切换到日志页面
            self.tab_widget.setCurrentIndex(1)
            if self.is_running:
                return

            self._start_elective_subprocess()
            self._start_weixin_notification_runtime()
            self._set_running_ui(True)

            self.log_display.add_log("已启动独立刷课进程")
            if ConfigManager.get_notification_settings().get("yanxx_weixin", False):
                self.log_display.add_log("微信监听运行时已启动")
            if self.monitor_check.isChecked():
                self.log_display.add_log("监控功能已启用")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动失败: {str(e)}")
            self.log_display.add_log(f"启动失败: {str(e)}")
            
            # 启动失败时清理状态
            self._set_running_ui(False, status_text="启动失败", color="#dc3545")
            if self.elective_process is not None:
                self.elective_process.deleteLater()
                self.elective_process = None
            self._process_stdout_buffer = ""
            self._stop_weixin_notification_runtime()

    def _start_elective_subprocess(self):
        """以独立子进程启动刷课流程"""
        process = QProcess(self)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.readyReadStandardOutput.connect(self._on_process_output)
        process.finished.connect(self._on_process_finished)
        process.errorOccurred.connect(self._on_process_error)

        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONIOENCODING", "utf-8")
        process.setProcessEnvironment(env)

        args = ["-u", "-m", "autoelective.gui_worker"]
        if self.monitor_check.isChecked():
            args.append("--with-monitor")

        process.setWorkingDirectory(os.getcwd())
        process.start(sys.executable, args)
        if not process.waitForStarted(5000):
            raise RuntimeError("独立刷课进程未能正常启动")

        self.elective_process = process
        self._process_stdout_buffer = ""

    def _set_running_ui(self, running, status_text=None, color=None):
        """统一更新运行状态 UI"""
        self.is_running = running
        if running:
            status_text = status_text or "运行中"
            color = color or "#28a745"
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        else:
            status_text = status_text or "已停止"
            color = color or "#6c757d"
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

        self.status_label.setText(status_text)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: %s;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 15px;
                padding: 5px 15px;
            }
        """ % color)
        self.status_indicator.setStyleSheet("""
            QLabel {
                background-color: %s;
                border-radius: 10px;
            }
        """ % color)

    def _emit_process_line(self, line):
        """将子进程输出转换为日志栏格式"""
        text = line.strip()
        if not text:
            return

        # 兼容 autoelective 旧日志格式: [LEVEL] logger, 12:34:56, message
        m = re.match(r"^\[(?P<level>[A-Z]+)\]\s+[^,]+,\s+(?P<ts>\d{2}:\d{2}:\d{2}),\s*(?P<msg>.*)$", text)
        if m:
            level = m.group("level")
            ts = m.group("ts")
            msg = m.group("msg")
            self.log_display.add_log(f"[{ts}][{level}] {msg}")
            return

        # 若已经是 GUI 兼容格式，直接透传
        if text.startswith("[") and "][" in text:
            self.log_display.add_log(text)
            return

        self.log_display.add_log(f"[WORKER] {text}")

    def _on_process_output(self):
        """读取并处理子进程输出"""
        if self.elective_process is None:
            return

        chunk = bytes(self.elective_process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if not chunk:
            return

        self._process_stdout_buffer += chunk
        while "\n" in self._process_stdout_buffer:
            line, self._process_stdout_buffer = self._process_stdout_buffer.split("\n", 1)
            self._emit_process_line(line)

    def _on_process_finished(self, exit_code, exit_status):
        """子进程结束回调"""
        # 处理剩余缓冲
        if self._process_stdout_buffer:
            self._emit_process_line(self._process_stdout_buffer)
            self._process_stdout_buffer = ""

        normal = exit_status == QProcess.ExitStatus.NormalExit and exit_code == 0
        if normal:
            self.log_display.add_log("刷课进程已正常退出")
            self._set_running_ui(False, status_text="已停止", color="#6c757d")
        else:
            self.log_display.add_log(f"刷课进程异常退出 (code={exit_code})")
            self._set_running_ui(False, status_text="异常退出", color="#dc3545")

        self._stop_weixin_notification_runtime()

        if self.elective_process is not None:
            self.elective_process.deleteLater()
            self.elective_process = None

    def _on_process_error(self, process_error):
        """子进程错误回调"""
        self.log_display.add_log(f"刷课进程错误: {process_error}")
    
    def stop_auto_elective(self):
        """停止自动选课"""
        try:
            if not self.is_running:
                return

            if self.elective_process is not None and self.elective_process.state() != QProcess.ProcessState.NotRunning:
                self.log_display.add_log("正在停止独立刷课进程...")
                self.elective_process.terminate()
                if not self.elective_process.waitForFinished(3000):
                    self.log_display.add_log("子进程未及时退出，执行强制终止")
                    self.elective_process.kill()
                    self.elective_process.waitForFinished(2000)

            self._set_running_ui(False, status_text="已停止", color="#6c757d")
            self._stop_weixin_notification_runtime()
            self.log_display.add_log("选课任务已终止")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止失败: {str(e)}")
            self.log_display.add_log(f"停止失败: {str(e)}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.is_running:
            reply = QMessageBox.question(
                self, "确认退出", 
                "选课程序正在运行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.stop_auto_elective()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()