#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
作者圈名功能测试

测试圈名管理功能，包括：
1. 添加喜欢作者（带圈名）
2. 圈名管理（添加、删除、查询）
3. 通过圈名获取作者图片
4. 圈名冲突处理
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spiderPixiv import PixivSpider


async def test_author_alias_management():
    """测试作者圈名管理功能"""
    print("=" * 60)
    print("测试作者圈名管理功能")
    print("=" * 60)
    
    async with PixivSpider() as spider:
        # 1. 添加喜欢作者（带圈名）
        print("\n1. 添加喜欢作者（带圈名）")
        print("-" * 40)
        
        # 添加第一个作者
        success1 = spider.add_favorite_author(
            user_id="12345678",
            user_name="测试作者1",
            aliases=["画师A", "ArtistA", "测试画师1"]
        )
        print(f"添加作者1结果: {success1}")
        
        # 添加第二个作者
        success2 = spider.add_favorite_author(
            user_id="87654321",
            user_name="测试作者2",
            aliases=["画师B", "ArtistB"]
        )
        print(f"添加作者2结果: {success2}")
        
        # 2. 查看圈名映射
        print("\n2. 查看圈名映射")
        print("-" * 40)
        all_aliases = spider.get_all_aliases()
        print(f"所有圈名映射: {all_aliases}")
        
        # 3. 测试圈名搜索
        print("\n3. 测试圈名搜索")
        print("-" * 40)
        
        # 测试存在的圈名
        found_id1 = spider.search_author_by_alias("画师A")
        print(f"搜索 '画师A': {found_id1}")
        
        found_id2 = spider.search_author_by_alias("ArtistB")
        print(f"搜索 'ArtistB': {found_id2}")
        
        # 测试不存在的圈名
        found_id3 = spider.search_author_by_alias("不存在的圈名")
        print(f"搜索 '不存在的圈名': {found_id3}")
        
        # 4. 测试添加额外圈名
        print("\n4. 测试添加额外圈名")
        print("-" * 40)
        
        # 为第一个作者添加新圈名
        add_alias1 = spider.add_author_alias("12345678", "新圈名1")
        print(f"为作者12345678添加 '新圈名1': {add_alias1}")
        
        # 测试圈名冲突
        add_alias2 = spider.add_author_alias("87654321", "画师A")  # 这个圈名已被作者1使用
        print(f"为作者87654321添加 '画师A' (冲突测试): {add_alias2}")
        
        # 5. 获取作者的圈名列表
        print("\n5. 获取作者的圈名列表")
        print("-" * 40)
        
        aliases1 = spider.get_author_aliases("12345678")
        print(f"作者12345678的圈名: {aliases1}")
        
        aliases2 = spider.get_author_aliases("87654321")
        print(f"作者87654321的圈名: {aliases2}")
        
        # 6. 测试移除圈名
        print("\n6. 测试移除圈名")
        print("-" * 40)
        
        remove_alias1 = spider.remove_author_alias("12345678", "新圈名1")
        print(f"移除作者12345678的 '新圈名1': {remove_alias1}")
        
        # 7. 获取喜欢作者统计信息
        print("\n7. 获取喜欢作者统计信息")
        print("-" * 40)
        
        authors_info = spider.get_favorite_authors_info()
        print(f"喜欢作者统计:")
        print(f"  总数: {authors_info['total_count']}")
        print(f"  总圈名数: {authors_info['total_aliases']}")
        print(f"  最近添加: {authors_info['recent_added']}")
        print(f"  从未检查: {authors_info['never_checked']}")
        
        # 8. 保存配置
        print("\n8. 保存配置")
        print("-" * 40)
        
        save_result = spider.save_favorite_authors()
        print(f"保存喜欢作者配置: {save_result}")


