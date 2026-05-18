# tkHib

tkHib 是一个 NoneBot2 项目，当前包含两个主要插件：

| 插件 | 功能 |
| --- | --- |
| `dice_girl_plugin` | 骰娘、角色扮演回复、好感度、角色切换、短期记忆 |
| `pixiv_bot_plugin` | Pixiv 搜图、最新/热门图片、作者关注、偏好标签、图片/作者信息查询 |

## 本地运行

1. 安装依赖：

```bash
pdm install
```

2. 创建 `.env` 并填写至少以下配置：

```env
TKHIB_AI_API_KEY=your_api_key
TKHIB_AI_BASE_URL=https://api.example.com
TKHIB_AI_MODEL=your_model
TKHIB_DATA_DIR=data
```

3. 启动：

```bash
pdm run python bot.py
```

开发时可使用：

```bash
pdm run nb run --reload
```

## Docker 部署

1. 准备 `.env`：

```env
TKHIB_AI_API_KEY=your_api_key
TKHIB_AI_BASE_URL=https://api.example.com
TKHIB_AI_MODEL=your_model
```

2. 启动服务：

```bash
docker compose up -d --build
```

3. 数据会持久化到宿主机的 `./data` 目录，容器内路径为 `/app/data`。

| 数据 | 默认位置 |
| --- | --- |
| 骰娘 SQLite 数据库 | `data/dice_girl/dice_data.db` |
| Pixiv Cookie/偏好/作者数据 | `data/pixiv/` |

## 生产注意事项

| 项目 | 建议 |
| --- | --- |
| 启动命令 | 生产环境使用 `pdm run python bot.py`，不要使用 `--reload` |
| 数据备份 | 定期备份 `data/` 目录 |
| Cookie | Pixiv Cookie 属于敏感信息，不要提交到 Git |
| 日志 | 默认 `LOG_LEVEL=INFO`，需要排查问题时再临时调整为 `DEBUG` |
| Redis | 当前单容器部署暂不需要；多实例共享限流、缓存或会话时再引入 |

## 运行时优化

| 项目 | 当前策略 |
| --- | --- |
| AI 请求 | 复用全局 `httpx.AsyncClient`，减少连接开销 |
| Pixiv 请求 | 复用共享 `httpx.AsyncClient`、Cookie、偏好和作者状态 |
| Pixiv 限流 | 进程级共享限流锁，避免并发命令绕过间隔限制 |
| Pixiv 图片详情 | 使用有限并发和原图 URL 缓存 |
| 本地数据写入 | Pixiv pickle 写入使用进程内文件锁 |

## 可优化项

| 优先级 | 项目 | 当前状态 | 建议 |
| --- | --- | --- | --- |
| P0 | 敏感配置管理 | `.env` 仍需人工维护 | 生产环境使用服务器密钥管理或 CI/CD secret 注入，避免明文散落 |
| P1 | Pixiv 数据存储 | Cookie、标签、作者仍使用 pickle | 迁移到 SQLite 或 JSON，并保留一次性迁移脚本 |
| P1 | 骰娘数据库访问 | SQLite 调用仍为同步接口 | 高并发场景改为 `aiosqlite` 或放入线程池 |
| P1 | Pixiv 日志 | 已收敛高风险日志，但 `spiderPixiv.py` 仍有较多 `print` | 统一替换为 `logger.debug/info/warning`，并按环境控制级别 |
| P2 | 测试覆盖 | 当前主要依赖编译检查和启动验证 | 为骰子逻辑、AI JSON 解析、Pixiv URL 提取、数据迁移补单元测试 |
| P2 | Pixiv 缓存 | 当前为进程内内存缓存 | 多实例部署时接入 Redis 做共享缓存和全局限流 |
| P2 | NoneBot 项目格式 | 启动时提示 legacy project format | 后续执行官方格式升级并验证插件加载 |
| P3 | 观测与告警 | 暂无健康检查和指标 | 增加健康检查、错误计数、关键 API 延迟统计 |
