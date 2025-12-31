"""
@Author : xiaoce2025
@File   : update_check.py
@Date   : 2025-12-31
"""

"""更新检查模块"""

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox
from typing import Dict,List
from version.get_updater import check_for_updates


class UpdateWorker(QThread):
    """更新检查工作线程"""

    # 定义信号
    update_found = pyqtSignal(str)  # 发现更新
    update_error = pyqtSignal(str)  # 发生错误

    def __init__(self, gist_url=None):
        super().__init__()
        self.gist_url = gist_url

    def run(self):
        """线程执行函数"""
        try:
            # 调用updater模块的检查函数
            success, data, error = check_for_updates()

            # 格式化显示内容
            if success:
                message = format_update_message(data)

            if success and message:
                self.update_found.emit(message)
            else:
                self.update_error.emit(error or "未知错误")

        except Exception as e:
            error_msg = f"检查过程中发生错误: {str(e)}"
            self.update_error.emit(error_msg)

# 更新类型如下！写更新日志的时候记得看一眼！
# 虽然在拉取的信息中有这个字典段，但这里在代码中的处理都是硬编码！不能随意修改！
# //功能更新-Feature
# //增强更新-Enhancement
# //修复更新-BugFix
# //重大更新-CriticalBugFix
# //适配更新-Adaptation
# //常规更新-Regular
# //通知-Notification


type_mapping = {
    'Feature': '功能更新',
    'Enhancement': '增强更新',
    'BugFix': '修复更新',
    'CriticalBugFix': '恶性bug修复更新',
    'Adaptation': '适配更新',
    'Regular': '常规更新',
    'Notification': '通知'
}


# 格式化更新消息
def format_update_message(data: Dict) -> str:
    """
    格式化更新消息为可读字符串
    
    Args:
        data: 更新数据字典
        {
            "data": [
            {
                "version": "2025-Autumn-1.1.4",
                "download_url": "https://github.com/-2025/",
                "changelog": "1.xxxxxxxxxxxxd",
                "release_date": "2025-09-07",
                "type": "CriticalBugFix",
                "min_required_version": "1.1.4"
            }],
            "link":{
                "Feature": "功能更新"
            },
            "NewURL":"None"
            }
        
    Returns:
        格式化的消息字符串
    """
    update_data = data.get('data')
    if not update_data:
        return "[连接正常，但未拉取到有效更新信息]"
        
    formatted_messages = []
    for single_update_data in update_data:
        formatted_message = format_single_update_message(single_update_data)
        formatted_messages.append(formatted_message)
        
    # 在消息之间添加一个空行作为分隔
    return "\n\n".join(formatted_messages)


# 单个更新消息格式化函数
def format_single_update_message(data: Dict) -> str:
    """
    格式化更新消息为可读字符串

    Args:
        success: 是否成功
        data: 更新数据字典
        error: 错误信息

    Returns:
        格式化的消息字符串
    """
    version = data.get('version', '未知')
    changelog = data.get('changelog', '')
    release_date = data.get('release_date', '')
    download_url = data.get('download_url', '')
    update_type = data.get('type', '常规更新')
    # 对应中文字符串
    type_cn = type_mapping.get(update_type, update_type)

    # 构建消息
    lines = []
    lines.append("=" * 50)
    lines.append(f"📢 {type_cn} v{version}")
    lines.append("=" * 50)

    if release_date:
        lines.append(f"📅 发布日期: {release_date}")
        lines.append("-" * 30)

    lines.append("📋 更新内容:")

    # 处理changelog（支持字符串和列表格式）
    if isinstance(changelog, str):
        # 按行分割
        for line in changelog.strip().split('\n'):
            if line.strip():
                lines.append(f"  • {line.strip()}")
    elif isinstance(changelog, list):
        for item in changelog:
            lines.append(f"  • {item}")
    else:
        lines.append(f"  {changelog}")

    if download_url:
        lines.append("-" * 30)
        lines.append(f"🔗 下载地址: {download_url}")

    lines.append("=" * 50)

    return "\n".join(lines)


def check_update(parent=None, gist_url=None):
    """
    检查更新入口函数
    参数:
        parent: 父窗口，用于消息框的父窗口设置
        gist_url: 可选的gist URL，如果为None则使用默认配置
    """
    # 创建并启动工作线程
    worker = UpdateWorker(gist_url)

    def show_update_message(message):
        """显示更新消息"""
        QMessageBox.information(
            parent,
            "📢 更新日志",
            message,
            QMessageBox.StandardButton.Ok,
        )
        worker.deleteLater()

    def show_error_message(error):
        """显示错误消息"""
        QMessageBox.warning(
            parent,
            "⚠️ 检查更新失败",
            f"无法获取更新日志：\n\n{error}",
            QMessageBox.StandardButton.Ok
        )
        worker.deleteLater()

    # 连接信号
    worker.update_found.connect(show_update_message)
    worker.update_error.connect(show_error_message)

    # 启动线程
    worker.start()

    return worker
