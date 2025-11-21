"""统计分析工具窗口"""
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, 
    QTreeWidgetItem, QPushButton, QFileDialog, QMessageBox, QSplitter,
    QGridLayout, QLabel, QScrollArea, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path

from database import DatabaseManager

# 配置matplotlib中文字体，解决中文乱码问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class ChartWidget(QWidget):
    """图表部件"""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.figure = Figure(figsize=(4, 3))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel(title))
        layout.addWidget(self.canvas)
        self.setLayout(layout)
    
    def plot(self, x_data: List[float], y_data: List[float], label: str = ""):
        """绘制图表"""
        self.ax.clear()
        self.ax.plot(x_data, y_data, label=label)
        self.ax.set_title(self.title)
        self.ax.grid(True)
        # 设置纵轴起点为0
        if len(y_data) > 0:
            y_min = min(y_data)
            y_max = max(y_data)
            if y_min == y_max:
                # 如果所有值相同，设置一个小的范围
                self.ax.set_ylim(0, max(y_max * 1.1, 1))
            else:
                # 设置底部为0，顶部留一些空间
                self.ax.set_ylim(bottom=0, top=y_max * 1.05)
        else:
            self.ax.set_ylim(bottom=0)
        if label:
            self.ax.legend()
        self.canvas.draw()


