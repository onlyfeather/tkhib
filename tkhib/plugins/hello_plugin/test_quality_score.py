#!/usr/bin/env python3
"""
图片质量评价算法测试脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from spiderPixiv import PixivSpider


def test_quality_score_calculation():
    """测试质量评分计算"""
    print("=== 图片质量评分算法测试 ===")
    print()
    
    spider = PixivSpider()
    
    # 测试用例：不同质量的作品
    test_cases = [
        {
            'name': '高质量新作品',
            'data': {
                'bookmarkCount': 150,
                'likeCount': 89,
                'commentCount': 12,
                'responseCount': 3,
                'viewCount': 2000,
                'pageCount': 3,
                'width': 1920,
                'height': 1080,
                'createDate': '2025-11-21T10:00:00+09:00'  # 2小时前
            }
        },
        {
            'name': '中等质量老作品',
            'data': {
                'bookmarkCount': 800,
                'likeCount': 400,
                'commentCount': 25,
                'responseCount': 5,
                'viewCount': 15000,
                'pageCount': 1,
                'width': 1200,
                'height': 800,
                'createDate': '2025-10-21T10:00:00+09:00'  # 1个月前
            }
        },
        {
            'name': '低质量作品',
            'data': {
                'bookmarkCount': 15,
                'likeCount': 8,
                'commentCount': 1,
                'responseCount': 0,
                'viewCount': 200,
                'pageCount': 1,
                'width': 800,
                'height': 600,
                'createDate': '2025-11-20T10:00:00+09:00'  # 1天前
            }
        },
        {
            'name': '神级作品',
            'data': {
                'bookmarkCount': 5000,
                'likeCount': 2000,
                'commentCount': 150,
                'responseCount': 30,
                'viewCount': 50000,
                'pageCount': 5,
                'width': 2560,
                'height': 1440,
                'createDate': '2025-11-19T10:00:00+09:00'  # 2天前
            }
        },
        {
            'name': '用户提供的示例',
            'data': {
                'bookmarkCount': 82,
                'likeCount': 56,
                'commentCount': 4,
                'responseCount': 0,
                'viewCount': 601,
                'pageCount': 3,
                'width': 1668,
                'height': 2388,
                'createDate': '2025-11-21T06:12:32+09:00'  # 刚发布
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"📊 测试用例 {i}: {test_case['name']}")
        print("-" * 50)
        
        # 计算质量评分
        score_result = spider.calculate_quality_score(test_case['data'])
        
        # 显示详细结果
        print(f"🎯 总分: {score_result['total_score']} ({score_result['quality_level']})")
        print(f"   互动质量: {score_result['interaction_score']} (40%权重)")
        print(f"   内容质量: {score_result['content_score']} (25%权重)")
        print(f"   时间评分: {score_result['time_score']} (20%权重)")
        print(f"   参与度评分: {score_result['engagement_score']} (15%权重)")
        print()
        
        # 显示原始数据
        details = score_result['details']
        print("📈 原始数据:")
        print(f"   收藏数: {details['bookmark_count']}")
        print(f"   点赞数: {details['like_count']}")
        print(f"   评论数: {details['comment_count']}")
        print(f"   浏览数: {details['view_count']}")
        print(f"   发布时长: {details['hours_since_upload']:.1f}小时")
        print(f"   页数: {details['page_count']}")
        print(f"   分辨率: {details['resolution']}")
        
        # 计算关键指标
        if details['view_count'] > 0:
            bookmark_rate = (details['bookmark_count'] / details['view_count']) * 100
            like_rate = (details['like_count'] / details['view_count']) * 100
            comment_rate = (details['comment_count'] / details['view_count']) * 100
            
            print("📊 关键指标:")
            print(f"   收藏率: {bookmark_rate:.2f}%")
            print(f"   点赞率: {like_rate:.2f}%")
            print(f"   评论率: {comment_rate:.2f}%")
        
        print("\n" + "="*60 + "\n")


def test_edge_cases():
    """测试边界情况"""
    print("=== 边界情况测试 ===")
    print()
    
    spider = PixivSpider()
    
    edge_cases = [
        {
            'name': '空数据',
            'data': {}
        },
        {
            'name': '零互动数据',
            'data': {
                'bookmarkCount': 0,
                'likeCount': 0,
                'commentCount': 0,
                'responseCount': 0,
                'viewCount': 0,
                'pageCount': 1,
                'width': 100,
                'height': 100,
                'createDate': ''
            }
        },
        {
            'name': '超高收藏率',
            'data': {
                'bookmarkCount': 100,
                'likeCount': 50,
                'commentCount': 10,
                'responseCount': 2,
                'viewCount': 100,  # 100%收藏率
                'pageCount': 1,
                'width': 1920,
                'height': 1080,
                'createDate': '2025-11-21T12:00:00+09:00'
            }
        },
        {
            'name': '超高分辨率',
            'data': {
                'bookmarkCount': 50,
                'likeCount': 25,
                'commentCount': 5,
                'responseCount': 1,
                'viewCount': 1000,
                'pageCount': 1,
                'width': 7680,  # 8K分辨率
                'height': 4320,
                'createDate': '2025-11-20T12:00:00+09:00'
            }
        }
    ]
    
    for i, test_case in enumerate(edge_cases, 1):
        print(f"🔍 边界测试 {i}: {test_case['name']}")
        print("-" * 40)
        
        score_result = spider.calculate_quality_score(test_case['data'])
        print(f"总分: {score_result['total_score']} ({score_result['quality_level']})")
        
        if score_result['details']:
            details = score_result['details']
            print(f"收藏: {details['bookmark_count']}, 浏览: {details['view_count']}")
            if details['view_count'] > 0:
                rate = (details['bookmark_count'] / details['view_count']) * 100
                print(f"收藏率: {rate:.1f}%")
        
        print()


async def test_integration_with_daily_image():
    """测试与每日一图功能的集成"""
    print("=== 集成测试：每日一图 + 质量评分 ===")
    print()
    
    async with PixivSpider() as spider:
        if not spider.is_logged_in:
            print("❌ 未登录，跳过集成测试")
            return
        
        test_user_qq = "123456789"
        
        try:
            # 获取每日一图（现在包含质量评分）
            result = await spider.get_daily_image(test_user_qq)
            
            if result and 'quality_score' in result:
                print("✅ 集成测试成功！")
                print()
                
                quality = result['quality_score']
                print(f"📸 每日一图信息:")
                print(f"   图片ID: {result['image']['id']}")
                print(f"   标题: {result['image']['title']}")
                print(f"   作者: {result['image']['userName']}")
                print(f"   标签: {result['tag']}")
                print()
                
                print(f"🎯 质量评分结果:")
                print(f"   总分: {quality['total_score']} ({quality['quality_level']})")
                print(f"   互动质量: {quality['interaction_score']}")
                print(f"   内容质量: {quality['content_score']}")
                print(f"   时间评分: {quality['time_score']}")
                print(f"   参与度评分: {quality['engagement_score']}")
                print()
                
                details = quality['details']
                print(f"📊 作品统计:")
                print(f"   收藏数: {details['bookmark_count']}")
                print(f"   点赞数: {details['like_count']}")
                print(f"   评论数: {details['comment_count']}")
                print(f"   浏览数: {details['view_count']}")
                print(f"   发布时长: {details['hours_since_upload']:.1f}小时")
                
            else:
                print("❌ 集成测试失败：未获取到质量评分")
                
        except Exception as e:
            print(f"❌ 集成测试异常: {e}")


def test_algorithm_explanation():
    """算法原理说明"""
    print("=== 质量评价算法说明 ===")
    print()
    
    explanation = """