async def test_author_images_with_alias():
    """测试通过圈名获取作者图片"""
    print("\n" + "=" * 60)
    print("测试通过圈名获取作者图片")
    print("=" * 60)
    
    async with PixivSpider() as spider:
        # 注意：这里需要真实的Cookie才能测试
        if not spider.full_cookie:
            print("⚠️  需要设置Cookie才能测试获取作者图片功能")
            print("请先运行 test_save_cookie.py 设置Cookie")
            return
        
        # 1. 通过作者ID获取图片
        print("\n1. 通过作者ID获取图片")
        print("-" * 40)
        
        try:
            result_by_id = await spider.get_author_images(
                user_id="12345678",  # 使用上面添加的作者ID
                mode="recent",
                count=2
            )
            
            if result_by_id:
                print(f"✅ 通过ID获取成功:")
                print(f"  作者: {result_by_id['author_info']['name']}")
                print(f"  作品数: {result_by_id['author_info']['total_works']}")
                print(f"  获取图片数: {len(result_by_id['images'])}")
            else:
                print("❌ 通过ID获取失败")
        except Exception as e:
            print(f"❌ 通过ID获取异常: {e}")
        
        # 2. 通过圈名获取图片
        print("\n2. 通过圈名获取图片")
        print("-" * 40)
        
        try:
            result_by_alias = await spider.get_author_images(
                user_id="画师A",  # 使用上面添加的圈名
                mode="recent",
                count=2
            )
            
            if result_by_alias:
                print(f"✅ 通过圈名获取成功:")
                print(f"  作者: {result_by_alias['author_info']['name']}")
                print(f"  作品数: {result_by_alias['author_info']['total_works']}")
                print(f"  获取图片数: {len(result_by_alias['images'])}")
                print(f"  使用圈名: 是")
            else:
                print("❌ 通过圈名获取失败")
        except Exception as e:
            print(f"❌ 通过圈名获取异常: {e}")
        
        # 3. 测试不存在的圈名
        print("\n3. 测试不存在的圈名")
        print("-" * 40)
        
        try:
            result_invalid = await spider.get_author_images(
                user_id="不存在的圈名",
                mode="recent",
                count=1
            )
            
            if result_invalid:
                print(f"❌ 意外成功: {result_invalid}")
            else:
                print("✅ 正确处理了不存在的圈名")
        except Exception as e:
            print(f"✅ 正确抛出异常: {e}")


async def test_alias_conflict_handling():
    """测试圈名冲突处理"""
    print("\n" + "=" * 60)
    print("测试圈名冲突处理")
    print("=" * 60)
    
    spider = PixivSpider()
    
    # 1. 添加两个作者，使用相同的圈名
    print("\n1. 测试圈名冲突")
    print("-" * 40)
    
    # 添加第一个作者
    success1 = spider.add_favorite_author(
        user_id="11111111",
        user_name="冲突测试作者1",
        aliases=["冲突圈名"]
    )
    print(f"添加作者1 (冲突圈名): {success1}")
    
    # 添加第二个作者，使用相同圈名
    success2 = spider.add_favorite_author(
        user_id="22222222",
        user_name="冲突测试作者2",
        aliases=["冲突圈名"]  # 与作者1冲突
    )
    print(f"添加作者2 (冲突圈名): {success2}")
    
    # 查看最终的圈名映射
    print("\n2. 查看冲突后的圈名映射")
    print("-" * 40)
    
    all_aliases = spider.get_all_aliases()
    print(f"最终圈名映射: {all_aliases}")
    
    # 检查冲突圈名指向哪个作者
    conflict_author = spider.search_author_by_alias("冲突圈名")
    print(f"'冲突圈名' 现在指向作者: {conflict_author}")


async def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 60)
    print("测试边界情况")
    print("=" * 60)
    
    spider = PixivSpider()
    
    # 1. 测试空参数
    print("\n1. 测试空参数")
    print("-" * 40)
    
    # 空作者ID
    result1 = spider.add_favorite_author("", "测试作者")
    print(f"空作者ID: {result1}")
    
    # 空圈名
    result2 = spider.add_author_alias("11111111", "")
    print(f"空圈名: {result2}")
    
    # 空搜索
    result3 = spider.search_author_by_alias("")
    print(f"空圈名搜索: {result3}")
    
    # 2. 测试不存在的作者
    print("\n2. 测试不存在的作者")
    print("-" * 40)
    
    result4 = spider.add_author_alias("99999999", "新圈名")
    print(f"为不存在作者添加圈名: {result4}")
    
    result5 = spider.get_author_aliases("99999999")
    print(f"获取不存在作者的圈名: {result5}")
    
    # 3. 测试重复圈名
    print("\n3. 测试重复圈名")
    print("-" * 40)
    
    # 先添加一个作者
    spider.add_favorite_author("33333333", "重复测试作者", ["重复圈名"])
    
    # 尝试添加重复圈名
    result6 = spider.add_author_alias("33333333", "重复圈名")
    print(f"添加重复圈名: {result6}")
    
    # 4. 测试特殊字符圈名
    print("\n4. 测试特殊字符圈名")
    print("-" * 40)
    
    spider.add_favorite_author("44444444", "特殊字符作者", ["特殊圈名!@#$%", "圈名 with spaces"])
    
    aliases = spider.get_author_aliases("44444444")
    print(f"特殊字符圈名: {aliases}")


async def main():
    """主测试函数"""
    print("🎨 作者圈名功能测试")
    print("测试圈名管理、冲突处理、边界情况等功能")
    
    try:
        # 测试圈名管理
        await test_author_alias_management()
        
        # 测试通过圈名获取图片
        await test_author_images_with_alias()
        
        # 测试冲突处理
        await test_alias_conflict_handling()
        
        # 测试边界情况
        await test_edge_cases()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())