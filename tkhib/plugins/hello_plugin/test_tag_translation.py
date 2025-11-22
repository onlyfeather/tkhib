#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tag翻译功能测试
测试tag翻译获取和翻译增强的tag屏蔽功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from spiderPixiv import PixivSpider


async def test_tag_translation():
    """测试tag翻译功能"""
    print("=" * 60)
    print("测试Tag翻译功能")
    print("=" * 60)
    
    async with PixivSpider() as spider:
        # 测试tag翻译获取
        test_tags = ["挠脚心", "足裏", "foot tickle", "くすぐり"]
        
        for tag in test_tags:
            print(f"\n🔍 测试tag: '{tag}'")
            translations = await spider.get_tag_translation(tag)
            
            if translations:
                print(f"✅ 翻译结果:")
                for lang, translated in translations.items():
                    if translated:
                        print(f"  {lang}: {translated}")
                    else:
                        print(f"  {lang}: (无翻译)")
            else:
                print(f"❌ 翻译失败")
        
        print("\n" + "=" * 60)


async def test_translation_blocking():
    """测试翻译增强的tag屏蔽功能"""
    print("=" * 60)
    print("测试翻译增强的Tag屏蔽功能")
    print("=" * 60)
    
    async with PixivSpider() as spider:
        # 添加一些测试用的屏蔽tag（包括英文）
        spider.add_blocked_tag("foot tickle")  # 英文
        spider.add_blocked_tag("足裏")        # 日文
        spider.add_blocked_tag("搔痒")        # 中文
        
        print(f"当前屏蔽tag池: {spider.blocked_tags}")
        
        # 测试不同语言的tag
        test_cases = [
            {
                "name": "英文tag匹配",
                "tags": ["foot tickle", "feet", "tickling"],
                "should_block": True
            },
            {
                "name": "日文tag匹配", 
                "tags": ["足裏", "足", "くすぐり"],
                "should_block": True
            },
            {
                "name": "中文tag匹配",
                "tags": ["搔痒", "脚底", "挠痒"],
                "should_block": True
            },
            {
                "name": "无匹配tag",
                "tags": ["风景", "美少女", "可爱"],
                "should_block": False
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n🧪 测试案例 {i}: {case['name']}")
            print(f"   测试tags: {case['tags']}")
            
            # 测试基础屏蔽检查
            basic_blocked = spider._should_block_image(case['tags'])
            print(f"   基础屏蔽结果: {basic_blocked}")
            
            # 测试翻译增强屏蔽检查
            translation_blocked = await spider._should_block_image_with_translation(case['tags'])
            print(f"   翻译增强屏蔽结果: {translation_blocked}")
            
            # 验证结果
            expected = case['should_block']
            if translation_blocked == expected:
                print(f"   ✅ 测试通过")
            else:
                print(f"   ❌ 测试失败 - 期望: {expected}, 实际: {translation_blocked}")
        
        print("\n" + "=" * 60)


async def test_real_world_scenarios():
    """测试真实世界场景"""
    print("=" * 60)
    print("测试真实世界场景")
    print("=" * 60)
    
    async with PixivSpider() as spider:
        # 设置常见的屏蔽tag
        common_blocked_tags = ["R-18", "成人", "足裏", "foot tickle", "搔痒"]
        for tag in common_blocked_tags:
            spider.add_blocked_tag(tag)
        
        print(f"屏蔽tag池: {spider.blocked_tags}")
        
        # 模拟一些真实的图片tag组合
        real_world_cases = [
            {
                "description": "正常风景图片",
                "tags": ["风景", "自然", "唯美", "治愈"],
                "should_block": False
            },
            {
                "description": "包含足部内容的图片（日文tag）",
                "tags": ["足裏", "足", "くすぐり", "足こちょ"],
                "should_block": True
            },
            {
                "description": "包含足部内容的图片（英文tag）",
                "tags": ["foot tickle", "feet", "tickling", "soles"],
                "should_block": True
            },
            {
                "description": "成人内容图片",
                "tags": ["R-18", "成人", "性感"],
                "should_block": True
            },
            {
                "description": "正常美少女图片",
                "tags": ["美少女", "可爱", "萌", "二次元"],
                "should_block": False
            }
        ]
        
        for i, case in enumerate(real_world_cases, 1):
            print(f"\n🎯 场景 {i}: {case['description']}")
            print(f"   Tags: {case['tags']}")
            
            # 使用翻译增强检查
            is_blocked = await spider._should_block_image_with_translation(case['tags'])
            
            expected = case['should_block']
            if is_blocked == expected:
                status = "✅ 通过"
            else:
                status = "❌ 失败"
            
            print(f"   屏蔽结果: {is_blocked} ({status})")
            
            if is_blocked != expected:
                print(f"   ⚠️  期望: {expected}, 实际: {is_blocked}")
        
        print("\n" + "=" * 60)


async def test_translation_performance():
    """测试翻译功能性能"""
    print("=" * 60)
    print("测试翻译功能性能")
    print("=" * 60)
    
    async with PixivSpider() as spider:
        import time
        
        # 测试单个tag翻译时间
        test_tag = "挠脚心"
        start_time = time.time()
        translations = await spider.get_tag_translation(test_tag)
        end_time = time.time()
        
        print(f"单个tag翻译测试:")
        print(f"  Tag: '{test_tag}'")
        print(f"  翻译结果: {translations}")
        print(f"  耗时: {(end_time - start_time) * 1000:.2f}ms")
        
        # 测试批量翻译时间
        test_tags = ["挠脚心", "足裏", "foot tickle", "くすぐり", "风景", "美少女"]
        print(f"\n批量翻译测试 ({len(test_tags)} 个tags):")
        
        start_time = time.time()
        results = []
        for tag in test_tags:
            translations = await spider.get_tag_translation(tag)
            results.append((tag, translations))
        end_time = time.time()
        
        total_time = (end_time - start_time) * 1000
        avg_time = total_time / len(test_tags)
        
        print(f"  总耗时: {total_time:.2f}ms")
        print(f"  平均耗时: {avg_time:.2f}ms")
        print(f"  成功率: {sum(1 for _, t in results if t)}/{len(results)}")
        
        print("\n" + "=" * 60)


async def main():
    """主测试函数"""
    print("🚀 开始Tag翻译功能测试")
    
    try:
        # 1. 测试基础翻译功能
        await test_tag_translation()
        
        # 2. 测试翻译增强的屏蔽功能
        await test_translation_blocking()
        
        # 3. 测试真实世界场景
        await test_real_world_scenarios()
        
        # 4. 测试性能
        await test_translation_performance()
        
        print("\n🎉 所有测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
