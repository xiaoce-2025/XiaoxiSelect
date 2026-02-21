"""
@Author : xiaoce2025
@File   : console_window.py
@Date   : 2025-12-31
"""

"""Console窗口类"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from .about_window import YanPage
from config.config_manager import ConfigManager
import json
import os
import base64


class ConsoleWindow(QMainWindow):
    """Console窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        # 加密密钥（使用固定密钥，确保不同设备间可以正常解密）
        self.encryption_key = "yanxiaoxi_config_encrypt_key_2026"
        # 保存主窗口引用
        self.main_window = parent
    
    def _encrypt(self, data):
        """加密数据"""
        # 将数据转换为字节
        data_bytes = data.encode('utf-8')
        key_bytes = self.encryption_key.encode('utf-8')
        
        # XOR加密
        encrypted = bytearray()
        for i, b in enumerate(data_bytes):
            encrypted.append(b ^ key_bytes[i % len(key_bytes)])
        
        # Base64编码
        return base64.b64encode(encrypted).decode('utf-8')
    
    def _decrypt(self, encrypted_data):
        """解密数据"""
        try:
            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            key_bytes = self.encryption_key.encode('utf-8')
            
            # XOR解密
            decrypted = bytearray()
            for i, b in enumerate(encrypted_bytes):
                decrypted.append(b ^ key_bytes[i % len(key_bytes)])
            
            return decrypted.decode('utf-8')
        except Exception as e:
            raise Exception(f"解密失败: {str(e)}")
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("调试 Console")
        self.setGeometry(200, 200, 440, 610)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowMinimizeButtonHint
        )
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 设置背景色为白色
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
        self.setPalette(palette)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 按钮布局 - 用于放置多个按钮，每行两个
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 20)
        
        # 第一行按钮
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(20)
        row1_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 添加关于按钮
        about_button = QPushButton("关于严小希")
        about_button.setFixedSize(120, 36)
        about_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                font-size: 14px;
                font-weight: normal;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
        about_button.clicked.connect(self.open_about_window)
        row1_layout.addWidget(about_button)
        
        # 导出配置按钮
        export_button = QPushButton("导出配置")
        export_button.setFixedSize(120, 36)
        export_button.setStyleSheet(about_button.styleSheet())
        export_button.clicked.connect(self.export_config)
        row1_layout.addWidget(export_button)
        
        button_layout.addLayout(row1_layout)
        
        # 第二行按钮
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(20)
        row2_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 加载配置按钮
        load_button = QPushButton("加载配置")
        load_button.setFixedSize(120, 36)
        load_button.setStyleSheet(about_button.styleSheet())
        load_button.clicked.connect(self.load_config)
        row2_layout.addWidget(load_button)
        
        # 添加占位符以保持居中
        placeholder = QWidget()
        placeholder.setFixedSize(120, 36)
        row2_layout.addWidget(placeholder)
        
        button_layout.addLayout(row2_layout)


        # 向上对齐
        button_layout.addStretch()
        
        # 将按钮布局添加到主布局
        main_layout.addLayout(button_layout)

    def open_about_window(self):
        """打开关于窗口"""
        self.about_window = YanPage()
        self.about_window.setWindowTitle("严小希的自我介绍")
        self.about_window.showMaximized()
    
    def export_config(self):
        """导出配置"""
        try:
            # 创建配置管理器
            config_manager = ConfigManager()
            
            # 加载当前配置
            config_data = config_manager.load_config()
            
            # 打开文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出配置", "", "严小希配置文件 (*.yxx);;所有文件 (*.*)"
            )
            
            if file_path:
                # 确保文件扩展名为.yxx
                if not file_path.endswith('.yxx'):
                    file_path += '.yxx'
                
                # 将配置转换为JSON字符串
                json_data = json.dumps(config_data, indent=4, ensure_ascii=False)
                
                # 加密数据
                encrypted_data = self._encrypt(json_data)
                
                # 保存加密后的配置
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(encrypted_data)
                
                # 显示成功消息
                QMessageBox.information(
                    self, "导出成功", f"配置已成功加密导出到：\n{file_path}"
                )
        except Exception as e:
            # 显示错误消息
            QMessageBox.critical(
                self, "导出失败", f"导出配置时发生错误：\n{str(e)}"
            )
    
    def load_config(self):
        """加载配置"""
        try:
            # 打开文件选择对话框
            file_path, _ = QFileDialog.getOpenFileName(
                self, "加载配置", "", "严小希配置文件 (*.yxx);;所有文件 (*.*)"
            )
            
            if file_path:
                # 读取加密的配置文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    encrypted_data = f.read()
                
                # 解密数据
                json_data = self._decrypt(encrypted_data)
                
                # 解析JSON
                config_data = json.loads(json_data)
                
                # 创建配置管理器
                config_manager = ConfigManager()
                
                # 保存配置到系统
                config_manager.save_config(config_data)
                
                # 刷新主窗口的配置编辑器UI
                if self.main_window and hasattr(self.main_window, 'config_editor'):
                    self.main_window.config_editor.load_configs()
                    # 设置状态标签为刚启动时的样式
                    config_editor = self.main_window.config_editor
                    config_editor.save_status_label.setText("成功加载全部配置")
                    config_editor.save_status_label.setStyleSheet("""
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
                
                # 显示成功消息
                QMessageBox.information(
                    self, "加载成功", "配置已成功解密加载并应用！"
                )
        except json.JSONDecodeError as e:
            # 显示JSON解析错误
            QMessageBox.critical(
                self, "加载失败", f"配置文件格式错误：\n{str(e)}"
            )
        except Exception as e:
            # 显示其他错误
            QMessageBox.critical(
                self, "加载失败", f"加载配置时发生错误：\n{str(e)}"
            )
