#!/usr/bin/env python3
"""
搜图机器人核心功能测试脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from spiderPixiv import PixivSpider


async def test_search_bot():
    """测试搜图机器人核心功能"""
    
    print("=== 搜图机器人核心功能测试 ===")
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
        
        # 测试用例配置
        test_cases = [
            {
                'name': '随机图模式 - 单标签',
                'tags': '风景',
                'mode': 'random',
                'count': 2,
                'min_quality_score': 60.0
            },
            {
                'name': '随机图模式 - 多标签',
                'tags': ['风景', '唯美'],
                'mode': 'random',
                'count': 1,
                'min_quality_score': 70.0
            },
            {
                'name': '近日美图模式',
                'tags': '美少女',
                'mode': 'recent',
                'count': 3
            },
            {
                'name': '美图模式',
                'tags': '动漫',
                'mode': 'popular',
                'count': 2
            },
            {
                'name': '边界测试 - 最大数量',
                'tags': '插画',
                'mode': 'recent',
                'count': 5
            }
        ]
        
        # 执行测试用例
        for i, test_case in enumerate(test_cases, 1):
            print(f"🔍 测试 {i}: {test_case['name']}")
            print(f"   标签: {test_case['tags']}")
            print(f"   模式: {test_case['mode']}")
            print(f"   数量: {test_case['count']}")
            if 'min_quality_score' in test_case:
                print(f"   最低质量评分: {test_case['min_quality_score']}")
            print()
            
            try:
                # 调用搜图功能
                result = await spider.search_images(
                    tags=test_case['tags'],
                    mode=test_case['mode'],
                    count=test_case['count'],
                    min_quality_score=test_case.get('min_quality_score', 60.0)
                )
                
                if result:
                    print("✅ 搜图成功!")
                    print()
                    print("📊 搜索信息:")
                    search_info = result['search_info']
                    print(f"   搜索关键词: {search_info['search_keyword']}")
                    print(f"   模式: {search_info['mode']}")
                    print(f"   请求数量: {search_info['requested_count']}")
                    print(f"   实际数量: {search_info['actual_count']}")
                    print(f"   时间: {search_info['timestamp']}")
                    if search_info.get('min_quality_score'):
                        print(f"   最低质量评分: {search_info['min_quality_score']}")
                    print()
                    
                    print("📈 统计信息:")
                    stats = result['statistics']
                    print(f"   总搜索结果: {stats['total_search_results']}")
                    print(f"   近日热门: {stats['popular_recent_count']}")
                    print(f"   永久热门: {stats['popular_permanent_count']}")
                    print(f"   普通作品: {stats['regular_illust_count']}")
                    print()
                    
                    print("🖼️ 图片详情:")
                    for j, image in enumerate(result['images'], 1):
                        print(f"   图片 {j}:")
                        print(f"     ID: {image['id']}")
                        print(f"     标题: {image['title']}")
                        print(f"     作者: {image['userName']}")
                        print(f"     来源: {image['source']}")
                        if image.get('quality_score'):
                            qs = image['quality_score']
                            print(f"     质量评分: {qs['total_score']} ({qs['quality_level']})")
                        print(f"     标签: {', '.join(image['tags'][:3])}{'...' if len(image['tags']) > 3 else ''}")
                        print()
                else:
                    print("❌ 搜图失败")
                
            except Exception as e:
                print(f"❌ 测试异常: {e}")
            
            print("-" * 60)
            print()


async def test_edge_cases():
    """测试边界情况"""
    print("=== 边界情况测试 ===")
    print()
    
    async with PixivSpider() as spider:
        edge_cases = [
            {
                'name': '无效模式',
                'tags': '风景',
                'mode': 'invalid_mode',
                'count': 1,
                'should_fail': True
            },
            {
                'name': '数量超限',
                'tags': '风景',
                'mode': 'random',
                'count': 10,
                'should_fail': True
            },
            {
                'name': '空标签',
                'tags': '',
                'mode': 'random',
                'count': 1,
                'should_fail': True
            },
            {
                'name': '高质量要求',
                'tags': '风景',
                'mode': 'random',
                'count': 1,
                'min_quality_score': 95.0,
                'should_fail': False  # 可能成功，但很可能失败
            }
        ]
        
        for i, test_case in enumerate(edge_cases, 1):
            print(f"🧪 边界测试 {i}: {test_case['name']}")
            
            try:
                result = await spider.search_images(
                    tags=test_case['tags'],
                    mode=test_case['mode'],
                    count=test_case['count'],
                    min_quality_score=test_case.get('min_quality_score', 60.0)
                )
                
                if test_case['should_fail']:
                    print(f"❌ 预期失败但成功了: {result}")
                else:
                    if result:
                        print(f"✅ 成功: 找到 {len(result['images'])} 张图片")
                    else:
                        print(f"⚠️  失败: 符合预期（高质量要求可能找不到图片）")
                        
            except Exception as e:
                if test_case['should_fail']:
                    print(f"✅ 预期异常: {e}")
                else:
                    print(f"❌ 意外异常: {e}")
            
            print()


async def test_performance():
    """测试性能"""
    print("=== 性能测试 ===")
    print()
    
    async with PixivSpider() as spider:
        import time
        
        # 测试不同模式的响应时间
        performance_tests = [
            {
                'name': '随机图模式',
                'tags': '风景',
                'mode': 'random',
                'count': 1
            },
            {
                'name': '近日美图模式',
                'tags': '美少女',
                'mode': 'recent',
                'count': 3
            },
            {
                'name': '美图模式',
                'tags': '动漫',
                'mode': 'popular',
                'count': 2
            }
        ]
        
        for test in performance_tests:
            print(f"⏱️  性能测试: {test['name']}")
            
            start_time = time.time()
            result = await spider.search_images(
                tags=test['tags'],
                mode=test['mode'],
                count=test['count']
            )
            end_time = time.time()
            
            duration = end_time - start_time
            
            if result:
                print(f"   ✅ 成功 - 耗时: {duration:.2f}秒")
                print(f"   📊 找到 {len(result['images'])} 张图片")
            else:
                print(f"   ❌ 失败 - 耗时: {duration:.2f}秒")
            
            print()


if __name__ == "__main__":
    print("🚀 开始测试搜图机器人核心功能")
    print()
    
    # 基础功能测试
    asyncio.run(test_search_bot())
    
    # 边界情况测试
    asyncio.run(test_edge_cases())
    
    # 性能测试
    asyncio.run(test_performance())
    
    print("🎉 测试完成!")
