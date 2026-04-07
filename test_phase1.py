"""
Phase 1 功能测试脚本
用于验证基础功能是否正常工作
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_models():
    """测试数据模型"""
    print("=" * 50)
    print("测试数据模型...")
    
    from models.prize_model import PrizeItem
    from models.config_model import AppConfig
    
    # 测试奖项模型
    prize = PrizeItem(name="测试奖项", weight=10)
    assert prize.name == "测试奖项"
    assert prize.weight == 10
    
    # 测试验证
    valid, msg = prize.validate()
    assert valid, f"奖项验证失败: {msg}"
    
    # 测试序列化
    prize_dict = prize.to_dict()
    assert prize_dict["name"] == "测试奖项"
    assert prize_dict["weight"] == 10
    
    # 测试反序列化
    prize2 = PrizeItem.from_dict(prize_dict)
    assert prize2.name == prize.name
    assert prize2.weight == prize.weight
    
    print("✅ 奖项模型测试通过")
    
    # 测试配置模型
    config = AppConfig()
    config.mic_index = 0
    config.volume_threshold = 0.15
    config.reveal_seconds = 5.0
    config.decay_seconds = 7.0
    config.items = [
        PrizeItem(name="奖品1", weight=30),
        PrizeItem(name="奖品2", weight=70)
    ]
    
    # 测试验证
    valid, msg = config.validate()
    assert valid, f"配置验证失败: {msg}"
    
    # 测试序列化
    config_dict = config.to_dict()
    assert config_dict["mic_index"] == 0
    assert len(config_dict["items"]) == 2
    
    # 测试反序列化
    config2 = AppConfig.from_dict(config_dict)
    assert config2.mic_index == config.mic_index
    assert len(config2.items) == len(config.items)
    
    print("✅ 配置模型测试通过")
    print()

def test_services():
    """测试服务层"""
    print("=" * 50)
    print("测试服务层...")
    
    from services.config_service import ConfigService
    from models.config_model import AppConfig
    from models.prize_model import PrizeItem
    
    # 测试配置服务
    service = ConfigService("data/test_config.json")
    
    # 测试获取默认配置
    default_config = service.get_default_config()
    assert len(default_config.items) > 0
    print(f"✅ 默认配置有 {len(default_config.items)} 个奖项")
    
    # 测试保存配置
    test_config = AppConfig()
    test_config.mic_index = 1
    test_config.volume_threshold = 0.2
    test_config.reveal_seconds = 6.0
    test_config.decay_seconds = 8.0
    test_config.items = [
        PrizeItem(name="测试奖品", weight=100)
    ]
    
    success, error = service.save_config(test_config)
    assert success, f"保存配置失败: {error}"
    print("✅ 配置保存成功")
    
    # 测试加载配置
    loaded_config = service.load_config()
    assert loaded_config.mic_index == 1
    assert loaded_config.volume_threshold == 0.2
    assert len(loaded_config.items) == 1
    assert loaded_config.items[0].name == "测试奖品"
    print("✅ 配置加载成功")
    
    # 测试麦克风列表
    mic_list = service.get_microphone_list()
    assert len(mic_list) > 0
    print(f"✅ 麦克风列表有 {len(mic_list)} 个设备")
    
    # 清理测试文件
    if os.path.exists("data/test_config.json"):
        os.remove("data/test_config.json")
    
    print("✅ 配置服务测试通过")
    print()

def test_validation():
    """测试数据验证"""
    print("=" * 50)
    print("测试数据验证...")
    
    from models.prize_model import PrizeItem
    from models.config_model import AppConfig
    
    # 测试空名称验证
    prize = PrizeItem(name="", weight=10)
    valid, msg = prize.validate()
    assert not valid, "应该检测到空名称错误"
    print(f"✅ 空名称验证: {msg}")
    
    # 测试零权重验证
    prize = PrizeItem(name="奖品", weight=0)
    valid, msg = prize.validate()
    assert not valid, "应该检测到零权重错误"
    print(f"✅ 零权重验证: {msg}")
    
    # 测试无效阈值
    config = AppConfig()
    config.volume_threshold = 1.5
    config.items = [PrizeItem(name="奖品", weight=10)]
    valid, msg = config.validate()
    assert not valid, "应该检测到无效阈值错误"
    print(f"✅ 无效阈值验证: {msg}")
    
    # 测试空奖项列表
    config = AppConfig()
    config.volume_threshold = 0.12
    config.items = []
    valid, msg = config.validate()
    assert not valid, "应该检测到空奖项列表错误"
    print(f"✅ 空奖项验证: {msg}")
    
    print("✅ 数据验证测试通过")
    print()

def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("Phase 1 功能测试")
    print("=" * 50 + "\n")
    
    try:
        test_models()
        test_services()
        test_validation()
        
        print("=" * 50)
        print("🎉 所有测试通过！Phase 1 功能正常")
        print("=" * 50)
        print("\n提示: 运行 'python app.py' 启动图形界面")
        return 0
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
