# 搜图机器人核心功能使用指南

## 📖 功能概述

搜图机器人提供了三种不同的搜图模式，支持单标签或多标签搜索，可以返回1-5张高质量图片。

## 🚀 快速开始

### 基本用法

```python
import asyncio
from spiderPixiv import PixivSpider

async def main():
    async with PixivSpider() as spider:
        # 搜索风景主题的随机图片
        result = await spider.search_images(
            tags="风景",
            mode="random",
            count=2
        )
        
        if result:
            print(f"找到 {len(result['images'])} 张图片")
            for image in result['images']:
                print(f"- {image['title']} by {image['userName']}")

asyncio.run(main())
```

## 🔧 详细参数说明

### search_images() 方法参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `tags` | str 或 List[str] | 必填 | 搜索标签，支持单标签或多标签 |
| `mode` | str | "random" | 搜图模式：random/recent/popular |
| `count` | int | 1 | 返回图片数量，1-5张 |
| `min_quality_score` | float | 60.0 | 最低质量评分（仅random模式） |
| `max_attempts` | int | 10 | 最大尝试次数（仅random模式） |

## 📊 三种搜图模式

### 1. 随机图模式 (random)

**特点**：
- 从所有搜索结果中随机选择图片
- 进行质量评分检查
- 确保图片质量符合要求

**适用场景**：
- 需要高质量图片
- 不介意图片发布时间
- 希望发现隐藏的优质作品

```python
# 搜索高质量风景图片
result = await spider.search_images(
    tags="风景",
    mode="random",
    count=3,
    min_quality_score=70.0  # 要求70分以上
)
```

### 2. 近日美图模式 (recent)

**特点**：
- 从 popular.recent 中选择
- 快速响应，无需质量评分
- 获取当前热门作品

**适用场景**：
- 需要最新热门图片
- 追求速度
- 想了解当前流行趋势

```python
# 获取最新的美少女热门图片
result = await spider.search_images(
    tags="美少女",
    mode="recent",
    count=5
)
```

### 3. 美图模式 (popular)

**特点**：
- 从 popular.permanent 中选择
- 经典热门作品
- 质量有保障

**适用场景**：
- 需要经典热门图片
- 追求稳定质量
- 用于展示或推荐

```python
# 获取动漫经典热门图片
result = await spider.search_images(
    tags="动漫",
    mode="popular",
    count=2
)
```

## 🏷️ 标签使用技巧

### 单标签搜索
```python
# 简单单标签
result = await spider.search_images(tags="风景")
```

### 多标签搜索
```python
# 多标签组合搜索
result = await spider.search_images(
    tags=["风景", "唯美", "治愈"],
    mode="random",
    count=2
)

# 等效于搜索 "风景 唯美 治愈"
```

### 标签选择建议

| 类型 | 推荐标签 | 说明 |
|------|----------|------|
| 风景类 | 风景、夜景、星空、自然 | 自然风光主题 |
| 人物类 | 美少女、萌、可爱、二次元 | 角色插画 |
| 艺术类 | 插画、原创、唯美、治愈 | 艺术创作 |
| 风格类 | 动漫、清新、温暖 | 风格特征 |

## 📈 返回结果结构

