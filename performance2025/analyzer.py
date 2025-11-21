"""统计分析工具主程序"""
import sys
from PyQt6.QtWidgets import QApplication
from ui.analyzer_window import AnalyzerWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = AnalyzerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

