# 作者圈名功能使用指南

## 功能概述

作者圈名功能允许为喜欢的作者设置多个别名（圈名），方便记忆和使用。用户可以通过圈名来获取作者图片，而不需要记住复杂的作者ID。

## 主要特性

### 1. 圈名管理
- **多圈名支持**：每个作者可以设置多个圈名
- **冲突检测**：自动检测圈名冲突，防止重复
- **动态管理**：支持随时添加、删除圈名

### 2. 智能搜索
- **圈名解析**：自动识别圈名并转换为作者ID
- **回退机制**：圈名不存在时直接作为作者ID使用
- **大小写敏感**：圈名区分大小写

### 3. 数据持久化
- **自动保存**：圈名配置自动保存到文件
- **加载恢复**：程序启动时自动加载圈名配置
- **映射缓存**：维护圈名到作者ID的快速映射

## 使用方法

### 1. 添加喜欢作者（带圈名）

```python
import asyncio
from spiderPixiv import PixivSpider

async def add_author_with_aliases():
    async with PixivSpider() as spider:
        # 添加作者并设置多个圈名
        success = spider.add_favorite_author(
            user_id="12345678",
            user_name="测试作者",
            aliases=["画师A", "ArtistA", "测试画师1"]
        )
        print(f"添加结果: {success}")

asyncio.run(add_author_with_aliases())
```

### 2. 管理圈名

```python
async def manage_aliases():
    spider = PixivSpider()
    
    # 为已有作者添加圈名
    result = spider.add_author_alias("12345678", "新圈名")
    print(f"添加圈名: {result}")
    
    # 移除圈名
    result = spider.remove_author_alias("12345678", "新圈名")
    print(f"移除圈名: {result}")
    
    # 获取作者的所有圈名
    aliases = spider.get_author_aliases("12345678")
    print(f"作者圈名: {aliases}")
    
    # 搜索圈名对应的作者ID
    author_id = spider.search_author_by_alias("画师A")
    print(f"圈名对应的作者ID: {author_id}")

asyncio.run(manage_aliases())
```

### 3. 通过圈名获取图片

```python
async def get_images_by_alias():
    async with PixivSpider() as spider:
        # 通过圈名获取作者图片
        result = await spider.get_author_images(
            user_id="画师A",  # 使用圈名而不是作者ID
            mode="recent",
            count=3
        )
        
        if result:
            print(f"作者: {result['author_info']['name']}")
            print(f"作品数: {result['author_info']['total_works']}")
            print(f"获取图片数: {len(result['images'])}")
            
            for i, image in enumerate(result['images'], 1):
                print(f"图片{i}: {image['title']} (ID: {image['id']})")

asyncio.run(get_images_by_alias())
```

### 4. 查看圈名信息

```python
async def view_alias_info():
    spider = PixivSpider()
    
    # 获取所有圈名映射
    all_aliases = spider.get_all_aliases()
    print(f"所有圈名映射: {all_aliases}")
    
    # 获取喜欢作者统计信息
    authors_info = spider.get_favorite_authors_info()
    print(f"喜欢作者统计:")
    print(f"  总数: {authors_info['total_count']}")
    print(f"  总圈名数: {authors_info['total_aliases']}")
    print(f"  最近添加: {authors_info['recent_added']}")
    print(f"  从未检查: {authors_info['never_checked']}")

asyncio.run(view_alias_info())
```

## 数据结构

### 喜欢作者数据格式

```python
{
    "user_id": {
        "name": "作者名称",
        "aliases": ["圈名1", "圈名2", "圈名3"],
        "added_time": "2024-01-01T12:00:00",
        "last_check": "2024-01-01T12:00:00"
    }
}
```

### 圈名映射格式

```python
{
    "圈名1": "user_id_1",
    "圈名2": "user_id_1",
    "圈名3": "user_id_2"
}
```

## API 参考

### 圈名管理方法

#### `add_favorite_author(user_id, user_name="", aliases=None)`
添加喜欢作者并设置圈名

**参数：**
- `user_id` (str): 作者ID
- `user_name` (str): 作者名称
- `aliases` (list): 圈名列表

