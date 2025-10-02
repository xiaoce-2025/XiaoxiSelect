"""
配置管理器，负责加载和保存配置文件
"""

import os
import json
import configparser
from autoelective.environ import Environ
from autoelective.const import DEFAULT_CONFIG_INI,DEFAULT_CONFIG_TTAPI

class ConfigManager:
    """配置管理器类"""
    config_file = ""
    def __init__(self):
        # 使用与 AutoElectiveConfig 相同的路径解析逻辑
        env = Environ()
        self.config_file = env.config_ini or DEFAULT_CONFIG_INI
        ConfigManager.config_file = self.config_file
        self.apikey_file = DEFAULT_CONFIG_TTAPI
    
    # 此处的配置文件读写与选课时的配置文件读写是两套完全独立的逻辑
    # 仅共用配置文件路径
    def load_config(self):
        """加载配置文件"""
        config_data = {}
        
        try:
            # 使用解析后的配置文件路径
            config_path = os.path.normpath(os.path.abspath(self.config_file))
            
            # 加载config.ini
            if os.path.exists(config_path):
                config = configparser.ConfigParser()
                config.read(config_path, encoding='utf-8')
                
                # 加载用户设置
                if 'user' in config:
                    config_data['user'] = {
                        'student_id': config.get('user', 'student_id', fallback=''),
                        'password': config.get('user', 'password', fallback=''),
                        'dual_degree': config.getboolean('user', 'dual_degree', fallback=False),
                        'identity': config.get('user', 'identity', fallback='bzx')
                    }
                
                # 加载客户端设置
                if 'client' in config:
                    config_data['client'] = {
                        'supply_cancel_page': config.getint('client', 'supply_cancel_page', fallback=1),
                        'refresh_interval': config.getfloat('client', 'refresh_interval', fallback=1.0),
                        'random_deviation': config.getfloat('client', 'random_deviation', fallback=0.0),
                        'iaaa_client_timeout': config.getfloat('client', 'iaaa_client_timeout', fallback=10.0),
                        'elective_client_timeout': config.getfloat('client', 'elective_client_timeout', fallback=10.0),
                        'elective_client_pool_size': config.getint('client', 'elective_client_pool_size', fallback=5),
                        'elective_client_max_life': config.getint('client', 'elective_client_max_life', fallback=100),
                        'login_loop_interval': config.getfloat('client', 'login_loop_interval', fallback=1.0),
                        'print_mutex_rules': config.getboolean('client', 'print_mutex_rules', fallback=False),
                        'debug_print_request': config.getboolean('client', 'debug_print_request', fallback=False),
                        'debug_dump_request': config.getboolean('client', 'debug_dump_request', fallback=False)
                    }
                
                # 加载监控设置
                if 'monitor' in config:
                    config_data['monitor'] = {
                        'host': config.get('monitor', 'host', fallback='localhost'),
                        'port': config.getint('monitor', 'port', fallback=5000)
                    }
                
                # 加载通知设置
                '''
                通知设置(前四个为原有设置，弃用)
                yanxx_voice:严小希语音提醒
                yanxx_weixin:严小希微信提醒/控制
                yanxx_weixin_user:严小希微信监听账号
                '''
                if 'notification' in config:
                    config_data['notification'] = {
                        # 'disable_push': config.getboolean('notification', 'disable_push', fallback=False),
                        # 'token': config.get('notification', 'token', fallback=''),
                        # 'verbosity': config.getint('notification', 'verbosity', fallback=1),
                        # 'minimum_interval': config.getfloat('notification', 'minimum_interval', fallback=1.0),
                        'yanxx_voice': config.getboolean('notification', 'yanxx_voice', fallback=False),
                        'yanxx_weixin': config.getboolean('notification', 'yanxx_weixin', fallback=False),
                        'yanxx_weixin_user': config.get('notification', 'yanxx_weixin_user', fallback=''),
                    }
                
                # 加载课程配置
                config_data['courses'] = {}
                config_data['mutex'] = {}
                config_data['delay'] = {}
                
                for section in config.sections():
                    if section.startswith('course:'):
                        course_id = section[7:]  # 去掉 'course:' 前缀
                        config_data['courses'][course_id] = dict(config.items(section))
                    
                    elif section.startswith('mutex:'):
                        mutex_id = section[6:]  # 去掉 'mutex:' 前缀
                        courses = config.get(section, 'courses', fallback='').split(',')
                        courses = [c.strip() for c in courses if c.strip()]
                        config_data['mutex'][mutex_id] = courses
                    
                    elif section.startswith('delay:'):
                        delay_id = section[6:]  # 去掉 'delay:' 前缀
                        config_data['delay'][delay_id] = {
                            'course': config.get(section, 'course', fallback=''),
                            'threshold': config.getint(section, 'threshold', fallback= 10)
                        }
            
            # 加载apikey.json
            apikey_path = os.path.normpath(os.path.abspath(self.apikey_file))
            if os.path.exists(apikey_path):
                with open(apikey_path, 'r', encoding='utf-8') as f:
                    apikey_data = json.load(f)
                    config_data['apikey'] = apikey_data
        
        except Exception as e:
            raise Exception(f"加载配置文件失败: {str(e)}")
        
        return config_data
    
    def save_config(self, config_data):
        """保存配置文件"""
        try:
            # 保存config.ini
            config = configparser.ConfigParser()
            
            # 用户设置
            if 'user' in config_data:
                config.add_section('user')
                for key, value in config_data['user'].items():
                    config.set('user', key, str(value))
            
            # 客户端设置
            if 'client' in config_data:
                config.add_section('client')
                for key, value in config_data['client'].items():
                    config.set('client', key, str(value))
            
            # 监控设置
            if 'monitor' in config_data:
                config.add_section('monitor')
                for key, value in config_data['monitor'].items():
                    config.set('monitor', key, str(value))
            
            # 通知设置
            if 'notification' in config_data:
                config.add_section('notification')
                for key, value in config_data['notification'].items():
                    config.set('notification', key, str(value))
            
            # 保存课程配置
            if 'courses' in config_data:
                for course_id, course_data in config_data['courses'].items():
                    section_name = f"course:{course_id}"
                    config.add_section(section_name)
                    for key, value in course_data.items():
                        config.set(section_name, key, value)
            
            # 保存互斥规则配置
            if 'mutex' in config_data:
                for mutex_id, courses in config_data['mutex'].items():
                    section_name = f"mutex:{mutex_id}"
                    config.add_section(section_name)
                    config.set(section_name, 'courses', ', '.join(courses))
            
            # 保存延迟规则配置
            if 'delay' in config_data:
                for delay_id, delay_data in config_data['delay'].items():
                    section_name = f"delay:{delay_id}"
                    config.add_section(section_name)
                    for key, value in delay_data.items():
                        config.set(section_name, key, str(value))
            
            # 使用解析后的配置文件路径
            config_path = os.path.normpath(os.path.abspath(self.config_file))
            with open(config_path, 'w', encoding='utf-8') as f:
                config.write(f)
            
            # 保存apikey.json
            apikey_path = os.path.normpath(os.path.abspath(self.apikey_file))
            if 'apikey' in config_data:
                with open(apikey_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data['apikey'], f, indent=4, ensure_ascii=False)
        
        except Exception as e:
            raise Exception(f"保存配置文件失败: {str(e)}")
    
    # 读取提醒配置
    @classmethod
    def get_notification_settings(cls):
        try:
            # 使用解析后的配置文件路径
            config_path = os.path.normpath(os.path.abspath(cls.config_file))
            
            # 加载config.ini
            if os.path.exists(config_path):
                config = configparser.ConfigParser()
                config.read(config_path, encoding='utf-8')

                if 'notification' in config:
                    return {
                        'yanxx_voice': config.getboolean('notification', 'yanxx_voice', fallback=False),
                        'yanxx_weixin': config.getboolean('notification', 'yanxx_weixin', fallback=False),
                        'yanxx_weixin_user': config.get('notification', 'yanxx_weixin_user', fallback=''),
                    }
        except Exception as e:
            raise Exception(f"读取通知提醒配置失败: {str(e)}")
        
        return {}