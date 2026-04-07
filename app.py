"""
小学生朗读激励抽奖应用 - 主入口
Phase 3: 实现双界面切换
"""
import sys
from PySide6.QtWidgets import QApplication
from ui.config_window import ConfigWindow
from ui.activity_window import ActivityWindow


class AppController:
    """应用控制器，管理界面切换"""
    
    def __init__(self):
        self.config_window = None
        self.activity_window = None
        
    def show_config_window(self):
        """显示配置窗口"""
        if not self.config_window:
            self.config_window = ConfigWindow()
            self.config_window.start_clicked.connect(self.on_start_activity)
        
        self.config_window.show()
        
        # 如果活动窗口存在，关闭它
        if self.activity_window:
            self.activity_window.close()
            self.activity_window = None
    
    def on_start_activity(self, config):
        """启动活动界面"""
        # 隐藏配置窗口
        if self.config_window:
            self.config_window.hide()
        
        # 创建并显示活动窗口
        self.activity_window = ActivityWindow(config)
        self.activity_window.back_to_config.connect(self.on_back_to_config)
        self.activity_window.show()
    
    def on_back_to_config(self):
        """返回配置页"""
        # 关闭活动窗口
        if self.activity_window:
            self.activity_window.close()
            self.activity_window = None
        
        # 显示配置窗口
        self.show_config_window()


def main():
    """应用主入口"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    # 创建应用控制器
    controller = AppController()
    controller.show_config_window()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
