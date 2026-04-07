"""
小学生朗读激励抽奖应用 - 主入口
Phase 1: 基础骨架与配置页
"""
import sys
from PySide6.QtWidgets import QApplication
from ui.config_window import ConfigWindow


def main():
    """应用主入口"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    # 创建并显示配置窗口
    window = ConfigWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
