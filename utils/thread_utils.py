"""
线程工具函数
"""

import autoelective.loop

def cleanup_environment(environ):
    """清理环境状态"""
    try:
        # 清理环境中的线程引用
        if hasattr(environ, 'iaaa_loop_thread'):
            environ.iaaa_loop_thread = None
        if hasattr(environ, 'elective_loop_thread'):
            environ.elective_loop_thread = None
        if hasattr(environ, 'monitor_thread'):
            environ.monitor_thread = None
        
        # 重置环境状态
        environ.__init__()
        
        # 清理全局队列
        cleanup_global_queues()
        
        return True
        
    except Exception as e:
        return False

def cleanup_global_queues():
    """清理全局队列"""
    try:
        # 清空队列
        if hasattr(autoelective.loop, 'electivePool'):
            while not autoelective.loop.electivePool.empty():
                try:
                    autoelective.loop.electivePool.get_nowait()
                except:
                    break
        
        if hasattr(autoelective.loop, 'reloginPool'):
            while not autoelective.loop.reloginPool.empty():
                try:
                    autoelective.loop.reloginPool.get_nowait()
                except:
                    break
        
        # 重置环境变量
        if hasattr(autoelective.loop, 'environ'):
            from autoelective.environ import Environ
            autoelective.loop.environ = Environ()
        
        return True
        
    except Exception as e:
        return False

def verify_clean_state(environ):
    """验证清理状态"""
    try:
        # 检查队列是否为空
        if hasattr(autoelective.loop, 'electivePool') and not autoelective.loop.electivePool.empty():
            return False
        
        if hasattr(autoelective.loop, 'reloginPool') and not autoelective.loop.reloginPool.empty():
            return False
        
        # 检查环境状态
        if hasattr(environ, 'iaaa_loop_thread') and environ.iaaa_loop_thread is not None:
            return False
        
        return True
        
    except Exception as e:
        return False