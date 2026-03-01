"""
@Author : xiaoce2025
@File   : update_check.py
@Date   : 2025-12-31
"""

"""更新检查模块"""

from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QUrl
from version.get_updater import check_for_updates
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, List
from PyQt6.QtWidgets import QMessageBox

This_version = "1.3.0"
New_Download_URL = QUrl("https://github.com/xiaoce-2025/XiaoxiSelect")


class UpdateWorker(QThread):
    """更新检查工作线程"""

    # 定义信号
    update_found = pyqtSignal(str)  # 发现更新
    update_found_necessary = pyqtSignal(str)  # 发现必要更新
    update_error = pyqtSignal(str)  # 发生错误
    have_necessary_update = False

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
                message, have_necessary_update = format_update_message(data)

            if success and message == "[INFO]拉取更新成功！当前版本已是最新！":
                pass
            elif success and message and have_necessary_update:
                self.update_found_necessary.emit(message)
            elif success and message:
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


# 比较版本号大小
def compare_versions(version1: str, version2: str) -> int:
    """
    比较两个版本号的大小

    Args:
        version1: 版本号1，如"1.1.4"
        version2: 版本号2，如"1.1.5"

    Returns:
        1: version1 > version2
        0: version1 == version2
       -1: version1 < version2
    """
    try:
        v1_parts = [int(part) for part in version1.split('.')]
        v2_parts = [int(part) for part in version2.split('.')]

        # 补齐长度
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts += [0] * (max_len - len(v1_parts))
        v2_parts += [0] * (max_len - len(v2_parts))

        for v1, v2 in zip(v1_parts, v2_parts):
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1

        return 0
    except (ValueError, AttributeError):
        # 如果版本号格式错误，则视为不满足更新条件
        return -1


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
    have_necessary_update = False
    update_data = data.get('data')
    if not update_data:
        return "[连接正常，但未拉取到有效更新信息]"

    formatted_messages = []
    for single_update_data in update_data:
        # 获取版本号
        full_version = single_update_data.get('version', '')
        if not full_version:
            continue

        # 从完整版本号中提取最后的数字版本号
        # 版本号格式如"2025-Autumn-1.1.4"
        version_parts = full_version.split('-')
        if not version_parts:
            continue

        # 获取最后一部分，即数字版本号
        numeric_version = version_parts[-1]

        # 比较版本号，只有当新版本大于当前版本时才显示
        if compare_versions(numeric_version, This_version) <= 0:
            continue

        if (not have_necessary_update) and single_update_data.get('type', '') == "CriticalBugFix":
            have_necessary_update = True

        formatted_message = format_single_update_message(single_update_data)
        formatted_messages.append(formatted_message)

    # 在消息之间添加一个空行作为分隔
    if not formatted_messages:
        return "[INFO]拉取更新成功！当前版本已是最新！", False

    return "\n\n".join(formatted_messages), have_necessary_update


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
        msg_box = QMessageBox(
            QMessageBox.Icon.Information,
            "有新版本可用！",
            message,
            QMessageBox.StandardButton.NoButton,
            parent
        )
        # 创建自定义按钮
        ok_button = msg_box.addButton(
            "前往下载新版本", QMessageBox.ButtonRole.ActionRole)
        cancel_button = msg_box.addButton(
            "我知道了", QMessageBox.ButtonRole.RejectRole)

        msg_box.show()

        # 连接按钮点击信号
        def on_update_clicked():
            QDesktopServices.openUrl(New_Download_URL)
            worker.deleteLater()

        def on_cancel_clicked():
            msg_box.close()
            worker.deleteLater()

        ok_button.clicked.connect(on_update_clicked)
        cancel_button.clicked.connect(on_cancel_clicked)

    def show_update_necessary_message(message):
        """显示更新消息"""
        msg_box = QMessageBox(
            QMessageBox.Icon.Information,
            "有重要更新可用！请立即更新！",
            message,
            QMessageBox.StandardButton.NoButton,
            parent
        )
        # 创建自定义按钮
        ok_button = msg_box.addButton(
            "前往下载新版本", QMessageBox.ButtonRole.ActionRole)
        cancel_button = msg_box.addButton(
            "退出程序", QMessageBox.ButtonRole.RejectRole)

        msg_box.show()

        # 连接按钮点击信号
        def on_update_clicked():
            QDesktopServices.openUrl(New_Download_URL)
            worker.deleteLater()
            QApplication.quit()

        def on_cancel_clicked():
            msg_box.close()
            worker.deleteLater()
            QApplication.quit()

        ok_button.clicked.connect(on_update_clicked)
        cancel_button.clicked.connect(on_cancel_clicked)

    def show_error_message(error):
        """显示错误消息"""
        QMessageBox.warning(
            parent,
            "检查更新失败",
            f"无法获取更新日志",
            QMessageBox.StandardButton.Ok
        )
        worker.deleteLater()

    # 连接信号
    worker.update_found.connect(show_update_message)
    worker.update_error.connect(show_error_message)
    worker.update_found_necessary.connect(show_update_necessary_message)

    # 启动线程
    worker.start()

    return worker