class ChartDialog(QDialog):
    """图表放大对话框"""
    def __init__(self, title: str, x_data: List[float], y_data: List[float], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        self.ax.plot(x_data, y_data)
        self.ax.set_title(title)
        self.ax.grid(True)
        # 设置纵轴起点为0
        if len(y_data) > 0:
            y_min = min(y_data)
            y_max = max(y_data)
            if y_min == y_max:
                # 如果所有值相同，设置一个小的范围
                self.ax.set_ylim(0, max(y_max * 1.1, 1))
            else:
                # 设置底部为0，顶部留一些空间
                self.ax.set_ylim(bottom=0, top=y_max * 1.05)
        else:
            self.ax.set_ylim(bottom=0)
        
        layout.addWidget(self.canvas)
        self.setLayout(layout)


class AnalyzerWindow(QMainWindow):
    """统计分析工具主窗口"""
    
    def __init__(self):
        super().__init__()
        self.db_managers: Dict[str, DatabaseManager] = {}  # {db_path: DatabaseManager}
        self.current_process_data: Optional[Dict] = None
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("性能统计分析工具")
        self.setGeometry(100, 100, 1400, 900)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        load_db_btn = QPushButton("加载数据库")
        load_db_btn.clicked.connect(self.load_database)
        toolbar_layout.addWidget(load_db_btn)
        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：数据库和进程树
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("数据库和进程树"))
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("数据库文件")
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        left_layout.addWidget(self.tree)
        left_widget.setMaximumWidth(300)
        
        # 右侧：图表区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 分析结果标签
        self.analysis_label = QLabel("分析结果: 请选择进程")
        self.analysis_label.setWordWrap(True)
        right_layout.addWidget(self.analysis_label)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.chart_layout = QGridLayout(scroll_widget)
        self.chart_layout.setSpacing(10)
        
        # 创建9个图表占位符
        self.charts = []
        chart_titles = [
            "CPU使用率 (%)", "内存使用 (MB)", "线程数",
            "句柄数/文件描述符", "IO读取 (Bytes)", "IO写入 (Bytes)",
            "系统CPU (%)", "系统内存 (%)", "其他指标"
        ]
        
        for i, title in enumerate(chart_titles):
            chart = ChartWidget(title)
            self.charts.append(chart)
            row = i // 3
            col = i % 3
            self.chart_layout.addWidget(chart, row, col)
            
            # 双击事件
            chart.canvas.mpl_connect('button_press_event', 
                lambda e, idx=i: self.on_chart_double_click(e, idx) if e.dblclick else None)
        
        scroll_area.setWidget(scroll_widget)
        right_layout.addWidget(scroll_area)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
    
    def load_database(self):
        """加载数据库文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择数据库文件", "", "SQLite数据库 (*.db);;所有文件 (*)"
        )
        
        for file_path in file_paths:
            if file_path not in self.db_managers:
                try:
                    db_manager = DatabaseManager(file_path)
                    self.db_managers[file_path] = db_manager
                    
                    # 添加到树
                    db_item = QTreeWidgetItem(self.tree)
                    db_item.setText(0, Path(file_path).name)
                    db_item.setData(0, Qt.ItemDataRole.UserRole, file_path)
                    db_item.setExpanded(True)
                    
                    # 添加进程
                    process_names = db_manager.get_all_process_names()
                    for name in sorted(process_names):
                        pids = db_manager.get_all_pids(name)
                        for pid in sorted(pids):
                            process_item = QTreeWidgetItem(db_item)
                            process_item.setText(0, f"{name} (PID: {pid})")
                            process_item.setData(0, Qt.ItemDataRole.UserRole, {
                                'db_path': file_path,
                                'name': name,
                                'pid': pid
                            })
                    
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"加载数据库失败: {e}")
    
    def on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """树项点击事件"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, dict):
            # 进程项
            self.load_process_data(data['db_path'], data['name'], data['pid'])
    
    def load_process_data(self, db_path: str, name: str, pid: int):
        """加载进程数据"""
        db_manager = self.db_managers[db_path]
        process_data = db_manager.get_process_data(pid=pid)
        system_data = db_manager.get_system_data()
        
        if not process_data:
            QMessageBox.information(self, "提示", "该进程没有数据")
            return
        
        self.current_process_data = {
            'process': process_data,
            'system': system_data,
            'name': name,
            'pid': pid
        }
        
        self.update_charts()
        self.update_analysis()
    
    def sample_data(self, data: List[Dict], max_points: int = 1000) -> List[Dict]:
        """数据采样，避免数据量过大"""
        if len(data) <= max_points:
            return data
        
        step = len(data) / max_points
        indices = [int(i * step) for i in range(max_points)]
        return [data[i] for i in indices]
    
    def update_charts(self):
        """更新图表"""
        if not self.current_process_data:
            return
        
        process_data = self.sample_data(self.current_process_data['process'])
        system_data = self.sample_data(self.current_process_data['system'])
        
        # 准备时间轴（转换为相对时间，秒）
        if process_data:
            start_time = process_data[0]['timestamp']
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_time)
            
            # CPU使用率
            timestamps = [(datetime.fromisoformat(d['timestamp']) - start_dt).total_seconds() 
                         for d in process_data]
            cpu_values = [d['cpu_percent'] for d in process_data]
            self.charts[0].plot(timestamps, cpu_values)
            
            # 内存使用
            memory_values = [d['memory_mb'] for d in process_data]
            self.charts[1].plot(timestamps, memory_values)
            
            # 线程数
            thread_values = [d.get('extra_metrics', {}).get('num_threads', 0) for d in process_data]
            self.charts[2].plot(timestamps, thread_values)
            
            # 句柄数/文件描述符
            handles_key = 'num_handles' if 'num_handles' in process_data[0].get('extra_metrics', {}) else 'num_fds'
            handles_values = [d.get('extra_metrics', {}).get(handles_key, 0) for d in process_data]
            self.charts[3].plot(timestamps, handles_values)
            
            # IO读取
            io_read_values = [d.get('extra_metrics', {}).get('io_read_bytes', 0) / 1024 / 1024 
                            for d in process_data]  # 转换为MB
            self.charts[4].plot(timestamps, io_read_values)
            
            # IO写入
            io_write_values = [d.get('extra_metrics', {}).get('io_write_bytes', 0) / 1024 / 1024 
                             for d in process_data]  # 转换为MB
            self.charts[5].plot(timestamps, io_write_values)
        
        # 系统指标
        if system_data:
            start_time = system_data[0]['timestamp']
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_time)
            
            sys_timestamps = [(datetime.fromisoformat(d['timestamp']) - start_dt).total_seconds() 
                            for d in system_data]
            sys_cpu_values = [d['cpu_percent'] for d in system_data]
            self.charts[6].plot(sys_timestamps, sys_cpu_values)
            
            sys_memory_values = [d['memory_percent'] for d in system_data]
            self.charts[7].plot(sys_timestamps, sys_memory_values)
            
            # 其他指标（可以显示磁盘IO等）
            if system_data[0].get('extra_metrics'):
                disk_usage = [d.get('extra_metrics', {}).get('disk_usage', {}).get('used', 0) 
                            for d in system_data]
                self.charts[8].plot(sys_timestamps, disk_usage)
    
    def update_analysis(self):
        """更新分析结果"""
        if not self.current_process_data:
            return
        
        process_data = self.current_process_data['process']
        name = self.current_process_data['name']
        pid = self.current_process_data['pid']
        
        if not process_data:
            return
        
        # 计算统计信息
        cpu_values = [d['cpu_percent'] for d in process_data]
        memory_values = [d['memory_mb'] for d in process_data]
        
        analysis_text = f"""
进程: {name} (PID: {pid})
数据点数: {len(process_data)}

CPU使用率:
  平均值: {np.mean(cpu_values):.2f}%
  最大值: {np.max(cpu_values):.2f}%
  最小值: {np.min(cpu_values):.2f}%

内存使用:
  平均值: {np.mean(memory_values):.2f} MB
  最大值: {np.max(memory_values):.2f} MB
  最小值: {np.min(memory_values):.2f} MB
        """
        
        self.analysis_label.setText(analysis_text.strip())
    
    def on_chart_double_click(self, event, chart_index: int):
        """图表双击事件"""
        if not self.current_process_data or chart_index >= len(self.charts):
            return
        
        chart = self.charts[chart_index]
        # 获取图表数据
        if len(chart.ax.lines) > 0:
            line = chart.ax.lines[0]
            x_data = line.get_xdata()
            y_data = line.get_ydata()
            
            dialog = ChartDialog(chart.title, x_data, y_data, self)
            dialog.exec()
    
    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() == Qt.Key.Key_Escape:
            # ESC关闭当前对话框
            for widget in self.findChildren(QDialog):
                if widget.isVisible():
                    widget.close()
                    return
        super().keyPressEvent(event)

