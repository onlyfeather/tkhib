#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试获取标签最新更新图片功能
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from spiderPixiv import PixivSpider


async def test_get_tag_latest_images():
    """测试获取标签最新更新图片功能"""
    
    print("=== 测试获取标签最新更新图片功能 ===\n")
    
    async with PixivSpider() as spider:
        # 测试1: 获取单个标签的最新图片
        print("1. 测试获取单个标签的最新图片...")
        try:
            result = await spider.get_tag_latest_images(
                tag="风景",
                count=3,
                hours_limit=24
            )
            
            if result:
                print(f"✅ 成功获取标签最新图片")
                print(f"搜索信息: {result['search_info']}")
                print(f"统计信息: {result['statistics']}")
                print(f"图片数量: {len(result['images'])}")
                
                for i, image in enumerate(result['images'], 1):
                    print(f"  图片 {i}:")
                    print(f"    ID: {image['id']}")
                    print(f"    标题: {image['title']}")
                    print(f"    作者: {image['userName']}")
                    print(f"    创建时间: {image['createDate']}")
                    print(f"    上传小时数: {image.get('hours_since_upload', 0):.1f}")
                    print(f"    质量评分: {image.get('quality_score', {}).get('total_score', 'N/A')}")
                    print(f"    标签: {', '.join(image['tags'][:3])}...")
                    print()
            else:
                print("❌ 获取标签最新图片失败")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # 测试2: 获取多标签的最新图片
        print("2. 测试获取多标签的最新图片...")
        try:
            result = await spider.get_tag_latest_images(
                tag=["风景", "原创"],
                count=2,
                hours_limit=12
            )
            
            if result:
                print(f"✅ 成功获取多标签最新图片")
                print(f"搜索关键词: {result['search_info']['search_keyword']}")
                print(f"图片数量: {len(result['images'])}")
                
                for i, image in enumerate(result['images'], 1):
                    print(f"  图片 {i}: {image['title']} (ID: {image['id']})")
                    
            else:
                print("❌ 获取多标签最新图片失败")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # 测试3: 测试时间限制（短时间范围）
        print("3. 测试短时间范围（6小时内）...")
        try:
            result = await spider.get_tag_latest_images(
                tag="插画",
                count=5,
                hours_limit=6
            )
            
            if result:
                print(f"✅ 成功获取短时间范围内的最新图片")
                print(f"时间阈值: {result['search_info']['time_threshold']}")
                print(f"搜索页数: {result['search_info']['pages_searched']}")
                print(f"候选图片: {result['search_info']['total_candidates']}")
                print(f"实际返回: {len(result['images'])}")
                
                # 验证时间范围
                for image in result['images']:
                    hours = image.get('hours_since_upload', 0)
                    if hours > 6:
                        print(f"⚠️ 警告: 图片 {image['id']} 超出时间范围 ({hours:.1f}小时)")
                    
            else:
                print("❌ 获取短时间范围内图片失败（可能该时间段内没有新图片）")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # 测试4: 测试参数验证
        print("4. 测试参数验证...")
        try:
            # 测试无效的图片数量
            result = await spider.get_tag_latest_images(
                tag="风景",
                count=15,  # 超出范围
                hours_limit=24
            )
            print("❌ 应该拒绝无效的图片数量")
            
        except Exception as e:
            print(f"✅ 正确捕获参数错误: {e}")
        
        try:
            # 测试无效的时间限制
            result = await spider.get_tag_latest_images(
                tag="风景",
                count=3,
                hours_limit=200  # 超出范围
            )
            print("❌ 应该拒绝无效的时间限制")
            
        except Exception as e:
            print(f"✅ 正确捕获参数错误: {e}")
        
        try:
            # 测试空标签
            result = await spider.get_tag_latest_images(
                tag="",
                count=3,
                hours_limit=24
            )
            print("❌ 应该拒绝空标签")
            
        except Exception as e:
            print(f"✅ 正确捕获空标签错误: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # 测试5: 测试热门标签的最新图片
        print("5. 测试热门标签的最新图片...")
        try:
            result = await spider.get_tag_latest_images(
                tag="美少女",
                count=3,
                hours_limit=48  # 2天内
            )
            
            if result:
                print(f"✅ 成功获取热门标签最新图片")
                print(f"平均上传时间: {result['statistics']['avg_hours_since_upload']:.1f}小时")
                print(f"有质量评分的图片: {result['statistics']['quality_scored']}/{len(result['images'])}")
                
                # 显示质量评分统计
                quality_scores = [img.get('quality_score', {}).get('total_score', 0) 
                                 for img in result['images'] if img.get('quality_score')]
                if quality_scores:
                    avg_score = sum(quality_scores) / len(quality_scores)
                    print(f"平均质量评分: {avg_score:.1f}")
                    
            else:
                print("❌ 获取热门标签最新图片失败")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
        
        print("\n=== 测试完成 ===")


async def test_performance():
    """测试性能和限流"""
    
    print("\n=== 测试性能和限流 ===\n")
    
    async with PixivSpider() as spider:
        start_time = datetime.now()
        
        # 连续请求多个标签
        tags = ["风景", "插画", "原创", "动漫", "二次元"]
        
        for i, tag in enumerate(tags, 1):
            print(f"第 {i} 次请求: {tag}")
            
            try:
                result = await spider.get_tag_latest_images(
                    tag=tag,
                    count=2,
                    hours_limit=24
                )
                
                if result:
                    print(f"  ✅ 成功获取 {len(result['images'])} 张图片")
                else:
                    print(f"  ❌ 获取失败")
                    
            except Exception as e:
                print(f"  ❌ 请求异常: {e}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n总耗时: {duration:.2f}秒")
        print(f"平均每次请求: {duration/len(tags):.2f}秒")
        print("限流机制应该在工作，避免请求过快")


async def main():
    """主函数"""
    print("开始标签最新图片功能测试...\n")
    
    try:
        await test_get_tag_latest_images()
        await test_performance()
        
        print("\n=== 所有测试完成 ===")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
