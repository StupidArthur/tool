"""配置文件管理器"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """配置文件管理器，支持 JSON 格式，方便修改"""
    
    DEFAULT_CONFIG = {
        "output_dir": "D:\\system_performance_record",
        "record_interval": 5,  # 秒
        "monitored_processes": [],  # 监控的进程列表
        "monitor_by_pid": {},  # {pid: True/False} 是否仅监控该PID
        "ui": {
            "window_width": 1200,
            "window_height": 800
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为 None，则使用默认路径
        """
        if config_path is None:
            # 默认配置文件路径：当前目录下的 config.json
            self.config_path = Path(__file__).parent.parent / "config.json"
        else:
            self.config_path = Path(config_path)
        
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                # 合并默认配置，确保所有键都存在
                self._merge_defaults()
            except Exception as e:
                print(f"加载配置文件失败: {e}，使用默认配置")
                self.config = self.DEFAULT_CONFIG.copy()
                self.save_config()
        else:
            # 配置文件不存在，创建默认配置
            self.config = self.DEFAULT_CONFIG.copy()
            self.save_config()
    
    def _merge_defaults(self) -> None:
        """合并默认配置，确保所有键都存在"""
        def merge_dict(default: dict, current: dict) -> dict:
            result = default.copy()
            for key, value in current.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dict(result[key], value)
                else:
                    result[key] = value
            return result
        
        self.config = merge_dict(self.DEFAULT_CONFIG, self.config)
    
    def save_config(self) -> None:
        """保存配置文件"""
        try:
            # 确保目录存在（如果父目录不存在，创建它）
            parent_dir = self.config_path.parent
            if parent_dir and not parent_dir.exists():
                parent_dir.mkdir(parents=True, exist_ok=True)
            # 使用临时文件写入，避免文件锁定问题
            import tempfile
            import shutil
            temp_path = str(self.config_path) + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            # 原子性替换
            if self.config_path.exists():
                self.config_path.unlink()
            shutil.move(temp_path, self.config_path)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            # 如果保存失败，不影响程序运行，只是使用内存中的配置
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def get_output_dir(self) -> str:
        """获取输出目录"""
        return self.get("output_dir", self.DEFAULT_CONFIG["output_dir"])
    
    def set_output_dir(self, path: str) -> None:
        """设置输出目录"""
        self.set("output_dir", path)
    
    def get_record_interval(self) -> int:
        """获取记录间隔（秒）"""
        return self.get("record_interval", self.DEFAULT_CONFIG["record_interval"])
    
    def set_record_interval(self, interval: int) -> None:
        """设置记录间隔（秒）"""
        self.set("record_interval", interval)
    
    def get_monitored_processes(self) -> list:
        """获取监控的进程列表"""
        return self.get("monitored_processes", [])
    
    def set_monitored_processes(self, processes: list) -> None:
        """设置监控的进程列表"""
        self.set("monitored_processes", processes)
    
    def get_monitor_by_pid(self) -> dict:
        """获取按PID监控的配置"""
        return self.get("monitor_by_pid", {})
    
    def set_monitor_by_pid(self, monitor_by_pid: dict) -> None:
        """设置按PID监控的配置"""
        self.set("monitor_by_pid", monitor_by_pid)