🎯 算法设计理念：

1. 多维度综合评价 (总分100分)
   ├─ 互动质量评分 (40%权重) - 收藏、评论、点赞等互动数据
   ├─ 内容质量评分 (25%权重) - 分辨率、页数、收藏率等
   ├─ 时间衰减评分 (20%权重) - 新作品时效性加分
   └─ 参与度评分 (15%权重) - 各项互动与浏览量的比例

2. 智能时间处理
   ├─ 新作品(≤72小时)：按每小时表现评分
   ├─ 老作品(>72小时)：按绝对数值评分
   └─ 时间衰减：越新的作品时间分越高

3. 内容质量考量
   ├─ 多页作品加分：每页+5分，最高+20分
   ├─ 高分辨率加分：4K以上+20分，2K-4K+15分
   └─ 收藏率加分：10%以上+10分，5-10%+7分

4. 质量等级划分
   ├─ S级(90-100分)：神作级别
   ├─ A级(80-89分)：优秀作品
   ├─ B级(70-79分)：良好作品
   ├─ C级(60-69分)：一般作品
   ├─ D级(40-59分)：较差作品
   └─ E级(0-39分)：低质作品

5. 核心优势
   ✅ 公平性：新老作品采用不同评分标准
   ✅ 全面性：综合考虑多个质量维度
   ✅ 实时性：反映作品的当前热度
   ✅ 准确性：基于真实用户互动数据
"""
    
    print(explanation)


if __name__ == "__main__":
    print("🚀 开始测试图片质量评价算法")
    print("="*60)
    
    # 1. 基础功能测试
    test_quality_score_calculation()
    
    # 2. 边界情况测试
    test_edge_cases()
    
    # 3. 算法说明
    test_algorithm_explanation()
    
    # 4. 集成测试
    asyncio.run(test_integration_with_daily_image())
    
