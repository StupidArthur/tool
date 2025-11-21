"""平台工具函数"""
import platform
from enum import Enum


class Platform(Enum):
    """支持的平台"""
    WINDOWS = "windows"
    LINUX = "linux"
    UNKNOWN = "unknown"


def get_platform() -> Platform:
    """获取当前操作系统平台"""
    system = platform.system().lower()
    if system == "windows":
        return Platform.WINDOWS
    elif system == "linux":
        return Platform.LINUX
    else:
        return Platform.UNKNOWN


def get_timestamp_string() -> str:
    """获取时间戳字符串（到秒），格式：YYYYMMDD_HHMMSS"""
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")