**返回：**
- `bool`: 添加成功返回True，失败返回False

#### `add_author_alias(user_id, alias)`
为作者添加圈名

**参数：**
- `user_id` (str): 作者ID
- `alias` (str): 圈名

**返回：**
- `bool`: 添加成功返回True，失败返回False

#### `remove_author_alias(user_id, alias)`
移除作者的圈名

**参数：**
- `user_id` (str): 作者ID
- `alias` (str): 圈名

**返回：**
- `bool`: 移除成功返回True，失败返回False

#### `search_author_by_alias(alias)`
通过圈名搜索作者ID

**参数：**
- `alias` (str): 圈名

**返回：**
- `str`: 作者ID，未找到返回None

#### `get_author_aliases(user_id)`
获取作者的所有圈名

**参数：**
- `user_id` (str): 作者ID

**返回：**
- `list`: 圈名列表

#### `get_all_aliases()`
获取所有圈名映射

**返回：**
- `dict`: 圈名到作者ID的映射

### 图片获取方法

#### `get_author_images(user_id, mode="recent", count=3)`
获取作者图片（支持圈名）

**参数：**
- `user_id` (str): 作者ID或圈名
- `mode` (str): 获取模式 ("recent"/"popular"/"random")
- `count` (int): 图片数量 (1-5)

**返回：**
- `dict`: 包含作者信息和图片列表的结果

## 使用场景

### 1. 日常使用
```python
# 用户可以通过熟悉的圈名获取图片
result = await spider.get_author_images("我最喜欢的画师", mode="recent", count=3)
```

### 2. 批量管理
```python
# 批量添加作者和圈名
authors_data = [
    {"id": "123", "name": "画师A", "aliases": ["A画师", "ArtistA"]},
    {"id": "456", "name": "画师B", "aliases": ["B画师", "ArtistB"]}
]

for author in authors_data:
    spider.add_favorite_author(
        user_id=author["id"],
        user_name=author["name"],
        aliases=author["aliases"]
    )
```

### 3. 圈名冲突处理
```python
# 检查圈名是否已被使用
existing_author = spider.search_author_by_alias("目标圈名")
if existing_author:
    print(f"圈名已被作者 {existing_author} 使用")
else:
    # 安全添加圈名
    spider.add_author_alias("新作者ID", "目标圈名")
```

## 注意事项

### 1. 圈名规则
- 圈名不能为空
- 圈名区分大小写
- 不支持重复圈名
- 支持中文、英文、数字和特殊字符

### 2. 冲突处理
- 后添加的圈名会覆盖已存在的圈名映射
- 建议在添加前先检查圈名是否已被使用
- 系统会输出冲突警告信息

### 3. 数据持久化
- 圈名配置保存在 `favorite_authors.pkl` 文件中
- 程序启动时自动加载配置
- 修改后需要手动调用 `save_favorite_authors()` 保存

### 4. 性能考虑
- 圈名映射缓存在内存中，查询速度快
- 大量圈名时建议定期清理不用的圈名
- 圈名数量没有硬性限制

## 测试

运行测试文件验证功能：

```bash
python test_author_alias.py
```

测试包括：
- 圈名管理功能
- 圈名搜索功能
- 冲突处理
- 边界情况
- 通过圈名获取图片

## 故障排除

### 常见问题

1. **圈名搜索失败**
   - 检查圈名是否正确添加
   - 确认圈名拼写和大小写
   - 使用 `get_all_aliases()` 查看所有圈名

2. **圈名冲突**
   - 使用 `search_author_by_alias()` 检查圈名是否被占用
   - 选择唯一的圈名
   - 考虑使用作者ID作为圈名后缀

3. **数据丢失**
   - 检查 `favorite_authors.pkl` 文件是否存在
   - 确认程序有文件写入权限
   - 重新添加作者和圈名

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看内部状态
spider = PixivSpider()
print(f"圈名映射: {spider.alias_to_user_id}")
print(f"喜欢作者: {spider.favorite_authors}")
```

## 更新日志

### v1.0.0
- 初始版本发布
- 支持基本的圈名管理功能
- 支持通过圈名获取作者图片
