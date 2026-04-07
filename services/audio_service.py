"""
音频采集服务
Phase 2: 实现麦克风音频采集和音量计算
Phase 5: 增强异常处理和兜底逻辑
"""
import numpy as np
import sounddevice as sd
from typing import Optional, Callable, List
from collections import deque


class AudioService:
    """音频采集服务类"""
    
    def __init__(self, 
                 device_index: int = 0,
                 sample_rate: int = 44100,
                 block_size: int = 1024,
                 smoothing_window: int = 5):
        """
        初始化音频服务
        
        Args:
            device_index: 麦克风设备索引
            sample_rate: 采样率
            block_size: 每次读取的采样块大小
            smoothing_window: 平滑窗口大小（用于移动平均）
        """
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.smoothing_window = smoothing_window
        
        self.stream: Optional[sd.InputStream] = None
        self.is_running = False
        self.volume_callback: Optional[Callable[[float], None]] = None
        
        # 用于音量平滑的缓冲区
        self.volume_buffer = deque(maxlen=smoothing_window)
        self.current_volume = 0.0
        self.smoothed_volume = 0.0
    
    @staticmethod
    def get_device_list() -> List[tuple]:
        """
        获取系统音频设备列表
        
        Returns:
            [(设备索引, 设备名称, 输入通道数), ...]
        """
        devices = []
        try:
            device_info = sd.query_devices()
            
            for idx, device in enumerate(device_info):
                # 只返回有输入通道的设备（麦克风）
                if device['max_input_channels'] > 0:
                    name = device['name']
                    channels = device['max_input_channels']
                    devices.append((idx, name, channels))
            
            # Phase 5: 如果没有找到任何输入设备，返回默认设备
            if not devices:
                print("警告: 未找到任何音频输入设备，使用默认设备")
                devices.append((0, "默认麦克风", 1))
                
        except Exception as e:
            print(f"获取设备列表失败: {e}")
            # 返回默认设备作为兜底
            devices.append((0, "默认麦克风", 1))
        
        return devices
    
    @staticmethod
    def get_default_input_device() -> int:
        """
        获取默认输入设备索引
        
        Returns:
            默认设备索引
        """
        try:
            device = sd.query_devices(kind='input')
            if device and 'index' in device:
                return device['index']
            return 0
        except Exception as e:
            print(f"获取默认输入设备失败: {e}，使用设备索引0")
            return 0
    
    def calculate_volume(self, audio_data: np.ndarray) -> float:
        """
        计算音频数据的音量（RMS值）
        
        Args:
            audio_data: 音频数据数组
            
        Returns:
            归一化的音量值 (0.0 - 1.0)
        """
        try:
            # Phase 5: 添加数据有效性检查
            if audio_data is None or len(audio_data) == 0:
                return 0.0
            
            # 计算均方根(RMS)
            rms = np.sqrt(np.mean(audio_data**2))
            
            # 归一化到 0.0 - 1.0 范围
            # 通常RMS值在 0-0.5 之间，我们将其映射到 0-1
            volume = min(rms * 2.0, 1.0)
            
            return float(volume)
        except Exception as e:
            print(f"计算音量失败: {e}")
            return 0.0
    
    def smooth_volume(self, volume: float) -> float:
        """
        对音量值进行平滑处理（移动平均）
        
        Args:
            volume: 当前音量值
            
        Returns:
            平滑后的音量值
        """
        self.volume_buffer.append(volume)
        
        if len(self.volume_buffer) > 0:
            # 计算移动平均
            smoothed = sum(self.volume_buffer) / len(self.volume_buffer)
            return smoothed
        
        return volume
    
    def _audio_callback(self, indata, frames, time, status):
        """
        音频流回调函数
        
        Args:
            indata: 输入音频数据
            frames: 帧数
            time: 时间信息
            status: 状态信息
        """
        if status:
            print(f"音频流状态: {status}")
        
        try:
            # Phase 5: 添加数据有效性检查
            if indata is None or len(indata) == 0:
                return
            
            # 计算当前音量
            audio_data = indata[:, 0] if indata.ndim > 1 else indata
            self.current_volume = self.calculate_volume(audio_data)
            
            # 平滑处理
            self.smoothed_volume = self.smooth_volume(self.current_volume)
            
            # 调用音量回调
            if self.volume_callback:
                self.volume_callback(self.smoothed_volume)
        except Exception as e:
            print(f"音频回调处理失败: {e}")
    
    def start(self, volume_callback: Optional[Callable[[float], None]] = None):
        """
        启动音频采集
        
        Args:
            volume_callback: 音量更新回调函数，接收当前音量值
        """
        if self.is_running:
            return
        
        self.volume_callback = volume_callback
        
        try:
            self.stream = sd.InputStream(
                device=self.device_index,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                callback=self._audio_callback
            )
            self.stream.start()
            self.is_running = True
            print(f"音频采集已启动，设备索引: {self.device_index}")
        except sd.PortAudioError as e:
            # Phase 5: 更详细的错误处理
            error_msg = f"无法访问音频设备 {self.device_index}，可能设备不可用或被占用"
            print(f"{error_msg}: {e}")
            self.is_running = False
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"启动音频采集时发生未知错误"
            print(f"{error_msg}: {e}")
            self.is_running = False
            raise RuntimeError(error_msg) from e
    
    def stop(self):
        """停止音频采集"""
        if not self.is_running:
            return
        
        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            
            self.is_running = False
            self.volume_buffer.clear()
            self.current_volume = 0.0
            self.smoothed_volume = 0.0
            print("音频采集已停止")
        except Exception as e:
            print(f"停止音频采集失败: {e}")
            # Phase 5: 即使停止失败，也要重置状态
            self.is_running = False
            self.stream = None
    
    def set_device(self, device_index: int):
        """
        设置音频设备
        
        Args:
            device_index: 设备索引
        """
        was_running = self.is_running
        
        if was_running:
            self.stop()
        
        self.device_index = device_index
        
        if was_running:
            try:
                self.start(self.volume_callback)
            except Exception as e:
                print(f"切换设备后重新启动失败: {e}")
    
    def get_current_volume(self) -> float:
        """
        获取当前音量值（原始值）
        
        Returns:
            当前音量值
        """
        return self.current_volume
    
    def get_smoothed_volume(self) -> float:
        """
        获取平滑后的音量值
        
        Returns:
            平滑后的音量值
        """
        return self.smoothed_volume
    
    def test_device(self, device_index: int, duration: float = 2.0) -> bool:
        """
        测试音频设备是否可用
        
        Args:
            device_index: 设备索引
            duration: 测试持续时间（秒）
            
        Returns:
            设备是否可用
        """
        try:
            # 尝试录制一小段音频
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                device=device_index
            )
            sd.wait()
            
            # 检查是否有有效数据
            if recording is not None and len(recording) > 0:
                return True
            
            return False
        except Exception as e:
            print(f"测试设备 {device_index} 失败: {e}")
            return False
