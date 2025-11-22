#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试精简数据结构
"""

import asyncio
import json
from spiderPixiv import PixivSpider


async def test_simplified_data_structure():
    """测试精简数据结构"""
    print("=== 测试精简数据结构 ===")
    
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
                        "description": "测试描述",
                        "tags": [
                            "動圖",
                            "鳴潮",
                            "鸣潮",
                            "吟霖",
                            "くすぐり",
                            "足裏",
                            "拘束",
                            "足こちょ",
                            "WutheringWaves"
                        ],
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
                    {"min": 10000, "max": None}
                ]
            },
            "popular": {
                "recent": [],
                "permanent": []
            },
            "relatedTags": [
                "動圖",
                "鳴潮",
                "鸣潮",
                "吟霖",
                "くすぐり",
                "足裏",
                "拘束",
                "足こちょ",
                "WutheringWaves"
            ],
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
                "header": {"url": "https://pixon.ads-pixiv.net/show?zone_id=header"},
                "footer": {"url": "https://pixon.ads-pixiv.net/show?zone_id=footer"}
            },
            "extraData": {
                "meta": {
                    "title": "#鸣潮 tickleのイラスト・マンガ作品 - pixiv",
                    "description": "pixiv"
                }
            }
        }
    }
    
    # 创建爬虫实例
    spider = PixivSpider()
    
    # 测试数据提取
    search_keyword = "鸣潮 tickle"
    simplified_data = spider._extract_simplified_data(mock_raw_data, search_keyword)
    
    print("\n=== 精简后的数据结构 ===")
    print(json.dumps(simplified_data, ensure_ascii=False, indent=2))
    
    # 验证数据结构
    print("\n=== 数据结构验证 ===")
    
    # 检查必要字段
    required_fields = ['illusts', 'total', 'lastPage', 'relatedTags', 'tagTranslation', 'searchInfo']
    for field in required_fields:
        if field in simplified_data:
            print(f"✓ {field}: 存在")
        else:
            print(f"✗ {field}: 缺失")
    
    # 检查图片数据字段
    if simplified_data.get('illusts'):
        illust = simplified_data['illusts'][0]
        illust_required_fields = [
            'id', 'title', 'url', 'tags', 'userId', 'userName', 
            'pageCount', 'width', 'height', 'illustType', 'xRestrict'
        ]
        
        print("\n--- 图片数据字段检查 ---")
        for field in illust_required_fields:
            if field in illust:
                print(f"✓ {field}: {illust[field]}")
            else:
                print(f"✗ {field}: 缺失")
    
    # 数据大小对比
    print("\n=== 数据大小对比 ===")
    original_size = len(json.dumps(mock_raw_data, ensure_ascii=False))
    simplified_size = len(json.dumps(simplified_data, ensure_ascii=False))
    reduction = (1 - simplified_size / original_size) * 100
    
    print(f"原始数据大小: {original_size} 字符")
    print(f"精简数据大小: {simplified_size} 字符")
    print(f"数据减少: {reduction:.1f}%")
    
    return simplified_data


if __name__ == "__main__":
    asyncio.run(test_simplified_data_structure())