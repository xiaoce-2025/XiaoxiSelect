"""
配置文件编辑器界面
"""

import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QPushButton, QLabel, QLineEdit, QSpinBox,
                             QDoubleSpinBox, QCheckBox, QComboBox, QGroupBox,
                             QFormLayout, QMessageBox, QScrollArea, QFrame, QRadioButton,
                             QStackedWidget, QDialog, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QDialogButtonBox, QListWidgetItem)
from PyQt6.QtCore import Qt, QTimer
from config.config_manager import ConfigManager
from .components.QTabBar import VerticalTabBar
from PyQt6.QtGui import QIcon, QPixmap
import re
import pyperclip  # 用于访问剪贴板
from datetime import datetime


class ConfigEditor(QWidget):
    """配置文件编辑器"""

    def __init__(self, log_display=None):
        super().__init__()
        self.config_manager = ConfigManager()
        self.log_display = log_display

        # 初始化数据结构
        self.courses_data = {}
        self.mutex_data = {}
        self.delay_data = {}

        # 自动保存相关变量
        self.last_save_time = None
        self.autosave_enabled = True

        # 创建配置统计标签和删除按钮
        self.config_stats_label = QLabel("配置统计：0 个课程，0 个互斥规则，0 个延迟规则")
        self.config_stats_label.setStyleSheet("""
            QLabel {
                background-color: #e9ecef;
                border: 1px solid #adb5bd;
                border-radius: 6px;
                padding: 10px 15px;
                margin: 5px;
                font-size: 10pt;
                color: #495057;
            }
        """)
        self.config_stats_label.hide()  # 默认隐藏

        self.clear_btn = QPushButton("删除所有课程配置")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 12px;
                margin: 5px;
                border-radius: 6px;
                font-size: 10pt;
                font-weight: 500;
                max-width: 140px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        self.clear_btn.setToolTip("清空所有课程、互斥规则和延迟规则")
        self.clear_btn.clicked.connect(self.clear_all_course_configs)
        self.clear_btn.hide()  # 默认隐藏

        self.init_ui()
        self.load_configs()

    def init_ui(self):
        # 应用现代样式表
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10pt;
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background: #ffffff;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #e9ecef;
                border: 1px solid #dee2e6;
                padding: 10px 20px;
                margin-right: 2px;
                border-radius: 6px 6px 0 0;
                color: #495057;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom: 2px solid #007bff;
                color: #007bff;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #f8f9fa;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 10pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px 8px;
                background: #ffffff;
                font-size: 10pt;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #007bff;
                outline: none;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #ced4da;
                border-radius: 3px;
                background: #ffffff;
            }
            QCheckBox::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
            }
            QLabel {
                color: #495057;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                margin-top: 1ex;
                background: #f8f9fa;
                           
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #495057;
            }
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background: #ffffff;
            }
            QTableWidget {
                gridline-color: #dee2e6;
                background: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f3f4;
            }
            QTableWidget::item:selected {
                background: #e3f2fd;
            }
            QRadioButton {
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #ced4da;
                border-radius: 8px;
                background: #ffffff;
            }
            QRadioButton::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # 创建切换按钮
        self.switch_button = QPushButton("切换到课程设置")
        self.switch_button.clicked.connect(self.switch_view)
        self.switch_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 10pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)

        # 顶部布局：右上角按钮
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        top_layout.addWidget(self.config_stats_label)
        top_layout.addWidget(self.clear_btn)
        top_layout.addWidget(self.switch_button)
        layout.addLayout(top_layout)

        # 创建堆叠窗口
        self.stacked_widget = QStackedWidget()

        # 系统设置页面
        self.system_widget = self.create_system_settings_widget()
        system_scroll = QScrollArea()
        system_scroll.setWidget(self.system_widget)
        system_scroll.setWidgetResizable(True)
        self.stacked_widget.addWidget(system_scroll)

        # 课程设置页面
        self.course_widget = self.create_course_tab()
        course_scroll = QScrollArea()
        course_scroll.setWidget(self.course_widget)
        course_scroll.setWidgetResizable(True)
        self.stacked_widget.addWidget(course_scroll)

        layout.addWidget(self.stacked_widget)

        # 保存按钮
        save_btn = QPushButton("保存所有设置")
        save_btn.clicked.connect(self.save_all_configs)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 12pt;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)

        # 已启用自动保存，手动保存可弃用
        save_btn.hide()

        layout.addWidget(save_btn)

        # 添加保存状态标签
        self.save_status_label = QLabel("成功加载全部配置")
        self.save_status_label.setStyleSheet("""
            QLabel {
                color: #28a745;
                font-size: 10pt;
                padding: 8px 12px;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 4px;
                margin: 5px 0;
            }
        """)
        layout.addWidget(self.save_status_label)

        self.setLayout(layout)

    # 加载配置
    def load_configs(self):
        """加载配置文件"""
        try:
            config_data = self.config_manager.load_config()

            # 加载用户设置
            if 'user' in config_data:
                user_data = config_data['user']
                self.student_id_edit.setText(user_data.get('student_id', ''))
                self.password_edit.setText(user_data.get('password', ''))
                self.dual_degree_check.setChecked(
                    user_data.get('dual_degree', False))
                self.identity_combo.setCurrentText(
                    user_data.get('identity', 'bzx'))

            # 加载客户端设置
            if 'client' in config_data:
                client_data = config_data['client']
                self.supply_cancel_page_spin.setValue(
                    client_data.get('supply_cancel_page', 1))
                self.refresh_interval_spin.setValue(
                    client_data.get('refresh_interval', 1.0))
                self.refresh_random_deviation_spin.setValue(
                    client_data.get('random_deviation', 0.0))
                self.iaaa_timeout_spin.setValue(
                    client_data.get('iaaa_client_timeout', 10.0))
                self.elective_timeout_spin.setValue(
                    client_data.get('elective_client_timeout', 10.0))
                self.pool_size_spin.setValue(
                    client_data.get('elective_client_pool_size', 5))
                self.max_life_spin.setValue(
                    client_data.get('elective_client_max_life', 100))
                self.login_loop_interval_spin.setValue(
                    client_data.get('login_loop_interval', 1.0))
                self.print_mutex_check.setChecked(
                    client_data.get('print_mutex_rules', False))
                self.debug_request_check.setChecked(
                    client_data.get('debug_print_request', False))
                self.debug_dump_check.setChecked(
                    client_data.get('debug_dump_request', False))

            # 加载监控设置
            if 'monitor' in config_data:
                monitor_data = config_data['monitor']
                self.monitor_host_edit.setText(
                    monitor_data.get('host', 'localhost'))
                self.monitor_port_spin.setValue(monitor_data.get('port', 5000))

            # 加载通知设置
            if 'notification' in config_data:
                notification_data = config_data['notification']
                self.yanxx_voice_check.setChecked(
                    notification_data.get('yanxx_voice', False))
                self.yanxx_weixin_check.setChecked(
                    notification_data.get('yanxx_weixin', False))
                self.yanxx_weixin_user_edit.setText(
                    notification_data.get('yanxx_weixin_user', ''))

            # 加载API密钥设置
            if 'apikey' in config_data:
                apikey_data = config_data['apikey']
                self.username_edit.setText(apikey_data.get('username', ''))
                self.apikey_password_edit.setText(
                    apikey_data.get('password', ''))
                self.recognition_type_edit.setText(
                    apikey_data.get('RecognitionTypeid', ''))

            # 加载课程配置
            if 'courses' in config_data:
                self.courses_data = config_data['courses']

            # 加载互斥规则
            if 'mutex' in config_data:
                self.mutex_data = config_data['mutex']

            # 加载延迟规则
            if 'delay' in config_data:
                self.delay_data = config_data['delay']

            # 更新课程配置界面
            self.load_course_config()

            # 更新统计信息
            self.update_config_stats()

            # 连接自动保存信号
            self.setup_autosave_connections()

        except Exception as e:
            if self.log_display:
                self.log_display.add_log(f"加载配置文件失败: {str(e)}")
            QMessageBox.warning(self, "警告", f"加载配置文件失败: {str(e)}")

    def setup_autosave_connections(self):
        """设置自动保存的信号连接"""
        # 用户设置
        self.student_id_edit.editingFinished.connect(
            self.save_non_course_configs)
        self.password_edit.editingFinished.connect(
            self.save_non_course_configs)
        self.dual_degree_check.stateChanged.connect(
            self.save_non_course_configs)
        self.identity_combo.currentIndexChanged.connect(
            self.save_non_course_configs)

        # 客户端设置
        self.supply_cancel_page_spin.valueChanged.connect(
            self.save_non_course_configs)
        self.refresh_interval_spin.valueChanged.connect(
            self.save_non_course_configs)
        self.refresh_random_deviation_spin.valueChanged.connect(
            self.save_non_course_configs)
        self.iaaa_timeout_spin.valueChanged.connect(
            self.save_non_course_configs)
        self.elective_timeout_spin.valueChanged.connect(
            self.save_non_course_configs)
        self.pool_size_spin.valueChanged.connect(self.save_non_course_configs)
        self.max_life_spin.valueChanged.connect(self.save_non_course_configs)
        self.login_loop_interval_spin.valueChanged.connect(
            self.save_non_course_configs)
        self.print_mutex_check.stateChanged.connect(
            self.save_non_course_configs)
        self.debug_request_check.stateChanged.connect(
            self.save_non_course_configs)
        self.debug_dump_check.stateChanged.connect(
            self.save_non_course_configs)

        # 监控设置
        self.monitor_host_edit.editingFinished.connect(
            self.save_non_course_configs)
        self.monitor_port_spin.valueChanged.connect(
            self.save_non_course_configs)

        # 通知设置
        self.yanxx_voice_check.stateChanged.connect(
            self.save_non_course_configs)
        self.yanxx_weixin_check.stateChanged.connect(
            self.save_non_course_configs)
        self.yanxx_weixin_user_edit.editingFinished.connect(
            self.save_non_course_configs)

        # 验证码识别设置
        self.username_edit.editingFinished.connect(
            self.save_non_course_configs)
        self.apikey_password_edit.editingFinished.connect(
            self.save_non_course_configs)
        self.recognition_type_edit.editingFinished.connect(
            self.save_non_course_configs)
        self.local_model_radio.toggled.connect(self.save_non_course_configs)
        self.tt_platform_radio.toggled.connect(self.save_non_course_configs)
        self.custom_system_radio.toggled.connect(self.save_non_course_configs)

    def save_non_course_configs(self):
        """保存非课程相关配置"""
        if not self.autosave_enabled:
            return

        try:
            config_data = self.config_manager.load_config()

            # 更新非课程配置部分
            config_data['user'] = self.get_user_config()
            config_data['client'] = self.get_client_config()
            config_data['monitor'] = self.get_monitor_config()
            config_data['notification'] = self.get_notification_config()
            config_data['apikey'] = self.get_apikey_config()

            # 保存配置
            self.config_manager.save_config(config_data)
            self.update_save_status("系统设置已自动保存")

        except Exception as e:
            self.update_save_status(f"自动保存失败: {str(e)}", error=True)
            if self.log_display:
                self.log_display.add_log(f"自动保存失败: {str(e)}")

    def save_course_configs(self):
        """保存课程相关配置"""
        try:
            config_data = self.config_manager.load_config()

            # 更新课程配置部分
            config_data['courses'] = self.courses_data
            config_data['mutex'] = self.mutex_data
            config_data['delay'] = self.delay_data

            # 保存配置
            self.config_manager.save_config(config_data)
            self.update_save_status("课程设置已保存")
            self.update_config_stats()

        except Exception as e:
            self.update_save_status(f"课程设置保存失败: {str(e)}", error=True)
            if self.log_display:
                self.log_display.add_log(f"课程设置保存失败: {str(e)}")

    def save_all_configs(self):
        """手动保存所有配置"""
        try:
            config_data = {}

            # 收集所有配置
            config_data['user'] = self.get_user_config()
            config_data['client'] = self.get_client_config()
            config_data['monitor'] = self.get_monitor_config()
            config_data['notification'] = self.get_notification_config()
            config_data['apikey'] = self.get_apikey_config()
            config_data['courses'] = self.courses_data
            config_data['mutex'] = self.mutex_data
            config_data['delay'] = self.delay_data

            # 保存配置
            self.config_manager.save_config(config_data)
            self.update_save_status("所有设置已手动保存")
            self.update_config_stats()

            QMessageBox.information(self, "成功", "配置文件保存成功！")

        except Exception as e:
            self.update_save_status(f"保存失败: {str(e)}", error=True)
            QMessageBox.critical(self, "错误", f"保存配置文件失败: {str(e)}")

    # 各个辅助保存函数
    def get_user_config(self):
        """获取用户配置数据"""
        return {
            'student_id': self.student_id_edit.text(),
            'password': self.password_edit.text(),
            'dual_degree': self.dual_degree_check.isChecked(),
            'identity': self.identity_combo.currentText()
        }

    def get_client_config(self):
        return {
            'supply_cancel_page': self.supply_cancel_page_spin.value(),
            'refresh_interval': self.refresh_interval_spin.value(),
            'random_deviation': self.refresh_random_deviation_spin.value(),
            'iaaa_client_timeout': self.iaaa_timeout_spin.value(),
            'elective_client_timeout': self.elective_timeout_spin.value(),
            'elective_client_pool_size': self.pool_size_spin.value(),
            'elective_client_max_life': self.max_life_spin.value(),
            'login_loop_interval': self.login_loop_interval_spin.value(),
            'print_mutex_rules': self.print_mutex_check.isChecked(),
            'debug_print_request': self.debug_request_check.isChecked(),
            'debug_dump_request': self.debug_dump_check.isChecked()
        }

    def get_monitor_config(self):
        return {
            'host': self.monitor_host_edit.text(),
            'port': self.monitor_port_spin.value()
        }

    def get_notification_config(self):
        return {
            'yanxx_voice': self.yanxx_voice_check.isChecked(),
            'yanxx_weixin': self.yanxx_weixin_check.isChecked(),
            'yanxx_weixin_user': self.yanxx_weixin_user_edit.text(),
        }

    def get_apikey_config(self):
        return {
            'username': self.username_edit.text(),
            'password': self.apikey_password_edit.text(),
            'RecognitionTypeid': self.recognition_type_edit.text()
        }

    # 状态更新标签
    def update_save_status(self, message, error=False):
        """更新保存状态标签，包括时间戳"""
        # 获取当前时间并格式化为字符串
        current_time = datetime.now().strftime("%H:%M:%S")
        
        if error:
            status_text = f"⚠ {message} [{current_time}]"
            self.save_status_label.setStyleSheet("""
                QLabel {
                    color: #dc3545;
                    font-size: 10pt;
                    padding: 8px 12px;
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 4px;
                    margin: 5px 0;
                }
            """)
        else:
            status_text = f"✓ {message} [{current_time}]"
            self.save_status_label.setStyleSheet("""
                QLabel {
                    color: #155724;
                    font-size: 10pt;
                    padding: 8px 12px;
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 4px;
                    margin: 5px 0;
                }
            """)
        
        self.save_status_label.setText(status_text)
        self.last_save_time = datetime.now()
        
        # 5秒后自动清除成功状态
        if not error:
            QTimer.singleShot(5000, self.clear_success_status)
    
    def clear_success_status(self):
        """清除成功状态，只保留最后保存时间"""
        if self.last_save_time:
            last_save_str = self.last_save_time.strftime("%H:%M:%S")
            self.save_status_label.setText(f"最后保存于: {last_save_str}")
            self.save_status_label.setStyleSheet("""
                QLabel {
                    color: #6c757d;
                    font-size: 10pt;
                    padding: 8px 12px;
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    margin: 5px 0;
                }
            """)

    # 各标签页创建
    # 创建带提示图标的标签函数
    # help_icon = QIcon(":/icons/help_icon.png")
    def create_label_with_tooltip(self, text, tooltip):
        hbox = QHBoxLayout()
        label = QLabel(text)
        # 创建帮助按钮
        help_btn = QPushButton("?")
        help_btn.setFixedSize(20, 20)
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        help_btn.setToolTip("点击查看详细提示")
        help_btn.clicked.connect(lambda: QMessageBox.information(self, "填写提示", tooltip))
    
        hbox.addWidget(label)
        hbox.addWidget(help_btn)
        hbox.addStretch()  # 添加弹性空间
        hbox.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setLayout(hbox)
        return container

    def create_system_settings_widget(self):
        """创建系统设置页面"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)  # 增加行距，避免堆在一起

        # 用户设置
        user_tab = self.create_user_tab()
        layout.addWidget(user_tab)

        # 客户端设置
        client_tab = self.create_client_tab()
        layout.addWidget(client_tab)

        # 监控设置
        monitor_tab = self.create_monitor_tab()
        layout.addWidget(monitor_tab)

        # 通知设置
        notification_tab = self.create_notification_tab()
        layout.addWidget(notification_tab)

        # 验证码识别设置
        apikey_tab = self.create_apikey_tab()
        layout.addWidget(apikey_tab)

        widget.setLayout(layout)
        return widget

    def create_user_tab(self):
        """创建用户设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        group = QGroupBox("用户认证设置")
        group_layout = QFormLayout()
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(10)

        self.student_id_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.dual_degree_check = QCheckBox()
        self.identity_combo = QComboBox()
        self.identity_combo.addItems(["bzx", "bfx"])

        group_layout.addRow(self.create_label_with_tooltip(
            "IAAA账号:", "请输入您的IAAA认证账号，如: 2500011111"), self.student_id_edit)
        group_layout.addRow(self.create_label_with_tooltip(
            "IAAA密码:", "请输入您的IAAA认证密码"), self.password_edit)
        group_layout.addRow(self.create_label_with_tooltip(
            "是否为双学位账号", "只要你的账号在登录时需要选择“主修/辅双”身份，此处就需要勾选"), self.dual_degree_check)
        # 创建身份选择容器（初始隐藏）
        self.identity_container = QWidget()
        identity_layout = QFormLayout()
        identity_layout.addRow(self.create_label_with_tooltip(
            "身份", "双学位账号登录身份，bzx主修，bfx辅双"), self.identity_combo)
        self.identity_container.setLayout(identity_layout)
        self.identity_container.setVisible(False)  # 初始隐藏
        group_layout.addRow("",self.identity_container)  # 添加身份容器
        # 连接双学位复选框状态改变信号
        self.dual_degree_check.stateChanged.connect(self.toggle_identity_visibility)

        group.setLayout(group_layout)
        layout.addWidget(group)

        widget.setLayout(layout)
        return widget
    
    def toggle_identity_visibility(self, state):
        """根据双学位复选框状态显示/隐藏身份选择"""
        self.identity_container.setVisible(state == Qt.CheckState.Checked.value)

    def create_client_tab(self):
        """创建客户端设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        group = QGroupBox("客户端参数设置")
        group_layout = QFormLayout()
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(10)

        self.supply_cancel_page_spin = QSpinBox()
        self.supply_cancel_page_spin.setRange(1, 100)
        self.refresh_interval_spin = QDoubleSpinBox()
        self.refresh_interval_spin.setRange(0.1, 10.0)
        self.refresh_interval_spin.setSingleStep(0.1)
        self.refresh_random_deviation_spin = QDoubleSpinBox()
        self.refresh_random_deviation_spin.setRange(0.0, 5.0)
        self.refresh_random_deviation_spin.setSingleStep(0.1)
        self.iaaa_timeout_spin = QDoubleSpinBox()
        self.iaaa_timeout_spin.setRange(1.0, 60.0)
        self.elective_timeout_spin = QDoubleSpinBox()
        self.elective_timeout_spin.setRange(1.0, 60.0)
        self.pool_size_spin = QSpinBox()
        self.pool_size_spin.setRange(1, 100)
        self.max_life_spin = QSpinBox()
        self.max_life_spin.setRange(1, 1000)
        self.login_loop_interval_spin = QDoubleSpinBox()
        self.login_loop_interval_spin.setRange(0.1, 10.0)
        self.login_loop_interval_spin.setSingleStep(0.1)
        self.print_mutex_check = QCheckBox()
        self.debug_request_check = QCheckBox()
        self.debug_dump_check = QCheckBox()

        group_layout.addRow(self.create_label_with_tooltip(
            "补退选页数:", "待刷课程处在“补退选”选课计划的第几页"), self.supply_cancel_page_spin)
        group_layout.addRow(self.create_label_with_tooltip(
            "刷新间隔(秒):", "每次循环后的暂停时间"), self.refresh_interval_spin)
        group_layout.addRow(self.create_label_with_tooltip(
            "随机偏差(秒):", "偏移量分数，如果设置为 <= 0 的值，则视为 0"), self.refresh_random_deviation_spin)
        group_layout.addRow(self.create_label_with_tooltip(
            "IAAA超时(秒):", "IAAA 客户端最长请求超时"), self.iaaa_timeout_spin)
        group_layout.addRow(self.create_label_with_tooltip(
            "选课超时(秒):", "elective 客户端最长请求超时"), self.elective_timeout_spin)
        group_layout.addRow(self.create_label_with_tooltip(
            "连接池大小:", "最多同时保持几个 elective 的有效会话（同一 IP 下最多为 5）"), self.pool_size_spin)
        group_layout.addRow(self.create_label_with_tooltip(
            "最大生命周期(秒):", "elvetive 客户端的存活时间，设置为 -1 则存活时间为无限长"), self.max_life_spin)
        group_layout.addRow(self.create_label_with_tooltip(
            "登录循环间隔(秒):", "IAAA 登录线程每回合结束后的等待时间"), self.login_loop_interval_spin)
        group_layout.addRow(self.create_label_with_tooltip(
            "打印互斥规则:", "是否在每次循环时打印完整的互斥规则列表"), self.print_mutex_check)
        group_layout.addRow(self.create_label_with_tooltip(
            "调试请求:", "是否打印请求细节"), self.debug_request_check)
        group_layout.addRow(self.create_label_with_tooltip(
            "调试转储:", "是否将重要接口的请求以日志的形式记录到本地（包括补退选页、提交选课等接口）"), self.debug_dump_check)

        group.setLayout(group_layout)
        layout.addWidget(group)

        widget.setLayout(layout)
        return widget

    def create_monitor_tab(self):
        """创建监控设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        group = QGroupBox("监控参数设置")
        group_layout = QFormLayout()
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(10)

        self.monitor_host_edit = QLineEdit()
        self.monitor_port_spin = QSpinBox()
        self.monitor_port_spin.setRange(1, 65535)

        group_layout.addRow("提示", QLabel("如非专业人员，请勿修改此页配置！"))
        group_layout.addRow("监控主机:", self.monitor_host_edit)
        group_layout.addRow("监控端口:", self.monitor_port_spin)

        group.setLayout(group_layout)
        layout.addWidget(group)

        widget.setLayout(layout)
        return widget

    def create_notification_tab(self):
        """创建通知设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        group = QGroupBox("通知设置")
        group_layout = QFormLayout()
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(10)

        self.yanxx_voice_check = QCheckBox()
        self.yanxx_weixin_check = QCheckBox()
        self.yanxx_weixin_user_edit = QLineEdit()

        group_layout.addRow(self.create_label_with_tooltip(
            "语音提醒：", "是否开启语音提醒"), self.yanxx_voice_check)
        group_layout.addRow(self.create_label_with_tooltip(
            "微信提醒与控制：", "是否开启微信提醒与控制"), self.yanxx_weixin_check)
         # 创建微信昵称容器（初始隐藏）
        self.yanxx_weixin_user_container = QWidget()
        yanxx_weixin_user_layout = QFormLayout()
        yanxx_weixin_user_layout.addRow(self.create_label_with_tooltip(
            "监听微信账号昵称：", "请输入进行微信提醒与控制的账号的昵称"), self.yanxx_weixin_user_edit)
        test_button = QPushButton("测试通知功能")
        test_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                font-size: 11pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:pressed {
                background-color: #117a8b;
            }
        """)
        test_button.clicked.connect(self.start_notification_test)
        yanxx_weixin_user_layout.addRow(test_button)
        self.yanxx_weixin_user_container.setLayout(yanxx_weixin_user_layout)
        self.yanxx_weixin_user_container.setVisible(False)  # 初始隐藏
        group_layout.addRow("",self.yanxx_weixin_user_container)  # 添加微信昵称容器
        # 连接微信监听状态复选框状态改变信号
        self.yanxx_weixin_check.stateChanged.connect(self.yanxx_weixin_user_visibility)

        group.setLayout(group_layout)
        layout.addWidget(group)

        widget.setLayout(layout)
        return widget
    
    def yanxx_weixin_user_visibility(self, state):
        """根据双学位复选框状态显示/隐藏微信昵称"""
        self.yanxx_weixin_user_container.setVisible(state == Qt.CheckState.Checked.value)

    def start_notification_test(self):
        """启动通知测试进程"""
        # 这里添加启动通知测试进程的代码
        # 在实际应用中，这里会调用通知系统的测试功能
        
        # 示例：模拟测试过程
        QMessageBox.information(self, "通知测试", "正在启动通知测试进程...")
        success = False
        try:
            from wxauto4 import WeChat
            wx = WeChat()
            wx.SendMsg(self.yanxx_weixin_user_edit.text(),"[系统自检]信息发送测试")
            wx.StopListening()
            del wx
        except Exception as e:
            print(e)
        
        if success:
            QMessageBox.information(self, "测试成功", "通知功能测试成功！")
        else:
            QMessageBox.warning(self, "测试失败", "通知功能测试失败，请检查配置")


    def create_apikey_tab(self):
        """创建验证码识别API密钥设置标签页"""
        widget = QWidget()
        main_layout = QVBoxLayout()

        # 创建选项组
        options_group = QGroupBox("验证码识别系统选择")
        options_layout = QVBoxLayout()

        # 创建单选按钮
        self.local_model_radio = QRadioButton("内置本地识别模型")
        self.tt_platform_radio = QRadioButton("TT商用识别平台")
        self.custom_system_radio = QRadioButton("自定义验证码识别系统")

        # 默认选择第一个选项
        self.tt_platform_radio.setChecked(True)

        # 将单选按钮添加到布局
        options_layout.addWidget(self.local_model_radio)
        options_layout.addWidget(self.tt_platform_radio)
        options_layout.addWidget(self.custom_system_radio)
        options_group.setLayout(options_layout)

        # 创建堆叠窗口用于显示不同选项对应的内容
        self.apikey_stacked_widget = QStackedWidget()

        # 本地识别模型页面
        local_widget = QWidget()
        local_layout = QVBoxLayout()
        local_label = QLabel("使用内置本地识别模型，无需额外配置。\n本地模型正在开发中，请选择其他模型！")
        local_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-style: italic;
                padding: 10px;
            }
        """)
        local_layout.addWidget(local_label)
        local_widget.setLayout(local_layout)

        # TT商用识别平台页面
        tt_widget = QWidget()
        tt_layout = QFormLayout()
        self.username_edit = QLineEdit()
        self.apikey_password_edit = QLineEdit()
        self.apikey_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.recognition_type_edit = QLineEdit()

        # TT识图api表单
        tt_layout.addRow("用户名:", self.username_edit)
        tt_layout.addRow("密码:", self.apikey_password_edit)
        tt_layout.addRow("识别类型ID:", self.recognition_type_edit)
        tt_widget.setLayout(tt_layout)
        # 占位空行
        tt_layout.addRow(QLabel())
        # TT识图API获取指引
        api_link = QLabel("<a href=\"https://www.ttshitu.com/user/password.html\">点击前往获取TT识图API↗</a>")
        api_link.setOpenExternalLinks(True)  # 允许打开外部链接
        api_link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)  # 启用链接交互
        tt_layout.addRow(api_link)

        # 自定义验证码识别系统页面
        custom_widget = QWidget()
        custom_layout = QVBoxLayout()
        custom_label = QLabel("自定义验证码识别系统配置页面\n验证码识别接口正在开发中，请选择其他模型！")
        custom_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-style: italic;
                padding: 10px;
            }
        """)
        custom_layout.addWidget(custom_label)
        custom_widget.setLayout(custom_layout)

        # 将各个页面添加到堆叠窗口
        self.apikey_stacked_widget.addWidget(local_widget)
        self.apikey_stacked_widget.addWidget(tt_widget)
        self.apikey_stacked_widget.addWidget(custom_widget)

        # 栈窗口默认显示TT识别
        self.apikey_stacked_widget.setCurrentIndex(1)

        # 连接单选按钮的信号到槽函数
        self.local_model_radio.toggled.connect(self.on_apikey_option_changed)
        self.tt_platform_radio.toggled.connect(self.on_apikey_option_changed)
        self.custom_system_radio.toggled.connect(self.on_apikey_option_changed)

        # 将组件添加到主布局
        main_layout.addWidget(options_group)
        main_layout.addWidget(self.apikey_stacked_widget)
        main_layout.addStretch(1)  # 添加伸缩因子使内容顶部对齐

        widget.setLayout(main_layout)
        return widget

    def on_apikey_option_changed(self):
        """当API密钥选项改变时的槽函数"""
        if self.local_model_radio.isChecked():
            self.apikey_stacked_widget.setCurrentIndex(0)
        elif self.tt_platform_radio.isChecked():
            self.apikey_stacked_widget.setCurrentIndex(1)
        elif self.custom_system_radio.isChecked():
            self.apikey_stacked_widget.setCurrentIndex(2)

    def create_course_tab(self):
        """创建课程设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 课程部分
        course_tab = self.create_course_list_tab()
        layout.addWidget(course_tab)

        # 互斥规则部分
        mutex_tab = self.create_mutex_list_tab()
        layout.addWidget(mutex_tab)

        # 延迟规则部分
        delay_tab = self.create_delay_list_tab()
        layout.addWidget(delay_tab)

        widget.setLayout(layout)
        return widget

    def create_course_list_tab(self):
        """创建课程列表标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 说明标签
        info_label = QLabel("课程配置：每个课程包含ID、名称、班级号和学院信息。\n在此添加要刷取的课程")
        info_label.setStyleSheet("""
            QLabel {
                background-color: #e7f3ff;
                border: 1px solid #b3d9ff;
                border-radius: 6px;
                padding: 12px;
                margin: 5px;
                color: #004085;
                font-size: 10pt;
            }
        """)
        layout.addWidget(info_label)

        # 课程列表
        self.course_list_widget = QWidget()
        self.course_list_layout = QVBoxLayout()
        self.course_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.course_list_widget.setLayout(self.course_list_layout)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.course_list_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)

        layout.addWidget(scroll_area)

        # 添加课程按钮
        button_layout = QHBoxLayout()
        add_course_btn = QPushButton("添加课程")
        add_course_btn.clicked.connect(self.add_course)
        add_course_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 11pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        button_layout.addWidget(add_course_btn)
        fast_add_course_btn = QPushButton("快捷输入")
        fast_add_course_btn.clicked.connect(self.fast_add_course)
        fast_add_course_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 11pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        button_layout.addWidget(fast_add_course_btn)

        layout.addLayout(button_layout)

        widget.setLayout(layout)
        return widget

    def create_mutex_list_tab(self):
        """创建互斥规则列表标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 说明标签
        info_label = QLabel("互斥规则：指定哪些课程不能同时选择。同一个互斥规则下选上一门课后则不会再选择其他课程")
        info_label.setStyleSheet("""
            QLabel {
                background-color: #fff3e0;
                border: 1px solid #ffc107;
                border-radius: 6px;
                padding: 12px;
                margin: 5px;
                color: #856404;
                font-size: 10pt;
            }
        """)
        layout.addWidget(info_label)

        # 互斥规则列表
        self.mutex_list_widget = QWidget()
        self.mutex_list_layout = QVBoxLayout()
        self.mutex_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.mutex_list_widget.setLayout(self.mutex_list_layout)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.mutex_list_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)

        layout.addWidget(scroll_area)

        # 添加互斥规则按钮
        add_mutex_btn = QPushButton("添加互斥规则")
        add_mutex_btn.clicked.connect(self.add_mutex_rule)
        add_mutex_btn.setStyleSheet("""
            QPushButton {
                background-color: #fd7e14;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 11pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e8590c;
            }
            QPushButton:pressed {
                background-color: #d9480f;
            }
        """)

        layout.addWidget(add_mutex_btn)

        widget.setLayout(layout)
        return widget

    def create_delay_list_tab(self):
        """创建延迟规则列表标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 说明标签
        info_label = QLabel("延迟规则：指定课程在达到特定人数后才开始选课")
        info_label.setStyleSheet("""
            QLabel {
                background-color: #e8f5e8;
                border: 1px solid #28a745;
                border-radius: 6px;
                padding: 12px;
                margin: 5px;
                color: #155724;
                font-size: 10pt;
            }
        """)
        layout.addWidget(info_label)

        # 延迟规则列表
        self.delay_list_widget = QWidget()
        self.delay_list_layout = QVBoxLayout()
        self.delay_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.delay_list_widget.setLayout(self.delay_list_layout)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.delay_list_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)

        layout.addWidget(scroll_area)

        # 添加延迟规则按钮
        add_delay_btn = QPushButton("添加延迟规则")
        add_delay_btn.clicked.connect(self.add_delay_rule)
        add_delay_btn.setStyleSheet("""
            QPushButton {
                background-color: #20c997;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 11pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #17a2b8;
            }
            QPushButton:pressed {
                background-color: #138496;
            }
        """)

        layout.addWidget(add_delay_btn)

        widget.setLayout(layout)
        return widget

    def create_course_item(self, course_id, course_name, class_no, school):
        """创建课程条目组件"""
        item_widget = QFrame()
        item_widget.setFrameStyle(QFrame.Shape.Box)
        item_widget.setLineWidth(1)
        item_widget.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        item_layout = QHBoxLayout()
        item_layout.setContentsMargins(10, 10, 10, 10)

        # 课程信息标签
        info_label = QLabel(
            f"<b>ID:</b> {course_id}<br><b>课程名:</b> {course_name}<br><b>班号:</b> {class_no}<br><b>开课院系:</b> {school}")
        info_label.setStyleSheet("QLabel { color: #495057; }")
        info_label.setWordWrap(True)

        # 按钮容器
        button_layout = QVBoxLayout()
        # 编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(lambda: self.edit_course(
            course_id, course_name, class_no, school))
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)

        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(lambda: self.delete_course(course_id))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)

        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()

        item_layout.addWidget(info_label, 1)
        item_layout.addLayout(button_layout)

        item_widget.setLayout(item_layout)
        return item_widget

    def create_mutex_item(self, mutex_id, courses):
        """创建互斥规则条目组件"""
        item_widget = QFrame()
        item_widget.setFrameStyle(QFrame.Shape.Box)
        item_widget.setLineWidth(1)
        item_widget.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        item_layout = QHBoxLayout()
        item_layout.setContentsMargins(10, 10, 10, 10)

        # 互斥规则信息标签
        courses_text = ", ".join(courses)
        info_label = QLabel(f"<b>{mutex_id}:</b> {courses_text}")
        info_label.setStyleSheet("QLabel { color: #856404; }")
        info_label.setWordWrap(True)

        # 按钮容器
        button_layout = QVBoxLayout()
        # 编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(
            lambda: self.edit_mutex_rule(mutex_id, courses))
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)

        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(lambda: self.delete_mutex_rule(mutex_id))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)

        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()

        item_layout.addWidget(info_label, 1)
        item_layout.addLayout(button_layout)

        item_widget.setLayout(item_layout)
        return item_widget

    def create_delay_item(self, delay_id, course_id, threshold):
        """创建延迟规则条目组件"""
        item_widget = QFrame()
        item_widget.setFrameStyle(QFrame.Shape.Box)
        item_widget.setLineWidth(1)
        item_widget.setStyleSheet("""
            QFrame {
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        item_layout = QHBoxLayout()
        item_layout.setContentsMargins(10, 10, 10, 10)

        # 延迟规则信息标签
        info_label = QLabel(
            f"<b>{delay_id}:</b> 课程 {course_id} 在人数达到 {threshold} 后开始选课")
        info_label.setStyleSheet("QLabel { color: #155724; }")
        info_label.setWordWrap(True)

        # 按钮容器
        button_layout = QVBoxLayout()
        # 编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(lambda: self.edit_delay_rule(
            delay_id, course_id, threshold))
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)

        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(lambda: self.delete_delay_rule(delay_id))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)

        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()

        item_layout.addWidget(info_label, 1)
        item_layout.addLayout(button_layout)

        item_widget.setLayout(item_layout)
        return item_widget

    def add_course(self):
        """添加课程"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("添加课程")
        dialog.setModal(True)

        layout = QFormLayout()

        course_id_edit = QLineEdit()
        course_name_edit = QLineEdit()
        class_no_edit = QLineEdit()
        school_edit = QLineEdit()

        layout.addRow("课程ID（自定义，用于后续规则识别）:", course_id_edit)
        layout.addRow("课程名称（须与选课网完全一致）:", course_name_edit)
        layout.addRow("班级号（数字，须与选课网一致）:", class_no_edit)
        layout.addRow("开课院系（须与选课网完全一致）:", school_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout.addRow(buttons)
        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            course_id = course_id_edit.text().strip()
            course_name = course_name_edit.text().strip()
            class_no = class_no_edit.text().strip()
            school = school_edit.text().strip()

            if course_id and course_name and class_no and school:
                if course_id not in self.courses_data.keys():
                    # 创建课程条目
                    course_item = self.create_course_item(
                        course_id, course_name, class_no, school)
                    self.course_list_layout.addWidget(course_item)

                    # 更新统计信息
                    self.update_config_stats()

                    # 保存到内部数据结构
                    if not hasattr(self, 'courses_data'):
                        self.courses_data = {}
                    self.courses_data[course_id] = {
                        'name': course_name,
                        'class': class_no,
                        'school': school
                    }
                    self.save_course_configs()
                else:
                    QMessageBox.warning(self, "警告", "该课程ID已被使用！请更换其他ID")
            else:
                QMessageBox.warning(self, "警告", "请填写所有字段！")

    def fast_add_course(self):
        """快捷添加课程 - 从剪贴板批量导入"""

        # 尝试从剪贴板获取数据
        try:
            clipboard_text = pyperclip.paste().strip()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"访问剪贴板失败: {str(e)}")
            return

        if not clipboard_text:
            QMessageBox.warning(self, "提示", "剪贴板中没有找到有效数据")
            return

        # 使用正则表达式解析课程信息
        # 此处信息可能需要随选课网变化而更新！
        # 2025秋季选课网复制下来的格式为
        # 当前利用学分与周学时作为标志进行提取（两个连续的浮点数做每行定位）
        clipboard_text = re.split(r'[\t\n]+', clipboard_text)
        matches = []
        for i in range(len(clipboard_text)):
            # 匹配"x.0"形式，如4.0 12.0
            if re.fullmatch(r'^\d+\.0$', clipboard_text[i]) and i+4 < len(clipboard_text) and i-2 >= 0:
                if re.fullmatch(r'^\d+\.0$', clipboard_text[i+1]):
                    matches.append(
                        (clipboard_text[i-2].strip(), clipboard_text[i+3].strip(), clipboard_text[i+4].strip()))

        if not matches:
            QMessageBox.warning(
                self, "提示", "未能从剪贴板中识别出课程信息\n请检查是否正确复制了选课网信息，或使用手动输入进行添加\n注意：若当前版本非本学期版本，可能由于选课网更改导致无法正确检测")
            return

        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("批量添加课程 - 确认信息")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout()

        # 创建表格
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["课程ID", "课程名称", "班级号", "开课院系", "操作"])
        table.setRowCount(len(matches))

        # 填充表格数据
        for row, (course_name, class_no, school) in enumerate(matches):
            # 自动生成课程ID: 课程名前2字拼音首字母+班级号
            course_id = self.generate_course_id(course_name, class_no)

            table.setItem(row, 0, QTableWidgetItem(course_id))
            table.setItem(row, 1, QTableWidgetItem(course_name))
            table.setItem(row, 2, QTableWidgetItem(class_no))
            table.setItem(row, 3, QTableWidgetItem(school))

            # 添加删除按钮
            delete_btn = QPushButton("删除")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 4px;
                    border-radius: 3px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            delete_btn.setProperty("row", row)  # 存储行号
            delete_btn.clicked.connect(lambda _, r=row: self.delete_table_row(table, r))
            table.setCellWidget(row, 4, delete_btn)

        table.resizeColumnsToContents()
        layout.addWidget(table)

        # 添加按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            added_count = 0
            duplicate_ids = []

            for row in range(table.rowCount()):
                course_id = table.item(row, 0).text().strip()
                course_name = table.item(row, 1).text().strip()
                class_no = table.item(row, 2).text().strip()
                school = table.item(row, 3).text().strip()

                if course_id and course_name and class_no and school:
                    if course_id not in self.courses_data.keys():
                        # 创建课程条目
                        course_item = self.create_course_item(
                            course_id, course_name, class_no, school)
                        self.course_list_layout.addWidget(course_item)

                        # 保存到内部数据结构
                        if not hasattr(self, 'courses_data'):
                            self.courses_data = {}
                        self.courses_data[course_id] = {
                            'name': course_name,
                            'class': class_no,
                            'school': school
                        }
                        added_count += 1
                    else:
                        duplicate_ids.append(course_id)

            # 更新统计信息
            if added_count > 0:
                self.update_config_stats()

            # 保存导入信息
            self.save_course_configs()

            # 显示导入结果
            msg = f"成功添加 {added_count} 门课程"
            if duplicate_ids:
                msg += f"\n以下课程ID已存在，未重复添加: {', '.join(duplicate_ids)}"
            QMessageBox.information(self, "导入结果", msg)

    # 快捷添加中的行删除功能
    def delete_table_row(self, table, row):
        """删除表格中的指定行"""
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除第{row+1}行的课程吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 删除行
            table.removeRow(row)
            
            # 更新按钮的行号属性
            for r in range(table.rowCount()):
                if r >= row:
                    btn = table.cellWidget(r, 4)
                    if btn:
                        # 断开旧连接
                        try:
                            btn.clicked.disconnect()
                        except:
                            pass
                        # 重新连接新行号
                        btn.clicked.connect(lambda _, row=row, table=table: self.delete_table_row(table, row))

    def generate_course_id(self, course_name, class_no):
        """生成默认课程ID（中文取前2字拼音首字母+班级号）"""
        # 简单实现：取前2个汉字（如果长度足够）
        if len(course_name) >= 2:
            prefix = course_name[:2]
        else:
            prefix = course_name

        # 移除空格和特殊字符
        prefix = re.sub(r'[^\w\u4e00-\u9fff]', '', prefix)

        # 如果是中文，取拼音首字母（这里简化处理，实际应用中可以使用拼音库）
        if re.search(r'[\u4e00-\u9fff]', prefix):
            # 模拟拼音首字母 - 实际项目中应使用拼音库如pypinyin
            pinyin_initials = ''.join([c[0] for c in prefix.lower()])
        else:
            pinyin_initials = prefix.lower()[:2]

        return f"{pinyin_initials}{class_no}".lower()

    def add_mutex_rule(self):
        """添加互斥规则"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QListWidget, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("添加互斥规则")
        dialog.setModal(True)
        dialog.resize(400, 300)

        layout = QVBoxLayout()

        # 规则ID输入
        from PyQt6.QtWidgets import QHBoxLayout
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("规则ID:"))
        rule_id_edit = QLineEdit()
        id_layout.addWidget(rule_id_edit)
        layout.addLayout(id_layout)

        # 课程选择列表
        layout.addWidget(QLabel("选择互斥的课程:"))
        course_list = QListWidget()
        course_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        # 添加可选的课程
        if hasattr(self, 'courses_data'):
            for course_id in self.courses_data.keys():
                course_list.addItem(course_id)

        layout.addWidget(course_list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout.addWidget(buttons)
        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            rule_id = rule_id_edit.text().strip()
            selected_courses = [item.text()
                                for item in course_list.selectedItems()]

            if rule_id and len(selected_courses) >= 2:
                if rule_id not in self.mutex_data.keys():
                    # 创建互斥规则条目
                    mutex_item = self.create_mutex_item(
                        rule_id, selected_courses)
                    self.mutex_list_layout.addWidget(mutex_item)

                    # 更新统计信息
                    self.update_config_stats()

                    # 保存到内部数据结构
                    if not hasattr(self, 'mutex_data'):
                        self.mutex_data = {}
                    self.mutex_data[rule_id] = selected_courses
                    self.save_course_configs()
                else:
                    QMessageBox.warning(self, "警告", "该互斥规则ID已被使用！请更换其他ID")
            else:
                QMessageBox.warning(self, "警告", "请填写规则ID并选择至少2个课程！")

    def add_delay_rule(self):
        """添加延迟规则"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QComboBox, QSpinBox

        dialog = QDialog(self)
        dialog.setWindowTitle("添加延迟规则")
        dialog.setModal(True)

        layout = QFormLayout()

        delay_id_edit = QLineEdit()
        course_combo = QComboBox()
        threshold_spin = QSpinBox()
        threshold_spin.setRange(1, 1000)
        threshold_spin.setValue(10)

        # 添加可选的课程
        if hasattr(self, 'courses_data'):
            for course_id in self.courses_data.keys():
                course_combo.addItem(course_id)

        layout.addRow("规则ID:", delay_id_edit)
        layout.addRow("课程:", course_combo)
        layout.addRow("人数阈值:", threshold_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout.addRow(buttons)
        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            delay_id = delay_id_edit.text().strip()
            course_id = course_combo.currentText()
            threshold = threshold_spin.value()

            if delay_id and course_id:
                if delay_id not in self.delay_data.keys():
                    # 创建延迟规则条目
                    delay_item = self.create_delay_item(
                        delay_id, course_id, threshold)
                    self.delay_list_layout.addWidget(delay_item)

                    # 更新统计信息
                    self.update_config_stats()

                    # 保存到内部数据结构
                    if not hasattr(self, 'delay_data'):
                        self.delay_data = {}
                    self.delay_data[delay_id] = {
                        'course': course_id,
                        'threshold': threshold
                    }
                    self.save_course_configs()
                else:
                    QMessageBox.warning(self, "警告", "该延迟规则ID已被使用！请更换其他ID")
            else:
                QMessageBox.warning(self, "警告", "请填写所有字段！")

    def load_course_config(self):
        """加载课程配置"""
        try:
            config_data = self.config_manager.load_config()

            # 清空现有条目
            self.clear_all_items()

            # 初始化数据结构
            self.courses_data = {}
            self.mutex_data = {}
            self.delay_data = {}

            # 加载课程配置
            courses = config_data.get('courses', {})
            for course_id, course_data in courses.items():
                # 创建课程条目
                course_item = self.create_course_item(
                    course_id,
                    course_data.get('name', ''),
                    course_data.get('class', ''),
                    course_data.get('school', '')
                )
                self.course_list_layout.addWidget(course_item)

                # 保存到数据结构
                self.courses_data[course_id] = course_data

            # 加载互斥规则
            mutex_rules = config_data.get('mutex', {})
            for mutex_id, courses in mutex_rules.items():
                # 创建互斥规则条目
                mutex_item = self.create_mutex_item(mutex_id, courses)
                self.mutex_list_layout.addWidget(mutex_item)

                # 保存到数据结构
                self.mutex_data[mutex_id] = courses

            # 加载延迟规则
            delay_rules = config_data.get('delay', {})
            for delay_id, delay_data in delay_rules.items():
                # 创建延迟规则条目
                delay_item = self.create_delay_item(
                    delay_id,
                    delay_data.get('course', ''),
                    delay_data.get('threshold', 10)
                )
                self.delay_list_layout.addWidget(delay_item)

                # 保存到数据结构
                self.delay_data[delay_id] = delay_data

            # 更新统计信息
            self.update_config_stats()

        except Exception as e:
            if self.log_display:
                self.log_display.add_log(f"加载课程配置失败: {str(e)}")
            QMessageBox.warning(self, "警告", f"加载课程配置失败: {str(e)}")

    # 清空课程界面的所有条目（只是清除显示，不涉及删数据！）
    def clear_all_items(self):
        """清空所有条目"""
        # 清空课程列表
        while self.course_list_layout.count():
            child = self.course_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 清空互斥规则列表
        while self.mutex_list_layout.count():
            child = self.mutex_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 清空延迟规则列表
        while self.delay_list_layout.count():
            child = self.delay_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    # 清空课程相关配置（清除显示+清空数据）
    def clear_all_course_configs(self):
        """清空所有课程相关配置"""
        # 确认对话框
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有课程、互斥规则和延迟规则吗？此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 清空数据结构
            self.courses_data = {}
            self.mutex_data = {}
            self.delay_data = {}
            
            # 清空界面
            self.clear_all_items()
            
            # 保存空配置
            self.save_course_configs()
            
            # 更新统计信息
            self.update_config_stats()
            
            QMessageBox.information(self, "成功", "已清空所有课程配置！")

    def update_config_stats(self):
        """更新配置统计信息"""
        try:
            course_count = len(self.courses_data) if hasattr(
                self, 'courses_data') else 0
            mutex_count = len(self.mutex_data) if hasattr(
                self, 'mutex_data') else 0
            delay_count = len(self.delay_data) if hasattr(
                self, 'delay_data') else 0

            self.config_stats_label.setText(
                f"配置统计：{course_count} 个课程，{mutex_count} 个互斥规则，{delay_count} 个延迟规则")

        except Exception as e:
            self.config_stats_label.setText("配置统计：统计失败")

    def edit_course(self, course_id, course_name, class_no, school):
        """编辑课程"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle(f"编辑课程 {course_id}")
        dialog.setModal(True)

        layout = QFormLayout()

        course_name_edit = QLineEdit(course_name)
        class_no_edit = QLineEdit(class_no)
        school_edit = QLineEdit(school)

        layout.addRow("课程名称:", course_name_edit)
        layout.addRow("班级号:", class_no_edit)
        layout.addRow("学院:", school_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout.addRow(buttons)
        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = course_name_edit.text().strip()
            new_class = class_no_edit.text().strip()
            new_school = school_edit.text().strip()

            if new_name and new_class and new_school:
                # 更新数据结构
                self.courses_data[course_id] = {
                    'name': new_name,
                    'class': new_class,
                    'school': new_school
                }

                # 重新创建条目
                self.refresh_course_item(course_id)

                # 保存到本地
                self.save_course_configs()

                # 更新统计信息
                self.update_config_stats()
            else:
                QMessageBox.warning(self, "警告", "请填写所有字段！")

    def delete_course(self, course_id):
        """删除课程并同步清理相关规则"""
        # 收集受影响的规则
        affected_mutex_rules = self.collect_affected_mutex_rules(course_id)
        affected_delay_rules = self.collect_affected_delay_rules(course_id)

        # 构建警告信息
        warning_message = f"确定要删除课程 {course_id} 吗？"

        if affected_mutex_rules or affected_delay_rules:
            warning_message += "\n\n删除此课程将同时删除以下相关规则："

            if affected_mutex_rules:
                warning_message += f"\n\n互斥规则:\n（删除该课程后该互斥规则内课程数量<2）\n" + \
                    "\n".join(affected_mutex_rules)

            if affected_delay_rules:
                warning_message += f"\n\n延迟规则:\n" + \
                    "\n".join(affected_delay_rules)

        # 显示确认对话框
        reply = QMessageBox.question(
            self, "确认删除",
            warning_message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 从数据结构中删除课程
            if course_id in self.courses_data:
                del self.courses_data[course_id]

            # 从界面中删除课程条目
            self.remove_course_item(course_id)

            # 清理依赖此课程的互斥规则
            self.cleanup_mutex_rules(course_id)

            # 清理依赖此课程的延迟规则
            self.cleanup_delay_rules(course_id)

            # 保存到本地
            self.save_course_configs()

            # 更新统计信息
            self.update_config_stats()

            QMessageBox.information(self, "成功", f"课程 {course_id} 及相关规则已删除！")

    def collect_affected_mutex_rules(self, course_id):
        """收集依赖该课程的互斥规则"""
        affected_rules = []

        # 遍历所有互斥规则
        for mutex_id, courses in self.mutex_data.items():
            # 如果课程在该互斥规则中
            if course_id in courses and len(courses) <= 2:
                affected_rules.append(f"- 互斥规则 {mutex_id} (包含课程: {course_id})")

        return affected_rules

    def collect_affected_delay_rules(self, course_id):
        """收集依赖该课程的延迟规则"""
        affected_rules = []

        # 遍历所有延迟规则
        for delay_id, rule_data in self.delay_data.items():
            # 如果规则依赖该课程
            if 'course' in rule_data and rule_data['course'] == course_id:
                affected_rules.append(f"- 延迟规则 {delay_id} (依赖课程: {course_id})")

        return affected_rules

    def cleanup_mutex_rules(self, course_id):
        """清理依赖该课程的互斥规则"""
        # 收集需要删除的互斥规则ID
        mutex_ids_to_remove = []

        # 收集需要更新的互斥规则（移除课程引用）
        mutex_to_update = {}

        # 遍历所有互斥规则
        for mutex_id, courses in self.mutex_data.items():
            # 如果课程在该互斥规则中
            if course_id in courses:
                # 创建一个不包含该课程的新课程列表
                new_courses = [c for c in courses if c != course_id]

                # 如果移除后课程数少于2，则删除该规则
                if len(new_courses) < 2:
                    mutex_ids_to_remove.append(mutex_id)
                else:
                    # 否则更新规则
                    mutex_to_update[mutex_id] = new_courses

        # 删除无效的互斥规则
        for mutex_id in mutex_ids_to_remove:
            if mutex_id in self.mutex_data:
                del self.mutex_data[mutex_id]
            # 从界面删除条目
            self.remove_mutex_item(mutex_id)

        # 更新需要修改的互斥规则
        for mutex_id, new_courses in mutex_to_update.items():
            self.mutex_data[mutex_id] = new_courses
            # 刷新界面显示
            self.refresh_mutex_item(mutex_id)

    def cleanup_delay_rules(self, course_id):
        """清理依赖该课程的延迟规则"""
        # 收集需要删除的延迟规则ID
        delay_ids_to_remove = []

        # 遍历所有延迟规则
        for delay_id, rule_data in self.delay_data.items():
            # 如果规则依赖该课程
            if 'course' in rule_data and rule_data['course'] == course_id:
                delay_ids_to_remove.append(delay_id)

        # 删除规则
        for delay_id in delay_ids_to_remove:
            if delay_id in self.delay_data:
                del self.delay_data[delay_id]
            # 从界面删除条目
            self.remove_delay_item(delay_id)

    def edit_mutex_rule(self, mutex_id, courses):
        """编辑互斥规则"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QListWidget, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle(f"编辑互斥规则 {mutex_id}")
        dialog.setModal(True)
        dialog.resize(400, 300)

        layout = QVBoxLayout()

        # 课程选择列表
        layout.addWidget(QLabel("选择互斥的课程:"))
        course_list = QListWidget()
        course_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        # 添加可选的课程
        if hasattr(self, 'courses_data'):
            for course_id in self.courses_data.keys():
                item = QListWidgetItem(course_id)
                course_list.addItem(item)
                if course_id in courses:
                    item.setSelected(True)

        layout.addWidget(course_list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout.addWidget(buttons)
        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_courses = [item.text()
                                for item in course_list.selectedItems()]

            if len(selected_courses) >= 2:
                # 更新数据结构
                self.mutex_data[mutex_id] = selected_courses

                # 重新创建条目
                self.refresh_mutex_item(mutex_id)

                # 保存到本地
                self.save_course_configs()

                # 更新统计信息
                self.update_config_stats()
            else:
                QMessageBox.warning(self, "警告", "请选择至少2个课程！")

    def delete_mutex_rule(self, mutex_id):
        """删除互斥规则"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除互斥规则 {mutex_id} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 从数据结构中删除
            if mutex_id in self.mutex_data:
                del self.mutex_data[mutex_id]

            # 从界面中删除条目
            self.remove_mutex_item(mutex_id)

            # 保存到本地
            self.save_course_configs()

            # 更新统计信息
            self.update_config_stats()

    def edit_delay_rule(self, delay_id, course_id, threshold):
        """编辑延迟规则"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QComboBox, QSpinBox

        dialog = QDialog(self)
        dialog.setWindowTitle(f"编辑延迟规则 {delay_id}")
        dialog.setModal(True)

        layout = QFormLayout()

        course_combo = QComboBox()
        threshold_spin = QSpinBox()
        threshold_spin.setRange(1, 1000)
        threshold_spin.setValue(threshold)

        # 添加可选的课程
        if hasattr(self, 'courses_data'):
            for cid in self.courses_data.keys():
                course_combo.addItem(cid)
                if cid == course_id:
                    course_combo.setCurrentText(cid)

        layout.addRow("课程:", course_combo)
        layout.addRow("人数阈值:", threshold_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout.addRow(buttons)
        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_course_id = course_combo.currentText()
            new_threshold = threshold_spin.value()

            if new_course_id:
                # 更新数据结构
                self.delay_data[delay_id] = {
                    'course': new_course_id,
                    'threshold': new_threshold
                }

                # 重新创建条目
                self.refresh_delay_item(delay_id)

                # 保存到本地
                self.save_course_configs()

                # 更新统计信息
                self.update_config_stats()
            else:
                QMessageBox.warning(self, "警告", "请选择课程！")

    def delete_delay_rule(self, delay_id):
        """删除延迟规则"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除延迟规则 {delay_id} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 从数据结构中删除
            if delay_id in self.delay_data:
                del self.delay_data[delay_id]

            # 从界面中删除条目
            self.remove_delay_item(delay_id)

            # 保存到本地
            self.save_course_configs()

            # 更新统计信息
            self.update_config_stats()

    def refresh_course_item(self, course_id):
        """刷新课程条目"""
        if course_id in self.courses_data:
            course_data = self.courses_data[course_id]
            # 删除旧条目
            self.remove_course_item(course_id)
            # 创建新条目
            course_item = self.create_course_item(
                course_id,
                course_data.get('name', ''),
                course_data.get('class', ''),
                course_data.get('school', '')
            )
            self.course_list_layout.addWidget(course_item)

    def refresh_mutex_item(self, mutex_id):
        """刷新互斥规则条目"""
        if mutex_id in self.mutex_data:
            courses = self.mutex_data[mutex_id]
            # 删除旧条目
            self.remove_mutex_item(mutex_id)
            # 创建新条目
            mutex_item = self.create_mutex_item(mutex_id, courses)
            self.mutex_list_layout.addWidget(mutex_item)

    def refresh_delay_item(self, delay_id):
        """刷新延迟规则条目"""
        if delay_id in self.delay_data:
            delay_data = self.delay_data[delay_id]
            # 删除旧条目
            self.remove_delay_item(delay_id)
            # 创建新条目
            delay_item = self.create_delay_item(
                delay_id,
                delay_data.get('course', ''),
                delay_data.get('threshold', 10)
            )
            self.delay_list_layout.addWidget(delay_item)

    def remove_course_item(self, course_id):
        """从界面中删除课程条目"""
        # 遍历布局找到对应的条目并删除
        i = 0
        while i < self.course_list_layout.count():
            layout_item = self.course_list_layout.itemAt(i)
            if layout_item is not None:
                widget = layout_item.widget()
                if widget is not None:
                    # 查找包含课程ID的标签
                    labels = widget.findChildren(QLabel)
                    for label in labels:
                        if course_id in label.text():
                            # 删除小部件并移除布局项
                            widget.deleteLater()
                            self.course_list_layout.removeItem(layout_item)
                            # 因为移除了一个元素，索引不变，继续检查当前索引
                            continue
            i += 1

    def remove_mutex_item(self, mutex_id):
        """从界面中删除互斥规则条目"""
        i = 0
        while i < self.mutex_list_layout.count():
            layout_item = self.mutex_list_layout.itemAt(i)
            if layout_item is not None:
                widget = layout_item.widget()
                if widget is not None:
                    # 查找包含互斥规则ID的标签
                    labels = widget.findChildren(QLabel)
                    for label in labels:
                        if mutex_id in label.text():
                            widget.deleteLater()
                            self.mutex_list_layout.removeItem(layout_item)
                            continue
            i += 1

    def remove_delay_item(self, delay_id):
        """从界面中删除延迟规则条目"""
        i = 0
        while i < self.delay_list_layout.count():
            layout_item = self.delay_list_layout.itemAt(i)
            if layout_item is not None:
                widget = layout_item.widget()
                if widget is not None:
                    # 查找包含延迟规则ID的标签
                    labels = widget.findChildren(QLabel)
                    for label in labels:
                        if delay_id in label.text():
                            widget.deleteLater()
                            self.delay_list_layout.removeItem(layout_item)
                            continue
            i += 1

    def switch_view(self):
        """切换系统设置和课程设置视图"""
        current_index = self.stacked_widget.currentIndex()
        if current_index == 0:
            self.stacked_widget.setCurrentIndex(1)
            self.switch_button.setText("切换到系统设置")
            self.config_stats_label.show()
            self.clear_btn.show()
            self.update_config_stats()  # 更新统计信息
        else:
            self.stacked_widget.setCurrentIndex(0)
            self.switch_button.setText("切换到课程设置")
            self.config_stats_label.hide()
            self.clear_btn.hide()
