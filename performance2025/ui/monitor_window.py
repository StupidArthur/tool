"""监测工具主窗口"""
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QFileDialog, QSpinBox, QMessageBox, QSplitter, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from typing import Dict, Set, Optional
import threading
import time

from config import ConfigManager


class MonitorWindow(QMainWindow):
    """监测工具主窗口"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        try:
            self.config_manager = config_manager
            self.db_manager = None
            self.monitoring = False
            self.monitor_thread: threading.Thread = None
            self.monitored_pids: Set[int] = set()
            self.collector = None  # 延迟初始化
            
            # 用于增量更新的进程字典 {进程名小写: 进程名}
            self.current_processes: Dict[str, str] = {}
            
            # 监测相关
            self.last_record_time = None
            self.update_time_timer = QTimer()
            self.update_time_timer.timeout.connect(self.update_last_record_time)
            
            self.init_ui()
            self.load_config()
            
            # 延迟创建采集器和启动定时器
            QTimer.singleShot(100, self._delayed_init)
        except Exception as e:
            import traceback
            print(f"初始化窗口时出错: {e}")
            traceback.print_exc()
            raise
    
    def _delayed_init(self):
        """延迟初始化，避免阻塞窗口显示"""
        try:
            from collector import create_collector
            self.collector = create_collector()
            self.start_refresh_timer()
        except Exception as e:
            import traceback
            print(f"延迟初始化时出错: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"初始化采集器失败: {e}")
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("系统性能监测工具")
        self.setGeometry(100, 100, 1400, 900)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setStretch(0, 1)  # splitter占据主要空间
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 左侧：监控的进程表格
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        left_layout.addWidget(QLabel("监控的进程列表（按进程名监控）"))
        
        self.monitored_table = QTableWidget()
        self.monitored_table.setColumnCount(1)
        self.monitored_table.setHorizontalHeaderLabels(["进程名"])
        self.monitored_table.horizontalHeader().setStretchLastSection(True)
        self.monitored_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.monitored_table.setMinimumWidth(350)
        left_layout.addWidget(self.monitored_table, 1)  # 设置stretch factor为1
        
        # 添加进程按钮
        add_layout = QHBoxLayout()
        self.process_name_input = QLineEdit()
        self.process_name_input.setPlaceholderText("输入进程名")
        add_btn = QPushButton("添加进程")
        add_btn.clicked.connect(self.add_process)
        add_layout.addWidget(self.process_name_input)
        add_layout.addWidget(add_btn)
        left_layout.addLayout(add_layout)
        
        remove_btn = QPushButton("移除选中")
        remove_btn.clicked.connect(self.remove_selected_process)
        left_layout.addWidget(remove_btn)
        
        # 右侧：当前运行的进程表格
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        right_layout.addWidget(QLabel("当前系统运行的进程（按进程名排序）"))
        
        self.running_table = QTableWidget()
        self.running_table.setColumnCount(1)
        self.running_table.setHorizontalHeaderLabels(["进程名"])
        self.running_table.horizontalHeader().setStretchLastSection(True)
        self.running_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.running_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)  # 支持多选
        self.running_table.setSortingEnabled(True)  # 启用排序
        # 双击事件
        self.running_table.itemDoubleClicked.connect(self.on_running_table_double_clicked)
        right_layout.addWidget(self.running_table, 1)  # 设置stretch factor为1
        
        add_to_monitor_btn = QPushButton("添加到监控列表")
        add_to_monitor_btn.clicked.connect(self.add_to_monitor)
        right_layout.addWidget(add_to_monitor_btn)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        # 配置和控制区域（合并到一行，更紧凑）
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)
        
        # 配置区域
        bottom_layout.addWidget(QLabel("输出目录:"))
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setReadOnly(True)
        bottom_layout.addWidget(self.output_dir_input, 2)
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_output_dir)
        bottom_layout.addWidget(browse_btn)
        
        bottom_layout.addWidget(QLabel("记录间隔(秒):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(1)
        self.interval_spin.setMaximum(3600)
        self.interval_spin.setValue(5)
        self.interval_spin.setMaximumWidth(80)
        bottom_layout.addWidget(self.interval_spin)
        
        bottom_layout.addStretch()
        
        # 控制按钮
        self.start_btn = QPushButton("开始监测")
        self.start_btn.clicked.connect(self.toggle_monitoring)
        self.stop_btn = QPushButton("停止监测")
        self.stop_btn.clicked.connect(self.toggle_monitoring)
        self.stop_btn.setEnabled(False)
        
        bottom_layout.addWidget(self.start_btn)
        bottom_layout.addWidget(self.stop_btn)
        
        self.status_label = QLabel("状态: 未开始")
        bottom_layout.addWidget(self.status_label)
        
        self.last_record_label = QLabel("")
        bottom_layout.addWidget(self.last_record_label)
        
        main_layout.addWidget(bottom_widget, 0)  # stretch factor为0，不扩展
    
    def load_config(self):
        """加载配置"""
        self.output_dir_input.setText(self.config_manager.get_output_dir())
        self.interval_spin.setValue(self.config_manager.get_record_interval())
        
        # 加载监控的进程列表（去重，不区分大小写）
        monitored_processes = self.config_manager.get_monitored_processes()
        # 去重，保留第一次出现的（不区分大小写）
        seen = set()
        unique_processes = []
        for proc in monitored_processes:
            proc_lower = proc.lower()
            if proc_lower not in seen:
                seen.add(proc_lower)
                unique_processes.append(proc)
        
        self.monitored_table.setRowCount(len(unique_processes))
        for i, process_name in enumerate(unique_processes):
            name_item = QTableWidgetItem(process_name)
            self.monitored_table.setItem(i, 0, name_item)
    
    def save_config(self):
        """保存配置"""
        self.config_manager.set_output_dir(self.output_dir_input.text())
        self.config_manager.set_record_interval(self.interval_spin.value())
        
        # 保存监控的进程列表
        monitored_processes = []
        for i in range(self.monitored_table.rowCount()):
            name_item = self.monitored_table.item(i, 0)
            if name_item:
                monitored_processes.append(name_item.text())
        
        self.config_manager.set_monitored_processes(monitored_processes)
        self.config_manager.set_monitor_by_pid({})  # 不再使用
        self.config_manager.save_config()
    
    def browse_output_dir(self):
        """浏览输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_dir_input.setText(directory)
    
    def add_process(self):
        """添加进程到监控列表"""
        process_name = self.process_name_input.text().strip()
        if not process_name:
            QMessageBox.warning(self, "警告", "请输入进程名")
            return
        
        # 检查是否已存在（不区分大小写）
        process_name_lower = process_name.lower()
        for i in range(self.monitored_table.rowCount()):
            name_item = self.monitored_table.item(i, 0)
            if name_item and name_item.text().lower() == process_name_lower:
                QMessageBox.information(self, "提示", "该进程已在监控列表中")
                return
        
        # 添加新行
        row = self.monitored_table.rowCount()
        self.monitored_table.insertRow(row)
        name_item = QTableWidgetItem(process_name)
        self.monitored_table.setItem(row, 0, name_item)
        
        self.process_name_input.clear()
    
    def remove_selected_process(self):
        """移除选中的进程（从监控列表）"""
        # 获取所有选中的行
        selected_rows = []
        if self.monitored_table.selectionModel():
            selected_indexes = self.monitored_table.selectionModel().selectedRows()
            for index in selected_indexes:
                selected_rows.append(index.row())
        
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择要移除的进程")
            return
        
        # 从后往前删除，避免索引变化
        for row in sorted(selected_rows, reverse=True):
            self.monitored_table.removeRow(row)
    
    def on_running_table_double_clicked(self, item):
        """双击运行列表项，添加到监控列表"""
        row = item.row()
        self._add_process_to_monitor(row)
    
    def add_to_monitor(self):
        """从运行列表添加到监控列表（支持多选）"""
        # 获取所有选中的行
        selected_rows = []
        if self.running_table.selectionModel():
            selected_indexes = self.running_table.selectionModel().selectedRows()
            for index in selected_indexes:
                selected_rows.append(index.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要监控的进程")
            return
        
        # 添加所有选中的进程
        added_count = 0
        for row in selected_rows:
            if self._add_process_to_monitor(row, show_message=False):
                added_count += 1
        
        if added_count > 0:
            QMessageBox.information(self, "提示", f"已添加 {added_count} 个进程到监控列表")
    
    def _add_process_to_monitor(self, row, show_message=True):
        """添加指定行的进程到监控列表"""
        name_item = self.running_table.item(row, 0)
        if not name_item:
            return False
        
        name = name_item.text()
        name_lower = name.lower()
        
        # 检查是否已存在（不区分大小写）
        for i in range(self.monitored_table.rowCount()):
            existing_item = self.monitored_table.item(i, 0)
            if existing_item and existing_item.text().lower() == name_lower:
                if show_message:
                    QMessageBox.information(self, "提示", f"进程 '{name}' 已在监控列表中")
                return False
        
        # 添加新行
        new_row = self.monitored_table.rowCount()
        self.monitored_table.insertRow(new_row)
        new_item = QTableWidgetItem(name)
        self.monitored_table.setItem(new_row, 0, new_item)
        return True
    
    def start_refresh_timer(self):
        """启动刷新定时器"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_running_processes)
        self.refresh_timer.start(2000)  # 每2秒刷新一次
        # 延迟首次刷新
        QTimer.singleShot(500, self.refresh_running_processes)
    
    def refresh_running_processes(self):
        """增量刷新运行中的进程列表（按进程名去重）"""
        if self.monitoring or self.collector is None:
            return
        
        try:
            # 保存当前选中状态（按进程名）
            selected_names = set()
            if self.running_table.selectionModel():
                selected_indexes = self.running_table.selectionModel().selectedRows()
                for index in selected_indexes:
                    name_item = self.running_table.item(index.row(), 0)
                    if name_item:
                        selected_names.add(name_item.text().lower())
            
            # 获取新进程列表
            new_processes = self.collector.get_process_list_fast()
            
            # 按进程名去重（不区分大小写），保留第一个
            process_names_seen = {}
            for proc in new_processes:
                name_lower = proc.name.lower()
                if name_lower not in process_names_seen:
                    process_names_seen[name_lower] = proc.name
            
            # 获取去重后的进程名列表并排序
            unique_names = sorted(process_names_seen.values(), key=lambda n: n.lower())
            
            # 创建当前表格中的进程名集合（不区分大小写）
            current_names = set()
            for row in range(self.running_table.rowCount()):
                name_item = self.running_table.item(row, 0)
                if name_item:
                    current_names.add(name_item.text().lower())
            
            # 找出需要删除的进程名（旧的有，新的没有）
            names_to_remove = current_names - set(n.lower() for n in unique_names)
            
            # 找出需要添加的进程名（新的有，旧的没有）
            names_to_add = set(n.lower() for n in unique_names) - current_names
            
            # 禁用排序，避免更新时自动排序
            was_sorting_enabled = self.running_table.isSortingEnabled()
            self.running_table.setSortingEnabled(False)
            
            # 删除不存在的进程
            rows_to_remove = []
            for row in range(self.running_table.rowCount()):
                name_item = self.running_table.item(row, 0)
                if name_item and name_item.text().lower() in names_to_remove:
                    rows_to_remove.append(row)
            
            # 从后往前删除，避免索引变化
            for row in reversed(rows_to_remove):
                self.running_table.removeRow(row)
            
            # 添加新进程（插入到合适位置保持排序）
            for name in unique_names:
                if name.lower() in names_to_add:
                    # 找到插入位置（保持按进程名排序）
                    insert_row = self.running_table.rowCount()
                    for row in range(self.running_table.rowCount()):
                        name_item = self.running_table.item(row, 0)
                        if name_item and name_item.text().lower() > name.lower():
                            insert_row = row
                            break
                    
                    self.running_table.insertRow(insert_row)
                    name_item = QTableWidgetItem(name)
                    self.running_table.setItem(insert_row, 0, name_item)
            
            # 恢复排序
            self.running_table.setSortingEnabled(was_sorting_enabled)
            
            # 恢复选中状态（按进程名）
            if selected_names:
                for row in range(self.running_table.rowCount()):
                    name_item = self.running_table.item(row, 0)
                    if name_item and name_item.text().lower() in selected_names:
                        self.running_table.selectRow(row)
            
            # 更新当前进程字典（按进程名）
            self.current_processes = {name.lower(): name for name in unique_names}
            
        except Exception as e:
            import traceback
            print(f"刷新进程列表时出错: {e}")
            traceback.print_exc()
    
    def toggle_monitoring(self):
        """切换监测状态"""
        if not self.monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """开始监测"""
        if self.collector is None:
            QMessageBox.warning(self, "警告", "采集器尚未初始化，请稍候再试")
            return
        
        self.save_config()
        
        output_dir = self.output_dir_input.text()
        if not output_dir:
            QMessageBox.warning(self, "警告", "请设置输出目录")
            return
        
        if self.monitored_table.rowCount() == 0:
            QMessageBox.warning(self, "警告", "请至少添加一个要监控的进程")
            return
        
        from pathlib import Path
        from utils.platform_utils import get_timestamp_string
        from database import DatabaseManager
        
        timestamp_str = get_timestamp_string()
        db_filename = f"{timestamp_str}.db"
        db_path = str(Path(output_dir) / db_filename)
        self.db_manager = DatabaseManager(db_path)
        
        self.monitoring = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText(f"状态: 监测中 - 数据库: {db_filename}")
        self.last_record_time = None
        self.last_record_label.setText("最新记录时间: 等待中...")
        
        # 启动更新时间的定时器（每秒更新一次）
        self.update_time_timer.start(1000)
        
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监测"""
        self.monitoring = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("状态: 已停止")
        self.update_time_timer.stop()
        self.last_record_label.setText("")
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def update_last_record_time(self):
        """更新最新记录时间显示"""
        if self.last_record_time:
            from datetime import datetime
            now = datetime.now()
            elapsed = (now - self.last_record_time).total_seconds()
            time_str = self.last_record_time.strftime("%Y-%m-%d %H:%M:%S")
            self.last_record_label.setText(f"最新记录时间: {time_str} ({elapsed:.0f}秒前)")
        else:
            self.last_record_label.setText("最新记录时间: 等待中...")
    
    def monitor_loop(self):
        """监测循环（按进程名监控，不区分大小写）"""
        interval = self.interval_spin.value()
        
        # 获取要监控的进程名列表（不区分大小写）
        monitored_names = set()
        for i in range(self.monitored_table.rowCount()):
            name_item = self.monitored_table.item(i, 0)
            if name_item:
                monitored_names.add(name_item.text().lower())
        
        # 初始化所有进程的CPU使用率（非阻塞模式需要先初始化）
        import psutil
        try:
            # 初始化系统CPU
            psutil.cpu_percent(interval=None)
            
            # 初始化所有监控进程的CPU
            for name_lower in monitored_names:
                procs = self.collector.get_processes_by_name(name_lower)
                for proc_info in procs:
                    try:
                        proc = psutil.Process(proc_info.pid)
                        proc.cpu_percent(interval=None)  # 初始化，建立基准
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
        except Exception as e:
            print(f"初始化CPU使用率时出错: {e}")
        
        # 等待一个间隔，让CPU数据有值
        time.sleep(interval)
        
        while self.monitoring:
            try:
                processes_to_record = []
                
                # 按进程名获取所有匹配的进程（不区分大小写）
                for name_lower in monitored_names:
                    # 获取所有同名进程（包括新启动的）
                    procs = self.collector.get_processes_by_name(name_lower)
                    processes_to_record.extend(procs)
                
                # 记录进程数据
                if processes_to_record:
                    for proc_info in processes_to_record:
                        self.db_manager.insert_process_info(proc_info)
                
                # 记录系统数据
                system_info = self.collector.get_system_info()
                self.db_manager.insert_system_info(system_info)
                
                # 更新最新记录时间
                from datetime import datetime
                self.last_record_time = datetime.now()
                
                time.sleep(interval)
            except Exception as e:
                print(f"监测错误: {e}")
                time.sleep(interval)
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.monitoring:
            reply = QMessageBox.question(
                self, "确认", "监测正在进行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            
            self.stop_monitoring()
        
        self.save_config()
        event.accept()
