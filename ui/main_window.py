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
                             QLabel, QPushButton, QCheckBox, QMessageBox,
                             QFrame, QSizePolicy, QStackedWidget, QTextEdit)
from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment, QTimer
from PyQt6.QtGui import (QIcon, QFont, QColor, QLinearGradient, QBrush, QPalette,
                         QShortcut, QKeySequence, QTextCursor, QTextCharFormat)
from ui.config_editor import ConfigEditor
from ui.log_display import LogDisplay
from ui.console_window import ConsoleWindow
from handlers.log_server import LogServer

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
        
        # 页面容器
        page_frame = QFrame()
        page_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
            }
        """)

        page_layout = QVBoxLayout(page_frame)
        page_layout.setContentsMargins(0, 0, 0, 0)

        # 页面切换容器
        self.stacked_widget = QStackedWidget()

        # 配置页面
        self.config_editor = ConfigEditor()
        self.stacked_widget.addWidget(self.config_editor)

        # 日志页面（带返回按钮）
        log_page = QWidget()
        log_page_layout = QVBoxLayout(log_page)
        log_page_layout.setContentsMargins(10, 10, 10, 10)
        log_page_layout.setSpacing(10)

        back_btn_layout = QHBoxLayout()
        self.back_btn = QPushButton("← 返回配置页面")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setFixedWidth(150)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #495057;
            }
        """)
        self.back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        back_btn_layout.addWidget(self.back_btn)
        back_btn_layout.addStretch()
        log_page_layout.addLayout(back_btn_layout)

        # 上半部分：控制台输出（深色主题）
        console_label = QLabel("进程输出")
        console_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 11px;
                font-weight: bold;
                padding: 2px 0;
            }
        """)
        log_page_layout.addWidget(console_label)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Consolas", 10))
        self.console_output.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 6px;
                selection-background-color: #b3d7ff;
            }
        """)
        log_page_layout.addWidget(self.console_output, 1)

        # 下半部分：运行状态仪表盘（深色主题）
        dashboard_label = QLabel("运行状态")
        dashboard_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 11px;
                font-weight: bold;
                padding: 2px 0;
            }
        """)
        log_page_layout.addWidget(dashboard_label)

        dashboard_frame = QFrame()
        dashboard_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        dashboard_layout = QVBoxLayout(dashboard_frame)
        dashboard_layout.setContentsMargins(12, 10, 12, 10)
        dashboard_layout.setSpacing(8)

        # 第一行：4 个指标卡片
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        self._stat_labels = {}
        stat_defs = [
            ("runtime", "已运行", "00:00:00", "#0d6efd"),
            ("loop", "当前轮次", "第 0 轮", "#664d03"),
            ("elected", "已选课程", "0 门", "#0a8754"),
            ("active", "刷取中", "0 门", "#b35c00"),
            ("ignored", "已跳过", "0 门", "#6c757d"),
        ]

        for key, title, default, accent in stat_defs:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 6px 10px;
                }
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(4, 4, 4, 4)
            card_layout.setSpacing(2)

            title_lbl = QLabel(title)
            title_lbl.setStyleSheet("color: #6c757d; font-size: 11px; border: none;")
            title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(title_lbl)

            value_lbl = QLabel(default)
            value_lbl.setStyleSheet(f"color: {accent}; font-size: 18px; font-weight: bold; border: none; font-family: Consolas, monospace;")
            value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(value_lbl)

            self._stat_labels[key] = value_lbl
            stats_row.addWidget(card)

        dashboard_layout.addLayout(stats_row)

        # 第二行：最近事件（单行滚动）
        self._event_label = QLabel("等待启动...")
        self._event_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 12px;
                font-family: Consolas, monospace;
                padding: 4px 0;
                border: none;
            }
        """)
        self._event_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        dashboard_layout.addWidget(self._event_label)

        log_page_layout.addWidget(dashboard_frame, 1)

        # 初始化仪表盘状态
        self._dashboard_start_time = None
        self._dashboard_stats = {"loop": 0, "elected": 0, "active": set(), "ignored": 0}

        # 运行时间定时器
        self._runtime_timer = QTimer()
        self._runtime_timer.timeout.connect(self._update_runtime_display)

        # LogDisplay（内部日志机制依赖，不在 UI 中显示）
        self.log_display = LogDisplay()
        self.log_display.hide()

        self.stacked_widget.addWidget(log_page)

        page_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(page_frame, 1)
        
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
        # 日志服务器（子进程 → GUI 的结构化日志通道）
        self._log_server = LogServer()
    
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
            self.stacked_widget.setCurrentIndex(1)
            if self.is_running:
                return

            # 检查 IAAA 公钥是否变更
            passed, reason = self.config_editor.check_iaaa_public_key()
            if not passed:
                QMessageBox.warning(self, "提示", reason)
                self.stacked_widget.setCurrentIndex(0)  # 切换到设置页
                return

            self._start_elective_subprocess()
            self._set_running_ui(True)

            self.log_display.add_log("已启动独立刷课进程")
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

    def _start_elective_subprocess(self):
        """以独立子进程启动刷课流程"""
        # 重置仪表盘
        self._reset_dashboard()

        # 启动日志服务器，获取端口
        log_port = self._log_server.start()
        # 连接结构化日志信号
        self._log_server.log_received.connect(self._on_structured_log)

        process = QProcess(self)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.readyReadStandardOutput.connect(self._on_process_output)
        process.finished.connect(self._on_process_finished)
        process.errorOccurred.connect(self._on_process_error)

        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONIOENCODING", "utf-8")
        process.setProcessEnvironment(env)

        args = ["-u", "-m", "autoelective.gui_worker", "--log-port", str(log_port)]
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

    def _write_to_console(self, text, color=None):
        """写入控制台输出区域"""
        cursor = self.console_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color or "#333333"))
        cursor.insertText(text + '\n', fmt)
        self.console_output.setTextCursor(cursor)
        self.console_output.ensureCursorVisible()
        # 限制行数
        if self.console_output.document().blockCount() > 500:
            c = self.console_output.textCursor()
            c.setPosition(0)
            c.select(QTextCursor.SelectionType.BlockUnderCursor)
            c.removeSelectedText()

    # ---- 仪表盘 ----

    def _reset_dashboard(self):
        """重置仪表盘数据"""
        from datetime import datetime
        self._dashboard_start_time = datetime.now()
        self._dashboard_stats = {"loop": 0, "elected": 0, "active": set(), "ignored": 0}
        for lbl in self._stat_labels.values():
            lbl.setText("—")
        self._stat_labels["runtime"].setText("00:00:00")
        self._stat_labels["loop"].setText("第 0 轮")
        self._stat_labels["elected"].setText("0 门")
        self._stat_labels["active"].setText("0 门")
        self._stat_labels["ignored"].setText("0 门")
        self._event_label.setText("正在启动...")
        self._runtime_timer.start(1000)

    def _update_runtime_display(self):
        """定时更新运行时间"""
        if self._dashboard_start_time:
            from datetime import datetime
            delta = datetime.now() - self._dashboard_start_time
            total = int(delta.total_seconds())
            h, m, s = total // 3600, (total % 3600) // 60, total % 60
            self._stat_labels["runtime"].setText(f"{h:02d}:{m:02d}:{s:02d}")

    def _update_dashboard(self, text):
        """解析日志行，更新仪表盘指标"""
        # 轮次
        m = re.search(r"======== Loop (\d+) ========", text)
        if m:
            self._dashboard_stats["loop"] = int(m.group(1))
            self._stat_labels["loop"].setText(f"第 {m.group(1)} 轮")
            self._event_label.setText(f"正在进行第 {m.group(1)} 轮刷取...")
            return

        # 尝试选课（加入活跃集合）
        m = re.search(r"Try to elect (.+)", text)
        if m:
            course = m.group(1).strip()
            self._dashboard_stats["active"].add(course)
            self._stat_labels["active"].setText(f"{len(self._dashboard_stats['active'])} 门")
            self._event_label.setText(f"正在尝试选课: {course}")
            return

        # 选课成功
        if "is ELECTED" in text and "ignored" not in text:
            self._dashboard_stats["elected"] += 1
            self._stat_labels["elected"].setText(f"{self._dashboard_stats['elected']} 门")
            # 从活跃集合移除
            m = re.search(r"(.+?) is ELECTED", text)
            if m:
                self._dashboard_stats["active"].discard(m.group(1).strip())
                self._stat_labels["active"].setText(f"{len(self._dashboard_stats['active'])} 门")
            self._event_label.setText(f"✅ 选课成功: {text.split('is ELECTED')[0].strip()}")
            return

        # 已选上被忽略
        if "is elected, ignored" in text:
            self._dashboard_stats["ignored"] += 1
            self._stat_labels["ignored"].setText(f"{self._dashboard_stats['ignored']} 门")
            m = re.search(r"(.+?) is elected, ignored", text)
            if m:
                self._dashboard_stats["active"].discard(m.group(1).strip())
                self._stat_labels["active"].setText(f"{len(self._dashboard_stats['active'])} 门")
            return

        # 互斥忽略
        if "ignored by mutex rules" in text:
            self._dashboard_stats["ignored"] += 1
            self._stat_labels["ignored"].setText(f"{self._dashboard_stats['ignored']} 门")
            return

        # 各种错误 → 从活跃移除，计入忽略
        for err in ["QuotaLimitedError", "TimeConflictError", "ExamTimeConflictError",
                     "ElectionRepeatedError", "ElectionPermissionError",
                     "CreditsLimitedError", "MutexCourseError"]:
            if err in text:
                self._dashboard_stats["ignored"] += 1
                self._stat_labels["ignored"].setText(f"{self._dashboard_stats['ignored']} 门")
                self._event_label.setText(f"⚠ {err}")
                # 尝试从活跃集合移除上一个课程
                return

        # 验证码
        if "Validation failed" in text:
            self._event_label.setText("⚠ 验证码识别失败，重试中...")
            return
        if "Validation passed" in text:
            self._event_label.setText("验证码校验通过")
            return

        # 无任务
        if "No tasks" in text:
            self._event_label.setText("所有课程已处理完毕")
            return

        # 会话过期
        if "needs relogin" in text or "expired" in text:
            self._event_label.setText("⚠ 会话过期，正在重新登录...")
            return

        # 登录成功
        if "IAAA login success" in text:
            self._event_label.setText("IAAA 登录成功")
            return
        if "SSO login success" in text:
            self._event_label.setText("SSO 登录成功")
            return

    def _emit_process_line(self, line):
        """将子进程 stdout 输出转换为日志栏格式（Socket 日志的回退通道）"""
        text = line.strip()
        if not text:
            return

        # 更新仪表盘
        self._update_dashboard(text)

        # 写入控制台（根据级别着色）
        console_color = "#333333"
        if "[ERROR]" in text.upper() or "CRITICAL" in text.upper():
            console_color = "#dc3545"
        elif "[WARNING]" in text.upper():
            console_color = "#b8860b"
        elif "[INFO]" in text.upper():
            console_color = "#333333"
        elif "[DEBUG]" in text.upper():
            console_color = "#808080"
        self._write_to_console(text, console_color)

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

    def _on_structured_log(self, record: dict):
        """接收 Socket 日志服务器发来的结构化日志"""
        level = record.get("level", "INFO")
        ts = record.get("timestamp", "??:??:??")
        msg = record.get("message", "")
        self._update_dashboard(msg)
        self.log_display.add_log(f"[{ts}][{level}] {msg}")

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
        # 停止运行时间计时器
        self._runtime_timer.stop()

        # 停止日志服务器
        self._log_server.stop()
        try:
            self._log_server.log_received.disconnect(self._on_structured_log)
        except TypeError:
            pass

        # 处理剩余 stdout 缓冲
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

            # 停止日志服务器
            self._log_server.stop()

            self._set_running_ui(False, status_text="已停止", color="#6c757d")
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