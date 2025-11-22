#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tag屏蔽功能测试
测试tag屏蔽是否正确整合到搜索功能中
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spiderPixiv import PixivSpider


async def test_tag_blocking():
    """测试tag屏蔽功能"""
    print("=== Tag屏蔽功能测试 ===\n")
    
    async with PixivSpider() as spider:
        # 1. 检查默认tag池配置
        print("1. 检查默认tag池配置:")
        tag_info = spider.get_tag_pools_info()
        print(f"   喜好tag数量: {tag_info['preferred_count']}")
        print(f"   厌恶tag数量: {tag_info['blocked_count']}")
        print(f"   默认厌恶tag: {tag_info['blocked_tags']}")
        print()
        
        # 2. 测试_should_block_image方法
        print("2. 测试_should_block_image方法:")
        
        # 获取当前实际的屏蔽tag池
        actual_blocked_tags = set(tag.lower().strip() for tag in spider.blocked_tags if tag and tag.strip())
        print(f"   当前实际屏蔽tag池: {list(actual_blocked_tags)}")
        print()
        
        # 测试用例 - 根据实际屏蔽tag池调整
        test_cases = [
            {
                "name": "正常图片（无屏蔽tag）",
                "tags": ["风景", "插画", "原创"],
                "should_block": False
            },
            {
                "name": "包含R-18 tag的图片",
                "tags": ["R-18", "插画"],
                "should_block": "r-18" in actual_blocked_tags
            },
            {
                "name": "包含血腥tag的图片",
                "tags": ["血腥", "暴力"],
                "should_block": "血腥" in actual_blocked_tags or "暴力" in actual_blocked_tags
            },
            {
                "name": "包含成人tag的图片",
                "tags": ["成人", "原创"],
                "should_block": "成人" in actual_blocked_tags
            },
            {
                "name": "大小写混合的R18 tag",
                "tags": ["r18", "插画"],
                "should_block": "r18" in actual_blocked_tags or "r-18" in actual_blocked_tags
            },
            {
                "name": "包含空格的tag",
                "tags": [" 暴力 ", "原创"],
                "should_block": "暴力" in actual_blocked_tags
            },
            {
                "name": "空tag列表",
                "tags": [],
                "should_block": False
            },
            {
                "name": "包含部分匹配的tag",
                "tags": ["血腥内容", "插画"],
                "should_block": any(blocked in "血腥内容" or "血腥内容" in blocked for blocked in actual_blocked_tags)
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            result = spider._should_block_image(test_case["tags"])
            expected = test_case["should_block"]
            status = "✅" if result == expected else "❌"
            
            print(f"   测试 {i}: {test_case['name']}")
            print(f"   输入tags: {test_case['tags']}")
            print(f"   预期结果: {expected}")
            print(f"   实际结果: {result}")
            print(f"   {status} {'通过' if result == expected else '失败'}")
            print()
        
        # 3. 测试添加和移除屏蔽tag
        print("3. 测试tag管理功能:")
        
        # 添加新的屏蔽tag
        test_blocked_tag = "测试屏蔽"
        print(f"   添加屏蔽tag: {test_blocked_tag}")
        spider.add_blocked_tag(test_blocked_tag)
        
        # 测试新添加的屏蔽tag
        test_tags = ["测试屏蔽", "插画"]
        result = spider._should_block_image(test_tags)
        print(f"   测试新添加的屏蔽tag: {result} (应该为True)")
        print(f"   ✅ {'通过' if result else '失败'}")
        print()
        
        # 移除屏蔽tag
        print(f"   移除屏蔽tag: {test_blocked_tag}")
        spider.remove_blocked_tag(test_blocked_tag)
        
        # 再次测试
        result = spider._should_block_image(test_tags)
        print(f"   测试移除后的屏蔽tag: {result} (应该为False)")
        print(f"   ✅ {'通过' if not result else '失败'}")
        print()
        
        # 4. 测试搜索功能中的tag屏蔽（如果有Cookie）
        print("4. 测试搜索功能中的tag屏蔽:")
        
        if spider.full_cookie:
            print("   检测到Cookie，测试搜索功能...")
            
            # 测试搜索可能包含屏蔽内容的tag
            test_search_tags = ["R-18", "风景"]
            
            for tag in test_search_tags:
                print(f"   搜索tag: {tag}")
                try:
                    result = await spider.search_illustrations(tag)
                    if result:
                        print(f"   ✅ 搜索成功，找到 {len(result.get('illusts', []))} 个结果")
                        print(f"   总计: {result.get('total', 0)} 个作品")
                        
                        # 检查返回的结果是否包含屏蔽内容
                        found_blocked = False
                        for illust in result.get('illusts', []):
                            if spider._should_block_image(illust.get('tags', [])):
                                found_blocked = True
                                break
                        
                        if not found_blocked:
                            print(f"   ✅ Tag屏蔽正常工作，返回结果中无屏蔽内容")
                        else:
                            print(f"   ❌ Tag屏蔽失效，返回结果中包含屏蔽内容")
                    else:
                        print(f"   ❌ 搜索失败")
                except Exception as e:
                    print(f"   ❌ 搜索异常: {e}")
                print()
        else:
            print("   ⚠️  未检测到Cookie，跳过搜索功能测试")
            print("   要测试搜索功能，请先设置Cookie")
        
        print("=== Tag屏蔽功能测试完成 ===")


if __name__ == "__main__":
    asyncio.run(test_tag_blocking())
