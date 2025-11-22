# plugins/hello_plugin/hello.py
import asyncio
import re
import logging
from nonebot_plugin_alconna import Command, Alconna, Args, Arparma, on_alconna
from nonebot_plugin_alconna.uniseg import Image, UniMessage
from nonebot.plugin import PluginMetadata
from nonebot import logger
from nonebot.log import LoguruHandler
from .spider import PixivSpider
import os

# 设置配置文件路径
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

# 配置logging重定向到loguru
logging.basicConfig(handlers=[LoguruHandler()])

# 使用nonebot的logger
bot_logger = logger

# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="hello_plugin",
    description="Pixiv图片搜索插件",
    usage="使用命令搜索图片"
)

# 随机图片命令（触发词改为"搜图"，支持多tag）
random_pics = Alconna(
    "搜图",
    Args["tags", str]["count", int, 1]
)

# 每日一图命令
daily_pic = Alconna("每日一图")

# Tag管理命令
tag_manage = Alconna(
    "标签管理",
    Args["action", str]["tag", str, None]
)

# 帮助命令
help_cmd = Alconna("help")

# 注册命令
random_matcher = on_alconna(random_pics, use_cmd_start=True)
daily_matcher = on_alconna(daily_pic, use_cmd_start=True)
tag_matcher = on_alconna(tag_manage, use_cmd_start=True)
help_matcher = on_alconna(help_cmd, use_cmd_start=True)


@random_matcher.handle()
async def random_pics_handle(result: Arparma):
    """处理随机图片命令"""
    tags = result.query[str]("tags")
    count = result.query[int]("count")
    
    if not tags or not count:
        await UniMessage.text("请指定有效的标签和数量，例如：搜图 美少女 5 或 搜图 美少女,风景 3").send()
        return
    
    count = min(count, 20)  # 限制最多20张
    await search_and_send_images(tags, count, "随机图片", random_mode=True)


@daily_matcher.handle()
async def daily_pic_handle(result: Arparma):
    """处理每日一图命令"""
    try:
        await UniMessage.text("正在获取每日一图，请稍候...").send()
        
        async with PixivSpider() as spider:
            daily_image = await spider.get_daily_image(page_size=10)
            
            if not daily_image:
                await UniMessage.text("获取每日一图失败，请稍后重试").send()
                return
            
            # 提取图片信息
            image_info = daily_image.get('urls')
            if not image_info:
                await UniMessage.text("图片信息获取失败").send()
                return
            
            title = image_info.get('title', '无标题')
            artist = image_info.get('artist', '未知作者')
            reconstructed_url = image_info.get('reconstructed_url')
            search_tag = daily_image.get('search_tag', '随机')
            
            # 获取所有标签
            all_tags = image_info.get('tags', set())
            if all_tags:
                tags_text = "、".join(sorted(str(tag) for tag in all_tags))
            else:
                tags_text = search_tag  # 如果没有详细标签，使用搜索标签
            
            if reconstructed_url:
                try:
                    message = UniMessage.text(f"📅 每日一图\n{title} - {artist}\n") + Image(url=reconstructed_url) + UniMessage.text(f"\n标签: {tags_text}；画师：{artist}")
                    
                    # 重试发送机制
                    max_retries = 3
                    for retry in range(max_retries):
                        try:
                            await message.send()
                            logger.info("每日一图发送成功")
                            break
                        except Exception as retry_error:
                            if retry < max_retries - 1:
                                logger.warning(f"每日一图发送失败，第{retry + 1}次重试: {retry_error}")
                                await asyncio.sleep(2)  # 重试前等待2秒
                            else:
                                raise retry_error
                except Exception as img_error:
                    logger.error(f"每日一图发送失败: {img_error}")
                    await UniMessage.text(f"📅 每日一图\n{title} - {artist}\n图片链接: {reconstructed_url}\n标签: {tags_text}；画师：{artist}").send()
            else:
                await UniMessage.text("每日一图URL获取失败").send()
                
    except Exception as e:
        await UniMessage.text(f"获取每日一图时发生错误：{str(e)}").send()


