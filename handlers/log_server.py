"""
基于 Socket 的日志服务器，用于子进程 → GUI 的结构化日志通信。

架构：
  - GUI 启动时在随机端口开启 TCP 服务器
  - 子进程通过 SocketLogHandler 连接服务器，发送 JSON 格式的日志
  - GUI 主线程通过 Qt 信号接收结构化日志，无需正则解析

日志 JSON 格式：
  {"level": "INFO", "name": "loop", "message": "...", "timestamp": "12:34:56"}
"""

import json
import logging
import socket
import threading
from typing import Optional
from queue import Queue, Empty
from PyQt6.QtCore import QObject, pyqtSignal


class LogSignalBridge(QObject):
    """Qt 信号桥接：从非 Qt 线程安全地传递日志到 GUI 线程。"""
    log_received = pyqtSignal(dict)  # {"level", "name", "message", "timestamp"}


class LogServer:
    """TCP 日志服务器。

    在后台线程运行，接收子进程发来的 JSON 日志，
    通过 Qt 信号转发给 GUI 主线程。
    """

    def __init__(self):
        self._server_socket = None  # type: Optional[socket.socket]
        self._port = 0  # type: int
        self._running = False
        self._thread = None  # type: Optional[threading.Thread]
        self._bridge = LogSignalBridge()
        # 所有客户端连接线程共享此信号
        self.log_received = self._bridge.log_received

    @property
    def port(self) -> int:
        """服务器监听端口（start() 后可用）。"""
        return self._port

    def start(self) -> int:
        """启动日志服务器，返回监听端口。"""
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind(("127.0.0.1", 0))  # 随机端口
        self._port = self._server_socket.getsockname()[1]
        self._server_socket.listen(5)
        self._server_socket.settimeout(1.0)

        self._running = True
        self._thread = threading.Thread(
            target=self._accept_loop, name="LogServer", daemon=True
        )
        self._thread.start()
        return self._port

    def stop(self) -> None:
        """停止日志服务器。"""
        self._running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass
            self._server_socket = None

    def _accept_loop(self) -> None:
        """接受客户端连接的主循环。"""
        while self._running:
            try:
                client_sock, addr = self._server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            # 每个客户端独立线程处理
            t = threading.Thread(
                target=self._handle_client,
                args=(client_sock,),
                name="LogClient-%s:%d" % addr,
                daemon=True,
            )
            t.start()

    def _handle_client(self, sock: socket.socket) -> None:
        """处理单个客户端连接，逐行读取 JSON 日志。"""
        buffer = ""
        try:
            sock.settimeout(None)
            fp = sock.makefile("r", encoding="utf-8")
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    # 通过 Qt 信号发送到 GUI 线程
                    self._bridge.log_received.emit(record)
                except json.JSONDecodeError:
                    pass  # 忽略格式错误的行
            fp.close()
        except (ConnectionResetError, BrokenPipeError, OSError):
            pass
        finally:
            try:
                sock.close()
            except OSError:
                pass


class SocketLogHandler:
    """Socket 日志 Handler（供子进程使用）。

    替代 stdout 输出，直接发送结构化 JSON 日志到 GUI。
    实现 logging.Handler 接口。
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        self._host = host
        self._port = port
        self._socket = None  # type: Optional[socket.socket]
        self._lock = threading.Lock()
        self._connected = False

    def connect(self) -> bool:
        """连接到日志服务器。返回是否成功。"""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self._host, self._port))
            self._connected = True
            return True
        except (ConnectionRefusedError, OSError):
            self._socket = None
            self._connected = False
            return False

    def emit(self, level: str, name: str, message: str, timestamp: str) -> None:
        """发送一条日志记录（非阻塞，失败则丢弃）。"""
        if not self._connected:
            return
        record = {
            "level": level,
            "name": name,
            "message": message,
            "timestamp": timestamp,
        }
        try:
            data = json.dumps(record, ensure_ascii=False) + "\n"
            with self._lock:
                self._socket.sendall(data.encode("utf-8"))
        except (BrokenPipeError, ConnectionResetError, OSError):
            self._connected = False

    def close(self) -> None:
        """关闭连接。"""
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None
            self._connected = False


class PythonSocketHandler(logging.Handler):
    """Python logging.Handler 适配器，将标准日志转发到 Socket。

    可直接添加到 root logger，所有已有 logger 自动生效。
    """

    def __init__(self, socket_handler: SocketLogHandler):
        super().__init__()
        self._socket_handler = socket_handler
        self.setFormatter(logging.Formatter(
            "[%(levelname)s] %(name)s, %(asctime)s, %(message)s", "%H:%M:%S"
        ))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self._socket_handler.emit(
                level=record.levelname,
                name=record.name,
                message=msg,
                timestamp=self.formatTime(record, "%H:%M:%S"),
            )
        except Exception:
            pass  # 不能因为日志发送失败影响主逻辑


# ────────────────────────── 全局实例（子进程侧） ──────────────────────────

_socket_handler = None  # type: Optional[SocketLogHandler]
_python_socket_handler = None  # type: Optional[PythonSocketHandler]


def init_socket_logging(port: int) -> bool:
    """初始化 Socket 日志（子进程启动时调用）。

    连接成功后会自动将 PythonSocketHandler 添加到 root logger，
    使得所有已有的 ConsoleLogger / FileLogger 输出同时通过 Socket 发送给 GUI。

    Args:
        port: GUI 日志服务器的端口

    Returns:
        是否连接成功
    """
    global _socket_handler, _python_socket_handler
    _socket_handler = SocketLogHandler(port=port)
    if not _socket_handler.connect():
        return False

    _python_socket_handler = PythonSocketHandler(_socket_handler)
    logging.getLogger().addHandler(_python_socket_handler)
    return True


def get_socket_handler():  # type: () -> Optional[SocketLogHandler]
    """获取全局 Socket 日志 Handler。"""
    return _socket_handler
