#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立刷课子进程入口。"""

from multiprocessing import Queue

from .cli import (
    create_default_parser,
    create_default_threads_reload,
    setup_default_environ,
)
from .environ import Environ


def run_worker():
    """在独立进程中启动刷课线程组。"""
    environ = Environ()

    parser = create_default_parser()
    options, args = parser.parse_args()

    setup_default_environ(options, args, environ)

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
