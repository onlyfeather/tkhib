#!/usr/bin/env python3
"""
测试小众tag降级策略
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from spiderPixiv import PixivSpider


async def test_fallback_strategy():
    """测试降级策略"""
    
    print("=== 测试小众tag降级策略 ===")
    print()
    
    async with PixivSpider() as spider:
        # 检查Cookie状态
        if not spider.is_logged_in:
            print("❌ 未登录，请先设置Cookie")
            return
        
        print("✅ Cookie已加载")
        print()
        
        # 测试用例：小众tag + 高质量要求
        test_cases = [
            {
                'name': '小众tag组合 + 极高质量要求',
                'tags': ['风景', '唯美', '治愈', '温暖'],
                'mode': 'random',
                'count': 3,
                'min_quality_score': 95.0,  # 极高要求
                'description': '测试降级策略是否生效'
            },
            {
                'name': '小众tag组合 + 高质量要求',
                'tags': '风景 唯美 治愈',
                'mode': 'random',
                'count': 2,
                'min_quality_score': 80.0,  # 高要求
                'description': '测试部分降级'
            },
            {
                'name': '普通tag + 中等质量要求',
                'tags': '风景',
                'mode': 'random',
                'count': 2,
                'min_quality_score': 70.0,  # 中等要求
                'description': '对比测试'
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"🧪 测试 {i}: {test_case['name']}")
            print(f"   标签: {test_case['tags']}")
            print(f"   质量要求: {test_case['min_quality_score']}")
            print(f"   说明: {test_case['description']}")
            print()
            
            try:
                # 执行搜索
                result = await spider.search_images(
                    tags=test_case['tags'],
                    mode=test_case['mode'],
                    count=test_case['count'],
                    min_quality_score=test_case['min_quality_score']
                )
                
                if result:
                    print("✅ 搜索成功!")
                    print(f"   请求数量: {result['search_info']['requested_count']}")
                    print(f"   实际数量: {result['search_info']['actual_count']}")
                    print()
                    
                    # 分析图片来源
                    source_stats = {}
                    quality_stats = {'high_quality': 0, 'fallback': 0, 'no_score': 0}
                    
                    print("📊 图片分析:")
                    for j, image in enumerate(result['images'], 1):
                        source = image.get('source', 'unknown')
                        quality_score = image.get('quality_score')
                        
                        # 统计来源
                        source_stats[source] = source_stats.get(source, 0) + 1
                        
                        # 统计质量
                        if quality_score:
                            if quality_score['total_score'] >= test_case['min_quality_score']:
                                quality_stats['high_quality'] += 1
                            else:
                                quality_stats['fallback'] += 1
                            score_text = f"{quality_score['total_score']} ({quality_score['quality_level']})"
                        else:
                            quality_stats['no_score'] += 1
                            score_text = "无评分"
                        
                        print(f"   图片{j}: ID={image['id']}, 来源={source}, 评分={score_text}")
                    
                    print()
                    print("📈 统计结果:")
                    print(f"   来源统计: {dict(source_stats)}")
                    print(f"   质量统计: 高质量={quality_stats['high_quality']}, 降级={quality_stats['fallback']}, 无评分={quality_stats['no_score']}")
                    
                    # 判断降级策略是否生效
                    if quality_stats['fallback'] > 0 or quality_stats['no_score'] > 0:
                        print("   🔄 降级策略: 已生效")
                    else:
                        print("   ✅ 降级策略: 未需要（所有图片都符合高质量要求）")
                    
                else:
                    print("❌ 搜索失败")
                
            except Exception as e:
                print(f"❌ 测试异常: {e}")
            
            print("-" * 60)
            print()


async def test_edge_fallback():
    """测试极端降级情况"""
    print("=== 极端降级情况测试 ===")
    print()
    
    async with PixivSpider() as spider:
        # 测试极端情况：不存在的tag + 极高质量要求
        print("🧪 极端测试: 不存在的tag + 极高质量要求")
        
        try:
            result = await spider.search_images(
                tags='这个tag肯定不存在12345',
                mode='random',
                count=3,
                min_quality_score=99.0
            )
            
            if result:
                print("✅ 意外成功 - 返回了结果")
                print(f"   返回数量: {len(result['images'])}")
                for img in result['images']:
                    print(f"   ID: {img['id']}, 来源: {img.get('source', 'unknown')}")
            else:
                print("❌ 预期失败 - 没有找到任何图片")
                
        except Exception as e:
            print(f"❌ 异常: {e}")
        
        print()
        
        # 测试边界情况：很少结果的tag
        print("🧪 边界测试: 很少结果的tag")
        
        try:
            result = await spider.search_images(
                tags='风景 极其特殊的组合',
                mode='random',
                count=5,
                min_quality_score=85.0
            )
            
            if result:
                print("✅ 成功 - 使用了降级策略")
                print(f"   返回数量: {len(result['images'])}")
                source_stats = {}
                for img in result['images']:
                    source = img.get('source', 'unknown')
                    source_stats[source] = source_stats.get(source, 0) + 1
                print(f"   来源统计: {dict(source_stats)}")
            else:
                print("❌ 失败 - 没有找到任何图片")
                
        except Exception as e:
            print(f"❌ 异常: {e}")


if __name__ == "__main__":
    print("🚀 开始测试降级策略")
    print()
    
    # 基础降级测试
    asyncio.run(test_fallback_strategy())
    
    # 极端情况测试
    asyncio.run(test_edge_fallback())
    
