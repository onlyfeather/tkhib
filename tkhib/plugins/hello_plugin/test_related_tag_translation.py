#!/usr/bin/env python3
"""
测试相关标签翻译检查功能

这个测试文件验证：
1. _should_block_image_with_translation 方法是否正确利用 API 返回的 tagTranslation 数据
2. 相关标签翻译检查是否限制检查范围（前5个）
3. 翻译匹配逻辑是否正确工作
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spiderPixiv import PixivSpider


async def test_related_tag_translation():
    """测试相关标签翻译检查功能"""
    
    print("=== 测试相关标签翻译检查功能 ===\n")
    
    # 模拟 API 返回的数据结构
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
                "lastPage": 1
            },
            "relatedTags": ["動圖", "鳴潮", "鸣潮", "吟霖", "くすぐり", "足裏", "拘束", "足こちょ", "WutheringWaves", "R-18", "成人内容"],
            "tagTranslation": {
                "動圖": {"zh": "动图"},
                "鳴潮": {"zh": "Wuthering Waves"},
                "鸣潮": {"zh": "Wuthering Waves"},
                "吟霖": {"zh": "Yinlin"},
                "くすぐり": {"zh": "搔痒"},
                "足裏": {"zh": "脚底"},
                "拘束": {"zh": "束缚"},
                "足こちょ": {"zh": "挠脚心"},
                "WutheringWaves": {"zh": "Wuthering Waves"},
                "R-18": {"zh": "R-18"},
                "成人内容": {"zh": "成人内容"}
            },
            "popular": {
                "recent": [],
                "permanent": []
            }
        }
    }
    
    # 创建爬虫实例
    spider = PixivSpider()
    
    # 设置测试用的屏蔽标签
    spider.blocked_tags = {"R-18", "成人", "成人内容", "搔痒"}
    
    print("1. 测试数据准备:")
    print(f"   图片标签: {mock_raw_data['body']['illustManga']['data'][0]['tags']}")
    print(f"   相关标签: {mock_raw_data['body']['relatedTags']}")
    print(f"   屏蔽标签: {list(spider.blocked_tags)}")
    print(f"   翻译数据: {mock_raw_data['body']['tagTranslation']}")
    print()
    
    # 测试场景1：图片标签包含屏蔽标签
    print("2. 测试场景1：图片标签包含屏蔽标签")
    illust_tags_with_blocked = ["動圖", "R-18"]
    related_tags = mock_raw_data['body']['relatedTags']
    tag_translation = mock_raw_data['body']['tagTranslation']
    
    result1 = await spider._should_block_image_with_translation(
        illust_tags_with_blocked, related_tags, tag_translation
    )
    print(f"   结果: {result1} (应该为 True)")
    print()
    
    # 测试场景2：相关标签包含屏蔽标签（原始标签）
    print("3. 测试场景2：相关标签包含屏蔽标签（原始标签）")
    illust_tags_clean = ["動圖", "鳴潮"]
    
    result2 = await spider._should_block_image_with_translation(
        illust_tags_clean, related_tags, tag_translation
    )
    print(f"   结果: {result2} (应该为 True，因为相关标签包含 'R-18')")
    print()
    
    # 测试场景3：相关标签翻译包含屏蔽标签
    print("4. 测试场景3：相关标签翻译包含屏蔽标签")
    illust_tags_clean2 = ["動圖", "鳴潮"]
    # 移除直接的屏蔽标签，只保留翻译匹配的
    related_tags_clean = ["動圖", "鳴潮", "吟霖", "くすぐり", "足裏", "拘束", "足こちょ", "WutheringWaves"]
    tag_translation_clean = {
        "動圖": {"zh": "动图"},
        "鳴潮": {"zh": "Wuthering Waves"},
        "吟霖": {"zh": "Yinlin"},
        "くすぐり": {"zh": "搔痒"},  # 这个翻译匹配屏蔽标签
        "足裏": {"zh": "脚底"},
        "拘束": {"zh": "束缚"},
        "足こちょ": {"zh": "挠脚心"},
        "WutheringWaves": {"zh": "Wuthering Waves"}
    }
    
    result3 = await spider._should_block_image_with_translation(
        illust_tags_clean2, related_tags_clean, tag_translation_clean
    )
    print(f"   结果: {result3} (应该为 True，因为 'くすぐり' 翻译为 '搔痒' 匹配屏蔽标签)")
    print()
    
    # 测试场景4：检查范围限制（前5个相关标签）
    print("5. 测试场景4：检查范围限制（前5个相关标签）")
    # 创建包含第6个标签翻译匹配屏蔽标签的情况
    related_tags_with_six = ["動圖", "鳴潮", "吟霖", "安全标签1", "安全标签2", "成人内容"]
    tag_translation_with_six = {
        "動圖": {"zh": "动图"},
        "鳴潮": {"zh": "Wuthering Waves"},
        "吟霖": {"zh": "Yinlin"},
        "安全标签1": {"zh": "安全1"},
        "安全标签2": {"zh": "安全2"},
        "成人内容": {"zh": "成人"}  # 第6个标签翻译匹配屏蔽标签
    }
    
    result4 = await spider._should_block_image_with_translation(
        ["安全标签"], related_tags_with_six, tag_translation_with_six
    )
    print(f"   结果: {result4} (应该为 False，因为第6个标签 '成人内容' 不在前5个检查范围内)")
    print()
    
    # 测试场景5：无屏蔽标签的情况
    print("6. 测试场景5：无屏蔽标签的情况")
    illust_tags_safe = ["動圖", "鳴潮"]
    related_tags_safe = ["動圖", "鳴潮", "吟霖"]
    tag_translation_safe = {
        "動圖": {"zh": "动图"},
        "鳴潮": {"zh": "Wuthering Waves"},
        "吟霖": {"zh": "Yinlin"}
    }
    
    result5 = await spider._should_block_image_with_translation(
        illust_tags_safe, related_tags_safe, tag_translation_safe
    )
    print(f"   结果: {result5} (应该为 False，没有匹配的屏蔽标签)")
    print()
    
    # 测试场景6：边界匹配测试
    print("7. 测试场景6：边界匹配测试")
    # 测试 "ai" 不会匹配 "ka-ai" 中的 "ai"
    illust_tags_boundary = ["ka-ai"]
    related_tags_boundary = []
    tag_translation_boundary = {}
    
    result6 = await spider._should_block_image_with_translation(
        illust_tags_boundary, related_tags_boundary, tag_translation_boundary
    )
    print(f"   结果: {result6} (应该为 False，'ai' 不应该匹配 'ka-ai' 中的子字符串)")
    print()
    
    # 总结
    print("=== 测试总结 ===")
    print(f"场景1 (图片标签包含屏蔽): {'✓ 通过' if result1 else '✗ 失败'}")
    print(f"场景2 (相关标签原始匹配): {'✓ 通过' if result2 else '✗ 失败'}")
    print(f"场景3 (相关标签翻译匹配): {'✓ 通过' if result3 else '✗ 失败'}")
    print(f"场景4 (范围限制测试): {'✓ 通过' if not result4 else '✗ 失败'}")
    print(f"场景5 (无屏蔽标签): {'✓ 通过' if not result5 else '✗ 失败'}")
    print(f"场景6 (边界匹配测试): {'✓ 通过' if not result6 else '✗ 失败'}")
    
    # 验证所有测试是否通过
    all_passed = all([
        result1,      # 应该为 True
        result2,      # 应该为 True
        result3,      # 应该为 True
        not result4,  # 应该为 False
        not result5,  # 应该为 False
        not result6   # 应该为 False
    ])
    
    print(f"\n总体结果: {'✓ 所有测试通过' if all_passed else '✗ 部分测试失败'}")
    
    return all_passed


async def test_extract_simplified_data_integration():
    """测试 _extract_simplified_data 方法集成"""
    
    print("\n=== 测试 _extract_simplified_data 集成 ===\n")
    
    spider = PixivSpider()
    spider.blocked_tags = {"R-18", "成人"}
    
    # 模拟包含屏蔽标签的搜索结果
    mock_raw_data_with_blocked = {
        "error": False,
        "body": {
            "illustManga": {
                "data": [
                    {
                        "id": "119563554",
                        "title": "包含R-18的作品",
                        "tags": ["動圖", "R-18"],  # 包含屏蔽标签
                        "userId": "69117363",
                        "userName": "TestUser"
                    },
                    {
                        "id": "119563555",
                        "title": "正常作品",
                        "tags": ["動圖", "風景"],  # 不包含屏蔽标签
                        "userId": "69117364",
                        "userName": "TestUser2"
                    }
                ],
                "total": 2
            },
            "relatedTags": ["動圖", "風景", "R-18"],
            "tagTranslation": {
                "動圖": {"zh": "动图"},
                "風景": {"zh": "风景"},
                "R-18": {"zh": "R-18"}
            }
        }
    }
    
    print("测试数据提取和屏蔽功能:")
    result = spider._extract_simplified_data(mock_raw_data_with_blocked, "测试关键词")
    
    print(f"   原始作品数量: 2")
    print(f"   过滤后作品数量: {len(result['illusts'])}")
    print(f"   预期结果: 1 (应该过滤掉包含 R-18 的作品)")
    print(f"   实际结果: {'✓ 正确' if len(result['illusts']) == 1 else '✗ 错误'}")
    
    # 验证过滤的作品是否正确
    if len(result['illusts']) == 1:
        filtered_illust = result['illusts'][0]
        is_correct = filtered_illust['id'] == "119563555" and filtered_illust['title'] == "正常作品"
        print(f"   过滤的作品ID正确: {'✓ 是' if is_correct else '✗ 否'}")
    
    return len(result['illusts']) == 1


async def main():
    """主测试函数"""
    print("开始相关标签翻译检查功能测试...\n")
    
    try:
        # 测试相关标签翻译检查
        translation_test_passed = await test_related_tag_translation()
        
        # 测试数据提取集成
        integration_test_passed = await test_extract_simplified_data_integration()
        
        print(f"\n=== 最终测试结果 ===")
        print(f"翻译检查测试: {'✓ 通过' if translation_test_passed else '✗ 失败'}")
        print(f"集成测试: {'✓ 通过' if integration_test_passed else '✗ 失败'}")
        
        if translation_test_passed and integration_test_passed:
            print("\n🎉 所有测试通过！相关标签翻译检查功能工作正常。")
            return True
        else:
            print("\n❌ 部分测试失败，请检查实现。")
            return False
            
    except Exception as e:
        print(f"\n💥 测试过程中出现异常: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(main())
