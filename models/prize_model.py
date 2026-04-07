"""
奖项数据模型
"""
from dataclasses import dataclass


@dataclass
class PrizeItem:
    """奖项模型"""
    name: str = ""
    weight: int = 1
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "weight": self.weight
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'PrizeItem':
        """从字典创建奖项对象"""
        return PrizeItem(
            name=data.get("name", ""),
            weight=data.get("weight", 1)
        )
    
    def validate(self) -> tuple[bool, str]:
        """验证奖项是否合法"""
        if not self.name or not self.name.strip():
            return False, "奖项名称不能为空"
        
        if self.weight <= 0:
            return False, "奖项权重必须大于 0"
        
        return True, ""
