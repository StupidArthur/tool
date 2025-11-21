"""Linux 平台数据采集器（预留实现）"""
import psutil
from typing import List, Optional
from datetime import datetime
from .base import BaseCollector, ProcessInfo, SystemInfo


class LinuxCollector(BaseCollector):
    """Linux 平台数据采集器实现（预留）"""
    
    def get_process_list_fast(self) -> List[ProcessInfo]:
        """快速获取进程列表（仅基本信息，用于显示列表）"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pinfo = proc.info
                process_info = ProcessInfo(
                    pid=pinfo['pid'],
                    name=pinfo['name'],
                    command_line='',
                    user='N/A',
                    cpu_percent=0.0,
                    memory_mb=0.0,
                    extra_metrics={}
                )
                processes.append(process_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return processes
    
    def get_all_processes(self) -> List[ProcessInfo]:
        """获取所有进程信息"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'username', 'cpu_percent', 'memory_info']):
            try:
                pinfo = proc.info
                cpu_percent = proc.cpu_percent(interval=None)  # 非阻塞模式
                
                memory_info = pinfo.get('memory_info')
                memory_mb = memory_info.rss / 1024 / 1024 if memory_info else 0
                
                cmdline = pinfo.get('cmdline', [])
                command_line = ' '.join(cmdline) if cmdline else ''
                
                username = pinfo.get('username', 'N/A')
                
                process_info = ProcessInfo(
                    pid=pinfo['pid'],
                    name=pinfo['name'],
                    command_line=command_line,
                    user=username or 'N/A',
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
                    extra_metrics={
                        'num_threads': proc.num_threads(),
                        'num_fds': proc.num_fds() if hasattr(proc, 'num_fds') else 0,
                        'io_read_bytes': proc.io_counters().read_bytes if proc.io_counters() else 0,
                        'io_write_bytes': proc.io_counters().write_bytes if proc.io_counters() else 0,
                    }
                )
                processes.append(process_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return processes
    
    def get_process_by_pid(self, pid: int) -> Optional[ProcessInfo]:
        """根据PID获取进程信息"""
        try:
            proc = psutil.Process(pid)
            cpu_percent = proc.cpu_percent(interval=None)  # 非阻塞模式
            memory_info = proc.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            cmdline = proc.cmdline()
            command_line = ' '.join(cmdline) if cmdline else ''
            
            username = proc.username()
            
            return ProcessInfo(
                pid=pid,
                name=proc.name(),
                command_line=command_line,
                user=username or 'N/A',
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                extra_metrics={
                    'num_threads': proc.num_threads(),
                    'num_fds': proc.num_fds() if hasattr(proc, 'num_fds') else 0,
                    'io_read_bytes': proc.io_counters().read_bytes if proc.io_counters() else 0,
                    'io_write_bytes': proc.io_counters().write_bytes if proc.io_counters() else 0,
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
    
    def get_processes_by_name(self, name: str) -> List[ProcessInfo]:
        """根据进程名获取进程信息（不区分大小写）"""
        processes = []
        name_lower = name.lower()
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() == name_lower:
                    process_info = self.get_process_by_pid(proc.info['pid'])
                    if process_info:
                        processes.append(process_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return processes
    
    def get_system_info(self) -> SystemInfo:
        """获取系统信息"""
        cpu_percent = psutil.cpu_percent(interval=None)  # 非阻塞模式
        memory = psutil.virtual_memory()
        
        return SystemInfo(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_total_mb=memory.total / 1024 / 1024,
            memory_used_mb=memory.used / 1024 / 1024,
            memory_percent=memory.percent,
            extra_metrics={
                'cpu_count': psutil.cpu_count(),
                'cpu_freq': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                'load_avg': psutil.getloadavg(),
                'disk_usage': {
                    'total': psutil.disk_usage('/').total / 1024 / 1024 / 1024,  # GB
                    'used': psutil.disk_usage('/').used / 1024 / 1024 / 1024,
                    'free': psutil.disk_usage('/').free / 1024 / 1024 / 1024,
                },
                'network_io': {
                    'bytes_sent': psutil.net_io_counters().bytes_sent if psutil.net_io_counters() else 0,
                    'bytes_recv': psutil.net_io_counters().bytes_recv if psutil.net_io_counters() else 0,
                }
            }
        )

