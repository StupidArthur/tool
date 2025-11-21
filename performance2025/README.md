# 系统性能监测工具 + 统计分析工具

一个基于 Python 3.13 + PyQt6 的系统性能监测和统计分析工具，支持 Windows 和 Linux（预留）。

## 功能特性

### 监测工具
- 监测指定进程和系统的性能指标
- 支持按进程名或PID监控
- 实时显示当前运行的进程列表
- 数据自动保存到 SQLite3 数据库
- 支持命令行和UI两种启动方式
- 配置文件管理，方便修改

### 统计分析工具
- 加载一个或多个数据库文件
- 树形结构展示数据库和进程
- 九宫格显示多个性能指标曲线图
- 数据量过大时自动采样
- 双击图表放大显示
- 显示统计分析结果

## 系统要求

- Python 3.13+
- Windows 10+ 或 Linux（预留）
- 依赖包见 `requirements.txt`

## 安装

1. 克隆或下载项目
2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

### 监测工具

**UI模式（推荐）：**
```bash
python monitor.py
```

**命令行模式（使用配置文件）：**
```bash
python monitor.py --config config.json
```

**配置文件说明：**
- `config.json` 是默认配置文件，位于项目根目录
- 可以手动编辑配置文件，或通过UI界面修改
- 配置文件格式为 JSON，方便修改

### 统计分析工具

```bash
python analyzer.py
```

启动后点击"加载数据库"按钮，选择要分析的数据库文件。

## 项目结构

```
performance2025/
├── config/              # 配置模块
│   ├── __init__.py
│   └── config_manager.py
├── collector/           # 数据采集模块
│   ├── __init__.py
│   ├── base.py          # 基础接口
│   ├── windows_collector.py    # Windows实现
│   ├── linux_collector.py      # Linux实现（预留）
│   └── collector_factory.py    # 工厂模式
├── database/            # 数据库模块
│   ├── __init__.py
│   └── db_manager.py
├── ui/                  # UI模块
│   ├── __init__.py
│   ├── monitor_window.py       # 监测工具窗口
│   └── analyzer_window.py      # 统计分析工具窗口
├── utils/               # 工具模块
│   ├── __init__.py
│   └── platform_utils.py
├── monitor.py           # 监测工具主程序
├── analyzer.py          # 统计分析工具主程序
├── config.json          # 默认配置文件
├── requirements.txt     # 依赖列表
└── README.md            # 说明文档
```

## 架构设计

### 跨平台支持
- 使用工厂模式创建平台特定的采集器
- Windows 和 Linux 分别实现，便于扩展
- 平台检测自动选择对应的实现

### 配置管理
- JSON 格式配置文件，易于修改
- 支持嵌套配置项
- 自动合并默认配置

### 数据库设计
- SQLite3 数据库，轻量级
- 进程信息表和系统信息表分离
- 索引优化查询性能
- 时间戳到秒的精度

## 打包

使用 PyInstaller 打包：

```bash
pyinstaller --onefile --windowed monitor.py
pyinstaller --onefile --windowed analyzer.py
```

## 注意事项

1. 首次运行会自动创建默认配置文件
2. 输出目录默认是 `D:\system_performance_record`（Windows）
3. 数据库文件名格式：`YYYYMMDD_HHMMSS.db`
4. 监测过程中会持续写入数据库，请确保有足够的磁盘空间
5. Linux 平台支持已预留，但需要进一步测试

## 许可证

MIT License

