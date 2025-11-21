"""基础采集器接口"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class ProcessInfo:
    """进程信息"""
    pid: int
    name: str
    command_line: str
    user: str
    cpu_percent: float
    memory_mb: float
    # 其他操作系统特定的资源指标
    extra_metrics: dict = None
    
    def __post_init__(self):
        if self.extra_metrics is None:
            self.extra_metrics = {}


@dataclass
class SystemInfo:
    """系统信息"""
    timestamp: datetime
    cpu_percent: float
    memory_total_mb: float
    memory_used_mb: float
    memory_percent: float
    # 其他系统指标
    extra_metrics: dict = None
    
    def __post_init__(self):
        if self.extra_metrics is None:
            self.extra_metrics = {}


class BaseCollector(ABC):
    """基础采集器抽象类"""
    
    @abstractmethod
    def get_all_processes(self) -> List[ProcessInfo]:
        """获取所有进程信息（包含详细指标，可能较慢）"""
        pass
    
    @abstractmethod
    def get_process_list_fast(self) -> List[ProcessInfo]:
        """快速获取进程列表（仅基本信息，用于显示列表）"""
        pass
    
    @abstractmethod
    def get_process_by_pid(self, pid: int) -> Optional[ProcessInfo]:
        """根据PID获取进程信息"""
        pass
    
    @abstractmethod
    def get_processes_by_name(self, name: str) -> List[ProcessInfo]:
        """根据进程名获取进程信息"""
        pass
    
    @abstractmethod
    def get_system_info(self) -> SystemInfo:
        """获取系统信息"""
        pass