@tag_matcher.handle()
async def tag_manage_handle(result: Arparma):
    """处理Tag管理命令"""
    action = result.query[str]("action")
    tag = result.query[str]("tag", None)
    
    try:
        async with PixivSpider() as spider:
            if action == "查看":
                # 查看Tag池信息
                info = spider.get_tag_pools_info()
                preferred_tags = info['preferred_tags']
                blocked_tags = info['blocked_tags']
                
                message = f"📋 Tag池信息\n\n"
                message += f"🏷️ 喜好标签 ({info['preferred_count']}个):\n"
                if preferred_tags:
                    message += "、".join(preferred_tags)  # 显示所有标签
                else:
                    message += "无"
                
                message += f"\n\n🚫 厌恶标签 ({info['blocked_count']}个):\n"
                if blocked_tags:
                    message += "、".join(blocked_tags)  # 显示所有标签
                else:
                    message += "无"
                
                await UniMessage.text(message).send()
                
            elif action in ["添加喜好", "加喜好", "喜欢"]:
                if not tag:
                    await UniMessage.text("请指定要添加的喜好标签，例如：标签管理 添加喜好 美少女").send()
                    return
                
                if spider.add_preferred_tag(tag):
                    spider.save_tag_pools()
                    await UniMessage.text(f"✅ 已添加喜好标签: {tag}").send()
                else:
                    await UniMessage.text(f"❌ 添加喜好标签失败: {tag}").send()
                    
            elif action in ["移除喜好", "删喜好", "不喜欢"]:
                if not tag:
                    await UniMessage.text("请指定要移除的喜好标签，例如：标签管理 移除喜好 美少女").send()
                    return
                
                if spider.remove_preferred_tag(tag):
                    spider.save_tag_pools()
                    await UniMessage.text(f"✅ 已移除喜好标签: {tag}").send()
                else:
                    await UniMessage.text(f"❌ 移除喜好标签失败: {tag}").send()
                    
            elif action in ["添加厌恶", "加厌恶", "讨厌"]:
                if not tag:
                    await UniMessage.text("请指定要添加的厌恶标签，例如：标签管理 添加厌恶 R-18").send()
                    return
                
                if spider.add_blocked_tag(tag):
                    spider.save_tag_pools()
                    await UniMessage.text(f"✅ 已添加厌恶标签: {tag}").send()
                else:
                    await UniMessage.text(f"❌ 添加厌恶标签失败: {tag}").send()
                    
            elif action in ["移除厌恶", "删厌恶", "不讨厌"]:
                if not tag:
                    await UniMessage.text("请指定要移除的厌恶标签，例如：标签管理 移除厌恶 R-18").send()
                    return
                
                if spider.remove_blocked_tag(tag):
                    spider.save_tag_pools()
                    await UniMessage.text(f"✅ 已移除厌恶标签: {tag}").send()
                else:
                    await UniMessage.text(f"❌ 移除厌恶标签失败: {tag}").send()
                    
            else:
                help_text = """
🏷️ Tag管理帮助:

📋 标签管理 查看 - 查看当前Tag池
➕ 标签管理 添加喜好 [标签] - 添加喜好标签
➖ 标签管理 移除喜好 [标签] - 移除喜好标签
🚫 标签管理 添加厌恶 [标签] - 添加厌恶标签
✅ 标签管理 移除厌恶 [标签] - 移除厌恶标签

示例:
• 标签管理 查看
• 标签管理 添加喜好 美少女
• 标签管理 添加厌恶 R-18
                """
                await UniMessage.text(help_text.strip()).send()
                
    except Exception as e:
        await UniMessage.text(f"Tag管理时发生错误：{str(e)}").send()


@help_matcher.handle()
async def help_handle(result: Arparma):
    """处理帮助命令"""
    help_text = """
🎨 Pixiv图片搜索插件帮助

📸 图片搜索:
• 搜图 [标签] [数量] - 随机获取指定标签的图片
  示例: 搜图 美少女 5
• 搜图 [标签1,标签2] [数量] - 多tag搜索图片
  示例: 搜图 美少女,风景 3
• 搜图 [标签1 标签2] [数量] - 空格分隔多tag搜索
  示例: 搜图 美少女 风景 2

📅 每日推荐:
• 每日一图 - 获取每日推荐图片

🏷️ 标签管理:
• 标签管理 查看 - 查看当前Tag池
• 标签管理 添加喜好 [标签] - 添加喜好标签
• 标签管理 移除喜好 [标签] - 移除喜好标签
• 标签管理 添加厌恶 [标签] - 添加厌恶标签
• 标签管理 移除厌恶 [标签] - 移除厌恶标签

💡 使用提示:
• 搜图功能会自动过滤厌恶标签，支持组图
• 支持智能降级重试，适合小众标签搜索
• 喜好标签会影响每日一图的推荐
• 图片数量限制: 搜图最多20张
• 组图会在一条消息中发送所有页面

🔧 高级功能:
• 自动标签验证确保图片相关性
• 智能错误处理和重试机制
• 支持多种标签管理操作
    """
    await UniMessage.text(help_text.strip()).send()


