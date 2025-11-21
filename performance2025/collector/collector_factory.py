"""采集器工厂"""
from utils.platform_utils import get_platform, Platform
from .windows_collector import WindowsCollector
from .linux_collector import LinuxCollector
from .base import BaseCollector


def create_collector() -> BaseCollector:
    """根据当前平台创建对应的采集器"""
    platform_type = get_platform()
    
    if platform_type == Platform.WINDOWS:
        return WindowsCollector()
    elif platform_type == Platform.LINUX:
        return LinuxCollector()
    else:
        raise NotImplementedError(f"不支持的平台: {platform_type}")

