"""
@Author : xiaoce2025
@File   : cli.py
@Date   : 2025-08-30
"""

from optparse import OptionParser
from threading import Thread
from multiprocessing import Queue
from . import __version__, __date__


def create_default_parser():

    parser = OptionParser(
        description='PKU Auto-Elective Tool v%s (%s)' % (__version__, __date__),
        version=__version__,
    )

    ## custom input files

    parser.add_option(
        '-c',
        '--config',
        dest='config_ini',
        metavar="FILE",
        help='custom config file encoded with utf8',
    )

    ## boolean (flag) options

    parser.add_option(
        '-m',
        '--with-monitor',
        dest='with_monitor',
        action='store_true',
        default=False,
        help='run the monitor thread simultaneously',
    )

    return parser


def setup_default_environ(options, args, environ):

    environ.config_ini = options.config_ini
    environ.with_monitor = options.with_monitor


def create_default_threads_reload(options, args, environ):
    # 重新加载主配置
    from .config import AutoElectiveConfig
    config = AutoElectiveConfig()
    config.reload()
    # 重新加载TT识图API配置
    from .captcha.online import APIConfig
    # 获取或创建全局APIConfig实例
    if not hasattr(environ, 'api_config'):
        environ.api_config = APIConfig()
    # 调用重载方法
    environ.api_config.reload()

    # 刷新配置
    from autoelective.loop import refreshsettings
    refreshsettings()

    # import here to ensure the singleton `config` will be init later than parse_args()
    from autoelective.loop import run_iaaa_loop, run_elective_loop
    from autoelective.monitor import run_monitor

    tList = []

    t = Thread(target=run_iaaa_loop, name="IAAA")
    environ.iaaa_loop_thread = t
    tList.append(t)

    t = Thread(target=run_elective_loop, name="Elective")
    environ.elective_loop_thread = t
    tList.append(t)

    if options.with_monitor:
        t = Thread(target=run_monitor, name="Monitor")
        environ.monitor_thread = t
        tList.append(t)

    return tList


def create_default_threads(options, args, environ):
    # import here to ensure the singleton `config` will be init later than parse_args()
    from autoelective.loop import run_iaaa_loop, run_elective_loop
    from autoelective.monitor import run_monitor

    tList = []

    t = Thread(target=run_iaaa_loop, name="IAAA")
    environ.iaaa_loop_thread = t
    tList.append(t)

    t = Thread(target=run_elective_loop, name="Elective")
    environ.elective_loop_thread = t
    tList.append(t)

    if options.with_monitor:
        t = Thread(target=run_monitor, name="Monitor")
        environ.monitor_thread = t
        tList.append(t)

    return tList


def run():

    from .environ import Environ

    environ = Environ()

    parser = create_default_parser()
    options, args = parser.parse_args()

    setup_default_environ(options, args, environ)

    tList = create_default_threads(options, args, environ)

    for t in tList:
        t.daemon = True
        t.start()

    #
    # Don't use join() to block the main thread, or Ctrl + C in Windows can't work.
    #
    # for t in tList:
    #     t.join()
    #
    try:
        Queue().get()
    except KeyboardInterrupt as e:
        pass
