#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立刷课子进程入口。"""

import sys
from multiprocessing import Queue
from optparse import OptionParser

from .environ import Environ


def _create_worker_parser():
    """创建子进程专用的命令行解析器（扩展 cli 的 parser）。"""
    from .cli import create_default_parser
    parser = create_default_parser()
    parser.add_option(
        '--log-port',
        dest='log_port',
        type='int',
        default=0,
        help='GUI log server port for socket-based log delivery',
    )
    return parser


def _init_notifications():
    """初始化通知管理器，注册 WeChat CLI Handler。"""
    from .notification.manager import notification_manager, WeChatCLIHandler
    # 注册微信 CLI 推送（接口预留，后续补充实现）
    notification_manager.register(WeChatCLIHandler())
    notification_manager.start()


def _init_socket_logging(port: int) -> bool:
    """初始化 Socket 日志连接。"""
    if port <= 0:
        return False
    from handlers.log_server import init_socket_logging
    return init_socket_logging(port)


def run_worker():
    """在独立进程中启动刷课线程组。"""
    environ = Environ()

    parser = _create_worker_parser()
    options, args = parser.parse_args()

    from .cli import setup_default_environ, create_default_threads_reload
    setup_default_environ(options, args, environ)

    # 初始化 Socket 日志（连接 GUI 日志服务器）
    log_port = getattr(options, 'log_port', 0)
    socket_ok = _init_socket_logging(log_port)
    if log_port > 0 and not socket_ok:
        print("[WARN] Failed to connect to GUI log server on port %d" % log_port, file=sys.stderr)

    # 初始化通知管理器
    _init_notifications()

    threads = create_default_threads_reload(options, args, environ)
    for thread in threads:
        thread.daemon = True
        thread.start()

    # 保持主线程存活，直到被外部终止。
    try:
        Queue().get()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run_worker()
