"""
活动界面窗口
Phase 3: 实现二层活动页与抽奖逻辑
Phase 4: 增强揭晓动画与视觉效果
Phase 5: 添加图标支持和错误处理
"""
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QMessageBox, QFrame,
    QGraphicsBlurEffect, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPalette, QIcon
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
        
        # Phase 4: 图形效果对象
        self.blur_effect = None
        self.opacity_effect = None
        self.reveal_animation = None
        
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
        
        # Phase 5: 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'read.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
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
        
        # Phase 4: 初始化图形效果
        self.init_graphics_effects()
        
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
    
    def init_graphics_effects(self):
        """Phase 4: 初始化图形效果"""
        # 模糊效果
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(30)  # 初始模糊半径
        
        # 透明度效果
        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0.3)  # 初始透明度
        
        # 将效果应用到结果标签
        # 注意：一个控件只能有一个图形效果，我们将优先使用模糊效果
        self.result_label.setGraphicsEffect(self.blur_effect)
    
    def start_new_round(self):
        """开始新一轮抽奖"""
        # 重置状态
        self.reveal_progress = 0.0
        self.is_revealed = False
        self.lottery_service.reset()
        
        # 预抽奖
        self.current_result = self.lottery_service.draw()
        
        # Phase 4: 重置UI和图形效果
        self.result_label.setText("???")
        self.result_label.setStyleSheet("""
            QLabel {
                color: #000;
                background-color: white;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        # 重置图形效果
        self.reset_graphics_effects()
        
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
        
        # Phase 4: 更新结果显示和图形效果
        self.update_result_display()
        self.update_reveal_effects()
    
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
            # 完全揭晓：清晰显示（在 on_fully_revealed 中处理）
            pass
        else:
            # 问题3优化：调整阶段阈值，90%才能看清文字
            if self.reveal_progress < 0.25:
                # 进度 < 25%: 显示问号
                self.result_label.setText("???")
            elif self.reveal_progress < 0.50:
                # 进度 25-50%: 显示部分遮挡的问号
                self.result_label.setText("? ? ?")
            elif self.reveal_progress < 0.75:
                # 进度 50-75%: 开始显示文字长度提示
                text_length = len(self.current_result.name)
                self.result_label.setText("□" * text_length)
            elif self.reveal_progress < 0.90:
                # 进度 75-90%: 显示模糊的文字（用特殊字符替换部分文字）
                text = self.current_result.name
                # 每隔一个字符用问号替换
                obscured = ''.join([c if i % 2 == 0 else '?' for i, c in enumerate(text)])
                self.result_label.setText(obscured)
            else:
                # 进度 ≥ 90%: 显示实际文字（配合模糊效果）
                self.result_label.setText(self.current_result.name)
            
            # 保持基础样式
            self.result_label.setStyleSheet("""
                QLabel {
                    color: #000;
                    background-color: white;
                    border-radius: 10px;
                    padding: 20px;
                }
            """)
    
    def update_reveal_effects(self):
        """Phase 4: 根据揭晓进度更新图形效果"""
        if not self.blur_effect or self.is_revealed:
            return
        
        # 计算模糊半径：从30降到0
        # progress: 0.0 -> 1.0, blur: 30 -> 0
        blur_radius = 30 * (1.0 - self.reveal_progress)
        self.blur_effect.setBlurRadius(max(0, blur_radius))
        
        # 额外的视觉反馈：根据进度改变背景色
        if self.reveal_progress < 0.3:
            bg_color = "#f0f0f0"  # 灰白色
        elif self.reveal_progress < 0.6:
            bg_color = "#e8f4f8"  # 淡蓝色
        elif self.reveal_progress < 0.9:
            bg_color = "#fff9e6"  # 淡黄色
        else:
            bg_color = "#fffacd"  # 柠檬黄
        
        self.result_label.setStyleSheet(f"""
            QLabel {{
                color: #000;
                background-color: {bg_color};
                border-radius: 10px;
                padding: 20px;
            }}
        """)
    
    def reset_graphics_effects(self):
        """Phase 4: 重置图形效果到初始状态"""
        # Bug修复：重新创建模糊效果对象（防止对象已被删除的问题）
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(30)
        
        # 应用效果到结果标签
        self.result_label.setGraphicsEffect(self.blur_effect)
    
    def on_fully_revealed(self):
        """完全揭晓时的处理"""
        self.is_revealed = True
        self.lottery_service.lock_result()
        
        # Phase 4: 移除模糊效果，显示最终结果
        self.result_label.setGraphicsEffect(None)
        self.result_label.setText(self.current_result.name)
        
        # Phase 4: 添加揭晓动画
        self.play_reveal_animation()
        
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
    
    def play_reveal_animation(self):
        """Phase 4: 播放揭晓完成动画"""
        # 创建临时的透明度效果用于动画
        temp_opacity_effect = QGraphicsOpacityEffect()
        temp_opacity_effect.setOpacity(0.3)
        self.result_label.setGraphicsEffect(temp_opacity_effect)
        
        # 创建透明度动画：从0.3淡入到1.0
        self.reveal_animation = QPropertyAnimation(temp_opacity_effect, b"opacity")
        self.reveal_animation.setDuration(600)  # 600ms动画
        self.reveal_animation.setStartValue(0.3)
        self.reveal_animation.setEndValue(1.0)
        self.reveal_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 动画结束后应用最终样式
        self.reveal_animation.finished.connect(self.apply_final_reveal_style)
        
        # 启动动画
        self.reveal_animation.start()
    
    def apply_final_reveal_style(self):
        """Phase 4: 应用揭晓完成后的最终样式"""
        # 移除动画效果
        self.result_label.setGraphicsEffect(None)
        
        # 应用高亮样式
        self.result_label.setStyleSheet("""
            QLabel {
                color: #000;
                background-color: #FFEB3B;
                border-radius: 10px;
                padding: 20px;
                border: 4px solid #FFC107;
            }
        """)
        
        # 清理动画对象
        if self.reveal_animation:
            self.reveal_animation.deleteLater()
            self.reveal_animation = None
    
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
        
        # Phase 4: 停止动画
        if self.reveal_animation and self.reveal_animation.state() == QPropertyAnimation.Running:
            self.reveal_animation.stop()
        
        if self.audio_service:
            self.audio_service.stop()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.stop_activity()
        event.accept()