```python
{
    'search_info': {
        'tags': ['风景'],                    # 搜索标签
        'search_keyword': '风景',            # 搜索关键词
        'mode': 'random',                   # 使用的模式
        'requested_count': 2,               # 请求的数量
        'actual_count': 2,                   # 实际返回的数量
        'min_quality_score': 60.0,          # 最低质量要求
        'timestamp': '2025-11-22 00:26:45'  # 搜索时间
    },
    'images': [                            # 图片列表
        {
            'id': '137444973',              # 图片ID
            'title': '富士山下',            # 图片标题
            'url': 'https://...',           # 图片URL
            'tags': ['風景', '空', '雲'],   # 图片标签
            'userId': '12345678',           # 作者ID
            'userName': 'Elop',             # 作者名
            'pageCount': 1,                 # 页数
            'width': 1920,                  # 宽度
            'height': 1080,                 # 高度
            'illustType': 0,                # 作品类型
            'xRestrict': 0,                # 限制等级
            'description': '',               # 描述
            'createDate': '2025-11-20...',  # 创建时间
            'aiType': 0,                   # AI类型
            'profileImageUrl': 'https://...', # 头像URL
            'quality_score': {               # 质量评分（random模式）
                'total_score': 69.4,
                'quality_level': 'C级 - 一般',
                'interaction_score': 52.7,
                'content_score': 70.0,
                'time_score': 50.0,
                'engagement_score': 100.0
            },
            'source': 'random_selection'     # 图片来源
        }
    ],
    'statistics': {                         # 统计信息
        'total_search_results': 303638,     # 总搜索结果数
        'popular_recent_count': 7,           # 近日热门数量
        'popular_permanent_count': 6,        # 永久热门数量
        'regular_illust_count': 60          # 普通作品数量
    }
}
```

## 🎯 质量评分系统

### 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 互动质量 | 40% | 收藏、评论、点赞等互动数据 |
| 内容质量 | 25% | 分辨率、页数、收藏率等 |
| 时间衰减 | 20% | 发布时间的新旧程度 |
| 参与度 | 15% | 综合参与度指标 |

### 质量等级

| 分数范围 | 等级 | 说明 |
|----------|------|------|
| 90-100 | S级 - 神作 | 极其优秀的作品 |
| 80-89 | A级 - 优秀 | 高质量作品 |
| 70-79 | B级 - 良好 | 良好作品 |
| 60-69 | C级 - 一般 | 一般作品 |
| 40-59 | D级 - 较差 | 质量较差 |
| 0-39 | E级 - 低质 | 低质量作品 |

### 🔄 智能降级策略

**问题背景**：对于小众tag，如果严格按照质量评分要求，可能找不到符合条件的图片，但用户仍然希望得到一些结果。

**解决方案**：实现了三层降级策略

#### 第一阶段：高质量筛选
- 严格按照 `min_quality_score` 要求筛选图片
- 只有达到质量要求的图片才会被选中
- 来源标记：`random_selection`

#### 第二阶段：智能降级
- 如果高质量图片不足，从已检查的候选中选择最佳图片
- 按质量评分排序，优先选择评分较高的图片
- 即使未达到最低要求，也选择相对最好的
- 来源标记：`fallback_selection`

#### 第三阶段：最终保障
- 如果前两阶段仍然不足，直接从剩余候选中随机选择
- 确保用户总能得到一些结果
- 来源标记：`final_fallback`

#### 降级策略示例

```python
# 小众tag + 高质量要求 - 会触发降级策略
result = await spider.search_images(
    tags=['小众', '特殊', '组合'],
    mode='random',
    count=3,
    min_quality_score=90.0  # 很高的要求
)

# 检查降级情况
for img in result['images']:
    source = img.get('source')
    if source == 'random_selection':
        print(f"高质量图片: {img['id']}")
    elif source == 'fallback_selection':
        print(f"降级选择: {img['id']}")
    elif source == 'final_fallback':
        print(f"最终选择: {img['id']}")
```

#### 降级策略优势

1. **保证有结果**：即使tag很小众，也能返回一些图片
2. **质量优先**：优先选择质量相对较好的图片
3. **透明度**：通过source字段明确标识图片来源
4. **渐进降级**：从严格到宽松，逐步降低要求
5. **用户友好**：避免"找不到图片"的糟糕体验

## ⚡ 性能优化建议

### 1. 选择合适的模式

```python
# 快速获取热门图片 - 使用recent模式
result = await spider.search_images(
    tags="美少女",
    mode="recent",      # 最快
    count=5
)

# 需要高质量 - 使用random模式
result = await spider.search_images(
    tags="风景",
    mode="random",      # 较慢，但质量高
    count=2,
    min_quality_score=75.0
)

# 稳定经典 - 使用popular模式
result = await spider.search_images(
    tags="动漫",
    mode="popular",     # 中等速度
    count=3
)
```

