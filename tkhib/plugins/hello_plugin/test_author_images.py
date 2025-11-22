#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试作者图片获取功能
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spiderPixiv import PixivSpider


async def test_author_images():
    """测试作者图片获取功能"""
    
    # 测试作者ID（从用户提供的实际数据中获取）
    test_author_id = "101598284"
    
    async with PixivSpider() as spider:
        print("=== 测试作者图片获取功能 ===\n")
        
        # 测试不同模式
        modes = ["recent", "popular", "random"]
        
        for mode in modes:
            print(f"--- 测试模式: {mode} ---")
            
            try:
                # 获取作者图片
                result = await spider.get_author_images(
                    user_id=test_author_id,
                    mode=mode,
                    count=2
                )
                
                if result:
                    print(f"✅ {mode} 模式测试成功")
                    
                    # 打印作者信息
                    author_info = result.get('author_info', {})
                    print(f"作者信息:")
                    print(f"  - ID: {author_info.get('user_id')}")
                    print(f"  - 名称: {author_info.get('name')}")
                    print(f"  - 作品总数: {author_info.get('total_works')}")
                    print(f"  - 是否喜欢: {author_info.get('is_favorite')}")
                    
                    # 打印搜索信息
                    search_info = result.get('search_info', {})
                    print(f"搜索信息:")
                    print(f"  - 模式: {search_info.get('mode')}")
                    print(f"  - 请求数量: {search_info.get('requested_count')}")
                    print(f"  - 实际数量: {search_info.get('actual_count')}")
                    print(f"  - 时间: {search_info.get('timestamp')}")
                    
                    # 打印图片信息
                    images = result.get('images', [])
                    print(f"图片列表 (共 {len(images)} 张):")
                    
                    for i, image in enumerate(images, 1):
                        print(f"  图片 {i}:")
                        print(f"    - ID: {image.get('id')}")
                        print(f"    - 标题: {image.get('title')}")
                        print(f"    - 作者: {image.get('userName')}")
                        print(f"    - 尺寸: {image.get('width')}x{image.get('height')}")
                        print(f"    - 页数: {image.get('pageCount')}")
                        print(f"    - 创建时间: {image.get('createDate')}")
                        print(f"    - 来源: {image.get('source')}")
                        
                        # 质量评分（如果有）
                        quality_score = image.get('quality_score')
                        if quality_score:
                            print(f"    - 质量评分: {quality_score.get('total_score')} ({quality_score.get('quality_level')})")
                        
                        # 标签（只显示前5个）
                        tags = image.get('tags', [])
                        if tags:
                            display_tags = tags[:5]
                            if len(tags) > 5:
                                display_tags.append(f"...(+{len(tags)-5})")
                            print(f"    - 标签: {', '.join(display_tags)}")
                        
                        print()
                    
                else:
                    print(f"❌ {mode} 模式测试失败")
                
            except Exception as e:
                print(f"❌ {mode} 模式测试异常: {e}")
            
            print("-" * 50 + "\n")
        
        # 测试喜欢作者管理功能
        print("--- 测试喜欢作者管理 ---")
        
        try:
            # 添加喜欢作者
            success = spider.add_favorite_author(test_author_id, "f")
            print(f"添加喜欢作者: {'✅ 成功' if success else '❌ 失败'}")
            
            # 获取喜欢作者列表
            favorite_authors = spider.get_favorite_authors()
            print(f"喜欢作者数量: {len(favorite_authors)}")
            
            # 再次获取作者图片（这次应该显示为喜欢作者）
            print("\n--- 作为喜欢作者再次测试 ---")
            result = await spider.get_author_images(
                user_id=test_author_id,
                mode="recent",
                count=1
            )
            
            if result:
                author_info = result.get('author_info', {})
                print(f"作者信息更新:")
                print(f"  - 是否喜欢: {author_info.get('is_favorite')}")
                print(f"  - 名称: {author_info.get('name')}")
            
            # 移除喜欢作者
            success = spider.remove_favorite_author(test_author_id)
            print(f"移除喜欢作者: {'✅ 成功' if success else '❌ 失败'}")
            
        except Exception as e:
            print(f"❌ 喜欢作者管理测试异常: {e}")


async def test_author_edge_cases():
    """测试边界情况"""
    
    async with PixivSpider() as spider:
        print("\n=== 测试边界情况 ===\n")
        
        # 测试无效作者ID
        print("--- 测试无效作者ID ---")
        result = await spider.get_author_images("", mode="recent", count=1)
        print(f"空ID测试: {'✅ 正确返回None' if result is None else '❌ 应该返回None'}")
        
        result = await spider.get_author_images("invalid_id", mode="recent", count=1)
        print(f"无效ID测试: {'✅ 正确处理' if result is not None else '❌ 处理异常'}")
        
        # 测试无效参数
        print("\n--- 测试无效参数 ---")
        result = await spider.get_author_images("101598284", mode="invalid", count=1)
        print(f"无效模式测试: {'✅ 正确返回None' if result is None else '❌ 应该返回None'}")
        
        result = await spider.get_author_images("101598284", mode="recent", count=0)
        print(f"无效数量测试: {'✅ 正确返回None' if result is None else '❌ 应该返回None'}")
        
        result = await spider.get_author_images("101598284", mode="recent", count=10)
        print(f"超量数量测试: {'✅ 正确返回None' if result is None else '❌ 应该返回None'}")


if __name__ == "__main__":
    print("开始测试作者图片获取功能...")
    
    try:
        # 运行主要测试
        asyncio.run(test_author_images())
        
        # 运行边界情况测试
        asyncio.run(test_author_edge_cases())
        
        print("\n🎉 所有测试完成！")
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
