"""
配置文件编辑器界面
"""

import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QPushButton, QLabel, QLineEdit, QSpinBox, 
                             QDoubleSpinBox, QCheckBox, QComboBox, QGroupBox, 
                             QFormLayout, QMessageBox, QScrollArea, QFrame)
from PyQt6.QtCore import Qt
from config.config_manager import ConfigManager

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
        
        self.init_ui()
        self.load_configs()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 用户设置标签页
        user_tab = self.create_user_tab()
        tab_widget.addTab(user_tab, "用户设置")
        
        # 客户端设置标签页
        client_tab = self.create_client_tab()
        tab_widget.addTab(client_tab, "客户端设置")
        
        # 监控设置标签页
        monitor_tab = self.create_monitor_tab()
        tab_widget.addTab(monitor_tab, "监控设置")
        
        # 通知设置标签页
        notification_tab = self.create_notification_tab()
        tab_widget.addTab(notification_tab, "通知设置")
        
        # API密钥设置标签页
        apikey_tab = self.create_apikey_tab()
        tab_widget.addTab(apikey_tab, "API密钥")
        
        # 课程设置标签页
        course_tab = self.create_course_tab()
        tab_widget.addTab(course_tab, "课程设置")
        
        # 保存按钮
        save_btn = QPushButton("保存所有设置")
        save_btn.clicked.connect(self.save_all_configs)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        layout.addWidget(tab_widget)
        layout.addWidget(save_btn)
        self.setLayout(layout)
    
    def create_user_tab(self):
        """创建用户设置标签页"""
        widget = QWidget()
        layout = QFormLayout()
        
        self.student_id_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.dual_degree_check = QCheckBox()
        self.identity_combo = QComboBox()
        self.identity_combo.addItems(["bzx", "bfx"])
        
        layout.addRow("学号:", self.student_id_edit)
        layout.addRow("密码:", self.password_edit)
        layout.addRow("双学位:", self.dual_degree_check)
        layout.addRow("身份:", self.identity_combo)
        
        widget.setLayout(layout)
        return widget
    
    # 其他创建标签页的方法...
    # 由于篇幅限制，这里只展示部分代码
    
    def load_configs(self):
        """加载配置文件"""
        try:
            config_data = self.config_manager.load_config()
            
            # 加载用户设置
            if 'user' in config_data:
                user_data = config_data['user']
                self.student_id_edit.setText(user_data.get('student_id', ''))
                self.password_edit.setText(user_data.get('password', ''))
                self.dual_degree_check.setChecked(user_data.get('dual_degree', False))
                self.identity_combo.setCurrentText(user_data.get('identity', 'bzx'))
            
            # 加载客户端设置
            if 'client' in config_data:
                client_data = config_data['client']
                self.supply_cancel_page_spin.setValue(client_data.get('supply_cancel_page', 1))
                self.refresh_interval_spin.setValue(client_data.get('refresh_interval', 1.0))
                self.refresh_random_deviation_spin.setValue(client_data.get('random_deviation', 0.0))
                self.iaaa_timeout_spin.setValue(client_data.get('iaaa_client_timeout', 10.0))
                self.elective_timeout_spin.setValue(client_data.get('elective_client_timeout', 10.0))
                self.pool_size_spin.setValue(client_data.get('elective_client_pool_size', 5))
                self.max_life_spin.setValue(client_data.get('elective_client_max_life', 100))
                self.login_loop_interval_spin.setValue(client_data.get('login_loop_interval', 1.0))
                self.print_mutex_check.setChecked(client_data.get('print_mutex_rules', False))
                self.debug_request_check.setChecked(client_data.get('debug_print_request', False))
                self.debug_dump_check.setChecked(client_data.get('debug_dump_request', False))
            
            # 加载监控设置
            if 'monitor' in config_data:
                monitor_data = config_data['monitor']
                self.monitor_host_edit.setText(monitor_data.get('host', 'localhost'))
                self.monitor_port_spin.setValue(monitor_data.get('port', 5000))
            
            # 加载通知设置
            if 'notification' in config_data:
                notification_data = config_data['notification']
                self.disable_push_check.setChecked(notification_data.get('disable_push', False))
                self.wechat_token_edit.setText(notification_data.get('token', ''))
                self.verbosity_spin.setValue(notification_data.get('verbosity', 1))
                self.minimum_interval_spin.setValue(notification_data.get('minimum_interval', 1.0))
            
            # 加载API密钥设置
            if 'apikey' in config_data:
                apikey_data = config_data['apikey']
                self.username_edit.setText(apikey_data.get('username', ''))
                self.apikey_password_edit.setText(apikey_data.get('password', ''))
                self.recognition_type_edit.setText(apikey_data.get('RecognitionTypeid', ''))
            
            # 加载课程配置
            if 'courses' in config_data:
                self.courses_data = config_data['courses']
                self.load_course_items()
            
            if 'mutex' in config_data:
                self.mutex_data = config_data['mutex']
                self.load_mutex_items()
            
            if 'delay' in config_data:
                self.delay_data = config_data['delay']
                self.load_delay_items()
            
            # 更新统计信息
            self.update_config_stats()
        
        except Exception as e:
            if self.log_display:
                self.log_display.add_log(f"加载配置文件失败: {str(e)}")
            QMessageBox.warning(self, "警告", f"加载配置文件失败: {str(e)}")
    
    def save_all_configs(self):
        """保存所有配置文件"""
        try:
            config_data = {}
            
            # 用户设置
            config_data['user'] = {
                'student_id': self.student_id_edit.text(),
                'password': self.password_edit.text(),
                'dual_degree': self.dual_degree_check.isChecked(),
                'identity': self.identity_combo.currentText()
            }
            
            # 客户端设置
            config_data['client'] = {
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
            
            # 监控设置
            config_data['monitor'] = {
                'host': self.monitor_host_edit.text(),
                'port': self.monitor_port_spin.value()
            }
            
            # 通知设置
            config_data['notification'] = {
                'disable_push': self.disable_push_check.isChecked(),
                'token': self.wechat_token_edit.text(),
                'verbosity': self.verbosity_spin.value(),
                'minimum_interval': self.minimum_interval_spin.value()
            }
            
            # API密钥设置
            config_data['apikey'] = {
                'username': self.username_edit.text(),
                'password': self.apikey_password_edit.text(),
                'RecognitionTypeid': self.recognition_type_edit.text()
            }
            
            # 课程配置
            config_data['courses'] = self.courses_data
            config_data['mutex'] = self.mutex_data
            config_data['delay'] = self.delay_data
            
            # 保存配置
            self.config_manager.save_config(config_data)
            
            if self.log_display:
                self.log_display.add_log("配置文件保存成功！")
            QMessageBox.information(self, "成功", "配置文件保存成功！")
        
        except Exception as e:
            if self.log_display:
                self.log_display.add_log(f"保存配置文件失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"保存配置文件失败: {str(e)}")
    
    def create_client_tab(self):
        """创建客户端设置标签页"""
        widget = QWidget()
        layout = QFormLayout()
        
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
        
        layout.addRow("补退选页数:", self.supply_cancel_page_spin)
        layout.addRow("刷新间隔(秒):", self.refresh_interval_spin)
        layout.addRow("随机偏差(秒):", self.refresh_random_deviation_spin)
        layout.addRow("IAAA超时(秒):", self.iaaa_timeout_spin)
        layout.addRow("选课超时(秒):", self.elective_timeout_spin)
        layout.addRow("连接池大小:", self.pool_size_spin)
        layout.addRow("最大生命周期:", self.max_life_spin)
        layout.addRow("登录循环间隔(秒):", self.login_loop_interval_spin)
        layout.addRow("打印互斥规则:", self.print_mutex_check)
        layout.addRow("调试请求:", self.debug_request_check)
        layout.addRow("调试转储:", self.debug_dump_check)
        
        widget.setLayout(layout)
        return widget

    def create_monitor_tab(self):
        """创建监控设置标签页"""
        widget = QWidget()
        layout = QFormLayout()
        
        self.monitor_host_edit = QLineEdit()
        self.monitor_port_spin = QSpinBox()
        self.monitor_port_spin.setRange(1, 65535)
        
        layout.addRow("监控主机:", self.monitor_host_edit)
        layout.addRow("监控端口:", self.monitor_port_spin)
        
        widget.setLayout(layout)
        return widget

    def create_notification_tab(self):
        """创建通知设置标签页"""
        widget = QWidget()
        layout = QFormLayout()
        
        self.disable_push_check = QCheckBox()
        self.wechat_token_edit = QLineEdit()
        self.verbosity_spin = QSpinBox()
        self.verbosity_spin.setRange(0, 5)
        self.minimum_interval_spin = QDoubleSpinBox()
        self.minimum_interval_spin.setRange(0.1, 10.0)
        self.minimum_interval_spin.setSingleStep(0.1)
        
        layout.addRow("禁用推送:", self.disable_push_check)
        layout.addRow("微信Token:", self.wechat_token_edit)
        layout.addRow("详细程度:", self.verbosity_spin)
        layout.addRow("最小间隔(秒):", self.minimum_interval_spin)
        
        widget.setLayout(layout)
        return widget

    def create_apikey_tab(self):
        """创建API密钥设置标签页"""
        widget = QWidget()
        layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.apikey_password_edit = QLineEdit()
        self.apikey_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.recognition_type_edit = QLineEdit()
        
        layout.addRow("用户名:", self.username_edit)
        layout.addRow("密码:", self.apikey_password_edit)
        layout.addRow("识别类型ID:", self.recognition_type_edit)
        
        widget.setLayout(layout)
        return widget

    def create_course_tab(self):
        """创建课程设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 配置统计信息
        self.config_stats_label = QLabel("配置统计：0 个课程，0 个互斥规则，0 个延迟规则")
        self.config_stats_label.setStyleSheet("""
            QLabel {
                background-color: #f3e5f5;
                border: 1px solid #9c27b0;
                border-radius: 5px;
                padding: 8px;
                margin: 5px;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.config_stats_label)
        
        # 创建标签页
        course_tab_widget = QTabWidget()
        
        # 课程标签页
        course_tab = self.create_course_list_tab()
        course_tab_widget.addTab(course_tab, "课程")
        
        # 互斥规则标签页
        mutex_tab = self.create_mutex_list_tab()
        course_tab_widget.addTab(mutex_tab, "互斥规则")
        
        # 延迟规则标签页
        delay_tab = self.create_delay_list_tab()
        course_tab_widget.addTab(delay_tab, "延迟规则")
        
        layout.addWidget(course_tab_widget)
        
        widget.setLayout(layout)
        return widget

    def create_course_list_tab(self):
        """创建课程列表标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 说明标签
        info_label = QLabel("课程配置：每个课程包含ID、名称、班级号和学院信息")
        info_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
        """)
        layout.addWidget(info_label)
        
        # 课程列表
        self.course_list_widget = QWidget()
        self.course_list_layout = QVBoxLayout()
        self.course_list_widget.setLayout(self.course_list_layout)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.course_list_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        
        layout.addWidget(scroll_area)
        
        # 添加课程按钮
        add_course_btn = QPushButton("添加课程")
        add_course_btn.clicked.connect(self.add_course)
        add_course_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        
        layout.addWidget(add_course_btn)
        
        return widget

    def create_mutex_list_tab(self):
        """创建互斥规则列表标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 说明标签
        info_label = QLabel("互斥规则：指定哪些课程不能同时选择")
        info_label.setStyleSheet("""
            QLabel {
                background-color: #fff3e0;
                border: 1px solid #ff9800;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
        """)
        layout.addWidget(info_label)
        
        # 互斥规则列表
        self.mutex_list_widget = QWidget()
        self.mutex_list_layout = QVBoxLayout()
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
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        
        layout.addWidget(add_mutex_btn)
        
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
                border: 1px solid #4caf50;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
        """)
        layout.addWidget(info_label)
        
        # 延迟规则列表
        self.delay_list_widget = QWidget()
        self.delay_list_layout = QVBoxLayout()
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
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        layout.addWidget(add_delay_btn)
        
        return widget

    def create_course_item(self, course_id, course_name, class_no, school):
        """创建课程条目组件"""
        item_widget = QWidget()
        item_layout = QHBoxLayout()
        
        # 课程信息标签
        info_label = QLabel(f"{course_id}: {course_name} (班级: {class_no}, 学院: {school})")
        info_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 8px;
                margin: 2px;
                flex: 1;
            }
        """)
        
        # 编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(lambda: self.edit_course(course_id, course_name, class_no, school))
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                min-width: 60px;
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
                border-radius: 3px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        item_layout.addWidget(info_label)
        item_layout.addWidget(edit_btn)
        item_layout.addWidget(delete_btn)
        
        item_widget.setLayout(item_layout)
        return item_widget

    def create_mutex_item(self, mutex_id, courses):
        """创建互斥规则条目组件"""
        item_widget = QWidget()
        item_layout = QHBoxLayout()
        
        # 互斥规则信息标签
        courses_text = ", ".join(courses)
        info_label = QLabel(f"{mutex_id}: {courses_text}")
        info_label.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 3px;
                padding: 8px;
                margin: 2px;
                flex: 1;
            }
        """)
        
        # 编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(lambda: self.edit_mutex_rule(mutex_id, courses))
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                min-width: 60px;
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
                border-radius: 3px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        item_layout.addWidget(info_label)
        item_layout.addWidget(edit_btn)
        item_layout.addWidget(delete_btn)
        
        item_widget.setLayout(item_layout)
        return item_widget

    def create_delay_item(self, delay_id, course_id, threshold):
        """创建延迟规则条目组件"""
        item_widget = QWidget()
        item_layout = QHBoxLayout()
        
        # 延迟规则信息标签
        info_label = QLabel(f"{delay_id}: 课程 {course_id} 在人数达到 {threshold} 后开始选课")
        info_label.setStyleSheet("""
            QLabel {
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 3px;
                padding: 8px;
                margin: 2px;
                flex: 1;
            }
        """)
        
        # 编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(lambda: self.edit_delay_rule(delay_id, course_id, threshold))
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                min-width: 60px;
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
                border-radius: 3px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        item_layout.addWidget(info_label)
        item_layout.addWidget(edit_btn)
        item_layout.addWidget(delete_btn)
        
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
        
        layout.addRow("课程ID:", course_id_edit)
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
            course_id = course_id_edit.text().strip()
            course_name = course_name_edit.text().strip()
            class_no = class_no_edit.text().strip()
            school = school_edit.text().strip()
            
            if course_id and course_name and class_no and school:
                # 创建课程条目
                course_item = self.create_course_item(course_id, course_name, class_no, school)
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
            else:
                QMessageBox.warning(self, "警告", "请填写所有字段！")

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
            selected_courses = [item.text() for item in course_list.selectedItems()]
            
            if rule_id and len(selected_courses) >= 2:
                # 创建互斥规则条目
                mutex_item = self.create_mutex_item(rule_id, selected_courses)
                self.mutex_list_layout.addWidget(mutex_item)
                
                # 更新统计信息
                self.update_config_stats()
                
                # 保存到内部数据结构
                if not hasattr(self, 'mutex_data'):
                    self.mutex_data = {}
                self.mutex_data[rule_id] = selected_courses
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
                # 创建延迟规则条目
                delay_item = self.create_delay_item(delay_id, course_id, threshold)
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

    def update_config_stats(self):
        """更新配置统计信息"""
        try:
            course_count = len(self.courses_data) if hasattr(self, 'courses_data') else 0
            mutex_count = len(self.mutex_data) if hasattr(self, 'mutex_data') else 0
            delay_count = len(self.delay_data) if hasattr(self, 'delay_data') else 0
            
            self.config_stats_label.setText(f"配置统计：{course_count} 个课程，{mutex_count} 个互斥规则，{delay_count} 个延迟规则")
            
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
                
                # 更新统计信息
                self.update_config_stats()
            else:
                QMessageBox.warning(self, "警告", "请填写所有字段！")

    def delete_course(self, course_id):
        """删除课程"""
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除课程 {course_id} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 从数据结构中删除
            if course_id in self.courses_data:
                del self.courses_data[course_id]
            
            # 从界面中删除条目
            self.remove_course_item(course_id)
            
            # 更新统计信息
            self.update_config_stats()

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
            selected_courses = [item.text() for item in course_list.selectedItems()]
            
            if len(selected_courses) >= 2:
                # 更新数据结构
                self.mutex_data[mutex_id] = selected_courses
                
                # 重新创建条目
                self.refresh_mutex_item(mutex_id)
                
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
        for i in range(self.course_list_layout.count()):
            child = self.course_list_layout.itemAt(i)
            if child.widget():
                widget = child.widget()
                # 查找包含课程ID的标签
                for child_widget in widget.findChildren(QLabel):
                    if course_id in child_widget.text():
                        widget.deleteLater()
                        self.course_list_layout.removeItem(child)
                        break

    def remove_mutex_item(self, mutex_id):
        """从界面中删除互斥规则条目"""
        # 遍历布局找到对应的条目并删除
        for i in range(self.mutex_list_layout.count()):
            child = self.mutex_list_layout.itemAt(i)
            if child.widget():
                widget = child.widget()
                # 查找包含互斥规则ID的标签
                for child_widget in widget.findChildren(QLabel):
                    if mutex_id in child_widget.text():
                        widget.deleteLater()
                        self.mutex_list_layout.removeItem(child)
                        break

    def remove_delay_item(self, delay_id):
        """从界面中删除延迟规则条目"""
        # 遍历布局找到对应的条目并删除
        for i in range(self.delay_list_layout.count()):
            child = self.delay_list_layout.itemAt(i)
            if child.widget():
                widget = child.widget()
                # 查找包含延迟规则ID的标签
                for child_widget in widget.findChildren(QLabel):
                    if delay_id in child_widget.text():
                        widget.deleteLater()
                        self.delay_list_layout.removeItem(child)
                        break