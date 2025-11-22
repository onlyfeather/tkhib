#!/usr/bin/env python3
"""
随机图片推荐功能测试脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from spiderPixiv import PixivSpider


async def test_random_image():
    """测试随机图片推荐功能"""
    
    # 测试用户QQ号
    test_user_qq = "123456789"
    
    print("=== 随机图片推荐功能测试 ===")
    print(f"测试用户QQ: {test_user_qq}")
    print()
    
    async with PixivSpider() as spider:
        # 检查Cookie状态
        if not spider.is_logged_in:
            print("❌ 未登录，请先设置Cookie")
            print("可以使用以下命令设置Cookie:")
            print("spider.set_cookie('your_cookie_string')")
            return
        
        print("✅ Cookie已加载")
        print()
        
        # 显示tag池信息
        tag_info = spider.get_tag_pools_info()
        print(f"📋 喜好tag池: {tag_info['preferred_count']}个标签")
        print(f"   标签列表: {', '.join(tag_info['preferred_tags'])}")
        print(f"🚫 厌恶tag池: {tag_info['blocked_count']}个标签")
        print(f"   标签列表: {', '.join(tag_info['blocked_tags'])}")
        print()
        
        # 测试种子生成
        seed = spider._get_daily_seed(test_user_qq)
        print(f"🎲 今日种子: {seed}")
        print()
        
        # 获取随机图片推荐
        print("🔍 开始获取随机图片推荐...")
        random_result = await spider.get_random_image(test_user_qq)
        
        if random_result:
            print("✅ 随机图片推荐获取成功!")
            print()
            print("📊 结果详情:")
            print(f"   用户QQ: {random_result['user_qq']}")
            print(f"   选中标签: {random_result['tag']}")
            print(f"   图片ID: {random_result['image']['id']}")
            print(f"   图片标题: {random_result['image']['title']}")
            print(f"   作者: {random_result['image']['userName']}")
            print(f"   图片URL: {random_result['image']['url']}")
            print(f"   日期: {random_result['date']}")
            print(f"   可用标签数: {random_result['available_tags_count']}")
            print(f"   可用图片数: {random_result['available_images_count']}")
            
            # 显示质量评分
            if random_result.get('quality_score'):
                qs = random_result['quality_score']
                print()
                print("🎯 质量评分:")
                print(f"   总分: {qs['total_score']}")
                print(f"   等级: {qs['quality_level']}")
                print(f"   互动分数: {qs['interaction_score']}")
                print(f"   内容分数: {qs['content_score']}")
                print(f"   时间分数: {qs['time_score']}")
                print(f"   参与分数: {qs['engagement_score']}")
            else:
                print()
                print("⚠️  质量评分: 未获取")
            
            print()
            
            # 测试随机性 - 再次调用应该返回不同结果
            print("🔄 测试随机性 (再次调用)...")
            random_result2 = await spider.get_random_image(test_user_qq)
            
            if random_result2 and random_result2['image']['id'] != random_result['image']['id']:
                print("✅ 随机性测试通过 - 两次调用返回不同图片")
            else:
                print("⚠️  随机性测试 - 两次调用返回相同图片(可能是随机巧合)")
            
            print()
            
            # 测试不同用户
            print("🔄 测试不同用户...")
            test_user_qq2 = "987654321"
            random_result3 = await spider.get_random_image(test_user_qq2)
            
            if random_result3:
                print("✅ 不同用户测试通过 - 成功获取图片推荐")
            else:
                print("❌ 不同用户测试失败")
            
        else:
            print("❌ 每日一图获取失败")


async def test_seed_generation():
    """测试种子生成的确定性"""
    print("\n=== 种子生成测试 ===")
    
    spider = PixivSpider()
    
    test_cases = [
        ("123456789", "20241121"),
        ("123456789", "20241121"),  # 相同输入应该产生相同种子
        ("987654321", "20241121"),  # 不同用户应该产生不同种子
        ("123456789", "20241122"),  # 不同日期应该产生不同种子
    ]
    
    for i, (user_qq, date) in enumerate(test_cases):
        # 模拟特定日期的种子生成
        from datetime import datetime
        original_now = datetime.now
        
        # 创建模拟的特定日期
        class MockDateTime:
            @staticmethod
            def now():
                return datetime.strptime(date, "%Y%m%d")
            
            @staticmethod
            def strftime(fmt):
                return date
        
        # 临时替换datetime.now
        import spiderPixiv as spider_module
        original_datetime = spider_module.datetime
        spider_module.datetime = MockDateTime()
        
        try:
            seed = spider._get_daily_seed(user_qq)
            print(f"测试 {i+1}: 用户={user_qq}, 日期={date} -> 种子={seed}")
        finally:
            # 恢复原始datetime
            spider_module.datetime = original_datetime


if __name__ == "__main__":
    print("🚀 开始测试随机图片推荐功能")
    
    # 测试种子生成
    asyncio.run(test_seed_generation())
    
    # 测试随机图片推荐功能
    asyncio.run(test_random_image())
    
    print("\n🎉 测试完成!")