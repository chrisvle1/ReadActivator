"""
抽奖服务
Phase 3: 实现加权随机抽奖逻辑
"""
import random
from typing import Optional
from models.prize_model import PrizeItem
from models.config_model import AppConfig


class LotteryService:
    """抽奖服务类"""
    
    def __init__(self, config: AppConfig):
        """
        初始化抽奖服务
        
        Args:
            config: 应用配置对象
        """
        self.config = config
        self.current_result: Optional[PrizeItem] = None
        self.is_locked = False  # 结果是否已锁定
    
    def draw(self) -> PrizeItem:
        """
        执行加权随机抽奖
        
        Returns:
            抽中的奖项
        """
        if not self.config.items:
            raise ValueError("奖项列表为空，无法抽奖")
        
        # 计算总权重
        total_weight = sum(item.weight for item in self.config.items)
        if total_weight <= 0:
            raise ValueError("奖项总权重必须大于0")
        
        # 生成随机数
        rand_value = random.uniform(0, total_weight)
        
        # 根据权重选择奖项
        cumulative_weight = 0
        for item in self.config.items:
            cumulative_weight += item.weight
            if rand_value <= cumulative_weight:
                self.current_result = item
                self.is_locked = False
                return item
        
        # 兜底：返回最后一个奖项
        self.current_result = self.config.items[-1]
        self.is_locked = False
        return self.current_result
    
    def get_current_result(self) -> Optional[PrizeItem]:
        """
        获取当前抽奖结果
        
        Returns:
            当前结果，如果未抽奖则返回 None
        """
        return self.current_result
    
    def lock_result(self):
        """锁定当前结果（揭晓完成后调用）"""
        self.is_locked = True
    
    def is_result_locked(self) -> bool:
        """
        检查结果是否已锁定
        
        Returns:
            True 如果结果已锁定
        """
        return self.is_locked
    
    def reset(self):
        """重置抽奖状态，准备下一轮"""
        self.current_result = None
        self.is_locked = False
    
    def update_config(self, config: AppConfig):
        """
        更新配置
        
        Args:
            config: 新的配置对象
        """
        self.config = config
        # 如果正在进行的抽奖，保持当前结果
        # 如果想重置，需要手动调用 reset()
