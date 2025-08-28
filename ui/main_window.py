"""
主窗口类
"""

import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QCheckBox, QTabWidget, QMessageBox)
from PyQt6.QtCore import QTimer
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
        self.setWindowTitle("PKU自动选课程序 v1.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("PKU自动选课程序")
        #title_label.setAlignment(qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px;
                background-color: #ecf0f0;
                border-radius: 10px;
                margin: 10px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # 状态显示
        status_layout = QHBoxLayout()
        self.status_label = QLabel("状态: 未启动")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 10px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
        """)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        main_layout.addLayout(status_layout)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        # 监控开关
        self.monitor_check = QCheckBox("启动监控")
        self.monitor_check.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                padding: 5px;
            }
        """)
        
        self.start_btn = QPushButton("启动选课")
        self.start_btn.clicked.connect(self.start_auto_elective)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 8px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        
        self.stop_btn = QPushButton("停止选课")
        self.stop_btn.clicked.connect(self.stop_auto_elective)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 8px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        
        control_layout.addWidget(self.monitor_check)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addStretch()
        
        main_layout.addLayout(control_layout)
        
        # 标签页
        tab_widget = QTabWidget()
        
        # 设置标签页
        self.config_editor = ConfigEditor()
        tab_widget.addTab(self.config_editor, "设置")
        
        # 日志标签页
        self.log_display = LogDisplay()
        tab_widget.addTab(self.log_display, "日志")
        
        main_layout.addWidget(tab_widget)
        
        # 初始化日志系统
        self.setup_logging()
        
        # 设置状态检查定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_thread_status)
        self.status_timer.start(2000)  # 每2秒检查一次
        
        central_widget.setLayout(main_layout)
    
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
                self.status_label.setText("状态: 运行中")
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                
                self.log_display.add_log("自动选课程序已启动")
                if options.with_monitor:
                    self.log_display.add_log("监控功能已启用")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动失败: {str(e)}")
            self.log_display.add_log(f"启动失败: {str(e)}")
            
            # 启动失败时清理状态
            self.is_running = False
            self.threads = []
            self.status_label.setText("状态: 启动失败")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
            # 清理环境
            cleanup_environment(self.environ)
    
    def stop_auto_elective(self):
        """停止自动选课"""
        try:
            if self.is_running:
                # 停止所有线程
                for thread in self.threads:
                    if thread.is_alive():
                        # 尝试优雅地停止线程
                        # 注意：这里只是标记状态，实际的停止逻辑需要在各个线程中实现
                        pass
                
                # 清空线程列表
                self.threads = []
                self.is_running = False
                self.status_label.setText("状态: 已停止")
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                
                # 清理环境状态
                cleanup_environment(self.environ)
                
                self.log_display.add_log("自动选课程序已停止")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止失败: {str(e)}")
            self.log_display.add_log(f"停止失败: {str(e)}")
    
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
                "程序正在运行中，确定要退出吗？",
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