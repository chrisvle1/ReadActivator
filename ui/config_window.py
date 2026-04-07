"""
配置界面窗口
Phase 2: 添加实时音量监测功能
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QComboBox, QDoubleSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QGroupBox, QFormLayout, QSpinBox,
    QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from models.config_model import AppConfig
from models.prize_model import PrizeItem
from services.config_service import ConfigService
from services.audio_service import AudioService


class ConfigWindow(QMainWindow):
    """配置窗口类"""
    
    # 信号：点击开始按钮
    start_clicked = Signal(AppConfig)
    
    def __init__(self):
        super().__init__()
        self.config_service = ConfigService()
        self.current_config = self.config_service.load_config()
        
        # Phase 2: 音频服务
        self.audio_service = None
        self.is_monitoring = False
        
        # 用于更新UI的定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_volume_display)
        
        self.init_ui()
        self.load_config_to_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("小学生朗读激励抽奖 - 配置")
        self.setMinimumSize(800, 600)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("教师配置页")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 麦克风设置组
        mic_group = self.create_mic_group()
        main_layout.addWidget(mic_group)
        
        # 参数设置组
        param_group = self.create_param_group()
        main_layout.addWidget(param_group)
        
        # 奖项设置组
        prize_group = self.create_prize_group()
        main_layout.addWidget(prize_group, 1)  # 奖项组占据更多空间
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("保存配置")
        self.save_button.setMinimumSize(120, 40)
        self.save_button.clicked.connect(self.on_save_config)
        button_layout.addWidget(self.save_button)
        
        self.start_button = QPushButton("开始活动")
        self.start_button.setMinimumSize(120, 40)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_button.clicked.connect(self.on_start_activity)
        button_layout.addWidget(self.start_button)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
    
    def create_mic_group(self) -> QGroupBox:
        """创建麦克风设置组"""
        group = QGroupBox("麦克风设置")
        layout = QVBoxLayout()
        
        # 麦克风选择
        form_layout = QFormLayout()
        self.mic_combo = QComboBox()
        self.mic_combo.currentIndexChanged.connect(self.on_mic_changed)
        
        mic_list = self.config_service.get_microphone_list()
        for idx, name in mic_list:
            self.mic_combo.addItem(name, idx)
        form_layout.addRow("麦克风设备:", self.mic_combo)
        layout.addLayout(form_layout)
        
        # Phase 2: 实时音量监测
        volume_layout = QVBoxLayout()
        
        # 音量标签
        volume_label_layout = QHBoxLayout()
        volume_label_layout.addWidget(QLabel("实时音量:"))
        self.volume_value_label = QLabel("0.00")
        self.volume_value_label.setStyleSheet("font-weight: bold;")
        volume_label_layout.addWidget(self.volume_value_label)
        volume_label_layout.addStretch()
        volume_layout.addLayout(volume_label_layout)
        
        # 音量进度条
        self.volume_bar = QProgressBar()
        self.volume_bar.setRange(0, 100)
        self.volume_bar.setValue(0)
        self.volume_bar.setTextVisible(False)
        self.volume_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f0f0f0;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
        volume_layout.addWidget(self.volume_bar)
        
        # 阈值指示线（在进度条下方显示）
        threshold_layout = QHBoxLayout()
        self.threshold_indicator = QLabel("← 阈值位置")
        self.threshold_indicator.setStyleSheet("color: #f44336; font-size: 9pt;")
        threshold_layout.addStretch()
        threshold_layout.addWidget(self.threshold_indicator)
        volume_layout.addLayout(threshold_layout)
        
        layout.addLayout(volume_layout)
        
        # 测试按钮
        button_layout = QHBoxLayout()
        self.test_button = QPushButton("开始测试")
        self.test_button.setMaximumWidth(120)
        self.test_button.clicked.connect(self.on_toggle_test)
        button_layout.addWidget(self.test_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        group.setLayout(layout)
        return group
    
    def create_param_group(self) -> QGroupBox:
        """创建参数设置组"""
        group = QGroupBox("活动参数设置")
        layout = QFormLayout()
        
        # 音量阈值
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.01, 1.0)
        self.threshold_spin.setSingleStep(0.01)
        self.threshold_spin.setDecimals(2)
        self.threshold_spin.setSuffix(" (0.01-1.0)")
        layout.addRow("音量阈值:", self.threshold_spin)
        
        # 揭晓时间
        self.reveal_spin = QDoubleSpinBox()
        self.reveal_spin.setRange(1.0, 60.0)
        self.reveal_spin.setSingleStep(0.5)
        self.reveal_spin.setDecimals(1)
        self.reveal_spin.setSuffix(" 秒")
        layout.addRow("揭晓时长:", self.reveal_spin)
        
        # 回退时间
        self.decay_spin = QDoubleSpinBox()
        self.decay_spin.setRange(1.0, 60.0)
        self.decay_spin.setSingleStep(0.5)
        self.decay_spin.setDecimals(1)
        self.decay_spin.setSuffix(" 秒")
        layout.addRow("回退时长:", self.decay_spin)
        
        group.setLayout(layout)
        return group
    
    def create_prize_group(self) -> QGroupBox:
        """创建奖项设置组"""
        group = QGroupBox("奖项设置")
        layout = QVBoxLayout()
        
        # 奖项表格
        self.prize_table = QTableWidget()
        self.prize_table.setColumnCount(3)
        self.prize_table.setHorizontalHeaderLabels(["奖项名称", "权重", "操作"])
        
        # 设置列宽
        header = self.prize_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.prize_table.setColumnWidth(1, 100)
        self.prize_table.setColumnWidth(2, 80)
        
        layout.addWidget(self.prize_table)
        
        # 添加奖项按钮
        add_button = QPushButton("➕ 添加奖项")
        add_button.setMaximumWidth(150)
        add_button.clicked.connect(self.on_add_prize)
        layout.addWidget(add_button)
        
        group.setLayout(layout)
        return group
    
    def load_config_to_ui(self):
        """将配置加载到UI"""
        # 设置麦克风索引
        index = self.mic_combo.findData(self.current_config.mic_index)
        if index >= 0:
            self.mic_combo.setCurrentIndex(index)
        
        # 设置参数
        self.threshold_spin.setValue(self.current_config.volume_threshold)
        self.reveal_spin.setValue(self.current_config.reveal_seconds)
        self.decay_spin.setValue(self.current_config.decay_seconds)
        
        # 加载奖项列表
        self.load_prizes_to_table()
    
    def load_prizes_to_table(self):
        """加载奖项到表格"""
        self.prize_table.setRowCount(0)
        
        for prize in self.current_config.items:
            self.add_prize_row(prize)
    
    def add_prize_row(self, prize: PrizeItem):
        """添加奖项行到表格"""
        row = self.prize_table.rowCount()
        self.prize_table.insertRow(row)
        
        # 奖项名称（可编辑）
        name_item = QTableWidgetItem(prize.name)
        self.prize_table.setItem(row, 0, name_item)
        
        # 权重（使用SpinBox）
        weight_spin = QSpinBox()
        weight_spin.setRange(1, 1000)
        weight_spin.setValue(prize.weight)
        self.prize_table.setCellWidget(row, 1, weight_spin)
        
        # 删除按钮
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(lambda checked, r=row: self.on_delete_prize(r))
        self.prize_table.setCellWidget(row, 2, delete_button)
    
    def on_add_prize(self):
        """添加新奖项"""
        new_prize = PrizeItem(name="新奖项", weight=10)
        self.current_config.items.append(new_prize)
        self.add_prize_row(new_prize)
    
    def on_delete_prize(self, row: int):
        """删除奖项"""
        if self.prize_table.rowCount() <= 1:
            QMessageBox.warning(self, "警告", "至少需要保留一个奖项！")
            return
        
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            "确定要删除这个奖项吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.prize_table.removeRow(row)
            # 重新构建配置中的奖项列表
            self.update_config_from_ui()
    
    def update_config_from_ui(self) -> bool:
        """从UI更新配置"""
        try:
            # 更新麦克风索引
            self.current_config.mic_index = self.mic_combo.currentData()
            
            # 更新参数
            self.current_config.volume_threshold = self.threshold_spin.value()
            self.current_config.reveal_seconds = self.reveal_spin.value()
            self.current_config.decay_seconds = self.decay_spin.value()
            
            # 更新奖项列表
            self.current_config.items.clear()
            for row in range(self.prize_table.rowCount()):
                name_item = self.prize_table.item(row, 0)
                weight_spin = self.prize_table.cellWidget(row, 1)
                
                if name_item and weight_spin:
                    prize = PrizeItem(
                        name=name_item.text().strip(),
                        weight=weight_spin.value()
                    )
                    # 验证奖项
                    valid, error = prize.validate()
                    if not valid:
                        QMessageBox.warning(self, "验证失败", f"第 {row + 1} 行: {error}")
                        return False
                    
                    self.current_config.items.append(prize)
            
            # 验证整体配置
            valid, error = self.current_config.validate()
            if not valid:
                QMessageBox.warning(self, "验证失败", error)
                return False
            
            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新配置失败: {str(e)}")
            return False
    
    def on_save_config(self):
        """保存配置"""
        if not self.update_config_from_ui():
            return
        
        success, error = self.config_service.save_config(self.current_config)
        if success:
            QMessageBox.information(self, "成功", "配置已保存！")
        else:
            QMessageBox.critical(self, "保存失败", error)
    
    def on_start_activity(self):
        """开始活动"""
        if not self.update_config_from_ui():
            return
        
        # 停止当前的音量监测
        if self.is_monitoring:
            self.stop_monitoring()
        
        # Phase 3: 发送信号切换到活动界面
        self.start_clicked.emit(self.current_config)
    
    def on_mic_changed(self, index: int):
        """麦克风选择改变"""
        if self.is_monitoring and self.audio_service:
            # 如果正在监测，切换设备
            device_index = self.mic_combo.currentData()
            try:
                self.audio_service.set_device(device_index)
            except Exception as e:
                QMessageBox.warning(self, "设备切换失败", f"无法切换到选中的麦克风设备:\n{str(e)}")
    
    def on_toggle_test(self):
        """切换音量测试状态"""
        if not self.is_monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """开始音量监测"""
        try:
            device_index = self.mic_combo.currentData()
            
            # 创建音频服务
            if not self.audio_service:
                self.audio_service = AudioService(device_index=device_index)
            else:
                self.audio_service.set_device(device_index)
            
            # 启动音频采集
            self.audio_service.start()
            
            # 启动UI更新定时器（每50ms更新一次）
            self.update_timer.start(50)
            
            self.is_monitoring = True
            self.test_button.setText("停止测试")
            self.test_button.setStyleSheet("background-color: #f44336; color: white;")
            
        except Exception as e:
            QMessageBox.critical(self, "启动失败", f"无法启动音量监测:\n{str(e)}")
            self.is_monitoring = False
    
    def stop_monitoring(self):
        """停止音量监测"""
        if self.audio_service:
            self.audio_service.stop()
        
        self.update_timer.stop()
        self.is_monitoring = False
        
        # 重置UI
        self.volume_bar.setValue(0)
        self.volume_value_label.setText("0.00")
        self.test_button.setText("开始测试")
        self.test_button.setStyleSheet("")
    
    def update_volume_display(self):
        """更新音量显示"""
        if not self.audio_service or not self.is_monitoring:
            return
        
        # 获取平滑后的音量值
        volume = self.audio_service.get_smoothed_volume()
        
        # 更新进度条（0-100）
        self.volume_bar.setValue(int(volume * 100))
        
        # 更新数值标签
        self.volume_value_label.setText(f"{volume:.2f}")
        
        # 根据阈值改变进度条颜色
        threshold = self.threshold_spin.value()
        if volume >= threshold:
            # 超过阈值，显示绿色
            self.volume_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: #f0f0f0;
                    height: 20px;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 2px;
                }
            """)
        else:
            # 低于阈值，显示橙色
            self.volume_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: #f0f0f0;
                    height: 20px;
                }
                QProgressBar::chunk {
                    background-color: #FF9800;
                    border-radius: 2px;
                }
            """)
        
        # 更新阈值指示器位置
        threshold_percent = int(threshold * 100)
        self.threshold_indicator.setText(f"← 阈值({threshold:.2f})")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止音频监测
        self.stop_monitoring()
        
        if self.audio_service:
            self.audio_service.stop()
        
        event.accept()
