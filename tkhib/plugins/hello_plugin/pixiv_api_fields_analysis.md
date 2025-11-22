# Pixiv 图片详情API字段分析

## API返回数据结构解析

基于 `https://www.pixiv.net/ajax/illust/{图片id}?lang=zh` 的返回数据

---

## 🔴 核心必要字段 (重要度: ⭐⭐⭐⭐⭐⭐)

### 基础信息
- **`id`** - 图片ID，唯一标识符
- **`title`** - 图片标题
- **`description`** - 图片描述/说明
- **`userName`** - 作者用户名
- **`userId`** - 作者用户ID

### 媒体信息
- **`urls`** - 图片URL集合
  - `original` - 原始大图URL
  - `regular` - 标准尺寸URL
  - `small` - 小图URL
  - `thumb` - 缩略图URL
  - `mini` - 迷你图URL

### 内容属性
- **`pageCount`** - 页数（多页漫画/动图）
- **`width`** - 图片宽度
- **`height`** - 图片高度
- **`illustType`** - 作品类型（0=插画，1=漫画，2=动图）
- **`createDate`** - 创建时间
- **`tags`** - 标签信息（包含翻译）

---

## 🟡 统计数据字段 (重要度: ⭐⭐⭐⭐⭐)

### 互动数据 - 质量评分核心
- **`bookmarkCount`** - 收藏数 ⭐⭐⭐⭐⭐
- **`likeCount`** - 点赞数 ⭐⭐⭐⭐
- **`commentCount`** - 评论数 ⭐⭐⭐⭐
- **`responseCount`** - 回复数 ⭐⭐⭐
- **`viewCount`** - 浏览数 ⭐⭐⭐⭐

### 用户状态
- **`likeData`** - 当前用户是否点赞
- **`bookmarkData`** - 当前用户收藏状态
- **`isBookmarkable`** - 是否可收藏

---

## 🟠 重要辅助字段 (重要度: ⭐⭐⭐)

### 内容分类
- **`xRestrict`** - 年龄限制（0=全年龄，1=R18，2=R18G）
- **`restrict`** - 访问限制
- **`sl`** - 安全级别
- **`aiType`** - AI类型（0=人工，1=AI生成，2=AI辅助）

### 作者信息
- **`userAccount`** - 作者账号名
- **`profileImageUrl`** - 作者头像URL
- **`userIllusts`** - 作者其他作品列表

### 翻译信息
- **`alt`** - SEO友好标题（包含标签翻译）
- **`titleCaptionTranslation`** - 标题和描述翻译

---

## 🔵 一般字段 (重要度: ⭐⭐)

### 元数据
- **`uploadDate`** - 上传时间
- **`updateDate`** - 更新时间
- **`reuploadDate`** - 重新上传时间
- **`isUnlisted`** - 是否非公开
- **`isMasked`** - 是否被遮罩
- **`locationMask`** - 是否隐藏位置
- **`isLoginOnly`** - 是否仅登录可见

### 功能标识
- **`isHowto`** - 是否教程类
- **`isOriginal`** - 是否原创
- **`bookStyle`** - 书籍样式
- **`commentOff`** - 是否关闭评论
- **`commissionLinkHidden`** - 是否隐藏委托链接

---

## 🟢 低优先级字段 (重要度: ⭐)

### 广告配置
- **`zoneConfig`** - 广告位配置（可忽略）
- **`contestBanners`** - 活动横幅
- **`comicPromotion`** - 漫画推广
- **`fanboxPromotion`** - Fanbox推广

### 互动功能
- **`imageResponseOutData`** - 图片回复输出数据
- **`imageResponseData`** - 图片回复数据
- **`imageResponseCount`** - 图片回复数量
- **`pollData`** - 投票数据
- **`seriesNavData`** - 系列导航数据

### 扩展数据
- **`extraData`** - 额外元数据（SEO相关）
- **`descriptionBoothId`** - Booth商品ID
- **`descriptionYoutubeId`** - YouTube视频ID

---

## 🎯 质量评分算法需要的字段

基于这个完整数据，质量评分算法现在可以正常工作：

### 核心统计字段
```python
bookmark_count = data.get('bookmarkCount', 0)    # 收藏数 - 最重要
like_count = data.get('likeCount', 0)            # 点赞数
comment_count = data.get('commentCount', 0)        # 评论数
response_count = data.get('responseCount', 0)      # 回复数
view_count = data.get('viewCount', 0)              # 浏览数
```

### 内容质量字段
```python
page_count = data.get('pageCount', 1)             # 页数
width = data.get('width', 0)                      # 宽度
height = data.get('height', 0)                     # 高度
create_date = data.get('createDate', '')            # 创建时间
```

### 安全性过滤
```python
x_restrict = data.get('xRestrict', 0)              # 年龄限制
ai_type = data.get('aiType', 0)                  # AI类型
```

---

## 📊 数据获取策略建议

### 1. 搜索结果使用精简数据
- 使用现有的 `search_illustrations()` 返回的精简结构
- 包含基础信息，不包含详细统计数据

### 2. 质量评分需要单独API调用
- 对选中的图片调用 `/ajax/illust/{id}` 获取完整数据
- 获取统计字段进行质量评分

### 3. 缓存策略
- 可以缓存图片详情数据一段时间
- 避免重复API调用

---

## 🔧 实现建议

现在可以重新集成质量评分功能：

1. **修改每日一图流程**
   - 选定图片后，调用详情API获取统计数据
   - 计算质量评分并包含在结果中

2. **添加统计字段提取**
   - 在 `_extract_simplified_data()` 中可选包含统计字段
   - 或者创建专门的详情数据提取方法

3. **优化API调用**
   - 只对最终选中的图片调用详情API
   - 减少不必要的网络请求