### 2. 合理设置质量要求

```python
# 快速搜索 - 降低质量要求
result = await spider.search_images(
    tags="风景",
    mode="random",
    count=3,
    min_quality_score=50.0  # 较低要求
)

# 精品搜索 - 提高质量要求
result = await spider.search_images(
    tags="插画",
    mode="random",
    count=1,
    min_quality_score=85.0  # 较高要求
)
```

### 3. 控制返回数量

```python
# 单张图片 - 最快
result = await spider.search_images(
    tags="风景",
    count=1
)

# 多张图片 - 需要更多时间
result = await spider.search_images(
    tags="风景",
    count=5  # 最大数量
)
```

## 🚨 错误处理

### 常见错误及解决方案

```python
async def safe_search():
    async with PixivSpider() as spider:
        try:
            result = await spider.search_images(
                tags="风景",
                mode="random",
                count=2
            )
            
            if result:
                print(f"成功找到 {len(result['images'])} 张图片")
                return result
            else:
                print("未找到符合条件的图片")
                return None
                
        except Exception as e:
            print(f"搜索失败: {e}")
            return None
```

### 参数验证

```python
# 检查参数有效性
def validate_search_params(tags, mode, count):
    if not tags or (isinstance(tags, str) and not tags.strip()):
        raise ValueError("标签不能为空")
    
    if mode not in ["random", "recent", "popular"]:
        raise ValueError("模式必须是 random、recent 或 popular")
    
    if not 1 <= count <= 5:
        raise ValueError("数量必须在1-5之间")

# 使用验证
validate_search_params("风景", "random", 2)
result = await spider.search_images("风景", "random", 2)
```

## 🎪 实际应用示例

### 1. 每日图片推荐

```python
async def daily_recommendation():
    """每日图片推荐"""
    async with PixivSpider() as spider:
        # 随机选择一个主题
        themes = ["风景", "美少女", "动漫", "插画", "治愈"]
        theme = random.choice(themes)
        
        # 获取高质量图片
        result = await spider.search_images(
            tags=theme,
            mode="random",
            count=3,
            min_quality_score=70.0
        )
        
        return result
```

### 2. 主题图片收集

```python
async def collect_theme_images(theme, max_images=20):
    """收集特定主题的图片"""
    async with PixivSpider() as spider:
        collected_images = []
        
        # 分批获取
        for _ in range((max_images + 4) // 5):  # 每次最多5张
            result = await spider.search_images(
                tags=theme,
                mode="recent",
                count=5
            )
            
            if result:
                collected_images.extend(result['images'])
            
            # 避免请求过快
            await asyncio.sleep(1)
        
        return collected_images[:max_images]
```

### 3. 质量筛选器

```python
async def quality_filter(tags, min_score=80):
    """高质量图片筛选器"""
    async with PixivSpider() as spider:
        result = await spider.search_images(
            tags=tags,
            mode="random",
            count=5,
            min_quality_score=min_score
        )
        
        if result:
            # 按质量评分排序
            sorted_images = sorted(
                result['images'],
                key=lambda x: x['quality_score']['total_score'],
                reverse=True
            )
            result['images'] = sorted_images
        
        return result
```

## 📝 最佳实践

1. **选择合适的模式**：根据需求选择速度或质量
2. **合理设置质量要求**：避免过高要求导致无结果
3. **控制请求频率**：避免触发API限制
4. **处理异常情况**：做好错误处理和重试机制
5. **缓存结果**：对于相同搜索可以缓存结果

## 🔗 相关功能

- `get_random_image()` - 智能随机图片推荐
- `search_illustrations()` - 基础图片搜索
- `calculate_quality_score()` - 质量评分计算
- `get_illust_details()` - 获取图片详情

---
