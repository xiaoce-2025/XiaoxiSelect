#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PKU自动选课程序 - PyQt6图形化界面
"""

import sys
import os
import json
import configparser
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QPushButton, QTextEdit, 
                             QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, 
                             QCheckBox, QComboBox, QGroupBox, QFormLayout,
                             QMessageBox, QFileDialog, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QTextCursor
import threading
import queue

# 导入自动选课模块
from autoelective.cli import create_default_threads, setup_default_environ
from autoelective.environ import Environ
from autoelective.config import AutoElectiveConfig
#from autoelective.logger import get_logger

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

class ConfigEditor(QWidget):
    """配置文件编辑器"""
    
    def __init__(self):
        super().__init__()
        self.config_file = "config.ini"
        self.apikey_file = "apikey.json"
        
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
    
    def load_configs(self):
        """加载配置文件"""
        try:
            # 加载config.ini
            if os.path.exists(self.config_file):
                config = configparser.ConfigParser()
                config.read(self.config_file, encoding='utf-8')
                
                # 加载用户设置
                if 'user' in config:
                    self.student_id_edit.setText(config.get('user', 'student_id', fallback=''))
                    self.password_edit.setText(config.get('user', 'password', fallback=''))
                    self.dual_degree_check.setChecked(config.getboolean('user', 'dual_degree', fallback=False))
                    self.identity_combo.setCurrentText(config.get('user', 'identity', fallback='bzx'))
                
                # 加载客户端设置
                if 'client' in config:
                    self.supply_cancel_page_spin.setValue(config.getint('client', 'supply_cancel_page', fallback=1))
                    self.refresh_interval_spin.setValue(config.getfloat('client', 'refresh_interval', fallback=1.0))
                    self.refresh_random_deviation_spin.setValue(config.getfloat('client', 'random_deviation', fallback=0.0))
                    self.iaaa_timeout_spin.setValue(config.getfloat('client', 'iaaa_client_timeout', fallback=10.0))
                    self.elective_timeout_spin.setValue(config.getfloat('client', 'elective_client_timeout', fallback=10.0))
                    self.pool_size_spin.setValue(config.getint('client', 'elective_client_pool_size', fallback=5))
                    self.max_life_spin.setValue(config.getint('client', 'elective_client_max_life', fallback=100))
                    self.login_loop_interval_spin.setValue(config.getfloat('client', 'login_loop_interval', fallback=1.0))
                    self.print_mutex_check.setChecked(config.getboolean('client', 'print_mutex_rules', fallback=False))
                    self.debug_request_check.setChecked(config.getboolean('client', 'debug_print_request', fallback=False))
                    self.debug_dump_check.setChecked(config.getboolean('client', 'debug_dump_request', fallback=False))
                
                # 加载监控设置
                if 'monitor' in config:
                    self.monitor_host_edit.setText(config.get('monitor', 'host', fallback='localhost'))
                    self.monitor_port_spin.setValue(config.getint('monitor', 'port', fallback=5000))
                
                # 加载通知设置
                if 'notification' in config:
                    self.disable_push_check.setChecked(config.getboolean('notification', 'disable_push', fallback=False))
                    self.wechat_token_edit.setText(config.get('notification', 'token', fallback=''))
                    self.verbosity_spin.setValue(config.getint('notification', 'verbosity', fallback=1))
                    self.minimum_interval_spin.setValue(config.getfloat('notification', 'minimum_interval', fallback=1.0))
            
            # 加载课程配置
            self.load_course_config()
            
            # 加载apikey.json
            if os.path.exists(self.apikey_file):
                with open(self.apikey_file, 'r', encoding='utf-8') as f:
                    apikey_data = json.load(f)
                    self.username_edit.setText(apikey_data.get('username', ''))
                    self.apikey_password_edit.setText(apikey_data.get('password', ''))
                    self.recognition_type_edit.setText(apikey_data.get('RecognitionTypeid', ''))
        
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载配置文件失败: {str(e)}")
    
    def save_all_configs(self):
        """保存所有配置文件"""
        try:
            # 保存config.ini
            config = configparser.ConfigParser()
            
            # 用户设置
            config.add_section('user')
            config.set('user', 'student_id', self.student_id_edit.text())
            config.set('user', 'password', self.password_edit.text())
            config.set('user', 'dual_degree', str(self.dual_degree_check.isChecked()))
            config.set('user', 'identity', self.identity_combo.currentText())
            
            # 客户端设置
            config.add_section('client')
            config.set('client', 'supply_cancel_page', str(self.supply_cancel_page_spin.value()))
            config.set('client', 'refresh_interval', str(self.refresh_interval_spin.value()))
            config.set('client', 'random_deviation', str(self.refresh_random_deviation_spin.value()))
            config.set('client', 'iaaa_client_timeout', str(self.iaaa_timeout_spin.value()))
            config.set('client', 'elective_client_timeout', str(self.elective_timeout_spin.value()))
            config.set('client', 'elective_client_pool_size', str(self.pool_size_spin.value()))
            config.set('client', 'elective_client_max_life', str(self.max_life_spin.value()))
            config.set('client', 'login_loop_interval', str(self.login_loop_interval_spin.value()))
            config.set('client', 'print_mutex_rules', str(self.print_mutex_check.isChecked()))
            config.set('client', 'debug_print_request', str(self.debug_request_check.isChecked()))
            config.set('client', 'debug_dump_request', str(self.debug_dump_check.isChecked()))
            
            # 监控设置
            config.add_section('monitor')
            config.set('monitor', 'host', self.monitor_host_edit.text())
            config.set('monitor', 'port', str(self.monitor_port_spin.value()))
            
            # 通知设置
            config.add_section('notification')
            config.set('notification', 'disable_push', str(self.disable_push_check.isChecked()))
            config.set('notification', 'token', self.wechat_token_edit.text())
            config.set('notification', 'verbosity', str(self.verbosity_spin.value()))
            config.set('notification', 'minimum_interval', str(self.minimum_interval_spin.value()))
            
            # 保存课程配置
            self.save_course_configs(config)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            
            # 保存apikey.json
            apikey_data = {
                'username': self.username_edit.text(),
                'password': self.apikey_password_edit.text(),
                'RecognitionTypeid': self.recognition_type_edit.text()
            }
            
            with open(self.apikey_file, 'w', encoding='utf-8') as f:
                json.dump(apikey_data, f, indent=4, ensure_ascii=False)
            
            QMessageBox.information(self, "成功", "配置文件保存成功！")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置文件失败: {str(e)}")
    
    def save_course_configs(self, config):
        """保存课程配置到config对象"""
        try:
            sections_saved = 0
            
            # 保存课程配置
            if hasattr(self, 'courses_data'):
                for course_id, course_data in self.courses_data.items():
                    section_name = f"course:{course_id}"
                    self._add_section_to_config(config, section_name, course_data)
                    sections_saved += 1
            
            # 保存互斥规则配置
            if hasattr(self, 'mutex_data'):
                for mutex_id, courses in self.mutex_data.items():
                    section_name = f"mutex:{mutex_id}"
                    mutex_data = {'courses': ', '.join(courses)}
                    self._add_section_to_config(config, section_name, mutex_data)
                    sections_saved += 1
            
            # 保存延迟规则配置
            if hasattr(self, 'delay_data'):
                for delay_id, delay_data in self.delay_data.items():
                    section_name = f"delay:{delay_id}"
                    self._add_section_to_config(config, section_name, delay_data)
                    sections_saved += 1
            
            if sections_saved > 0:
                self.log_display.add_log(f"已保存 {sections_saved} 个配置节")
            else:
                self.log_display.add_log("未找到有效的配置节")
            
        except Exception as e:
            self.log_display.add_log(f"保存课程配置失败: {str(e)}")
            raise
    
    def _add_section_to_config(self, config, section_name, data):
        """将section数据添加到config对象"""
        if not config.has_section(section_name):
            config.add_section(section_name)
        
        for key, value in data.items():
            config.set(section_name, key, value)
    
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
            if os.path.exists(self.config_file):
                config = configparser.ConfigParser()
                config.read(self.config_file, encoding='utf-8')
                
                # 清空现有条目
                self.clear_all_items()
                
                # 初始化数据结构
                self.courses_data = {}
                self.mutex_data = {}
                self.delay_data = {}
                
                # 加载课程配置
                for section in config.sections():
                    if section.startswith('course:'):
                        course_id = section[8:]  # 去掉 'course:' 前缀
                        course_data = dict(config.items(section))
                        
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
                    
                    elif section.startswith('mutex:'):
                        mutex_id = section[6:]  # 去掉 'mutex:' 前缀
                        courses = config.get(section, 'courses', '').split(',')
                        courses = [c.strip() for c in courses if c.strip()]
                        
                        # 创建互斥规则条目
                        mutex_item = self.create_mutex_item(mutex_id, courses)
                        self.mutex_list_layout.addWidget(mutex_item)
                        
                        # 保存到数据结构
                        self.mutex_data[mutex_id] = courses
                    
                    elif section.startswith('delay:'):
                        delay_id = section[6:]  # 去掉 'delay:' 前缀
                        course_id = config.get(section, 'course', '')
                        threshold = config.getint(section, 'threshold', 10)
                        
                        # 创建延迟规则条目
                        delay_item = self.create_delay_item(delay_id, course_id, threshold)
                        self.delay_list_layout.addWidget(delay_item)
                        
                        # 保存到数据结构
                        self.delay_data[delay_id] = {
                            'course': course_id,
                            'threshold': threshold
                        }
                
                # 更新统计信息
                self.update_config_stats()
                
        except Exception as e:
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
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QListWidget, QVBoxLayout, QHBoxLayout
        
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
        if message.startswith('20') and ' - ' in message:
            # 这是来自日志处理器的格式化消息
            self.log_text.append(message)
        else:
            # 这是手动添加的消息，添加时间戳
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.append(f"[{timestamp}] {message}")
        
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
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px;
                background-color: #ecf0f1;
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
                    self.cleanup_environment()
                
                # 强制清理全局状态
                self.log_display.add_log("正在清理全局状态...")
                self.cleanup_global_queues()
                
                # 等待一下确保清理完成
                import time
                time.sleep(0.5)
                
                # 验证清理是否成功
                if not self.verify_clean_state():
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
            self.cleanup_environment()
    
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
                self.cleanup_environment()
                
                self.log_display.add_log("自动选课程序已停止")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止失败: {str(e)}")
            self.log_display.add_log(f"停止失败: {str(e)}")
    
    def cleanup_environment(self):
        """清理环境状态"""
        try:
            # 清理环境中的线程引用
            if hasattr(self.environ, 'iaaa_loop_thread'):
                self.environ.iaaa_loop_thread = None
            if hasattr(self.environ, 'elective_loop_thread'):
                self.environ.elective_loop_thread = None
            if hasattr(self.environ, 'monitor_thread'):
                self.environ.monitor_thread = None
            
            # 重置环境状态
            self.environ = Environ()
            
            # 清理全局队列（这是关键！）
            self.cleanup_global_queues()
            
            self.log_display.add_log("环境状态已清理")
            
        except Exception as e:
            self.log_display.add_log(f"环境清理失败: {str(e)}")
    
    def cleanup_global_queues(self):
        """清理全局队列"""
        try:
            # 清理autoelective模块中的全局队列
            import autoelective.loop
            
            # 清空队列
            if hasattr(autoelective.loop, 'electivePool'):
                while not autoelective.loop.electivePool.empty():
                    try:
                        autoelective.loop.electivePool.get_nowait()
                    except:
                        break
            
            if hasattr(autoelective.loop, 'reloginPool'):
                while not autoelective.loop.reloginPool.empty():
                    try:
                        autoelective.loop.reloginPool.get_nowait()
                    except:
                        break
            
            # 重置环境变量
            if hasattr(autoelective.loop, 'environ'):
                autoelective.loop.environ = Environ()
            
            self.log_display.add_log("全局队列已清理")
            
        except Exception as e:
            self.log_display.add_log(f"全局队列清理失败: {str(e)}")
    
    def verify_clean_state(self):
        """验证清理状态"""
        try:
            import autoelective.loop
            
            # 检查队列是否为空
            if hasattr(autoelective.loop, 'electivePool') and not autoelective.loop.electivePool.empty():
                self.log_display.add_log("警告：electivePool队列未完全清空")
                return False
            
            if hasattr(autoelective.loop, 'reloginPool') and not autoelective.loop.reloginPool.empty():
                self.log_display.add_log("警告：reloginPool队列未完全清空")
                return False
            
            # 检查环境状态
            if hasattr(self.environ, 'iaaa_loop_thread') and self.environ.iaaa_loop_thread is not None:
                self.log_display.add_log("警告：环境线程引用未完全清理")
                return False
            
            self.log_display.add_log("状态验证通过")
            return True
            
        except Exception as e:
            self.log_display.add_log(f"状态验证失败: {str(e)}")
            return False
    
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
            self.cleanup_environment()
            event.accept()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
