# 相关标签屏蔽功能使用说明

## 功能概述

新增的相关标签屏蔽功能增强了原有的标签过滤系统，现在可以：

1. **检查图片标签的翻译匹配** - 支持多语言标签翻译后的屏蔽检查
2. **检查相关标签匹配** - 检查搜索结果中的相关标签是否包含屏蔽内容
3. **提供详细的调试信息** - 便于调试和监控屏蔽效果

## 数据结构分析

基于提供的Pixiv API响应数据，结构如下：

```json
{
  "error": false,
  "body": {
    "illustManga": {
      "data": [
        {
          "id": "137751257",
          "title": "ナミ　高画質Ver",
          "tags": ["R-18", "ナミ", "ワンピース", "くすぐり"],
          "xRestrict": 1,
          // ... 其他字段
        }
      ],
      "total": 112842,
      "lastPage": 1000
    },
    "popular": {
      "recent": [...],  // 近期热门作品
      "permanent": [...]  // 永久热门作品
    },
    "relatedTags": [
      "くすぐる", "tickling", "挠脚心", "足こちょ", 
      "くすぐり", "拘束", "足裏", "裸足", "触手"
    ],
    "tagTranslation": {
      "くすぐり": {"zh": "搔痒"},
      "拘束": {"zh": "束缚"},
      "足裏": {"zh": "脚底"}
    }
  }
}
```

## 屏蔽逻辑

### 1. 图片标签检查
- **直接匹配**：检查图片的 `tags` 数组是否直接包含屏蔽标签
- **翻译匹配**：获取每个标签的翻译，检查翻译结果是否匹配屏蔽标签
- **模糊匹配**：支持部分字符串匹配（改进后使用词汇边界匹配）

### 2. 相关标签检查
- 检查 `relatedTags` 数组是否包含屏蔽标签
- 相关标签不进行翻译检查，只检查原始标签

### 3. 词汇边界匹配改进
```python
# 避免像 "ka-ai" 匹配 "ai" 这样的误判
pattern = r'(?<![a-zA-Z0-9\-_])' + re.escape(blocked_tag) + r'(?![a-zA-Z0-9\-_])'
```

## 使用示例

### 基本配置
```python
# 设置屏蔽标签
spider.blocked_tags = {"R-18", "成人", "血腥", "暴力", "强暴"}

# 加载标签池
spider.load_tag_pools()
```

### 检查单个图片
```python
# 检查图片是否应该被屏蔽
illust_tags = ["くすぐり", "ナミ", "R-18"]
related_tags = ["tickle", "拘束", "足裏"]

should_block = await spider._should_block_image_with_translation(
    illust_tags, related_tags
)
print(f"是否屏蔽: {should_block}")
```

### 在搜索中使用
```python
# 搜索结果会自动应用标签屏蔽
result = await spider.search_illustrations("tickle")
print(f"找到 {len(result['illusts'])} 个结果（已过滤屏蔽内容）")
```

## 屏蔽效果示例

基于提供的数据，以下情况会被屏蔽：

### 直接匹配案例
```python
# 图片标签包含 "R-18"
illust_tags = ["R-18", "ナミ", "くすぐり"]  # ✅ 屏蔽

# 图片标签包含 "レイプ"（强暴的日文）
illust_tags = ["レイプ", "くすぐり"]  # ✅ 屏蔽
```

### 翻译匹配案例
```python
# "adult" 翻译为 "成人"
illust_tags = ["adult", "cute"]  # ✅ 屏蔽（翻译匹配）

# "gore" 翻译为 "血腥"  
illust_tags = ["gore", "anime"]  # ✅ 屏蔽（翻译匹配）
```

### 相关标签匹配案例
```python
# 图片标签安全，但相关标签包含屏蔽内容
illust_tags = ["くすぐり", "ナミ"]  # 安全
related_tags = ["R-18", "tickle"]  # ✅ 屏蔽（相关标签匹配）
```

## 性能优化

### 翻译缓存
```python
# 翻译结果会被缓存，避免重复API调用
spider.translation_cache = {
    "くすぐり": {"zh": "搔痒", "en": "tickle"},
    "R-18": {"zh": "成人", "en": "R-18"}
}
```

### 限流保护
```python
# 自动限流，避免API调用过频
spider.min_request_interval = 0.5  # 0.5秒最小间隔
```

## 调试信息

启用详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看屏蔽决策过程
await spider._should_block_image_with_translation(tags, related_tags)
```

输出示例：
```
检查标签屏蔽: 图片标签 3 个，相关标签 5 个，总计 8 个
图片标签精确匹配屏蔽: 'R-18'
翻译匹配屏蔽: 'adult' (zh: '成人') 精确匹配屏蔽tag '成人'
相关标签匹配屏蔽: 'R-18' 精确匹配屏蔽tag 'R-18'
```

## 配置建议

### 推荐屏蔽标签
```python
# 基础屏蔽
blocked_tags = {
    "R-18", "R18", "成人", "血腥", "暴力", "恐怖",
    "猎奇", "恶心", "重口", "黑暗", "抑郁"
}

# 扩展屏蔽（根据需要）
blocked_tags.update({
    "レイプ", "强暴", "拘束", "拷問", "陵辱",
    "乳首責め", "足フェチ", "触手"
})
```

### 翻译缓存配置
```python
spider.cache_max_size = 1000  # 最大缓存数量
```

## 注意事项

1. **性能考虑**：翻译检查会增加API调用，建议合理设置缓存
2. **误判处理**：使用词汇边界匹配减少误判
3. **语言支持**：目前支持中文、英文、日文等主要语言
4. **相关标签**：只检查原始标签，不进行翻译
5. **异步调用**：所有翻译检查都是异步的

## 测试验证

运行测试脚本验证功能：
```bash
cd tkhib/plugins/hello_plugin
python test_related_tag_blocking.py
```

测试覆盖：
- ✅ 图片标签直接匹配
- ✅ 图片标签翻译匹配  
- ✅ 相关标签匹配
- ✅ 词汇边界匹配
- ✅ 翻译缓存功能
- ✅ 性能优化验证

## 更新日志

### v2.0.0 (当前版本)
- ✅ 新增相关标签检查
- ✅ 改进翻译匹配逻辑
- ✅ 添加词汇边界匹配
- ✅ 优化翻译缓存
- ✅ 增强调试信息

### v1.0.0 (原版本)
- ✅ 基础标签屏蔽功能
