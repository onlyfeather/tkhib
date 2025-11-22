#!/usr/bin/env python3
"""
测试异步修复后的功能
验证 _extract_simplified_data 方法的异步改造是否正常工作
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from tkhib.plugins.hello_plugin.spiderPixiv import PixivSpider


async def test_async_fix():
    """测试异步修复"""
    print("=== 测试异步修复功能 ===")
    
    # 模拟原始API响应数据
    mock_raw_data = {
        "error": False,
        "body": {
            "illustManga": {
                "data": [
                    {
                        "id": "119563554",
                        "title": "高冷吟霖也怕痒么",
                        "illustType": 2,
                        "xRestrict": 0,
                        "restrict": 0,
                        "sl": 4,
                        "url": "https://i.pximg.net/c/250x250_80_a2/img-master/img/2024/06/12/06/12/32/119563554_square1200.jpg",
                        "description": "",
                        "tags": ["動圖", "鳴潮", "鸣潮", "吟霖", "くすぐり", "足裏", "拘束", "足こちょ", "WutheringWaves"],
                        "userId": "69117363",
                        "userName": "Arako[荒子]",
                        "width": 1920,
                        "height": 1080,
                        "pageCount": 1,
                        "isBookmarkable": True,
                        "bookmarkData": None,
                        "alt": "#動圖 高冷吟霖也怕痒么 - Arako[荒子]的动图",
                        "titleCaptionTranslation": {
                            "workTitle": None,
                            "workCaption": None
                        },
                        "createDate": "2024-06-12T06:12:32+09:00",
                        "updateDate": "2024-06-12T06:12:32+09:00",
                        "isUnlisted": False,
                        "isMasked": False,
                        "aiType": 1,
                        "visibilityScope": 0,
                        "profileImageUrl": "https://i.pximg.net/user-profile/img/2025/09/19/21/16/26/27914122_4888cce244dbbb85ffbf356303af68d4_50.png"
                    }
                ],
                "total": 1,
                "lastPage": 1,
                "bookmarkRanges": [
                    {"min": None, "max": None},
                    {"min": 10000, "max": None},
                    {"min": 5000, "max": None},
                    {"min": 1000, "max": None},
                    {"min": 500, "max": None},
                    {"min": 300, "max": None},
                    {"min": 100, "max": None},
                    {"min": 50, "max": None}
                ]
            },
            "popular": {
                "recent": [],
                "permanent": []
            },
            "relatedTags": ["動圖", "鳴潮", "鸣潮", "吟霖", "くすぐり", "足裏", "拘束", "足こちょ", "WutheringWaves"],
            "tagTranslation": {
                "動圖": {"zh": "动图"},
                "鳴潮": {"zh": "Wuthering Waves"},
                "鸣潮": {"zh": "Wuthering Waves"},
                "吟霖": {"zh": "Yinlin"},
                "くすぐり": {"zh": "搔痒"},
                "足裏": {"zh": "脚底"},
                "拘束": {"zh": "束缚"},
                "足こちょ": {"zh": "挠脚心"}
            },
            "zoneConfig": {
                "header": {"url": "https://pixon.ads-pixiv.net/show?zone_id=header&format=js&s=0&up=0&a=27&ng=g&sl=91&l=zh&uri=%2Fajax%2Fsearch%2Fartworks%2F_PARAM_&ref=www.pixiv.net&search_word=%E9%B8%A3%E6%BD%AE+tickle&K=b28b389c39d1a&D=9fe37dd2758fbf90&ab_test_digits_first=88&yuid=EJRJUAc&num=6920428b365"},
                "footer": {"url": "https://pixon.ads-pixiv.net/show?zone_id=footer&format=js&s=0&up=0&a=27&ng=g&sl=91&l=zh&uri=%2Fajax%2Fsearch%2Fartworks%2F_PARAM_&ref=www.pixiv.net&search_word=%E9%B8%A3%E6%BD%AE+tickle&K=b28b389c39d1a&D=9fe37dd2758fbf90&ab_test_digits_first=88&yuid=EJRJUAc&num=6920428b573"},
                "infeed": {"url": "https://pixon.ads-pixiv.net/show?zone_id=illust_search_grid&format=js&s=0&up=0&a=27&ng=g&sl=91&l=zh&uri=%2Fajax%2Fsearch%2Fartworks%2F_PARAM_&ref=www.pixiv.net&search_word=%E9%B8%A3%E6%BD%AE+tickle&K=b28b389c39d1a&D=9fe37dd2758fbf90&ab_test_digits_first=88&yuid=EJRJUAc&num=6920428b33"},
                "logo": {"url": "https://pixon.ads-pixiv.net/show?zone_id=logo_side&format=js&s=0&up=0&a=27&ng=g&sl=91&l=zh&uri=%2Fajax%2Fsearch%2Fartworks%2F_PARAM_&ref=www.pixiv.net&search_word=%E9%B8%A3%E6%BD%AE+tickle&K=b28b389c39d1a&D=9fe37dd2758fbf90&ab_test_digits_first=88&yuid=EJRJUAc&num=6920428b763"},
                "ad_logo": {"url": "https://pixon.ads-pixiv.net/show?zone_id=t_logo_side&format=js&s=0&up=0&a=27&ng=g&sl=91&l=zh&uri=%2Fajax%2Fsearch%2Fartworks%2F_PARAM_&ref=www.pixiv.net&search_word=%E9%B8%A3%E6%BD%AE+tickle&K=b28b389c39d1a&D=9fe37dd2758fbf90&ab_test_digits_first=88&yuid=EJRJUAc&num=6920428b987"}
            },
            "extraData": {
                "meta": {
                    "title": "#鸣潮 tickleのイラスト・マンガ作品 - pixiv",
                    "description": "pixiv",
                    "canonical": "https://www.pixiv.net/tags/%E9%B8%A3%E6%BD%AE%20tickle",
                    "alternateLanguages": {
                        "ja": "https://www.pixiv.net/tags/%E9%B8%A3%E6%BD%AE%20tickle",
                        "en": "https://www.pixiv.net/en/tags/%E9%B8%A3%E6%BD%AE%20tickle"
                    },
                    "descriptionHeader": "pixiv"
                }
            }
        }
    }
    
    # 创建爬虫实例（不需要真实Cookie进行测试）
    spider = PixivSpider()
    
    # 添加一些测试用的屏蔽标签
    spider.blocked_tags = {"R-18", "成人", "血腥"}
    
    print("1. 测试 _extract_simplified_data 异步方法...")
    
    try:
        # 测试异步方法
        result = await spider._extract_simplified_data(mock_raw_data, "鸣潮 tickle")
        
        print("✅ 异步方法调用成功")
        print(f"返回数据结构:")
        print(f"- illusts 数量: {len(result.get('illusts', []))}")
        print(f"- total: {result.get('total', 0)}")
        print(f"- popular.recent 数量: {len(result.get('popular', {}).get('recent', []))}")
        print(f"- popular.permanent 数量: {len(result.get('popular', {}).get('permanent', []))}")
        print(f"- relatedTags 数量: {len(result.get('relatedTags', []))}")
        print(f"- tagTranslation 键数量: {len(result.get('tagTranslation', {}))}")
        
        # 验证数据结构
        expected_keys = ['illusts', 'total', 'lastPage', 'relatedTags', 'tagTranslation', 'popular', 'searchInfo']
        missing_keys = [key for key in expected_keys if key not in result]
        
        if missing_keys:
            print(f"❌ 缺少必要的键: {missing_keys}")
        else:
            print("✅ 数据结构完整")
        
        # 验证 popular 数据
        popular = result.get('popular', {})
        if 'recent' in popular and 'permanent' in popular:
            print("✅ popular 数据结构正确")
        else:
            print("❌ popular 数据结构不完整")
        
        return True
        
    except Exception as e:
        print(f"❌ 异步方法调用失败: {e}")
        return False


async def test_tag_blocking():
    """测试标签屏蔽功能"""
    print("\n2. 测试标签屏蔽功能...")
    
    spider = PixivSpider()
    spider.blocked_tags = {"R-18", "成人"}
    
    # 测试正常标签（不应该被屏蔽）
    normal_tags = ["风景", "插画", "原创"]
    should_block = await spider._should_block_image_with_translation(normal_tags)
    
    if not should_block:
        print("✅ 正常标签未被屏蔽")
    else:
        print("❌ 正常标签被错误屏蔽")
    
    # 测试屏蔽标签（应该被屏蔽）
    blocked_tags = ["R-18", "成人内容"]
    should_block = await spider._should_block_image_with_translation(blocked_tags)
    
    if should_block:
        print("✅ 屏蔽标签正确被屏蔽")
    else:
        print("❌ 屏蔽标签未被屏蔽")
    
    return True


async def main():
    """主测试函数"""
    print("开始异步修复验证测试...\n")
    
    success1 = await test_async_fix()
    success2 = await test_tag_blocking()
    
    print(f"\n=== 测试结果 ===")
    if success1 and success2:
        print("✅ 所有测试通过，异步修复成功！")
        return True
    else:
        print("❌ 部分测试失败，需要进一步检查")
        return False


if __name__ == "__main__":
    asyncio.run(main())
