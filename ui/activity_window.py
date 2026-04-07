"""
活动界面窗口
Phase 3: 实现二层活动页与抽奖逻辑
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor, QPalette
from models.config_model import AppConfig
from models.prize_model import PrizeItem
from services.audio_service import AudioService
from services.lottery_service import LotteryService


class ActivityWindow(QMainWindow):
    """活动界面窗口类"""
    
    # 信号：返回配置页
    back_to_config = Signal()
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        
        # 初始化服务
        self.audio_service = AudioService(device_index=config.mic_index)
        self.lottery_service = LotteryService(config)
        
        # 状态变量
        self.current_result: PrizeItem = None
        self.reveal_progress = 0.0  # 揭晓进度 0.0 - 1.0
        self.is_revealed = False  # 是否已完全揭晓
        
        # UI更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        
        # 进度推进定时器（每100ms更新一次进度）
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        
        self.init_ui()
        self.start_new_round()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("小学生朗读激励抽奖 - 活动进行中")
        self.setMinimumSize(900, 700)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title_label = QLabel("🎉 朗读抽奖活动 🎉")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 提示文字
        hint_label = QLabel("大声朗读，让结果逐渐揭晓吧！")
        hint_font = QFont()
        hint_font.setPointSize(12)
        hint_label.setFont(hint_font)
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet("color: #666;")
        main_layout.addWidget(hint_label)
        
        # 抽奖结果显示区域
        result_frame = self.create_result_frame()
        main_layout.addWidget(result_frame, 1)
        
        # 音量监测区域
        volume_frame = self.create_volume_frame()
        main_layout.addWidget(volume_frame)
        
        # 揭晓进度区域
        progress_frame = self.create_progress_frame()
        main_layout.addWidget(progress_frame)
        
        # 状态提示标签
        self.status_label = QLabel("开始朗读，音量超过阈值时结果将逐渐清晰...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 13pt;
                color: #2196F3;
                padding: 10px;
                background-color: #E3F2FD;
                border-radius: 5px;
            }
        """)
        main_layout.addWidget(self.status_label)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.back_button = QPushButton("返回配置")
        self.back_button.setMinimumSize(120, 45)
        self.back_button.clicked.connect(self.on_back_to_config)
        button_layout.addWidget(self.back_button)
        
        button_layout.addStretch()
        
        self.reset_button = QPushButton("下一轮")
        self.reset_button.setMinimumSize(150, 45)
        self.reset_button.setEnabled(False)  # 初始禁用，揭晓完成后启用
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14pt;
                border-radius: 5px;
            }
            QPushButton:hover:enabled {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.reset_button.clicked.connect(self.on_reset)
        button_layout.addWidget(self.reset_button)
        
        main_layout.addLayout(button_layout)
    
    def create_result_frame(self) -> QFrame:
        """创建抽奖结果显示区域"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        frame.setLineWidth(3)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 3px solid #2196F3;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 结果标题
        result_title = QLabel("抽奖结果")
        result_title.setAlignment(Qt.AlignCenter)
        result_title_font = QFont()
        result_title_font.setPointSize(14)
        result_title_font.setBold(True)
        result_title.setFont(result_title_font)
        layout.addWidget(result_title)
        
        # 结果显示标签
        self.result_label = QLabel("???")
        self.result_label.setAlignment(Qt.AlignCenter)
        result_font = QFont()
        result_font.setPointSize(48)
        result_font.setBold(True)
        self.result_label.setFont(result_font)
        self.result_label.setMinimumHeight(200)
        self.result_label.setStyleSheet("""
            QLabel {
                color: #000;
                background-color: white;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        layout.addWidget(self.result_label)
        
        return frame
    
    def create_volume_frame(self) -> QFrame:
        """创建音量监测区域"""
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)
        
        # 音量标题和数值
        volume_header = QHBoxLayout()
        volume_title = QLabel("当前音量:")
        volume_title.setStyleSheet("font-size: 12pt; font-weight: bold;")
        volume_header.addWidget(volume_title)
        
        self.volume_value_label = QLabel("0.00")
        self.volume_value_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #4CAF50;")
        volume_header.addWidget(self.volume_value_label)
        
        volume_header.addSpacing(20)
        
        threshold_label = QLabel(f"阈值: {self.config.volume_threshold:.2f}")
        threshold_label.setStyleSheet("font-size: 12pt; color: #f44336;")
        volume_header.addWidget(threshold_label)
        
        volume_header.addStretch()
        layout.addLayout(volume_header)
        
        # 音量进度条
        self.volume_bar = QProgressBar()
        self.volume_bar.setRange(0, 100)
        self.volume_bar.setValue(0)
        self.volume_bar.setTextVisible(True)
        self.volume_bar.setFormat("%v%")
        self.volume_bar.setMinimumHeight(30)
        self.volume_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                background-color: #f0f0f0;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.volume_bar)
        
        return frame
    
    def create_progress_frame(self) -> QFrame:
        """创建揭晓进度区域"""
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)
        
        # 进度标题
        progress_header = QHBoxLayout()
        progress_title = QLabel("揭晓进度:")
        progress_title.setStyleSheet("font-size: 12pt; font-weight: bold;")
        progress_header.addWidget(progress_title)
        
        self.progress_percent_label = QLabel("0%")
        self.progress_percent_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #2196F3;")
        progress_header.addWidget(self.progress_percent_label)
        
        progress_header.addStretch()
        layout.addLayout(progress_header)
        
        # 揭晓进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("完成 %p%")
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                background-color: #f0f0f0;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        return frame
    
    def start_new_round(self):
        """开始新一轮抽奖"""
        # 重置状态
        self.reveal_progress = 0.0
        self.is_revealed = False
        self.lottery_service.reset()
        
        # 预抽奖
        self.current_result = self.lottery_service.draw()
        
        # 重置UI
        self.result_label.setText("???")
        self.result_label.setStyleSheet("""
            QLabel {
                color: #000;
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                opacity: 0.3;
            }
        """)
        self.progress_bar.setValue(0)
        self.progress_percent_label.setText("0%")
        self.reset_button.setEnabled(False)
        self.status_label.setText("开始朗读，音量超过阈值时结果将逐渐清晰...")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 13pt;
                color: #2196F3;
                padding: 10px;
                background-color: #E3F2FD;
                border-radius: 5px;
            }
        """)
        
        # 启动音频采集
        try:
            self.audio_service.start()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动音频采集失败:\n{str(e)}")
            return
        
        # 启动定时器
        self.update_timer.start(50)  # 50ms刷新UI
        self.progress_timer.start(100)  # 100ms更新进度
    
    def update_display(self):
        """更新显示（UI刷新）"""
        if not self.audio_service:
            return
        
        # 获取当前音量
        volume = self.audio_service.get_smoothed_volume()
        
        # 更新音量显示
        self.volume_bar.setValue(int(volume * 100))
        self.volume_value_label.setText(f"{volume:.2f}")
        
        # 根据阈值改变音量条颜色
        if volume >= self.config.volume_threshold:
            self.volume_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #ccc;
                    border-radius: 5px;
                    background-color: #f0f0f0;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 3px;
                }
            """)
        else:
            self.volume_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #ccc;
                    border-radius: 5px;
                    background-color: #f0f0f0;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #FF9800;
                    border-radius: 3px;
                }
            """)
        
        # 更新揭晓进度显示
        progress_percent = int(self.reveal_progress * 100)
        self.progress_bar.setValue(progress_percent)
        self.progress_percent_label.setText(f"{progress_percent}%")
        
        # 更新结果显示（根据进度调整可见度）
        self.update_result_display()
    
    def update_progress(self):
        """更新揭晓进度（逻辑更新）"""
        if self.is_revealed:
            return
        
        # 获取当前音量
        volume = self.audio_service.get_smoothed_volume()
        
        # 根据音量和阈值更新进度
        if volume >= self.config.volume_threshold:
            # 超过阈值，进度前进
            # 每100ms增加的进度 = 0.1秒 / reveal_seconds
            increment = 0.1 / self.config.reveal_seconds
            self.reveal_progress = min(1.0, self.reveal_progress + increment)
        else:
            # 低于阈值，进度回退
            # 每100ms减少的进度 = 0.1秒 / decay_seconds
            decrement = 0.1 / self.config.decay_seconds
            self.reveal_progress = max(0.0, self.reveal_progress - decrement)
        
        # 检查是否完全揭晓
        if self.reveal_progress >= 1.0 and not self.is_revealed:
            self.on_fully_revealed()
    
    def update_result_display(self):
        """根据揭晓进度更新结果显示"""
        if not self.current_result:
            return
        
        if self.is_revealed:
            # 完全揭晓：清晰显示
            self.result_label.setText(self.current_result.name)
            self.result_label.setStyleSheet("""
                QLabel {
                    color: #000;
                    background-color: #FFEB3B;
                    border-radius: 10px;
                    padding: 20px;
                    border: 3px solid #FFC107;
                }
            """)
        else:
            # 部分揭晓：根据进度显示
            if self.reveal_progress > 0.3:
                # 进度超过30%，开始显示文字
                self.result_label.setText(self.current_result.name)
            else:
                # 进度低于30%，显示问号
                self.result_label.setText("???")
            
            # 根据进度调整透明度（Phase 4 将实现更复杂的效果）
            # 这里使用简单的颜色深度变化
            opacity = int(self.reveal_progress * 255)
            bg_color = f"rgba(255, 255, 255, {opacity})"
            text_color = f"rgba(0, 0, 0, {opacity})"
            
            self.result_label.setStyleSheet(f"""
                QLabel {{
                    color: {text_color};
                    background-color: white;
                    border-radius: 10px;
                    padding: 20px;
                }}
            """)
    
    def on_fully_revealed(self):
        """完全揭晓时的处理"""
        self.is_revealed = True
        self.lottery_service.lock_result()
        
        # 更新状态提示
        self.status_label.setText(f"🎊 恭喜！抽中了: {self.current_result.name} 🎊")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 14pt;
                color: #4CAF50;
                font-weight: bold;
                padding: 15px;
                background-color: #C8E6C9;
                border-radius: 5px;
            }
        """)
        
        # 启用下一轮按钮
        self.reset_button.setEnabled(True)
        
        # 播放提示音（Phase 5 可选功能）
        # TODO: 添加音效
    
    def on_reset(self):
        """开始下一轮"""
        reply = QMessageBox.question(
            self,
            "开始下一轮",
            "确定开始下一轮抽奖吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.start_new_round()
    
    def on_back_to_config(self):
        """返回配置页"""
        reply = QMessageBox.question(
            self,
            "返回配置",
            "确定要返回配置页吗？当前活动将结束。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 停止定时器和音频
            self.stop_activity()
            # 发送信号
            self.back_to_config.emit()
            # 关闭窗口
            self.close()
    
    def stop_activity(self):
        """停止活动"""
        self.update_timer.stop()
        self.progress_timer.stop()
        
        if self.audio_service:
            self.audio_service.stop()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.stop_activity()
        event.accept()
