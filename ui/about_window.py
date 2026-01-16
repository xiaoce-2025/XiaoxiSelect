from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QHBoxLayout, QVBoxLayout, QPushButton
)
from PyQt6.QtGui import QPixmap, QFont, QFontDatabase, QCursor
from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtWebEngineWidgets import QWebEngineView
import webbrowser
import os

class YanPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 设置紫色背景
        self.setStyleSheet("""
            background-color: #f5f0ff;
            color: #4b0082;
        """)
        
        # 添加滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 添加标题
        title_label = QLabel("「严小希」的自我介绍")
        title_font = QFont("Comic Sans MS", 24, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            color: #8a2be2;
            padding: 15px 0;
            border-bottom: 3px dashed #d8bfd8;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title_label)
        
        # 添加头像和基本信息（水平布局）
        info_container = QWidget()
        info_layout = QHBoxLayout(info_container)
        
        # 头像区域
        avatar_frame = QFrame()
        avatar_layout = QVBoxLayout(avatar_frame)
        avatar_label = QLabel()
        # 图像
        pixmap = QPixmap("pictures/yanxx.png").scaled(
            150, 200, 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        avatar_label.setPixmap(pixmap)
        avatar_layout.addWidget(avatar_label)
        avatar_frame.setStyleSheet("""
            border: 3px solid #9370db;
            border-radius: 10px;
            padding: 5px;
        """)
        
        # 基本信息
        basic_info = QVBoxLayout()
        name_label = QLabel("👧 「严小希」")
        name_label.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        
        desc_label = QLabel("人小附大 · 高三 · 梦想进入北京大学")
        desc_label.setFont(QFont("Microsoft YaHei UI", 12))
        
        dream_label = QLabel("✨ 最喜欢物理和「泡泡」老师的物理课堂")
        dream_label.setFont(QFont("Microsoft YaHei UI", 11))
        
        [widget.setStyleSheet("margin-bottom: 8px;") 
         for widget in [name_label, desc_label, dream_label]]
        
        basic_info.addWidget(name_label)
        basic_info.addWidget(desc_label)
        basic_info.addWidget(dream_label)
        
        # 添加到信息布局
        info_layout.addWidget(avatar_frame)
        info_layout.addLayout(basic_info)
        info_layout.setStretch(0, 1)
        info_layout.setStretch(1, 2)
        
        content_layout.addWidget(info_container)
        
        # 添加分隔符
        content_layout.addWidget(self.create_divider())
        
        # 添加外貌和性格部分（水平布局）
        feature_container = QWidget()
        feature_layout = QHBoxLayout(feature_container)
        
        # 外貌部分
        appearance_frame = QFrame()
        appearance_layout = QVBoxLayout(appearance_frame)
        appearance_title = self.create_section_title("👩 外貌")
        appearance_layout.addWidget(appearance_title)
        
        appearance_items = [
            "💇 头发：浅棕色长发，常以半扎马尾",
            "👀 眼睛：琥珀色眼眸，笑起来像弯月",
            "👕 服装：标志性红白校服"
        ]
        for item in appearance_items:
            label = QLabel(item)
            label.setFont(QFont("Microsoft YaHei UI", 10))
            label.setStyleSheet("margin: 3px 0 3px 15px;")
            appearance_layout.addWidget(label)
            
        appearance_frame.setStyleSheet("""
            background-color: #f0e6ff;
            border-radius: 15px;
            padding: 10px;
        """)
        
        # 性格部分
        personality_frame = QFrame()
        personality_layout = QVBoxLayout(personality_frame)
        personality_title = self.create_section_title("🌟 性格")
        personality_layout.addWidget(personality_title)
        
        personality_items = [
            "😄 活泼乐观开朗 - 笑声有魔力的小太阳",
            "🔍 好奇探索 - 对物理世界充满热情",
            "🎨 创新创造 - 能把想法变成现实",
            "🫶 乐于助人 - 同学们的贴心伙伴"
        ]
        for item in personality_items:
            label = QLabel(item)
            label.setFont(QFont("Microsoft YaHei UI", 10))
            label.setStyleSheet("margin: 3px 0 3px 15px;")
            personality_layout.addWidget(label)
            
        personality_frame.setStyleSheet("""
            background-color: #f0e6ff;
            border-radius: 15px;
            padding: 10px;
        """)
        
        feature_layout.addWidget(appearance_frame)
        feature_layout.addWidget(personality_frame)
        content_layout.addWidget(feature_container)
        
        # 添加分隔符
        content_layout.addWidget(self.create_divider())
        
        # 添加作品部分
        works_container = QWidget()
        works_layout = QVBoxLayout(works_container)
        works_title = self.create_section_title("📚 代表作品")
        works_layout.addWidget(works_title)
        
        works_items = [
            ("《未名湖畔那银杏》", "https://www.cxxdgc.cn/blog/somewishesin2025"),
            ("《严小希进厂记》", "https://www.cxxdgc.cn/blog/yanxx/yanxxjinchangji"),
            ("蕉学网2025秋季更新回退插件（获取回放下载链接）-安装指南", "https://www.cxxdgc.cn/blog/project/videodownload2025autumn_addition")
        ]
        
        for name, url in works_items:
            btn = QPushButton(name)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFont(QFont("Microsoft YaHei UI", 10))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e6e6fa;
                    color: #663399;
                    padding: 8px;
                    border-radius: 10px;
                    text-align: left;
                    margin: 5px 0;
                }
                QPushButton:hover {
                    background-color: #d8bfd8;
                }
            """)
            btn.clicked.connect(lambda _, u=url: webbrowser.open(u))
            works_layout.addWidget(btn)
            
        works_container.setStyleSheet("""
            background-color: #faf0fa;
            border-radius: 15px;
            padding: 10px;
        """)
        content_layout.addWidget(works_container)
        
        # 添加分隔符
        content_layout.addWidget(self.create_divider())
        
        # 添加后记部分
        postscript = QLabel("感谢xiaoce-2025、firefly1145141919810对「严小希」做出的贡献~")
        postscript.setFont(QFont("Comic Sans MS", 9))
        postscript.setStyleSheet("color: #9370db; margin-top: 10px;")
        content_layout.addWidget(postscript)
        
        # 设置滚动区域内容
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
    def create_section_title(self, text):
        title = QLabel(text)
        title.setFont(QFont("Comic Sans MS", 14, QFont.Weight.Bold))
        title.setStyleSheet("""
            color: #9400d3;
            margin: 10px 0;
            padding-bottom: 5px;
            border-bottom: 1px dashed #dda0dd;
        """)
        return title
        
    def create_divider(self):
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #d8bfd8; margin: 15px 0;")
        return divider

if __name__ == "__main__":
    # 测试代码
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    # 加载字体
    font_paths = [
        "C:/Windows/Fonts/comic.ttf",  # Windows
        "/Library/Fonts/Comic Sans MS.ttf",  # macOS
        "/usr/share/fonts/truetype/msttcorefonts/comic.ttf"  # Linux
    ]
    for path in font_paths:
        if os.path.exists(path):
            QFontDatabase.addApplicationFont(path)
    
    window = YanPage()
    window.resize(600, 800)
    window.setWindowTitle("「严小希」的介绍")
    window.show()
    sys.exit(app.exec())