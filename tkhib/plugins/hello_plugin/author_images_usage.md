# 作者图片获取功能使用指南

## 功能概述

新增的作者图片获取功能允许用户根据作者ID获取特定作者的作品，支持多种获取模式和喜欢作者管理。

## 核心功能

### 1. 获取作者图片

```python
async def get_author_images(user_id: str, mode: str = "recent", count: int = 3) -> Optional[Dict[str, Any]]
```

**参数说明：**
- `user_id`: 作者ID（必需）
- `mode`: 获取模式
  - `"recent"`: 最新作品，按时间排序选择（默认）
  - `"popular"`: 热门作品，按收藏数排序选择
  - `"random"`: 随机选择，带质量评分检查
- `count`: 返回图片数量，1-5张，默认3张

**返回格式：**
```python
{
    'author_info': {
        'user_id': '作者ID',
        'name': '作者名称',
        'is_favorite': bool,  # 是否为喜欢作者
        'total_works': int,  # 作品总数
        'profile_image_url': '头像URL',
        'comment': '作者简介',
        'followable': bool  # 是否可关注
    },
    'search_info': {
        'mode': '获取模式',
        'requested_count': int,  # 请求数量
        'actual_count': int,     # 实际数量
        'timestamp': '操作时间'
    },
    'images': [  # 图片列表
        {
            'id': '图片ID',
            'title': '标题',
            'url': '图片URL',
            'tags': ['标签列表'],
            'userId': '作者ID',
            'userName': '作者名',
            'pageCount': int,  # 页数
            'width': int,      # 宽度
            'height': int,     # 高度
            'illustType': int,  # 作品类型
            'xRestrict': int,  # 限制级别
            'description': '描述',
            'createDate': '创建时间',
            'aiType': int,     # AI类型
            'profileImageUrl': '头像URL',
            'quality_score': {...},  # 质量评分（仅random模式）
            'source': '图片来源'  # author_recent, author_popular, author_random等
        }
    ]
}
```

### 2. 喜欢作者管理

#### 添加喜欢作者
```python
def add_favorite_author(user_id: str, user_name: str = "") -> bool
```

#### 移除喜欢作者
```python
def remove_favorite_author(user_id: str) -> bool
```

#### 获取喜欢作者列表
```python
def get_favorite_authors() -> Dict[str, Dict[str, Any]]
```

#### 获取喜欢作者统计信息
```python
def get_favorite_authors_info() -> Dict[str, Any]
```

#### 更新作者最后检查时间
```python
def update_author_last_check(user_id: str) -> bool
```

## 使用示例

### 基本用法

```python
import asyncio
from spiderPixiv import PixivSpider

async def main():
    async with PixivSpider() as spider:
        # 获取作者最新作品
        result = await spider.get_author_images(
            user_id="101598284",
            mode="recent",
            count=3
        )
        
        if result:
            print(f"找到 {len(result['images'])} 张图片")
            for image in result['images']:
                print(f"- {image['title']} ({image['id']})")

asyncio.run(main())
```

### 喜欢作者管理

```python
async def main():
    async with PixivSpider() as spider:
        # 添加喜欢作者
        spider.add_favorite_author("101598284", "f")
        
        # 获取喜欢作者的作品
        result = await spider.get_author_images(
            user_id="101598284",
            mode="recent",
            count=2
        )
        
        if result:
            author_info = result['author_info']
            print(f"作者 {author_info['name']} 是喜欢作者: {author_info['is_favorite']}")
        
        # 获取所有喜欢作者
        favorites = spider.get_favorite_authors()
        print(f"共有 {len(favorites)} 个喜欢作者")
        
        # 移除喜欢作者
        spider.remove_favorite_author("101598284")

asyncio.run(main())
```

### 不同模式示例

```python
async def demo_modes():
    async with PixivSpider() as spider:
        author_id = "101598284"
        
        # 最新作品模式
        recent_result = await spider.get_author_images(
            user_id=author_id,
            mode="recent",
            count=2
        )
        print("最新作品:", len(recent_result['images']) if recent_result else 0)
        
        # 热门作品模式
        popular_result = await spider.get_author_images(
            user_id=author_id,
            mode="popular",
            count=2
        )
        print("热门作品:", len(popular_result['images']) if popular_result else 0)
        
        # 随机作品模式（带质量评分）
        random_result = await spider.get_author_images(
            user_id=author_id,
            mode="random",
            count=2
        )
        print("随机作品:", len(random_result['images']) if random_result else 0)

asyncio.run(demo_modes())
```

## 数据持久化

### 存储文件
- `favorite_authors.pkl`: 喜欢作者数据
- `preferred_tags.pkl`: 喜好标签池
- `blocked_tags.pkl`: 厌恶标签池
- `pixiv_cookie.pkl`: Cookie和用户ID

### 数据结构

#### 喜欢作者数据
```python
{
    "作者ID": {
        'name': '作者名称',
        'added_time': '添加时间 (ISO格式)',
        'last_check': '最后检查时间 (ISO格式)'
    }
}
```

## 错误处理

### 常见错误情况
1. **无效作者ID**: 返回 `None`
2. **无效模式**: 返回 `None`
3. **数量超限**: 返回 `None`
4. **网络错误**: 返回 `None`
5. **作者无作品**: 返回 `None`

### 错误示例
```python
async def error_handling_demo():
    async with PixivSpider() as spider:
        # 空作者ID
        result = await spider.get_author_images("", mode="recent", count=1)
        # result == None
        
        # 无效模式
        result = await spider.get_author_images("101598284", mode="invalid", count=1)
        # result == None
        
        # 数量超限
        result = await spider.get_author_images("101598284", mode="recent", count=10)
        # result == None
```

## 质量评分

### 随机模式质量评分
- 仅在 `mode="random"` 时启用
- 默认最低质量评分：60分
- 支持降级策略确保总能返回结果

### 质量等级
- **S级 (90-100分)**: 神作
- **A级 (80-89分)**: 优秀
- **B级 (70-79分)**: 良好
- **C级 (60-69分)**: 一般
- **D级 (40-59分)**: 较差
- **E级 (0-39分)**: 低质

## 性能优化

### 限流机制
- 最小请求间隔：1秒
- 自动等待避免API限制
- 可通过 `rate_limit_enabled` 控制

### 缓存策略
- 喜欢作者信息本地缓存
- 标签池配置持久化
- Cookie信息自动加载

## 测试

运行测试文件验证功能：
```bash
python test_author_images.py
```

测试内容包括：
- 基本功能测试
- 不同模式测试
- 喜欢作者管理测试
- 边界情况测试
- 错误处理测试

## 注意事项

1. **Cookie要求**: 需要有效的Pixiv Cookie
2. **权限检查**: 某些作者可能需要登录才能查看
3. **作品限制**: R-18作品需要适当的Cookie设置
4. **API限制**: 遵循Pixiv API的调用限制
5. **数据更新**: 作者信息可能需要定期更新

## 扩展功能

### 未来可能的扩展
- 批量获取多个作者作品
- 作者作品分类筛选
- 订阅作者更新通知
- 作者作品统计分析
- 导出喜欢作者列表

### 集成建议
- 与现有搜图功能结合
- 添加到机器人命令中
- 支持作者ID自动识别
