"""
@Author : xiaoce2025
@File   : updater.py
@Date   : 2025-12-31
"""

"""更新检查模块，处理Gist请求和日志解析"""

# 这个链接地址必须是github的gist，其他可能需要调整后续校验
UPDATE_URL = "https://gist.githubusercontent.com/xiaoce-2025/d3015a91983023f19c4575f828f7f54b/raw/log.json"

import requests
import json
from typing import Optional, Dict, Tuple
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UpdateChecker:
    """Gist更新检查器"""
    
    def __init__(self, gist_url: str, timeout: int = 10):
        """
        初始化更新检查器
        
        Args:
            gist_url: Gist的raw文件URL
            timeout: 请求超时时间（秒）
        """
        self.gist_url = gist_url
        self.timeout = timeout
        self.last_check_time = None
        self.last_check_result = None
    
    def fetch_update_log(self) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        从Gist获取更新日志
        
        Returns:
            (success, data, error_message)
            success: 是否成功
            data: 成功时的数据字典
            error_message: 失败时的错误信息
        """
        try:
            logger.info(f"正在拉取更新日志")
            
            # 发送HTTP请求
            response = requests.get(
                self.gist_url,
                timeout=self.timeout,
                headers={
                    'User-Agent': 'ConsoleApp/1.0',
                    'Accept': 'application/json'
                }
            )
            
            # 检查HTTP状态码
            response.raise_for_status()
            
            # 解析JSON响应
            data = response.json()
            
            # 验证必要字段
            if not self._validate_update_data(data):
                error_msg = "更新日志格式不正确，缺少必要字段"
                logger.error(error_msg)
                return False, None, error_msg
            
            # 记录检查时间
            self.last_check_time = datetime.now().isoformat()
            self.last_check_result = data
            
            logger.info("成功获取更新日志")
            return True, data, None
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析失败: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
            
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _validate_update_data(self, data: Dict) -> bool:
        """验证更新数据格式"""
        required_fields = ['data']
        
        for field in required_fields:
            if field not in data:
                logger.warning(f"更新数据缺少必要字段: {field}")
                return False
        
        return True
   
    def get_last_check_info(self) -> Dict:
        """获取最后一次检查的信息"""
        return {
            'last_check_time': self.last_check_time,
            'last_check_result': self.last_check_result
        }


# 单例实例
_default_checker = None


def get_default_checker(gist_url: str = None) -> UpdateChecker:
    """
    获取默认的更新检查器实例
    
    Args:
        gist_url: 如果提供，将创建新的检查器
        
    Returns:
        UpdateChecker实例
    """
    global _default_checker
    
    if gist_url is not None or _default_checker is None:
        if gist_url is None:
            # 获取更新推送的地址
            gist_url = UPDATE_URL
        _default_checker = UpdateChecker(gist_url)
    
    return _default_checker


def check_for_updates(gist_url: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    检查更新的便捷函数
    
    Args:
        gist_url: Gist URL，如果为None则使用默认
        
    Returns:
        (success, message, error)
        success: 是否成功
        message: 成功时的格式化消息
        error: 失败时的错误消息
    """
    checker = get_default_checker(gist_url)
    success, data, error = checker.fetch_update_log()
    
    if success and data:
        return True, data, None
    else:
        return False, None, error