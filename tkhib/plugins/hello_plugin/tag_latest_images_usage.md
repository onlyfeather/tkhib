# 标签最新更新图片功能使用说明

## 功能概述

`get_tag_latest_images` 方法用于获取指定标签在指定时间范围内的最新更新图片。该功能特别适合用于：

- 监控特定标签的最新作品
- 获取热门标签的实时更新
- 发现新发布的优质内容
- 跟踪特定主题的创作动态

## 方法签名

```python
async def get_tag_latest_images(
    self, 
    tag: Union[str, List[str]], 
    count: int = 5,
    hours_limit: int = 24
) -> Optional[Dict[str, Any]]:
```

## 参数说明

### tag (必需)
- **类型**: `str` 或 `List[str]`
- **说明**: 搜索标签，支持单个标签或多个标签
- **示例**: 
  - 单标签: `"风景"`
  - 多标签: `["风景", "原创"]`

### count (可选)
- **类型**: `int`
- **默认值**: `5`
- **范围**: `1-10`
- **说明**: 返回图片数量
- **限制**: 最大10张，避免请求过多

### hours_limit (可选)
- **类型**: `int`
- **默认值**: `24`
- **范围**: `1-168`
- **说明**: 时间限制（小时），只获取指定小时内的更新
- **限制**: 最大7天（168小时）

## 返回值

成功时返回包含以下结构的字典：

```python
{
    'search_info': {
        'tags': List[str],              # 搜索标签列表
        'search_keyword': str,           # 合并后的搜索关键词
        'requested_count': int,          # 请求的图片数量
        'actual_count': int,             # 实际返回的图片数量
        'hours_limit': int,              # 时间限制
        'time_threshold': str,            # 时间阈值
        'total_candidates': int,          # 总候选图片数
        'pages_searched': int,            # 搜索的页数
        'timestamp': str                  # 搜索时间戳
    },
    'images': [
        {
            'id': str,                    # 图片ID
            'title': str,                 # 图片标题
            'url': str,                   # 图片URL
            'tags': List[str],             # 图片标签
            'userId': str,                # 作者ID
            'userName': str,              # 作者名
            'pageCount': int,              # 页数
            'width': int,                 # 宽度
            'height': int,                 # 高度
            'illustType': int,             # 作品类型
            'xRestrict': int,             # 年龄限制
            'description': str,             # 描述
            'createDate': str,             # 创建时间
            'aiType': int,                # AI类型
            'profileImageUrl': str,         # 作者头像
            'hours_since_upload': float,     # 上传小时数
            'quality_score': Dict,          # 质量评分（可选）
            'source': 'tag_latest'         # 数据来源标识
        }
    ],
    'statistics': {
        'total_found': int,               # 找到的总图片数
        'time_filtered': int,             # 时间筛选后的图片数
        'quality_scored': int,            # 有质量评分的图片数
        'avg_hours_since_upload': float    # 平均上传小时数
    }
}
```

失败时返回 `None`。

## 使用示例

### 基本用法

```python
import asyncio
from tkhib.plugins.hello_plugin.spiderPixiv import PixivSpider

async def example_basic():
    async with PixivSpider() as spider:
        # 获取"风景"标签24小时内的最新5张图片
        result = await spider.get_tag_latest_images(
            tag="风景",
            count=5,
            hours_limit=24
        )
        
        if result:
            print(f"找到 {len(result['images'])} 张最新图片")
            for image in result['images']:
                print(f"- {image['title']} (上传于 {image['hours_since_upload']:.1f} 小时前)")
        else:
            print("未找到最新图片")

asyncio.run(example_basic())
```

### 多标签搜索

```python
async def example_multiple_tags():
    async with PixivSpider() as spider:
        # 搜索包含"风景"和"原创"的图片
        result = await spider.get_tag_latest_images(
            tag=["风景", "原创"],
            count=3,
            hours_limit=12  # 12小时内
        )
        
        if result:
            print(f"搜索关键词: {result['search_info']['search_keyword']}")
            print(f"搜索页数: {result['search_info']['pages_searched']}")
            
            for image in result['images']:
                quality = image.get('quality_score', {})
                score = quality.get('total_score', 'N/A')
                print(f"- {image['title']} (质量评分: {score})")

asyncio.run(example_multiple_tags())
```

### 短时间监控

```python
async def example_recent_monitor():
    async with PixivSpider() as spider:
        # 获取6小时内的最新图片
        result = await spider.get_tag_latest_images(
            tag="美少女",
            count=8,
            hours_limit=6
        )
        
        if result:
            print(f"时间阈值: {result['search_info']['time_threshold']}")
            print(f"候选图片: {result['search_info']['total_candidates']}")
            print(f"实际返回: {result['search_info']['actual_count']}")
            
            # 验证时间范围
            for image in result['images']:
                hours = image['hours_since_upload']
                if hours <= 6:
                    print(f"✅ {image['title']} ({hours:.1f}小时前)")
                else:
                    print(f"⚠️ {image['title']} ({hours:.1f}小时前) - 超出范围")
        else:
            print("6小时内没有新图片")

asyncio.run(example_recent_monitor())
```

