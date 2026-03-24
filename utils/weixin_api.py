"""微信 API 运行期管理。"""

import threading
import importlib
from pathlib import Path


def _ensure_wxauto_importable():
    import sys

    root = Path(__file__).resolve().parent.parent
    src = root / "wxauto" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


class WeixinApiManager:
    """管理单个微信 API 会话的生命周期。"""

    def __init__(self):
        self._session = None

    def start_listener(self):
        """创建会话并静默启动监听。"""
        self.stop()

        _ensure_wxauto_importable()
        api_module = importlib.import_module("weixin_platform.api")
        WeixinApiSession = getattr(api_module, "WeixinApiSession")

        self._session = WeixinApiSession()

        try:
            self._session.start_listener_silent()
        except Exception:
            # 允许失败：只要会话可用，后续发送仍可按底层状态尝试。
            pass

    def send(self, text: str):
        """发送微信消息。"""
        if self._session is None:
            raise RuntimeError("Weixin API session is not started")
        return str(self._session.sendmessage(text))

    def stop(self):
        """关闭会话。"""
        if self._session is not None:
            try:
                self._session.close()
            finally:
                self._session = None


_lock = threading.Lock()
_active_manager = None


def create_and_start_active_weixin_api():
    """创建并启动全局活动微信 API。"""
    global _active_manager
    with _lock:
        if _active_manager is not None:
            _active_manager.stop()
        _active_manager = WeixinApiManager()
        _active_manager.start_listener()
        return _active_manager


def get_active_weixin_api():
    """获取全局活动微信 API。"""
    return _active_manager


def stop_active_weixin_api():
    """停止并清理全局活动微信 API。"""
    global _active_manager
    with _lock:
        if _active_manager is not None:
            _active_manager.stop()
            _active_manager = None
