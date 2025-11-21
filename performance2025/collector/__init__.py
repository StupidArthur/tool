"""数据采集模块"""
from .base import BaseCollector, ProcessInfo, SystemInfo
from .windows_collector import WindowsCollector
from .linux_collector import LinuxCollector
from .collector_factory import create_collector

__all__ = [
    'BaseCollector',
    'ProcessInfo',
    'SystemInfo',
    'WindowsCollector',
    'LinuxCollector',
    'create_collector'
]

