#!/usr/bin/env python3
"""
专门测试标签搜索功能的可行性
"""

import asyncio
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spiderPixiv import PixivSpider


async def test_tag_search():
    """测试标签搜索功能"""
    print("=== 测试标签搜索功能 ===")
    
    async with PixivSpider() as spider:
        # 测试单个标签搜索
        print("\n1. 测试单标签搜索: '风景'")
        try:
            result = await spider.search_illustrations('风景', page=1, page_size=5)
            if result and 'data' in result:
                print(f"✓ 单标签搜索成功，找到 {len(result['data'])} 张图片")
                for i, illust in enumerate(result['data'][:3], 1):
                    title = illust.get('title', '无标题')
                    artist = illust.get('userName', '未知作者')
                    print(f"  {i}. {title} - {artist}")
            else:
                print("✗ 单标签搜索失败")
        except Exception as e:
            print(f"✗ 单标签搜索出错: {e}")
        
        # 测试多个标签搜索
        print("\n2. 测试多标签搜索: ['美少女', '插画']")
        try:
            result = await spider.search_illustrations(['美少女', '插画'], page=1, page_size=5)
            if result and 'data' in result:
                print(f"✓ 多标签搜索成功，找到 {len(result['data'])} 张图片")
                for i, illust in enumerate(result['data'][:3], 1):
                    title = illust.get('title', '无标题')
                    artist = illust.get('userName', '未知作者')
                    print(f"  {i}. {title} - {artist}")
            else:
                print("✗ 多标签搜索失败")
        except Exception as e:
            print(f"✗ 多标签搜索出错: {e}")
        
        # 测试英文标签搜索
        print("\n3. 测试英文标签搜索: 'landscape'")
        try:
            result = await spider.search_illustrations('landscape', page=1, page_size=3)
            if result and 'data' in result:
                print(f"✓ 英文标签搜索成功，找到 {len(result['data'])} 张图片")
                for i, illust in enumerate(result['data'], 1):
                    title = illust.get('title', '无标题')
                    artist = illust.get('userName', '未知作者')
                    print(f"  {i}. {title} - {artist}")
            else:
                print("✗ 英文标签搜索失败")
        except Exception as e:
            print(f"✗ 英文标签搜索出错: {e}")


async def main():
    """主测试函数"""
    print("标签搜索功能可行性测试")
    print("=" * 40)
    
    try:
        # 检查Cookie
        spider = PixivSpider()
        if not spider.load_cookie():
            print("❌ 未找到有效的Cookie，请先运行 test_save_cookie.py")
            return
        
        print("✓ Cookie加载成功")
        
        # 运行标签搜索测试
        await test_tag_search()
        
        print("\n" + "=" * 40)
        print("✓ 标签搜索测试完成")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
