"""
配置数据模型
"""
from dataclasses import dataclass, field
from typing import List
from .prize_model import PrizeItem


@dataclass
class AppConfig:
    """应用配置模型"""
    mic_index: int = 0
    volume_threshold: float = 0.12
    reveal_seconds: float = 5.0
    decay_seconds: float = 7.0
    items: List[PrizeItem] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "mic_index": self.mic_index,
            "volume_threshold": self.volume_threshold,
            "reveal_seconds": self.reveal_seconds,
            "decay_seconds": self.decay_seconds,
            "items": [item.to_dict() for item in self.items]
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'AppConfig':
        """从字典创建配置对象"""
        config = AppConfig()
        config.mic_index = data.get("mic_index", 0)
        config.volume_threshold = data.get("volume_threshold", 0.12)
        config.reveal_seconds = data.get("reveal_seconds", 5.0)
        config.decay_seconds = data.get("decay_seconds", 7.0)
        config.items = [PrizeItem.from_dict(item) for item in data.get("items", [])]
        return config
    
    def validate(self) -> tuple[bool, str]:
        """验证配置是否合法"""
        if self.volume_threshold <= 0 or self.volume_threshold > 1:
            return False, "音量阈值必须在 0 到 1 之间"
        
        if self.reveal_seconds <= 0:
            return False, "揭晓时间必须大于 0"
        
        if self.decay_seconds <= 0:
            return False, "回退时间必须大于 0"
        
        if not self.items:
            return False, "至少需要一个奖项"
        
        total_weight = sum(item.weight for item in self.items)
        if total_weight <= 0:
            return False, "奖项权重总和必须大于 0"
        
        return True, ""
