"""监测工具主程序"""
import sys
import argparse
from PyQt6.QtWidgets import QApplication
from config import ConfigManager
from ui.monitor_window import MonitorWindow


def main():
    """主函数"""
    try:
        parser = argparse.ArgumentParser(description="系统性能监测工具")
        parser.add_argument(
            '--config', '-c',
            type=str,
            help='配置文件路径（可选）'
        )
        parser.add_argument(
            '--ui',
            action='store_true',
            help='启动UI界面（默认）'
        )
        parser.add_argument(
            '--no-ui',
            action='store_true',
            help='命令行模式（暂未实现）'
        )
        
        args = parser.parse_args()
        
        # 加载配置
        config_manager = ConfigManager(args.config)
        
        if args.no_ui:
            # 命令行模式（未来可以实现）
            print("命令行模式暂未实现，请使用 --ui 启动UI界面")
            return
        
        # UI模式
        app = QApplication(sys.argv)
        window = MonitorWindow(config_manager)
        window.show()
        window.raise_()  # 确保窗口在最前面
        window.activateWindow()  # 激活窗口
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        print(f"发生错误: {e}")
        traceback.print_exc()
        input("按回车键退出...")
        sys.exit(1)


if __name__ == '__main__':
    main()