### 质量分析

```python
async def example_quality_analysis():
    async with PixivSpider() as spider:
        result = await spider.get_tag_latest_images(
            tag="插画",
            count=5,
            hours_limit=48  # 2天内
        )
        
        if result:
            stats = result['statistics']
            print(f"统计信息:")
            print(f"- 总找到: {stats['total_found']} 张")
            print(f"- 时间筛选: {stats['time_filtered']} 张")
            print(f"- 有质量评分: {stats['quality_scored']} 张")
            print(f"- 平均上传时间: {stats['avg_hours_since_upload']:.1f} 小时")
            
            # 分析质量评分
            quality_scores = []
            for image in result['images']:
                quality = image.get('quality_score')
                if quality:
                    quality_scores.append(quality['total_score'])
                    level = quality['quality_level']
                    print(f"- {image['title']}: {quality['total_score']} ({level})")
            
            if quality_scores:
                avg_score = sum(quality_scores) / len(quality_scores)
                print(f"平均质量评分: {avg_score:.1f}")

asyncio.run(example_quality_analysis())
```

## 功能特性

### 1. 智能时间筛选
- 自动解析图片创建时间
- 精确计算上传小时数
- 支持时区处理
- 验证时间范围准确性

### 2. 多页搜索
- 自动搜索多页获取足够图片
- 最多搜索5页避免过度请求
- 智能停止机制（无新图片时停止）
- 请求间隔控制

### 3. 质量评分集成
- 自动获取图片详细信息
- 计算综合质量评分
- 包含多维度评分指标
- 提供质量等级分类

### 4. 参数验证
- 严格的参数范围检查
- 友好的错误提示
- 防止无效请求
- 边界值保护

### 5. 性能优化
- 异步请求处理
- 内置限流机制
- 缓存翻译结果
- 智能重试策略

## 使用场景

### 1. 实时监控
```python
# 监控热门标签的最新更新
result = await spider.get_tag_latest_images(
    tag="美少女",
    count=3,
    hours_limit=1  # 最近1小时
)
```

### 2. 内容发现
```python
# 发现特定主题的新作品
result = await spider.get_tag_latest_images(
    tag=["原创", "风景"],
    count=5,
    hours_limit=24  # 24小时内的新作品
)
```

### 3. 质量筛选
```python
# 获取最新高质量作品
result = await spider.get_tag_latest_images(
    tag="插画",
    count=8,
    hours_limit=48
)

# 筛选高质量图片
high_quality = [
    img for img in result['images']
    if img.get('quality_score', {}).get('total_score', 0) >= 70
]
```

### 4. 趋势分析
```python
# 分析标签活跃度
tags = ["风景", "插画", "原创", "动漫"]
for tag in tags:
    result = await spider.get_tag_latest_images(tag, count=5, hours_limit=24)
    if result:
        avg_hours = result['statistics']['avg_hours_since_upload']
        print(f"{tag}: 平均 {avg_hours:.1f} 小时前更新")
```

## 注意事项

### 1. 请求限制
- 遵循Pixiv的API限制
- 内置0.5秒请求间隔
- 避免频繁请求

### 2. 时间处理
- 使用服务器时间进行计算
- 考虑时区差异
- 时间解析容错处理

### 3. 数据完整性
- 部分图片可能缺少详细信息
- 质量评分可能获取失败
- 提供降级处理机制

### 4. 性能考虑
- 多页搜索会增加耗时
- 质量评分需要额外请求
- 建议合理设置参数

## 错误处理

常见错误及解决方法：

### 1. 参数错误
```python
# 错误：图片数量超出范围
result = await spider.get_tag_latest_images(tag="风景", count=15)  # ❌

# 正确：在允许范围内
result = await spider.get_tag_latest_images(tag="风景", count=5)   # ✅
```

### 2. 时间范围错误
```python
# 错误：时间限制超出范围
result = await spider.get_tag_latest_images(tag="风景", hours_limit=200)  # ❌

# 正确：在允许范围内
result = await spider.get_tag_latest_images(tag="风景", hours_limit=168) # ✅
```

### 3. 空标签错误
```python
# 错误：空标签
result = await spider.get_tag_latest_images(tag="")  # ❌

# 正确：提供有效标签
result = await spider.get_tag_latest_images(tag="风景")  # ✅
```

## 最佳实践

1. **合理设置时间范围**: 根据需求设置合适的时间限制，避免过短导致无结果
2. **控制图片数量**: 适中的图片数量（3-5张）平衡性能和信息量
3. **使用多标签**: 结合相关标签提高搜索精度
4. **检查质量评分**: 利用质量评分筛选优质内容
5. **处理异常情况**: 做好错误处理和降级策略
6. **监控性能**: 注意请求耗时和成功率

## 相关方法

- `search_illustrations()`: 基础搜索功能
- `search_images()`: 智能搜图功能
- `get_illust_details()`: 获取图片详情
- `calculate_quality_score()`: 计算质量评分

通过这些方法的组合使用，可以构建更复杂的图片获取和分析功能。
