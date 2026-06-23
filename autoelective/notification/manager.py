"""
统一通知管理器。

设计原则：
  - 通知投递是异步的，绝不阻塞调用线程（选课线程）
  - 通过注册 Handler 实现可插拔推送渠道（WeChat CLI、Bark 等）
  - 后台单线程消费通知队列，推送失败不影响主逻辑
"""

import logging
import threading
from typing import List, Optional
from queue import Queue, Empty
from abc import ABC, abstractmethod

_cout = logging.getLogger("notify")


# ────────────────────────── Handler 接口 ──────────────────────────

class NotifyHandler(ABC):
    """通知推送渠道的抽象基类。"""

    @abstractmethod
    def send(self, msg: str, prefix: str = "", level: int = 0) -> None:
        """发送一条通知。

        Args:
            msg: 通知正文
            prefix: 前缀标签（如 [成功]、[异常]）
            level: 通知等级，0=普通，1=重要，2=紧急
        """


# ────────────────────────── WeChat CLI Handler（接口预留） ──────────────────────────

class WeChatCLIHandler(NotifyHandler):
    """通过微信 CLI 工具发送通知（待实现）。

    TODO: 接入具体的微信 CLI 工具，例如：
      - wxauto4（PC 微信自动化）
      - wechat-cli（命令行工具）
      - 其他微信消息推送方案

    实现时只需完成 send() 方法即可。
    """

    def __init__(self, target: str = ""):
        """
        Args:
            target: 接收通知的微信用户/群名称
        """
        self._target = target

    def send(self, msg: str, prefix: str = "", level: int = 0) -> None:
        # TODO: 实现微信 CLI 推送
        # 示例（伪代码）：
        #   from wxauto4 import WeChat
        #   wx = WeChat()
        #   full_msg = f"{prefix}{msg}" if prefix else msg
        #   wx.SendMsg(self._target, full_msg)
        #   wx.StopListening()
        pass


# ────────────────────────── 通知管理器 ──────────────────────────

class NotificationManager:
    """异步通知管理器。

    - 调用 send() 将通知入队，立即返回
    - 后台线程逐条消费并分发给已注册的 Handler
    - Handler 异常不会影响选课线程
    """

    def __init__(self):
        self._handlers = []  # type: List[NotifyHandler]
        self._queue = Queue()
        self._running = False
        self._thread = None  # type: Optional[threading.Thread]

    def register(self, handler: NotifyHandler) -> None:
        """注册一个通知推送渠道。"""
        self._handlers.append(handler)

    def start(self) -> None:
        """启动后台消费线程。重复调用安全。"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._consume_loop, name="NotifyWorker", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """停止后台消费线程。"""
        self._running = False
        # 放入哨兵值唤醒阻塞的 get()
        self._queue.put(None)

    def send(self, msg: str, prefix: str = "", level: int = 0) -> None:
        """发送一条通知（非阻塞，线程安全）。

        Args:
            msg: 通知正文
            prefix: 前缀标签
            level: 通知等级
        """
        if not msg:
            return
        self._queue.put((msg, prefix, level))

    def _consume_loop(self) -> None:
        """后台消费循环。"""
        while self._running:
            try:
                item = self._queue.get(timeout=1.0)
            except Empty:
                continue
            if item is None:  # 哨兵值
                break
            msg, prefix, level = item
            for handler in self._handlers:
                try:
                    handler.send(msg=msg, prefix=prefix, level=level)
                except Exception as e:
                    # Handler 异常不能影响消费循环
                    _cout.warning("NotifyHandler error: %s" % e)


# ────────────────────────── 全局实例 ──────────────────────────

notification_manager = NotificationManager()


def send_notify(msg: str, prefix: str = "", level: int = 0) -> None:
    """便捷函数：向全局通知管理器发送一条通知（非阻塞）。"""
    notification_manager.send(msg=msg, prefix=prefix, level=level)
