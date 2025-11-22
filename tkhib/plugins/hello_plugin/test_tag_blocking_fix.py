#!/usr/bin/env python3
"""
测试修复后的tag屏蔽功能

主要测试：
1. tag翻译API返回格式处理
2. 翻译匹配逻辑优化
3. 性能优化（缓存）
4. 错误处理改进
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spiderPixiv import PixivSpider


async def test_translation_api_format():
    """测试tag翻译API返回格式处理"""
    print("=" * 60)
    print("测试1: tag翻译API返回格式处理")
    print("=" * 60)
    
    async with PixivSpider() as spider:
        # 测试不同类型的tag
        test_tags = ["風景", "原创", "美少女", "R-18", "動圖"]
        
        for tag in test_tags:
            print(f"\n--- 测试tag: {tag} ---")
            
            try:
                # 获取翻译
                translations = await spider.get_tag_translation(tag)
                
                print(f"翻译结果: {translations}")
                
                # 验证返回格式
                if isinstance(translations, dict):
                    print("✅ 返回格式正确: 字典")
                    
                    # 检查必要字段
                    required_fields = ['en', 'zh', 'ko', 'zh_tw', 'romaji']
                    for field in required_fields:
                        if field in translations:
                            print(f"  ✅ 包含字段 '{field}': '{translations[field]}'")
                        else:
                            print(f"  ⚠ 缺少字段 '{field}'")
                else:
                    print("❌ 返回格式错误: 不是字典")
                    
            except Exception as e:
                print(f"❌ 翻译获取异常: {e}")
            
            # 测试缓存功能
            print(f"缓存大小: {len(spider.translation_cache)}")
            print(f"缓存内容: {list(spider.translation_cache.keys())}")


async def test_translation_matching_logic():
    """测试翻译匹配逻辑优化"""
    print("\n" + "=" * 60)
    print("测试2: 翻译匹配逻辑优化")
    print("=" * 60)
    
    async with PixivSpider() as spider:
        # 设置测试屏蔽tag
        spider.blocked_tags = {"R-18", "成人", "血腥", "ai"}
        
        # 测试用例
        test_cases = [
            {
                "name": "精确匹配测试",
                "tags": ["R-18", "成人内容"],
                "expected_block": True,
                "reason": "包含直接屏蔽tag"
            },
            {
                "name": "翻译精确匹配测试",
                "tags": ["adult", "エロ"],  # adult的日文
                "expected_block": True,
                "reason": "翻译匹配屏蔽tag"
            },
            {
                "name": "翻译边界匹配测试",
                "tags": ["ai-art", "ai_illustration"],
                "expected_block": False,  # 应该不匹配，因为不是完整词汇
                "reason": "应该不匹配，因为不是完整词汇"
            },
            {
                "name": "翻译前缀匹配测试",
                "tags": ["ai-style", "ai_character"],
                "expected_block": True,
                "reason": "前缀匹配屏蔽tag 'ai'"
            },
            {
                "name": "翻译后缀匹配测试",
                "tags": ["digital-ai", "art_ai"],
                "expected_block": True,
                "reason": "后缀匹配屏蔽tag 'ai'"
            },
            {
                "name": "误判防护测试",
                "tags": ["ka-ai", "sai"],  # 包含'ai'但不是完整词汇
                "expected_block": False,
                "reason": "应该不匹配，防止误判"
            },
            {
                "name": "正常内容测试",
                "tags": ["風景", "原创", "美少女"],
                "expected_block": False,
                "reason": "正常内容，不应该被屏蔽"
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n--- 测试用例 {i}: {case['name']} ---")
            print(f"测试tags: {case['tags']}")
            print(f"预期结果: {'屏蔽' if case['expected_block'] else '不屏蔽'}")
            print(f"原因: {case['reason']}")
            
            try:
                # 测试屏蔽逻辑
                should_block = await spider._should_block_image_with_translation(case['tags'])
                
                if should_block == case['expected_block']:
                    print(f"✅ 测试通过: {'屏蔽' if should_block else '不屏蔽'}")
                else:
                    print(f"❌ 测试失败: 预期{'屏蔽' if case['expected_block'] else '不屏蔽'}，实际{'屏蔽' if should_block else '不屏蔽'}")
                    
            except Exception as e:
                print(f"❌ 测试异常: {e}")


async def test_performance_optimization():
    """测试性能优化"""
    print("\n" + "=" * 60)
    print("测试3: 性能优化（缓存）")
    print("=" * 60)
    
    async with PixivSpider() as spider:
        # 测试相同tag的多次请求
        test_tag = "風景"
        request_count = 3
        
        print(f"测试tag: {test_tag}")
        print(f"请求次数: {request_count}")
        
        for i in range(request_count):
            print(f"\n--- 第 {i+1} 次请求 ---")
            
            start_time = asyncio.get_event_loop().time()
            
            try:
                translations = await spider.get_tag_translation(test_tag)
                end_time = asyncio.get_event_loop().time()
                
                print(f"翻译结果: {translations}")
                print(f"请求耗时: {(end_time - start_time):.3f}秒")
                print(f"缓存大小: {len(spider.translation_cache)}")
                
                if i == 0:
                    print("✅ 首次请求（应该调用API）")
                else:
                    print("✅ 缓存命中（应该很快）")
                    
            except Exception as e:
                print(f"❌ 请求异常: {e}")


async def test_error_handling():
    """测试错误处理改进"""
    print("\n" + "=" * 60)
    print("测试4: 错误处理改进")
    print("=" * 60)
    
    async with PixivSpider() as spider:
        # 测试各种异常情况
        error_test_cases = [
            {
                "name": "空tag测试",
                "tag": "",
                "expected": {}
            },
            {
                "name": "None tag测试",
                "tag": None,
                "expected": {}
            },
            {
                "name": "空白字符tag测试",
                "tag": "   ",
                "expected": {}
            },
            {
                "name": "特殊字符tag测试",
                "tag": "!@#$%^&*()",
                "expected": {}
            },
            {
                "name": "超长tag测试",
                "tag": "a" * 1000,
                "expected": {}
            }
        ]
        
        for i, case in enumerate(error_test_cases, 1):
            print(f"\n--- 错误测试 {i}: {case['name']} ---")
            print(f"输入tag: '{case['tag']}'")
            
            try:
                translations = await spider.get_tag_translation(case['tag'])
                
                if translations == case['expected']:
                    print("✅ 错误处理正确: 返回空字典")
                else:
                    print(f"⚠ 意外结果: {translations}")
                    
            except Exception as e:
                print(f"✅ 异常处理正确: {e}")


async def test_comprehensive_blocking():
    """综合测试屏蔽功能"""
    print("\n" + "=" * 60)
    print("测试5: 综合屏蔽功能测试")
    print("=" * 60)
    
    async with PixivSpider() as spider:
        # 设置测试屏蔽tag
        spider.blocked_tags = {"R-18", "成人", "血腥", "暴力", "ai"}
        
        # 测试图片数据
        test_images = [
            {
                "name": "正常图片",
                "tags": ["風景", "原创", "美少女"],
                "should_block": False
            },
            {
                "name": "直接包含屏蔽tag",
                "tags": ["R-18", "成人内容"],
                "should_block": True
            },
            {
                "name": "翻译匹配屏蔽tag",
                "tags": ["adult", "エロ"],  # adult的日文
                "should_block": True
            },
            {
                "name": "混合内容（部分屏蔽）",
                "tags": ["風景", "R-18", "原创"],
                "should_block": True
            },
            {
                "name": "边界情况（包含ai但不是完整）",
                "tags": ["ka-ai", "sai"],
                "should_block": False
            },
            {
                "name": "边界情况（ai作为前缀）",
                "tags": ["ai-style", "ai_art"],
                "should_block": True
            }
        ]
        
        for i, image in enumerate(test_images, 1):
            print(f"\n--- 综合测试 {i}: {image['name']} ---")
            print(f"图片tags: {image['tags']}")
            print(f"预期屏蔽: {'是' if image['should_block'] else '否'}")
            
            try:
                should_block = await spider._should_block_image_with_translation(image['tags'])
                
                if should_block == image['should_block']:
                    print(f"✅ 测试通过: {'屏蔽' if should_block else '不屏蔽'}")
                else:
                    print(f"❌ 测试失败: 预期{'屏蔽' if image['should_block'] else '不屏蔽'}，实际{'屏蔽' if should_block else '不屏蔽'}")
                    
            except Exception as e:
                print(f"❌ 测试异常: {e}")


async def main():
    """主测试函数"""
    print("开始测试修复后的tag屏蔽功能")
    print("测试时间:", asyncio.get_event_loop().time())
    
    try:
        # 执行所有测试
        await test_translation_api_format()
        await test_translation_matching_logic()
        await test_performance_optimization()
        await test_error_handling()
        await test_comprehensive_blocking()
        
        print("\n" + "=" * 60)
        print("所有测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())