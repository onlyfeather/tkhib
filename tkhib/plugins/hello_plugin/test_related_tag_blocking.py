#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试相关标签屏蔽功能

验证新增的 _should_block_image_with_translation 方法是否能够：
1. 正确检查图片标签的翻译匹配
2. 正确检查相关标签的匹配
3. 提供详细的调试信息
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tkhib.plugins.hello_plugin.spiderPixiv import PixivSpider


class MockPixivSpider(PixivSpider):
    """模拟Pixiv爬虫类，用于测试屏蔽功能"""
    
    def __init__(self):
        # 不调用父类初始化，避免网络请求
        self.blocked_tags = {"R-18", "成人", "血腥", "暴力"}
        self.translation_cache = {}
        self.cache_max_size = 100
    
    async def get_tag_translation(self, tag: str) -> dict:
        """模拟翻译API返回"""
        # 模拟一些常见的翻译结果
        mock_translations = {
            "R-18": {"zh": "成人", "en": "R-18"},
            "adult": {"zh": "成人", "en": "adult"},
            "gore": {"zh": "血腥", "en": "gore"},
            "violence": {"zh": "暴力", "en": "violence"},
            "safe": {"zh": "安全", "en": "safe"},
            "cute": {"zh": "可爱", "en": "cute"},
            "anime": {"zh": "动漫", "en": "anime"}
        }
        
        # 模拟网络延迟
        await asyncio.sleep(0.01)
        
        return mock_translations.get(tag.lower(), {})
    
    async def _should_block_image_with_translation(self, illust_tags: list, related_tags: list = None) -> bool:
        """重写方法以添加测试日志"""
        print(f"\n🔍 检查图片屏蔽:")
        print(f"   图片标签: {illust_tags}")
        print(f"   相关标签: {related_tags or []}")
        print(f"   屏蔽标签: {self.blocked_tags}")
        
        result = await super()._should_block_image_with_translation(illust_tags, related_tags)
        
        print(f"   结果: {'🚫 屏蔽' if result else '✅ 通过'}")
        return result


async def test_tag_blocking():
    """测试标签屏蔽功能"""
    print("=== 测试相关标签屏蔽功能 ===\n")
    
    spider = MockPixivSpider()
    
    # 测试用例
    test_cases = [
        {
            "name": "测试1: 图片标签直接匹配屏蔽标签",
            "illust_tags": ["R-18", "anime"],
            "related_tags": [],
            "expected": True
        },
        {
            "name": "测试2: 图片标签翻译匹配屏蔽标签",
            "illust_tags": ["adult", "cute"],
            "related_tags": [],
            "expected": True
        },
        {
            "name": "测试3: 相关标签匹配屏蔽标签",
            "illust_tags": ["cute", "anime"],
            "related_tags": ["R-18", "safe"],
            "expected": True
        },
        {
            "name": "测试4: 无匹配标签",
            "illust_tags": ["cute", "anime", "safe"],
            "related_tags": ["beautiful", "art"],
            "expected": False
        },
        {
            "name": "测试5: 空标签列表",
            "illust_tags": [],
            "related_tags": ["R-18"],
            "expected": False
        },
        {
            "name": "测试6: 混合情况 - 图片标签安全但相关标签包含屏蔽内容",
            "illust_tags": ["cute", "anime"],
            "related_tags": ["gore", "violence"],
            "expected": True
        },
        {
            "name": "测试7: 翻译词汇边界测试",
            "illust_tags": ["ka-ai"],  # 不应该匹配 "ai"
            "related_tags": [],
            "expected": False
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"运行 {test_case['name']}")
        print(f"{'='*60}")
        
        try:
            related_tags = test_case["related_tags"] if test_case["related_tags"] else None
            result = await spider._should_block_image_with_translation(
                test_case["illust_tags"], 
            )
            
            if result == test_case["expected"]:
                print(f"✅ 测试通过")
                passed += 1
            else:
                print(f"❌ 测试失败")
                print(f"   期望: {test_case['expected']}")
                print(f"   实际: {result}")
                failed += 1
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"测试结果汇总:")
    print(f"{'='*60}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📊 总计: {passed + failed}")
    print(f"🎯 成功率: {passed/(passed+failed)*100:.1f}%")
    
    return failed == 0


async def test_translation_cache():
    """测试翻译缓存功能"""
    print(f"\n{'='*60}")
    print("测试翻译缓存功能")
    print(f"{'='*60}")
    
    spider = MockPixivSpider()
    
    # 第一次调用（应该访问API）
    print("第一次调用 get_tag_translation('R-18'):")
    result1 = await spider.get_tag_translation("R-18")
    print(f"结果: {result1}")
    print(f"缓存大小: {len(spider.translation_cache)}")
    
    # 第二次调用（应该使用缓存）
    print("\n第二次调用 get_tag_translation('R-18'):")
    result2 = await spider.get_tag_translation("R-18")
    print(f"结果: {result2}")
    print(f"缓存大小: {len(spider.translation_cache)}")
    
    # 验证缓存是否生效
    if result1 == result2 and len(spider.translation_cache) == 1:
        print("✅ 翻译缓存功能正常")
        return True
    else:
        print("❌ 翻译缓存功能异常")
        return False


async def main():
    """主测试函数"""
    print("开始测试相关标签屏蔽功能...")
    
    # 测试标签屏蔽
    blocking_passed = await test_tag_blocking()
    
    # 测试翻译缓存
    cache_passed = await test_translation_cache()
    
    print(f"\n{'='*60}")
    print("最终测试结果:")
    print(f"{'='*60}")
    print(f"标签屏蔽功能: {'✅ 通过' if blocking_passed else '❌ 失败'}")
    print(f"翻译缓存功能: {'✅ 通过' if cache_passed else '❌ 失败'}")
    
    overall_passed = blocking_passed and cache_passed
    print(f"整体测试: {'✅ 全部通过' if overall_passed else '❌ 存在失败'}")
    
    return overall_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