async def search_and_send_images(tags: str, count: int, command_name: str, random_mode: bool = False):
    """搜索并发送图片的通用函数（支持多tag）"""
    try:
        # 解析tags参数，支持多tag搜索
        if ',' in tags or '，' in tags or ' ' in tags:
            # 多tag搜索：按逗号或空格分割
            tag_list = []
            for separator in [',', '，', ' ']:
                if separator in tags:
                    tag_list = [tag.strip() for tag in tags.split(separator) if tag.strip()]
                    break
            search_tags = tag_list
            tags_display = "、".join(search_tags)
        else:
            # 单tag搜索
            search_tags = tags.strip()
            tags_display = tags.strip()
        
        # 发送开始搜索的消息
        await UniMessage.text(f"正在搜索「{tags_display}」的{count}张图片，请稍候...").send()
        
        # 使用spider搜索图片
        async with PixivSpider() as spider:
            if random_mode:
                # 使用随机图片功能（允许组图）
                images = await spider.get_random_images_by_tag(search_tags, count, use_filter=True, reject_manga=False)
            else:
                # 使用普通搜索功能
                # 如果是多tag，转换为字符串格式传递给search_with_tag_management
                search_tag_param = search_tags if isinstance(search_tags, str) else ' '.join(search_tags)
                search_result = await spider.search_with_tag_management(search_tag_param, use_filter=True, page_size=count)
                images = []
                if search_result:
                    for img_info in search_result[:count]:
                        images.append({
                            'image_data': img_info,
                            'urls': img_info,
                            'search_tag': search_tags
                        })
        
        if not images:
            await UniMessage.text(f"未找到标签「{tags_display}」的相关图片，请尝试其他标签").send()
            return
        
        # 如果实际获取的图片数量少于请求数量，给出提示但继续发送所有找到的图片
        if len(images) < count:
            logger.info(f"实际获取到{len(images)}张图片，少于请求的{count}张，将发送所有找到的图片")
            await UniMessage.text(f"实际获取到{len(images)}张图片，少于请求的{count}张，将发送所有找到的图片").send()
        
        # 发送图片，添加间隔以避免WebSocket连接问题
        for i, img_info in enumerate(images, 1):
            # 添加发送间隔，避免频繁发送导致连接问题
            if i > 1:
                await asyncio.sleep(1)  # 每张图片间隔1秒
            # 根据spider返回的数据结构提取信息
            title = "无标题"
            artist = "未知作者"
            is_manga = False
            pages = []
            
            if isinstance(img_info, dict):
                if 'urls' in img_info:
                    # 随机图片模式的数据结构
                    urls = img_info['urls']
                    title = urls.get('title', '无标题')
                    artist = urls.get('artist', '未知作者')
                    is_manga = urls.get('is_manga', False)
                    pages = urls.get('pages', [])
                    logger.debug(f"随机图片模式 - 标题: {title}, 作者: {artist}, 组图: {is_manga}")
                else:
                    # 普通搜索模式的数据结构（直接是图片信息字典）
                    title = img_info.get('title', '无标题')
                    artist = img_info.get('artist', '未知作者')
                    is_manga = img_info.get('is_manga', False)
                    pages = img_info.get('pages', [])
                    logger.debug(f"普通搜索模式 - 标题: {title}, 作者: {artist}, 组图: {is_manga}")
            else:
                # 直接是图片信息对象
                title = getattr(img_info, 'title', '无标题')
                artist = getattr(img_info, 'artist', '未知作者')
                is_manga = getattr(img_info, 'is_manga', False)
                pages = getattr(img_info, 'pages', [])
                logger.debug(f"对象模式 - 标题: {title}, 作者: {artist}, 组图: {is_manga}")
            
            if is_manga and pages:
                # 处理组图：一条消息发送所有页面
                logger.info(f"准备发送组图 {i}: {title} (共{len(pages)}页)")
                
                # 获取所有标签
                all_tags = set()
                if isinstance(img_info, dict):
                    if 'urls' in img_info and isinstance(img_info['urls'], dict):
                        tags = img_info['urls'].get('tags', set())
                        if isinstance(tags, (set, list)):
                            all_tags.update(str(tag) for tag in tags)
                    elif isinstance(img_info, dict):
                        tags = img_info.get('tags', set())
                        if isinstance(tags, (set, list)):
                            all_tags.update(str(tag) for tag in tags)
                else:
                    tags = getattr(img_info, 'tags', set())
                    if isinstance(tags, (set, list)):
                        all_tags.update(str(tag) for tag in tags)
                
                # 格式化标签显示
                tags_text = "、".join(sorted(str(tag) for tag in all_tags)) if all_tags else "无标签"
                
                try:
                    # 构建消息：标题 + 所有图片
                    message = UniMessage.text(f"{i}. {title} - {artist} (组图，共{len(pages)}页)\n")
                    
                    # 添加所有页面的图片
                    for page_info in pages:
                        page_url = page_info.get('reconstructed_url')
                        if page_url:
                            message = message + Image(url=page_url)
                            logger.debug(f"添加组图第{page_info['page']}页: {page_url}")
                    
                    # 添加所有标签和画师信息
                    message = message + UniMessage.text(f"\n标签: {tags_text}；画师：{artist}")
                    
                    # 重试发送机制
                    max_retries = 3
                    for retry in range(max_retries):
                        try:
                            await message.send()
                            logger.info(f"组图 {i} 发送成功，共{len(pages)}张图片")
                            break
                        except Exception as retry_error:
                            if retry < max_retries - 1:
                                logger.warning(f"组图 {i} 发送失败，第{retry + 1}次重试: {retry_error}")
                                await asyncio.sleep(2)  # 重试前等待2秒
                            else:
                                raise retry_error
                    
                except Exception as img_error:
                    logger.error(f"发送组图 {i} 失败: {img_error}")
                    logger.error(f"错误类型: {type(img_error).__name__}")
                    logger.error(f"错误详情: {str(img_error)}")
                    import traceback
                    logger.error(f"完整错误堆栈:\n{traceback.format_exc()}")
                    
                    # 如果组图发送失败，降级为文字模式 + 所有链接
                    logger.info(f"降级为文字模式发送组图 {i}")
                    text_parts = [f"{i}. {title} - {artist} (组图，共{len(pages)}页)\n"]
                    for page_info in pages:
                        page_url = page_info.get('reconstructed_url') or page_info.get('original_url')
                        if page_url:
                            text_parts.append(f"第{page_info['page']}页: {page_url}")
                    text_parts.append(f"\n标签: {tags_text}；画师：{artist}")
                    await UniMessage.text("\n".join(text_parts)).send()
                    
            elif not is_manga:
                # 处理单图
                reconstructed_url = None
                if isinstance(img_info, dict):
                    if 'urls' in img_info:
                        reconstructed_url = img_info['urls'].get('reconstructed_url')
                    else:
                        reconstructed_url = img_info.get('reconstructed_url')
                else:
                    reconstructed_url = getattr(img_info, 'reconstructed_url', None)
                
                # 获取所有标签
                all_tags = set()
                if isinstance(img_info, dict):
                    if 'urls' in img_info and isinstance(img_info['urls'], dict):
                        tags = img_info['urls'].get('tags', set())
                        if isinstance(tags, (set, list)):
                            all_tags.update(str(tag) for tag in tags)
                    elif isinstance(img_info, dict):
                        tags = img_info.get('tags', set())
                        if isinstance(tags, (set, list)):
                            all_tags.update(str(tag) for tag in tags)
                else:
                    tags = getattr(img_info, 'tags', set())
                    if isinstance(tags, (set, list)):
                        all_tags.update(str(tag) for tag in tags)
                
                # 格式化标签显示
                tags_text = "、".join(sorted(str(tag) for tag in all_tags)) if all_tags else "无标签"
                
                if reconstructed_url:
                    logger.info(f"准备发送单图 {i}: {title}")
                    logger.debug(f"图片URL: {reconstructed_url}")
                    
                    try:
                        # 使用alconna发送图片，添加重试机制
                        logger.debug("开始构建UniMessage...")
                        message = UniMessage.text(f"{i}. {title} - {artist}\n") + Image(url=reconstructed_url) + UniMessage.text(f"\n标签: {tags_text}；画师：{artist}")
                        logger.debug("UniMessage创建成功")
                        
                        # 重试发送机制
                        max_retries = 3
                        for retry in range(max_retries):
                            try:
                                await message.send()
                                logger.info(f"单图 {i} 发送成功")
                                break
                            except Exception as retry_error:
                                if retry < max_retries - 1:
                                    logger.warning(f"单图 {i} 发送失败，第{retry + 1}次重试: {retry_error}")
                                    await asyncio.sleep(2)  # 重试前等待2秒
                                else:
                                    raise retry_error
                    except Exception as img_error:
                        logger.error(f"发送单图 {i} 失败: {img_error}")
                        logger.error(f"错误类型: {type(img_error).__name__}")
                        logger.error(f"错误详情: {str(img_error)}")
                        import traceback
                        logger.error(f"完整错误堆栈:\n{traceback.format_exc()}")
                        
                        # 如果图片发送失败，只发送文字信息和链接
                        logger.info(f"降级为文字模式发送单图 {i}")
                        await UniMessage.text(f"{i}. {title} - {artist}\n图片链接: {reconstructed_url}\n标签: {tags_text}；画师：{artist}").send()
                else:
                    logger.warning(f"单图 {i} URL获取失败: {title}")
                    await UniMessage.text(f"{i}. {title} - {artist} (图片链接获取失败)").send()
        
        # 发送总结消息
        await UniMessage.text(f"已发送{len(images)}个作品").send()
        
    except Exception as e:
        await UniMessage.text(f"搜索图片时发生错误：{str(e)}").send()
        logger.error(f"搜索图片时发生错误: {e}")
        import traceback
        logger.error(f"完整错误堆栈:\n{traceback.format_exc()}")
