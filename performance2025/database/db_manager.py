"""数据库管理器"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from collector.base import ProcessInfo, SystemInfo


class DatabaseManager:
    """SQLite3 数据库管理器"""
    
    def __init__(self, db_path: str):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self) -> None:
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建进程信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                pid INTEGER NOT NULL,
                name TEXT NOT NULL,
                command_line TEXT,
                user TEXT,
                cpu_percent REAL,
                memory_mb REAL,
                extra_metrics TEXT,
                UNIQUE(timestamp, pid)
            )
        ''')
        
        # 创建系统信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL UNIQUE,
                cpu_percent REAL,
                memory_total_mb REAL,
                memory_used_mb REAL,
                memory_percent REAL,
                extra_metrics TEXT
            )
        ''')
        
        # 创建索引以提高查询性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_processes_timestamp ON processes(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_processes_pid ON processes(pid)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_processes_name ON processes(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_info_timestamp ON system_info(timestamp)')
        
        conn.commit()
        conn.close()
    
    def insert_process_info(self, process_info: ProcessInfo) -> None:
        """插入进程信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        extra_metrics_json = json.dumps(process_info.extra_metrics) if process_info.extra_metrics else '{}'
        
        cursor.execute('''
            INSERT OR REPLACE INTO processes 
            (timestamp, pid, name, command_line, user, cpu_percent, memory_mb, extra_metrics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            process_info.pid,
            process_info.name,
            process_info.command_line,
            process_info.user,
            process_info.cpu_percent,
            process_info.memory_mb,
            extra_metrics_json
        ))
        
        conn.commit()
        conn.close()
    
    def insert_system_info(self, system_info: SystemInfo) -> None:
        """插入系统信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = system_info.timestamp.isoformat()
        extra_metrics_json = json.dumps(system_info.extra_metrics) if system_info.extra_metrics else '{}'
        
        cursor.execute('''
            INSERT OR REPLACE INTO system_info 
            (timestamp, cpu_percent, memory_total_mb, memory_used_mb, memory_percent, extra_metrics)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            system_info.cpu_percent,
            system_info.memory_total_mb,
            system_info.memory_used_mb,
            system_info.memory_percent,
            extra_metrics_json
        ))
        
        conn.commit()
        conn.close()
    
    def get_process_data(self, pid: Optional[int] = None, name: Optional[str] = None, 
                        start_time: Optional[str] = None, end_time: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        查询进程数据
        
        Args:
            pid: 进程ID（可选）
            name: 进程名（可选）
            start_time: 开始时间（ISO格式，可选）
            end_time: 结束时间（ISO格式，可选）
        
        Returns:
            进程数据列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM processes WHERE 1=1'
        params = []
        
        if pid is not None:
            query += ' AND pid = ?'
            params.append(pid)
        
        if name is not None:
            query += ' AND name = ?'
            params.append(name)
        
        if start_time:
            query += ' AND timestamp >= ?'
            params.append(start_time)
        
        if end_time:
            query += ' AND timestamp <= ?'
            params.append(end_time)
        
        query += ' ORDER BY timestamp'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            data = dict(row)
            # 解析 extra_metrics JSON
            if data['extra_metrics']:
                try:
                    data['extra_metrics'] = json.loads(data['extra_metrics'])
                except:
                    data['extra_metrics'] = {}
            result.append(data)
        
        conn.close()
        return result
    
    def get_system_data(self, start_time: Optional[str] = None, end_time: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        查询系统数据
        
        Args:
            start_time: 开始时间（ISO格式，可选）
            end_time: 结束时间（ISO格式，可选）
        
        Returns:
            系统数据列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM system_info WHERE 1=1'
        params = []
        
        if start_time:
            query += ' AND timestamp >= ?'
            params.append(start_time)
        
        if end_time:
            query += ' AND timestamp <= ?'
            params.append(end_time)
        
        query += ' ORDER BY timestamp'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            data = dict(row)
            # 解析 extra_metrics JSON
            if data['extra_metrics']:
                try:
                    data['extra_metrics'] = json.loads(data['extra_metrics'])
                except:
                    data['extra_metrics'] = {}
            result.append(data)
        
        conn.close()
        return result
    
    def get_all_process_names(self) -> List[str]:
        """获取所有唯一的进程名"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT name FROM processes ORDER BY name')
        names = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return names
    
    def get_all_pids(self, name: Optional[str] = None) -> List[int]:
        """获取所有唯一的PID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if name:
            cursor.execute('SELECT DISTINCT pid FROM processes WHERE name = ? ORDER BY pid', (name,))
        else:
            cursor.execute('SELECT DISTINCT pid FROM processes ORDER BY pid')
        
        pids = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return pids
    
    def get_time_range(self) -> tuple:
        """获取数据的时间范围"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM processes')
        result = cursor.fetchone()
        
        conn.close()
        return result if result else (None, None)

