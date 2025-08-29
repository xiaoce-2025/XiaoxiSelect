"""主窗口类"""

import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QCheckBox, QTabWidget, QMessageBox,
                             QFrame, QSizePolicy)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon, QFont, QColor, QLinearGradient, QBrush, QPalette
from autoelective.environ import Environ
from ui.config_editor import ConfigEditor
from ui.log_display import LogDisplay
from utils.thread_utils import cleanup_environment, cleanup_global_queues, verify_clean_state

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_auto_elective()
    
    def init_ui(self):
        self.setWindowTitle("PKUElective2025Autumn")
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
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e5799, stop:1 #2989d8);
                border-radius: 10px;
                padding: 5px;
            }
        """)
        
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(10, 5, 10, 5)
        
        title_label = QLabel("PKUElective2025Autumm")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: white;
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
        
        # 设置状态检查定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_thread_status)
        self.status_timer.start(2000)  # 每2秒检查一次
    
    def setup_auto_elective(self):
        """设置自动选课系统"""
        self.environ = Environ()
        self.threads = []
        self.is_running = False
    
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
            if not self.is_running:
                # 确保环境是干净的
                if hasattr(self.environ, 'iaaa_loop_thread') and self.environ.iaaa_loop_thread is not None:
                    self.log_display.add_log("检测到残留的线程引用，正在清理...")
                    cleanup_environment(self.environ)
                
                # 强制清理全局状态
                self.log_display.add_log("正在清理全局状态...")
                cleanup_global_queues()
                
                # 等待一下确保清理完成
                import time
                time.sleep(0.5)
                
                # 验证清理是否成功
                if not verify_clean_state(self.environ):
                    raise Exception("全局状态清理失败，无法启动程序")
                
                # 使用cli的启动逻辑
                from autoelective.cli import create_default_parser, create_default_threads, setup_default_environ
                
                # 创建解析器并设置默认选项
                parser = create_default_parser()
                options, args = parser.parse_args([])  # 空参数列表，使用默认值
                
                # 根据监控开关设置选项
                options.with_monitor = self.monitor_check.isChecked()
                
                # 设置环境
                setup_default_environ(options, args, self.environ)
                
                # 创建线程
                self.threads = create_default_threads(options, args, self.environ)
                
                # 启动线程
                for thread in self.threads:
                    thread.daemon = True
                    thread.start()
                
                self.is_running = True
                self.status_label.setText("运行中")
                self.status_label.setStyleSheet("""
                    QLabel {
                        font-size: 16px;
                        font-weight: bold;
                        color: #28a745;
                        background-color: #f8f9fa;
                        border: 1px solid #dee2e6;
                        border-radius: 15px;
                        padding: 5px 15px;
                    }
                """)
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        background-color: #28a745;
                        border-radius: 10px;
                    }
                """)
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                
                self.log_display.add_log("选课任务正在执行...")
                if options.with_monitor:
                    self.log_display.add_log("监控功能已启用")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动失败: {str(e)}")
            self.log_display.add_log(f"启动失败: {str(e)}")
            
            # 启动失败时清理状态
            self.is_running = False
            self.threads = []
            self.status_label.setText("启动失败")
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    color: #dc3545;
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 15px;
                    padding: 5px 15px;
                }
            """)
            self.status_indicator.setStyleSheet("""
                QLabel {
                    background-color: #dc3545;
                    border-radius: 10px;
                }
            """)
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
            # 清理环境状态
            cleanup_environment(self.environ)
    
    def stop_auto_elective(self):
        """停止自动选课"""
        try:
            if self.is_running:
                # 停止所有线程
                for thread in self.threads:
                    if thread.is_alive():
                        # 强制终止线程（临时用）
                        self._force_stop_thread(thread)

                
                # 清空线程列表
                self.threads = []
                self.is_running = False
                self.status_label.setText("已停止")
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
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        background-color: #6c757d;
                        border-radius: 10px;
                    }
                """)
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                
                # 清理环境状态
                cleanup_environment(self.environ)
                
                self.log_display.add_log("选课任务已终止")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止失败: {str(e)}")
            self.log_display.add_log(f"停止失败: {str(e)}")

    # 强制线程终止（临时，后续待修改autoelective本身代码后做适配）
    def _force_stop_thread(self, thread):
        """强制停止线程"""
        try:
            # 使用PyQt6的线程终止方法（如果线程是QThread）
            if hasattr(thread, 'terminate'):
                thread.terminate()
                thread.wait()  # 等待线程实际结束
                self.log_display.add_log(f"已强制终止线程: {thread.name}")
            else:
                # 对于非QThread，使用更强制的方法
                import ctypes
                
                if not thread.is_alive():
                    return
                    
                # 获取线程ID
                thread_id = thread.ident
                
                # 使用ctypes调用系统API强制终止线程
                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_long(thread_id),
                    ctypes.py_object(SystemExit)
                )
                
                if res == 0:
                    self.log_display.add_log(f"无法终止线程 {thread_id}")
                elif res != 1:
                    # 如果返回值不是1，说明调用失败
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
                    self.log_display.add_log(f"终止线程 {thread_id} 失败")
                else:
                    self.log_display.add_log(f"已强制终止线程: {thread_id}")
                    
        except Exception as e:
            self.log_display.add_log(f"终止线程时出错: {str(e)}")
    
    def check_thread_status(self):
        """检查线程状态"""
        if self.is_running and self.threads:
            # 检查是否有线程已经结束
            active_threads = [t for t in self.threads if t.is_alive()]
            
            if len(active_threads) < len(self.threads):
                self.log_display.add_log(f"检测到 {len(self.threads) - len(active_threads)} 个线程已结束")
                
                # 如果所有线程都结束了，自动停止
                if not active_threads:
                    self.log_display.add_log("所有线程已结束，自动停止程序")
                    self.stop_auto_elective()
                else:
                    # 更新线程列表
                    self.threads = active_threads
    
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
                # 等待一下确保清理完成
                import time
                time.sleep(0.5)
                event.accept()
            else:
                event.ignore()
        else:
            # 即使没有运行，也清理一下环境
            cleanup_environment(self.environ)
            event.accept()