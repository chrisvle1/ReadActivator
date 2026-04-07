"""
配置管理服务
"""
import json
import os
from typing import Optional
from models.config_model import AppConfig
from models.prize_model import PrizeItem


class ConfigService:
    """配置服务类，负责配置的读取、保存和默认配置生成"""
    
    def __init__(self, config_path: str = "data/config.json"):
        """
        初始化配置服务
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        data_dir = os.path.dirname(self.config_path)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
    
    def get_default_config(self) -> AppConfig:
        """
        获取默认配置
        
        Returns:
            默认的应用配置对象
        """
        config = AppConfig()
        config.mic_index = 0
        config.volume_threshold = 0.12
        config.reveal_seconds = 5.0
        config.decay_seconds = 7.0
        config.items = [
            PrizeItem(name="谢谢惠顾", weight=50),
            PrizeItem(name="小玩具1个", weight=20),
            PrizeItem(name="休息5分钟", weight=20),
            PrizeItem(name="贴纸1张", weight=10)
        ]
        return config
    
    def load_config(self) -> AppConfig:
        """
        从文件加载配置
        
        Returns:
            应用配置对象
        """
        if not os.path.exists(self.config_path):
            # 配置文件不存在，返回默认配置
            return self.get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return AppConfig.from_dict(data)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return self.get_default_config()
    
    def save_config(self, config: AppConfig) -> tuple[bool, str]:
        """
        保存配置到文件
        
        Args:
            config: 要保存的配置对象
            
        Returns:
            (是否成功, 错误信息)
        """
        # 先验证配置
        valid, error_msg = config.validate()
        if not valid:
            return False, error_msg
        
        try:
            self._ensure_data_dir()
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
            return True, ""
        except Exception as e:
            return False, f"保存配置失败: {str(e)}"
    
    def get_microphone_list(self) -> list[tuple[int, str]]:
        """
        获取系统麦克风列表
        
        Returns:
            [(索引, 设备名称), ...]
        """
        # Phase 2: 使用 sounddevice 获取实际设备列表
        try:
            from services.audio_service import AudioService
            devices = AudioService.get_device_list()
            
            # 只返回索引和名称
            return [(idx, name) for idx, name, _ in devices]
        except Exception as e:
            print(f"获取麦克风列表失败: {e}")
            # 失败时返回默认设备
            return [(0, "默认麦克风")]
