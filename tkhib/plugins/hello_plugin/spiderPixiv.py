import asyncio
import json
import httpx
import pickle
import os
import random
import time
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List, Set, Union


class PixivSpider:
    """Pixiv爬虫类，支持Cookie登录"""
    
    def __init__(self, cookie_file: str = "pixiv_cookie.pkl"):
        self.session = None
        self.base_url = "https://www.pixiv.net"
        self.cookie_file = cookie_file
        self.full_cookie = None
        self.user_id = None
        self.is_logged_in = False
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Content-Type': 'application/json',
            'Origin': 'https://www.pixiv.net',
            'Referer': 'https://www.pixiv.net/'
        }
        
        # 限流配置
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 最小请求间隔（秒）- 降低到0.5秒提高性能
        self.rate_limit_enabled = True  # 是否启用限流
        
        # 翻译缓存
        self.translation_cache: Dict[str, Dict[str, str]] = {}  # 缓存翻译结果
        self.cache_max_size = 1000  # 最大缓存数量
        
        # Tag池配置
        self.preferred_tags_file = "preferred_tags.pkl"
        self.blocked_tags_file = "blocked_tags.pkl"
        self.preferred_tags: Set[str] = set()
        self.blocked_tags: Set[str] = set()
        
        # 喜欢作者配置
        self.favorite_authors_file = "favorite_authors.pkl"
        self.favorite_authors: Dict[str, Dict[str, Any]] = {}  # {user_id: {name, aliases, added_time, last_check}}
        
        # 圈名到作者ID的映射缓存
        self.alias_to_user_id: Dict[str, str] = {}  # {alias: user_id}
        
        # 默认喜好tag池
        self.default_preferred_tags = {
            "风景", "插画", "原创", "美少女", "动漫", "二次元", 
            "萌", "可爱", "唯美", "治愈", "清新", "温暖"
        }
        
        # 默认厌恶tag池
        self.default_blocked_tags = {
            "R-18", "R18", "成人", "血腥", "暴力", "恐怖", 
            "猎奇", "恶心", "重口", "黑暗", "抑郁"
        }
        
    def save_cookie(self, cookie_string: str, user_id: Optional[str] = None, keep_existing_id: bool = True) -> bool:
        """
        保存Cookie到专用文件
        
        Args:
            cookie_string: 从浏览器复制的完整Cookie字符串
            user_id: 用户ID，如果为None则尝试从现有数据中保留
            keep_existing_id: 是否保留现有的用户ID，默认为True
            
        Returns:
            保存成功返回True，失败返回False
        """
        try:
            if not cookie_string or not cookie_string.strip():
                print("Cookie字符串为空")
                return False
            
            # 检查是否为第一次保存（文件不存在）
            is_first_save = not os.path.exists(self.cookie_file)
            if is_first_save:
                print("=== 第一次保存Cookie ===")
                print("检测到这是第一次保存Cookie，将同时保存用户ID和Cookie")
                
                # 第一次保存时，如果没有提供user_id，需要提醒用户
                if not user_id:
                    print("警告: 第一次保存Cookie但没有提供用户ID")
                    print("建议在调用save_cookie时提供user_id参数")
                    print("例如: spider.save_cookie(cookie_string, user_id='12345678')")
                    print("继续保存，但用户ID将为空...")
            
            # 尝试加载现有的cookie数据以保留用户ID
            existing_user_id = None
            if not is_first_save and keep_existing_id:
                try:
                    with open(self.cookie_file, 'rb') as f:
                        existing_data = pickle.load(f)
                        existing_user_id = existing_data.get('user_id')
                        if existing_user_id:
                            print(f"检测到现有用户ID: {existing_user_id}")
                except Exception as e:
                    print(f"加载现有cookie数据失败: {e}")
            
            # 确定要保存的用户ID
            final_user_id = user_id
            if final_user_id is None and not is_first_save and keep_existing_id:
                final_user_id = existing_user_id
            
            # 保存完整的cookie字符串和用户ID
            cookie_data = {
                'full_cookie': cookie_string,
                'user_id': final_user_id,
                'saved_time': __import__('datetime').datetime.now().isoformat(),
                'is_first_save': is_first_save  # 标记是否为第一次保存
            }
            
            with open(self.cookie_file, 'wb') as f:
                pickle.dump(cookie_data, f)
            
            self.full_cookie = cookie_string  # 保存完整cookie
            self.user_id = final_user_id  # 保存用户ID
            self.is_logged_in = True
            
            # 根据保存类型输出不同的信息
            if is_first_save:
                print(f"✓ 首次Cookie保存成功")
                if final_user_id:
                    print(f"✓ 用户ID已保存: {final_user_id}")
                else:
                    print("⚠ 用户ID未保存（建议后续更新）")
            else:
                print(f"✓ Cookie更新成功")
                if final_user_id:
                    print(f"✓ 用户ID: {final_user_id}")
                else:
                    print("⚠ 用户ID: 未设置")
            
            return True
            
        except Exception as e:
            print(f"保存Cookie失败: {e}")
            return False
    
    def load_cookie(self) -> bool:
        """
        从专用文件加载Cookie
        
        Returns:
            加载成功返回True，失败返回False
        """
        try:
            if os.path.exists(self.cookie_file):
                with open(self.cookie_file, 'rb') as f:
                    cookie_data = pickle.load(f)
                    full_cookie = cookie_data.get('full_cookie')
                    user_id = cookie_data.get('user_id')
                    
                if full_cookie:
                    self.full_cookie = full_cookie  # 加载完整cookie
                    self.user_id = user_id  # 加载用户ID
                    self.is_logged_in = True
                    print(f"已加载Cookie")
                    if user_id:
                        print(f"用户ID: {user_id}")
                    else:
                        print("用户ID: 未设置")
                    return True
                else:
                    print("Cookie文件中没有找到完整Cookie")
                    return False
            else:
                print("Cookie文件不存在")
                return False
                
        except Exception as e:
            print(f"加载Cookie失败: {e}")
            return False
    
    def set_cookie(self, cookie_string: str) -> bool:
        """
        直接设置Cookie进行登录
        
        Args:
            cookie_string: 从浏览器复制的Cookie字符串
            
        Returns:
            设置成功返回True，失败返回False
        """
        try:
            if not cookie_string or not cookie_string.strip():
                print("Cookie字符串为空")
                return False
            
            # 直接保存完整的Cookie字符串，不再强制要求PHPSESSID
            # 保存Cookie到专用文件
            self.save_cookie(cookie_string)
            
            print(f"成功设置Cookie登录")
            return True
            
        except Exception as e:
            print(f"设置Cookie失败: {e}")
            return False
    
    def load_tag_pools(self) -> bool:
        """加载tag池配置"""
        try:
            # 加载喜好tag池
            if os.path.exists(self.preferred_tags_file):
                with open(self.preferred_tags_file, 'rb') as f:
                    self.preferred_tags = pickle.load(f)
                print(f"已加载喜好tag池: {len(self.preferred_tags)}个标签")
            else:
                self.preferred_tags = self.default_preferred_tags.copy()
                print("使用默认喜好tag池")
            
            # 加载厌恶tag池
            if os.path.exists(self.blocked_tags_file):
                with open(self.blocked_tags_file, 'rb') as f:
                    self.blocked_tags = pickle.load(f)
                print(f"已加载厌恶tag池: {len(self.blocked_tags)}个标签")
            else:
                self.blocked_tags = self.default_blocked_tags.copy()
                print("使用默认厌恶tag池")
            
            return True
        except Exception as e:
            print(f"加载tag池失败: {e}")
            # 使用默认tag池
            self.preferred_tags = self.default_preferred_tags.copy()
            self.blocked_tags = self.default_blocked_tags.copy()
            return False
    
    def save_tag_pools(self) -> bool:
        """保存tag池配置"""
        try:
            # 保存喜好tag池
            with open(self.preferred_tags_file, 'wb') as f:
                pickle.dump(self.preferred_tags, f)
            
            # 保存厌恶tag池
            with open(self.blocked_tags_file, 'wb') as f:
                pickle.dump(self.blocked_tags, f)
            
            print("Tag池保存成功")
            return True
        except Exception as e:
            print(f"保存tag池失败: {e}")
            return False
    
    def add_preferred_tag(self, tag: str) -> bool:
        """添加喜好tag"""
        try:
            self.preferred_tags.add(tag.strip())
            print(f"已添加喜好tag: {tag}")
            return True
        except Exception as e:
            print(f"添加喜好tag失败: {e}")
            return False
    
    def remove_preferred_tag(self, tag: str) -> bool:
        """移除喜好tag"""
        try:
            self.preferred_tags.discard(tag.strip())
            print(f"已移除喜好tag: {tag}")
            return True
        except Exception as e:
            print(f"移除喜好tag失败: {e}")
            return False
    
    def add_blocked_tag(self, tag: str) -> bool:
        """添加厌恶tag"""
        try:
            self.blocked_tags.add(tag.strip())
            print(f"已添加厌恶tag: {tag}")
            return True
        except Exception as e:
            print(f"添加厌恶tag失败: {e}")
            return False
    
    def remove_blocked_tag(self, tag: str) -> bool:
        """移除厌恶tag"""
        try:
            self.blocked_tags.discard(tag.strip())
            print(f"已移除厌恶tag: {tag}")
            return True
        except Exception as e:
            print(f"移除厌恶tag失败: {e}")
            return False
    
    def get_random_preferred_tag(self) -> Optional[str]:
        """从喜好tag池中随机选择一个tag"""
        try:
            if not self.preferred_tags:
                print("喜好tag池为空")
                return None
            return random.choice(list(self.preferred_tags))
        except Exception as e:
            print(f"随机选择喜好tag失败: {e}")
            return None
    
    def get_tag_pools_info(self) -> Dict[str, Any]:
        """获取tag池信息"""
        return {
            'preferred_tags': list(self.preferred_tags),
            'blocked_tags': list(self.blocked_tags),
            'preferred_count': len(self.preferred_tags),
            'blocked_count': len(self.blocked_tags)
        }

    async def get_tag_translation(self, tag: str) -> Dict[str, str]:
        """
        获取tag的翻译信息（带缓存优化）
        
        Args:
            tag: 标签名称
            
        Returns:
            翻译字典，失败返回空字典
        """
        try:
            if not tag or not tag.strip():
                return {}
            
            clean_tag = tag.strip()
            
            # 检查缓存
            if clean_tag in self.translation_cache:
                print(f"使用翻译缓存: {clean_tag}")
                return self.translation_cache[clean_tag]
            
            # 限流等待
            await self._rate_limit_wait()
            
            url = f"{self.base_url}/ajax/search/tags/{clean_tag}?lang=zh"
            
            # 设置认证头（如果有的话）
            headers = self.headers.copy()
            if self.full_cookie:
                headers['Cookie'] = self.full_cookie
            
            if not self.session:
                raise RuntimeError("Session not initialized")
            
            print(f"请求翻译API: {clean_tag}")
            response = await self.session.get(url, headers=headers)
            response.raise_for_status()
            
            tag_data = response.json()
            
            if tag_data.get('error'):
                return {}
            
            body = tag_data.get('body', {})
            tag_translation = body.get('tagTranslation', {})
            
            # 处理不同的返回格式
            translations = {}
            if isinstance(tag_translation, dict):
                # 标准格式：{tag: {translations}}
                translations = tag_translation.get(clean_tag, {})
            elif isinstance(tag_translation, list):
                # 列表格式：[{tag: translations}, ...]
                for item in tag_translation:
                    if isinstance(item, dict) and clean_tag in item:
                        translations = item[clean_tag]
                        break
            
            # 确保translations是字典格式
            if not isinstance(translations, dict):
                translations = {}
            
            # 构建翻译结果
            translation_result = {
                'en': translations.get('en', ''),
                'zh': translations.get('zh', ''),
                'ko': translations.get('ko', ''),
                'zh_tw': translations.get('zh_tw', ''),
                'romaji': translations.get('romaji', '')
            }
            
            # 缓存结果（限制缓存大小）
            if len(self.translation_cache) >= self.cache_max_size:
                # 清理最旧的缓存项（简单的FIFO策略）
                oldest_key = next(iter(self.translation_cache))
                del self.translation_cache[oldest_key]
                print(f"清理翻译缓存: {oldest_key}")
            
            self.translation_cache[clean_tag] = translation_result
            print(f"缓存翻译结果: {clean_tag}")
            
            return translation_result
            
        except Exception as e:
            print(f"获取tag翻译异常: {e}")
            return {}

    async def _should_block_image_with_translation(self, illust_tags: List[str], related_tags: Optional[List[str]] = None, tag_translation: Optional[Dict[str, Dict[str, str]]] = None) -> bool:
        """
        检查图片是否应该被屏蔽（基于tag和翻译，包括相关标签）
        
        Args:
            illust_tags: 图片的tag列表
            related_tags: 搜索结果中的相关标签列表（可选）
            tag_translation: API返回的tagTranslation数据（relatedTags的翻译）
            
        Returns:
            True表示应该屏蔽，False表示不屏蔽
        """
        try:
            if not illust_tags or not self.blocked_tags:
                return False
            
            # 将图片tag转换为小写集合，便于比较
            illust_tags_lower = {tag.lower().strip() for tag in illust_tags if tag and tag.strip()}
            blocked_tags_lower = {tag.lower().strip() for tag in self.blocked_tags if tag and tag.strip()}
            
            # 合并所有需要检查的标签（图片标签 + 相关标签）
            all_tags_to_check = list(illust_tags_lower)
            if related_tags:
                related_tags_lower = {tag.lower().strip() for tag in related_tags if tag and tag.strip()}
                all_tags_to_check.extend(related_tags_lower)
                print(f"检查标签屏蔽: 图片标签 {len(illust_tags_lower)} 个，相关标签 {len(related_tags_lower)} 个，总计 {len(all_tags_to_check)} 个")
            
            # 检查直接匹配
            for blocked_tag in blocked_tags_lower:
                # 精确匹配
                if blocked_tag in illust_tags_lower:
                    print(f"图片标签精确匹配屏蔽: '{blocked_tag}'")
                    return True
                
                # 模糊匹配（检查是否包含屏蔽tag作为子字符串）
                for illust_tag in illust_tags_lower:
                    if blocked_tag in illust_tag or illust_tag in blocked_tag:
                        print(f"图片标签模糊匹配屏蔽: '{blocked_tag}' in '{illust_tag}'")
                        return True
            
            # 检查翻译匹配（只检查图片标签，不检查相关标签的翻译）
            # 使用API返回的tagTranslation数据，避免重复请求
            if tag_translation:
                for illust_tag in illust_tags:
                    if illust_tag in tag_translation:
                        translations = tag_translation[illust_tag]
                        if isinstance(translations, dict):
                            # 检查翻译是否匹配屏蔽tag
                            for lang, translated in translations.items():
                                if translated and translated.strip():
                                    translated_lower = translated.lower().strip()
                                    
                                    # 检查翻译是否匹配屏蔽tag
                                    for blocked_tag in blocked_tags_lower:
                                        # 改进匹配逻辑：避免子字符串误判
                                        # 1. 精确匹配
                                        if translated_lower == blocked_tag:
                                            print(f"翻译匹配屏蔽: '{illust_tag}' ({lang}: '{translated}') 精确匹配屏蔽tag '{blocked_tag}'")
                                            return True
                                        
                                        # 2. 词汇边界匹配（避免像 "ka-ai" 匹配 "ai" 这样的误判）
                                        # 只有当屏蔽tag是完整词汇时才匹配
                                        if len(blocked_tag) >= 2:  # 至少2个字符才考虑模糊匹配
                                            # 检查是否作为独立词汇出现（前后有空格或标点符号，但不包括连字符和下划线）
                                            import re
                                            # 使用更精确的边界匹配：只允许空格和标点符号作为边界
                                            pattern = r'(?<![a-zA-Z0-9\-_])' + re.escape(blocked_tag) + r'(?![a-zA-Z0-9\-_])'
                                            if re.search(pattern, translated_lower, re.IGNORECASE):
                                                print(f"翻译匹配屏蔽: '{illust_tag}' ({lang}: '{translated}') 词汇匹配屏蔽tag '{blocked_tag}'")
                                                return True
            
            # 检查相关标签匹配（包括翻译检查，限制检查范围）
            if related_tags:
                # 限制检查范围：只取前5个相关标签
                limited_related_tags = related_tags[:5]
                print(f"限制相关标签检查范围: 从 {len(related_tags)} 个减少到 {len(limited_related_tags)} 个")
                
                for related_tag in limited_related_tags:
                    if not related_tag or not related_tag.strip():
                        continue
                    
                    related_tag_lower = related_tag.lower().strip()
                    
                    # 检查相关标签是否匹配屏蔽tag
                    for blocked_tag in blocked_tags_lower:
                        # 精确匹配
                        if related_tag_lower == blocked_tag:
                            print(f"相关标签匹配屏蔽: '{related_tag}' 精确匹配屏蔽tag '{blocked_tag}'")
                            return True
                        
                        # 模糊匹配（检查是否包含屏蔽tag作为子字符串）
                        if blocked_tag in related_tag_lower or related_tag_lower in blocked_tag:
                            print(f"相关标签模糊匹配屏蔽: '{blocked_tag}' in '{related_tag}'")
                            return True
                    
                    # 检查相关标签的翻译（使用API返回的tagTranslation数据）
                    if tag_translation and related_tag in tag_translation:
                        translations = tag_translation[related_tag]
                        if isinstance(translations, dict):
                            for lang, translated_text in translations.items():
                                if translated_text and translated_text.strip():
                                    translated_lower = translated_text.lower().strip()
                                    
                                    # 检查翻译是否匹配屏蔽tag
                                    for blocked_tag in blocked_tags_lower:
                                        # 精确匹配翻译结果
                                        if translated_lower == blocked_tag:
                                            print(f"相关标签翻译匹配屏蔽: '{related_tag}' ({lang}: '{translated_text}') 精确匹配屏蔽tag '{blocked_tag}'")
                                            return True
                                        
                                        # 词汇边界匹配翻译结果
                                        if len(blocked_tag) >= 2:
                                            import re
                                            pattern = r'(?<![a-zA-Z0-9\-_])' + re.escape(blocked_tag) + r'(?![a-zA-Z0-9\-_])'
                                            if re.search(pattern, translated_lower, re.IGNORECASE):
                                                print(f"相关标签翻译匹配屏蔽: '{related_tag}' ({lang}: '{translated_text}') 词汇匹配屏蔽tag '{blocked_tag}'")
                                                return True
            
            return False
            
        except Exception as e:
            print(f"检查图片屏蔽异常: {e}")
            return False  # 出错时不屏蔽，避免误删

    def _should_block_image(self, illust_tags: List[str]) -> bool:
        """
        检查图片是否应该被屏蔽（基于tag，不包含翻译检查）
        
        Args:
            illust_tags: 图片的tag列表
            
        Returns:
            True表示应该屏蔽，False表示不屏蔽
        """
        try:
            if not illust_tags or not self.blocked_tags:
                return False
            
            # 将图片tag转换为小写集合，便于比较
            illust_tags_lower = {tag.lower().strip() for tag in illust_tags if tag and tag.strip()}
            blocked_tags_lower = {tag.lower().strip() for tag in self.blocked_tags if tag and tag.strip()}
            
            # 检查是否有任何屏蔽tag匹配
            for blocked_tag in blocked_tags_lower:
                # 精确匹配
                if blocked_tag in illust_tags_lower:
                    return True
                
                # 模糊匹配（检查是否包含屏蔽tag作为子字符串）
                for illust_tag in illust_tags_lower:
                    if blocked_tag in illust_tag or illust_tag in blocked_tag:
                        return True
            
            return False
            
        except Exception as e:
            print(f"检查图片屏蔽异常: {e}")
            return False  # 出错时不屏蔽，避免误删
    
    def load_favorite_authors(self) -> bool:
        """加载喜欢作者配置"""
        try:
            if os.path.exists(self.favorite_authors_file):
                with open(self.favorite_authors_file, 'rb') as f:
                    self.favorite_authors = pickle.load(f)
                print(f"已加载喜欢作者: {len(self.favorite_authors)}个作者")
            else:
                self.favorite_authors = {}
                print("喜欢作者列表为空")
            return True
        except Exception as e:
            print(f"加载喜欢作者失败: {e}")
            self.favorite_authors = {}
            return False
    
    def save_favorite_authors(self) -> bool:
        """保存喜欢作者配置"""
        try:
            with open(self.favorite_authors_file, 'wb') as f:
                pickle.dump(self.favorite_authors, f)
            print("喜欢作者保存成功")
            return True
        except Exception as e:
            print(f"保存喜欢作者失败: {e}")
            return False
    
    def add_favorite_author(self, user_id: str, user_name: str = "", aliases: Optional[List[str]] = None) -> bool:
        """添加喜欢作者"""
        try:
            user_id = str(user_id).strip()
            if not user_id:
                print("作者ID不能为空")
                return False
            
            if user_id in self.favorite_authors:
                print(f"作者 {user_id} 已在喜欢列表中")
                return False
            
            # 处理圈名列表
            alias_list = []
            if aliases:
                alias_list = [alias.strip() for alias in aliases if alias and alias.strip()]
            
            # 添加作者名作为默认圈名
            if user_name and user_name.strip():
                clean_name = user_name.strip()
                if clean_name not in alias_list:
                    alias_list.append(clean_name)
            
            self.favorite_authors[user_id] = {
                'name': user_name.strip(),
                'aliases': alias_list,
                'added_time': datetime.now().isoformat(),
                'last_check': None
            }
            
            # 更新圈名映射缓存
            self._update_alias_mapping()
            
            print(f"已添加喜欢作者: {user_name} ({user_id})")
            if alias_list:
                print(f"圈名: {', '.join(alias_list)}")
            return True
        except Exception as e:
            print(f"添加喜欢作者失败: {e}")
            return False
    
    def remove_favorite_author(self, user_id: str) -> bool:
        """移除喜欢作者"""
        try:
            user_id = str(user_id).strip()
            if user_id in self.favorite_authors:
                author_info = self.favorite_authors[user_id]
                del self.favorite_authors[user_id]
                print(f"已移除喜欢作者: {author_info.get('name', '未知')} ({user_id})")
                return True
            else:
                print(f"作者 {user_id} 不在喜欢列表中")
                return False
        except Exception as e:
            print(f"移除喜欢作者失败: {e}")
            return False
    
    def get_favorite_authors(self) -> Dict[str, Dict[str, Any]]:
        """获取所有喜欢作者"""
        return self.favorite_authors.copy()
    
    def get_favorite_author_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取特定喜欢作者信息"""
        return self.favorite_authors.get(str(user_id))
    
    def update_author_last_check(self, user_id: str) -> bool:
        """更新作者最后检查时间"""
        try:
            user_id = str(user_id)
            if user_id in self.favorite_authors:
                self.favorite_authors[user_id]['last_check'] = datetime.now().isoformat()
                return True
            return False
        except Exception as e:
            print(f"更新作者检查时间失败: {e}")
            return False
    
    def _update_alias_mapping(self) -> None:
        """更新圈名到作者ID的映射缓存"""
        try:
            self.alias_to_user_id.clear()
            
            for user_id, author_info in self.favorite_authors.items():
                aliases = author_info.get('aliases', [])
                for alias in aliases:
                    if alias and alias.strip():
                        clean_alias = alias.strip()
                        # 检查圈名冲突
                        if clean_alias in self.alias_to_user_id:
                            existing_user_id = self.alias_to_user_id[clean_alias]
                            if existing_user_id != user_id:
                                print(f"警告: 圈名 '{clean_alias}' 冲突 - 已存在作者 {existing_user_id}，将被作者 {user_id} 覆盖")
                        self.alias_to_user_id[clean_alias] = user_id
            
            print(f"圈名映射已更新: {len(self.alias_to_user_id)} 个映射")
        except Exception as e:
            print(f"更新圈名映射失败: {e}")

    def add_author_alias(self, user_id: str, alias: str) -> bool:
        """为作者添加圈名"""
        try:
            user_id = str(user_id).strip()
            alias = alias.strip()
            
            if not user_id:
                print("作者ID不能为空")
                return False
            
            if not alias:
                print("圈名不能为空")
                return False
            
            if user_id not in self.favorite_authors:
                print(f"作者 {user_id} 不在喜欢列表中")
                return False
            
            # 检查圈名冲突
            if alias in self.alias_to_user_id and self.alias_to_user_id[alias] != user_id:
                existing_user_id = self.alias_to_user_id[alias]
                print(f"圈名 '{alias}' 已被作者 {existing_user_id} 使用")
                return False
            
            # 添加圈名
            author_info = self.favorite_authors[user_id]
            aliases = author_info.get('aliases', [])
            
            if alias not in aliases:
                aliases.append(alias)
                author_info['aliases'] = aliases
                self.alias_to_user_id[alias] = user_id
                print(f"已为作者 {user_id} 添加圈名: {alias}")
                return True
            else:
                print(f"圈名 '{alias}' 已存在")
                return False
                
        except Exception as e:
            print(f"添加圈名失败: {e}")
            return False

    def remove_author_alias(self, user_id: str, alias: str) -> bool:
        """移除作者的圈名"""
        try:
            user_id = str(user_id).strip()
            alias = alias.strip()
            
            if not user_id:
                print("作者ID不能为空")
                return False
            
            if not alias:
                print("圈名不能为空")
                return False
            
            if user_id not in self.favorite_authors:
                print(f"作者 {user_id} 不在喜欢列表中")
                return False
            
            # 移除圈名
            author_info = self.favorite_authors[user_id]
            aliases = author_info.get('aliases', [])
            
            if alias in aliases:
                aliases.remove(alias)
                author_info['aliases'] = aliases
                
                # 从映射中移除
                if alias in self.alias_to_user_id and self.alias_to_user_id[alias] == user_id:
                    del self.alias_to_user_id[alias]
                
                print(f"已为作者 {user_id} 移除圈名: {alias}")
                return True
            else:
                print(f"圈名 '{alias}' 不存在")
                return False
                
        except Exception as e:
            print(f"移除圈名失败: {e}")
            return False

    def search_author_by_alias(self, alias: str) -> Optional[str]:
        """通过圈名搜索作者ID"""
        try:
            alias = alias.strip()
            if not alias:
                return None
            
            return self.alias_to_user_id.get(alias)
        except Exception as e:
            print(f"通过圈名搜索作者失败: {e}")
            return None

    def get_author_aliases(self, user_id: str) -> List[str]:
        """获取作者的所有圈名"""
        try:
            user_id = str(user_id).strip()
            if not user_id:
                return []
            
            author_info = self.favorite_authors.get(user_id, {})
            return author_info.get('aliases', []).copy()
        except Exception as e:
            print(f"获取作者圈名失败: {e}")
            return []

    def get_all_aliases(self) -> Dict[str, str]:
        """获取所有圈名映射"""
        return self.alias_to_user_id.copy()

    def get_favorite_authors_info(self) -> Dict[str, Any]:
        """获取喜欢作者统计信息"""
        total_count = len(self.favorite_authors)
        recent_added = 0
        never_checked = 0
        total_aliases = 0
        
        current_time = datetime.now()
        for author_info in self.favorite_authors.values():
            # 检查最近7天内添加的作者
            try:
                added_time = datetime.fromisoformat(author_info.get('added_time', ''))
                if (current_time - added_time).days <= 7:
                    recent_added += 1
            except:
                pass
            
            # 检查从未检查过的作者
            if not author_info.get('last_check'):
                never_checked += 1
            
            # 统计圈名数量
            aliases = author_info.get('aliases', [])
            total_aliases += len(aliases)
        
        return {
            'total_count': total_count,
            'recent_added': recent_added,
            'never_checked': never_checked,
            'total_aliases': total_aliases,
            'authors': self.favorite_authors,
            'alias_mapping': self.alias_to_user_id.copy()
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 加载已保存的Cookie
        self.load_cookie()
        
        # 加载tag池配置
        self.load_tag_pools()
        
        # 加载喜欢作者配置
        self.load_favorite_authors()
        
        # 初始化圈名映射缓存
        self._update_alias_mapping()
        
        self.session = httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.aclose()
    
    async def get_user_info(self, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取用户信息（需要Cookie）
        
        Args:
            user_id: 用户ID，如果为None则尝试获取当前用户信息
            
        Returns:
            用户信息字典，失败返回None
        """
        try:
            # 限流等待
            await self._rate_limit_wait()
            
            if not self.full_cookie:
                print("没有可用的Cookie")
                return None
                
            # 设置认证头
            headers = self.headers.copy()
            # 使用完整的Cookie字符串
            headers['Cookie'] = self.full_cookie
            
            if user_id:
                # 获取指定用户信息
                url = f"{self.base_url}/ajax/user/{user_id}?full=1&lang=zh"
            else:
                # 获取当前用户信息
                url = f"{self.base_url}/ajax/user/self?full=1&lang=zh"
            
            if not self.session:
                raise RuntimeError("Session not initialized")
                
            print(f"请求用户信息URL: {url}")
            response = await self.session.get(url, headers=headers)
            response.raise_for_status()
            
            user_info = response.json()
            print(f"用户信息: {user_info}")
            
            return user_info
            
        except Exception as e:
            print(f"获取用户信息异常: {e}")
            return None

    async def get_author_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取作者作品列表（正确的API）
        
        Args:
            user_id: 作者ID
            
        Returns:
            作者作品信息，失败返回None
        """
        try:
            # 限流等待
            await self._rate_limit_wait()
            
            if not self.full_cookie:
                print("没有可用的Cookie，无法获取作者作品")
                return None
            
            # 构建正确的作者作品API URL
            url = f"{self.base_url}/ajax/user/{user_id}/profile/top?sensitiveFilterMode=userSetting&lang=zh"
            
            # 设置认证头
            headers = self.headers.copy()
            headers['Cookie'] = self.full_cookie
            
            if not self.session:
                raise RuntimeError("Session not initialized")
            
            print(f"获取作者作品 - ID: {user_id}, URL: {url}")
            
            response = await self.session.get(url, headers=headers)
            response.raise_for_status()
            
            author_data = response.json()
            
            if author_data.get('error'):
                print(f"获取作者作品失败: {author_data.get('message', '未知错误')}")
                return None
            
            print(f"成功获取作者作品数据")
            return author_data.get('body')
            
        except Exception as e:
            print(f"获取作者作品异常: {e}")
            return None
    
    async def _rate_limit_wait(self):
        """限流等待"""
        if not self.rate_limit_enabled:
            return
        
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last_request
            print(f"限流等待: {wait_time:.2f}秒")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()

    async def search_illustrations(self, tag: Union[str, List[str]], page: int = 1, page_size: int = 30) -> Optional[Dict[str, Any]]:
        """
        根据tag搜索图片（支持多tag搜索）
        
        Args:
            tag: 搜索标签，可以是字符串（单tag）或列表（多tag）
            page: 页码，默认为1
            page_size: 每页数量，默认为30
            
        Returns:
            精简的图片数据字典，失败返回None
        """
        try:
            # 限流等待
            await self._rate_limit_wait()
            
            # 检查是否有可用的Cookie
            if not self.full_cookie:
                print("没有可用的Cookie，无法搜索图片")
                return None
            
            # 处理搜索标签
            if isinstance(tag, list):
                # 多tag搜索，使用空格连接
                search_keyword = ' '.join([t.strip() for t in tag if t and t.strip()])
                print(f"多tag搜索: {tag} -> 合并关键词: '{search_keyword}'")
            else:
                search_keyword = tag.strip() if tag else ""
            
            if not search_keyword:
                print("搜索关键词为空")
                return None
            
            # 构建URL - 使用Pixiv的搜索API
            url = f"{self.base_url}/ajax/search/artworks/{search_keyword}"
            params = {
                'word': search_keyword,
                'order': 'date_d',
                'mode': 'all',
                'p': page,
                'csw': '0',
                's_mode': 's_tag',
                'type': 'all',
                'lang': 'zh',
                'ai_type': '1',
            }
            
            # 设置认证头
            headers = self.headers.copy()
            # 使用完整的Cookie字符串
            headers['Cookie'] = self.full_cookie
            
            if not self.session:
                raise RuntimeError("Session not initialized")
            
            print(f"搜索图片 - 关键词: '{search_keyword}', 页码: {page}")
            
            response = await self.session.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            raw_data = response.json()
            
            # 直接返回精简的数据结构
            return await self._extract_simplified_data(raw_data, search_keyword)
            
        except Exception as e:
            print(f"搜索图片异常: {e}")
            return None

    async def _extract_simplified_data(self, raw_data: Dict[str, Any], search_keyword: str) -> Dict[str, Any]:
        """
        从原始API响应中提取精简的数据结构
        
        Args:
            raw_data: 原始API响应数据
            search_keyword: 搜索关键词
            
        Returns:
            精简后的数据结构
        """
        try:
            if not raw_data or 'body' not in raw_data:
                return {
                    'illusts': [],
                    'total': 0,
                    'lastPage': 1,
                    'relatedTags': [],
                    'tagTranslation': {},
                    'popular': {
                        'recent': [],
                        'permanent': []
                    },
                    'searchInfo': {
                        'keyword': search_keyword,
                        'timestamp': __import__('datetime').datetime.now().isoformat()
                    }
                }
            
            body = raw_data['body']
            illust_manga = body.get('illustManga', {})
            
            # 提取图片数据 - 只保留核心必要字段，并应用tag屏蔽
            simplified_illusts = []
            blocked_count = 0
            
            for illust in illust_manga.get('data', []):
                # 检查是否包含屏蔽的tag（使用翻译增强检查，包括相关标签）
                illust_tags = illust.get('tags', [])
                related_tags = body.get('relatedTags', [])
                tag_translation = body.get('tagTranslation', {})
                
                # 使用增强的标签屏蔽检查（包括相关标签和翻译）
                if await self._should_block_image_with_translation(illust_tags, related_tags, tag_translation):
                    blocked_count += 1
                    continue
                
                simplified_illust = {
                    # 🔴 核心必要数据
                    'id': illust.get('id'),
                    'title': illust.get('title'),
                    'url': illust.get('url'),
                    'tags': illust.get('tags', []),
                    'userId': illust.get('userId'),
                    'userName': illust.get('userName'),
                    'pageCount': illust.get('pageCount', 1),
                    'width': illust.get('width'),
                    'height': illust.get('height'),
                    'illustType': illust.get('illustType'),
                    'xRestrict': illust.get('xRestrict', 0),
                    
                    # 🟡 重要数据
                    'description': illust.get('description', ''),
                    'createDate': illust.get('createDate'),
                    'aiType': illust.get('aiType', 0),
                    'profileImageUrl': illust.get('profileImageUrl', '')
                }
                simplified_illusts.append(simplified_illust)
            
            # 记录屏蔽统计
            if blocked_count > 0:
                print(f"Tag屏蔽: 过滤了 {blocked_count} 个包含屏蔽tag的作品")
            
            # 构建精简的数据结构
            simplified_data = {
                # 🔴 核心数据
                'illusts': simplified_illusts,
                'total': illust_manga.get('total', 0),
                'lastPage': illust_manga.get('lastPage', 1),
                
                # 🟡 重要数据
                'relatedTags': body.get('relatedTags', []),
                'tagTranslation': body.get('tagTranslation', {}),
                
                # 🔥 热门推荐数据
                'popular': {
                    'recent': body.get('popular', {}).get('recent', []),
                    'permanent': body.get('popular', {}).get('permanent', [])
                },
                
                # 搜索元信息
                'searchInfo': {
                    'keyword': search_keyword,
                    'timestamp': __import__('datetime').datetime.now().isoformat()
                }
            }
            
            print(f"搜索完成: 找到 {len(simplified_illusts)} 个结果，总计 {simplified_data['total']} 个")
            return simplified_data
            
        except Exception as e:
            print(f"提取精简数据异常: {e}")
            return {
                'illusts': [],
                'total': 0,
                'lastPage': 1,
                'relatedTags': [],
                'tagTranslation': {},
                'popular': {
                    'recent': [],
                    'permanent': []
                },
                'searchInfo': {
                    'keyword': search_keyword,
                    'timestamp': __import__('datetime').datetime.now().isoformat()
                }
            }

    def _get_daily_seed(self, user_qq: str) -> int:
        """
        生成用户每日固定种子
        
        Args:
            user_qq: 用户QQ号
            
        Returns:
            确定性的种子数字
        """
        today = datetime.now().strftime("%Y%m%d")  # 如: 20241121
        seed_string = f"{user_qq}_{today}"
        
        # 使用MD5哈希确保确定性
        hash_obj = hashlib.md5(seed_string.encode())
        hash_hex = hash_obj.hexdigest()
        
        # 取前8位十六进制转为整数
        return int(hash_hex[:8], 16)

    def _select_tag_by_seed(self, preferred_tags: List[str], seed: int) -> Optional[str]:
        """
        根据种子选择tag
        
        Args:
            preferred_tags: 喜好tag列表
            seed: 种子数字
            
        Returns:
            选中的tag，失败返回None
        """
        if not preferred_tags:
            return None
        
        tag_index = seed % len(preferred_tags)
        return preferred_tags[tag_index]

    def _select_image_by_seed(self, popular_images: List[Dict], seed: int) -> Optional[Dict]:
        """
        根据种子选择图片
        
        Args:
            popular_images: 热门图片列表
            seed: 种子数字
            
        Returns:
            选中的图片信息
        """
        if not popular_images:
            return None
        
        image_index = seed % len(popular_images)
        return popular_images[image_index]

    def calculate_quality_score(self, illust_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算图片质量评分
        
        Args:
            illust_data: 图片数据，包含统计信息
            
        Returns:
            质量评分结果，包含总分和各维度分数
        """
        try:
            # 基础数据提取
            bookmark_count = illust_data.get('bookmarkCount', 0)  # 收藏数
            like_count = illust_data.get('likeCount', 0)          # 点赞数
            comment_count = illust_data.get('commentCount', 0)    # 评论数
            view_count = illust_data.get('viewCount', 0)          # 浏览数
            response_count = illust_data.get('responseCount', 0)  # 回复数
            page_count = illust_data.get('pageCount', 1)          # 页数
            width = illust_data.get('width', 0)                   # 宽度
            height = illust_data.get('height', 0)                 # 高度
            create_date_str = illust_data.get('createDate', '')   # 创建时间
            
            # 计算作品发布时间（小时）
            hours_since_upload = self._calculate_hours_since_upload(create_date_str)
            
            # 1. 互动质量评分 (40%权重)
            interaction_score = self._calculate_interaction_score(
                bookmark_count, like_count, comment_count, response_count, hours_since_upload
            )
            
            # 2. 内容质量评分 (25%权重)
            content_score = self._calculate_content_score(
                page_count, width, height, bookmark_count, view_count
            )
            
            # 3. 时间衰减评分 (20%权重)
            time_score = self._calculate_time_score(hours_since_upload, bookmark_count)
            
            # 4. 参与度评分 (15%权重)
            engagement_score = self._calculate_engagement_score(
                bookmark_count, like_count, comment_count, view_count
            )
            
            # 计算加权总分
            total_score = (
                interaction_score * 0.4 +
                content_score * 0.25 +
                time_score * 0.2 +
                engagement_score * 0.15
            )
            
            # 限制分数范围 0-100
            total_score = max(0, min(100, total_score))
            
            return {
                'total_score': round(total_score, 2),
                'interaction_score': round(interaction_score, 2),
                'content_score': round(content_score, 2),
                'time_score': round(time_score, 2),
                'engagement_score': round(engagement_score, 2),
                'quality_level': self._get_quality_level(total_score),
                'details': {
                    'bookmark_count': bookmark_count,
                    'like_count': like_count,
                    'comment_count': comment_count,
                    'view_count': view_count,
                    'hours_since_upload': hours_since_upload,
                    'page_count': page_count,
                    'resolution': f"{width}x{height}"
                }
            }
            
        except Exception as e:
            print(f"计算质量评分异常: {e}")
            return {
                'total_score': 0,
                'interaction_score': 0,
                'content_score': 0,
                'time_score': 0,
                'engagement_score': 0,
                'quality_level': '未知',
                'details': {}
            }

    def _calculate_hours_since_upload(self, create_date_str: str) -> float:
        """计算作品发布至今的小时数"""
        try:
            if not create_date_str:
                return 24 * 30  # 默认30天
            
            # 解析时间字符串 (格式: "2025-11-21T06:12:32+09:00")
            from datetime import datetime
            import re
            
            # 提取主要时间部分，忽略时区
            time_match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', create_date_str)
            if not time_match:
                return 24 * 30
            
            create_time = datetime.fromisoformat(time_match.group(1))
            current_time = datetime.now()
            
            # 计算时间差（小时）
            time_diff = current_time - create_time
            hours = time_diff.total_seconds() / 3600
            
            return max(0.1, hours)  # 最小0.1小时，避免除零
            
        except Exception as e:
            print(f"计算时间差异常: {e}")
            return 24 * 30  # 默认30天

    def _calculate_interaction_score(self, bookmark_count: int, like_count: int, 
                                   comment_count: int, response_count: int, 
                                   hours_since_upload: float) -> float:
        """
        计算互动质量评分
        
        核心思路：收藏 > 评论 > 点赞 > 回复
        新作品考虑时间衰减，老作品直接看绝对数值
        """
        # 基础权重：收藏(40%) + 评论(30%) + 点赞(20%) + 回复(10%)
        base_score = (
            bookmark_count * 0.4 +
            comment_count * 0.3 +
            like_count * 0.2 +
            response_count * 0.1
        )
        
        if hours_since_upload <= 72:  # 3天内的新作品
            # 时间衰减：每小时的表现
            hourly_score = base_score / max(1, hours_since_upload)
            
            # 新作品评分标准（每小时）
            # 优秀: >10收藏/小时, 良好: 5-10, 一般: 2-5, 较差: <2
            if hourly_score >= 10:
                return 85 + min(15, hourly_score - 10)  # 85-100分
            elif hourly_score >= 5:
                return 70 + (hourly_score - 5) * 3  # 70-85分
            elif hourly_score >= 2:
                return 50 + (hourly_score - 2) * 6.67  # 50-70分
            else:
                return hourly_score * 25  # 0-50分
        else:
            # 老作品直接看绝对数值
            # 优秀: >1000收藏, 良好: 500-1000, 一般: 100-500, 较差: <100
            if bookmark_count >= 1000:
                return 85 + min(15, bookmark_count / 200)  # 85-100分
            elif bookmark_count >= 500:
                return 70 + (bookmark_count - 500) / 33.33  # 70-85分
            elif bookmark_count >= 100:
                return 50 + (bookmark_count - 100) / 13.33  # 50-70分
            else:
                return bookmark_count / 2  # 0-50分

    def _calculate_content_score(self, page_count: int, width: int, height: int, 
                                bookmark_count: int, view_count: int) -> float:
        """
        计算内容质量评分
        
        考虑因素：多页作品加分、高分辨率加分、收藏率加分
        """
        score = 50  # 基础分
        
        # 1. 多页作品加分 (0-20分)
        if page_count > 1:
            multi_page_bonus = min(20, page_count * 5)
            score += multi_page_bonus
        
        # 2. 分辨率加分 (0-20分)
        total_pixels = width * height
        if total_pixels >= 4000000:  # 4K以上
            score += 20
        elif total_pixels >= 2000000:  # 2K-4K
            score += 15
        elif total_pixels >= 1000000:  # 1M-2M
            score += 10
        elif total_pixels >= 500000:   # 500K-1M
            score += 5
        
        # 3. 收藏率加分 (0-10分)
        if view_count > 0:
            bookmark_rate = bookmark_count / view_count
            if bookmark_rate >= 0.1:  # 10%以上收藏率
                score += 10
            elif bookmark_rate >= 0.05:  # 5-10%
                score += 7
            elif bookmark_rate >= 0.02:  # 2-5%
                score += 4
            elif bookmark_rate >= 0.01:  # 1-2%
                score += 2
        
        return min(100, score)

    def _calculate_time_score(self, hours_since_upload: float, bookmark_count: int) -> float:
        """
        计算时间衰减评分
        
        新作品：时间越新分数越高
        老作品：根据收藏数给分
        """
        if hours_since_upload <= 1:  # 1小时内
            return 100
        elif hours_since_upload <= 6:  # 6小时内
            return 90
        elif hours_since_upload <= 24:  # 1天内
            return 80
        elif hours_since_upload <= 72:  # 3天内
            return 70
        elif hours_since_upload <= 168:  # 1周内
            return 60
        elif hours_since_upload <= 720:  # 1月内
            return 50
        else:
            # 老作品根据收藏数给分
            if bookmark_count >= 1000:
                return 40
            elif bookmark_count >= 500:
                return 30
            elif bookmark_count >= 100:
                return 20
            else:
                return 10

    def _calculate_engagement_score(self, bookmark_count: int, like_count: int, 
                                  comment_count: int, view_count: int) -> float:
        """
        计算参与度评分
        
        综合考虑各种互动数据与浏览量的比例
        """
        if view_count == 0:
            return 0
        
        # 计算各项参与度指标
        bookmark_rate = bookmark_count / view_count  # 收藏率
        like_rate = like_count / view_count          # 点赞率
        comment_rate = comment_count / view_count     # 评论率
        
        # 综合参与度评分
        engagement_score = (
            bookmark_rate * 50 +    # 收藏率权重50%
            like_rate * 30 +        # 点赞率权重30%
            comment_rate * 20       # 评论率权重20%
        ) * 100  # 转换为百分制
        
        # 根据收藏数额外加分
        if bookmark_count >= 1000:
            engagement_score += 20
        elif bookmark_count >= 500:
            engagement_score += 15
        elif bookmark_count >= 100:
            engagement_score += 10
        elif bookmark_count >= 50:
            engagement_score += 5
        
        return min(100, engagement_score)

    def _get_quality_level(self, score: float) -> str:
        """根据分数获取质量等级"""
        if score >= 90:
            return "S级 - 神作"
        elif score >= 80:
            return "A级 - 优秀"
        elif score >= 70:
            return "B级 - 良好"
        elif score >= 60:
            return "C级 - 一般"
        elif score >= 40:
            return "D级 - 较差"
        else:
            return "E级 - 低质"

    async def get_illust_details(self, illust_id: str) -> Optional[Dict[str, Any]]:
        """
        获取图片详细信息（包含统计数据）
        
        Args:
            illust_id: 图片ID
            
        Returns:
            图片详细信息，失败返回None
        """
        try:
            # 限流等待
            await self._rate_limit_wait()
            
            if not self.full_cookie:
                print("没有可用的Cookie，无法获取图片详情")
                return None
            
            # 构建URL
            url = f"{self.base_url}/ajax/illust/{illust_id}?lang=zh"
            
            # 设置认证头
            headers = self.headers.copy()
            headers['Cookie'] = self.full_cookie
            
            if not self.session:
                raise RuntimeError("Session not initialized")
            
            print(f"获取图片详情 - ID: {illust_id}")
            
            response = await self.session.get(url, headers=headers)
            response.raise_for_status()
            
            details_data = response.json()
            
            if details_data.get('error'):
                print(f"获取图片详情失败: {details_data.get('message', '未知错误')}")
                return None
            
            return details_data.get('body')
            
        except Exception as e:
            print(f"获取图片详情异常: {e}")
            return None

    async def search_images(self, 
                           tags: Union[str, List[str]], 
                           mode: str = "random", 
                           count: int = 1, 
                           min_quality_score: float = 60.0,
                           max_attempts: int = 10) -> Optional[Dict[str, Any]]:
        """
        搜图机器人核心功能
        
        Args:
            tags: 搜索标签，可以是字符串（单tag）或列表（多tag）
            mode: 搜图模式
                - "random": 随机图（默认），在搜索结果中随机选择，检查质量评分
                - "recent": 近日美图，从popular.recent中选择
                - "popular": 美图，从popular.permanent中选择
            count: 返回图片数量，1-5张，默认1张
            min_quality_score: 最低质量评分要求，仅对random模式有效，默认60分
            max_attempts: 最大尝试次数，仅对random模式有效，默认10次
            
        Returns:
            搜图结果字典，包含图片列表、统计信息等，失败返回None
        """
        try:
            # 参数验证
            if count < 1 or count > 5:
                print(f"图片数量必须在1-5之间，当前值: {count}")
                return None
            
            if mode not in ["random", "recent", "popular"]:
                print(f"不支持的搜图模式: {mode}，支持的模式: random, recent, popular")
                return None
            
            # 处理标签
            if isinstance(tags, str):
                tags = [tags.strip()] if tags.strip() else []
            elif isinstance(tags, list):
                tags = [tag.strip() for tag in tags if tag and tag.strip()]
            else:
                print("标签参数必须是字符串或字符串列表")
                return None
            
            if not tags:
                print("搜索标签不能为空")
                return None
            
            search_keyword = ' '.join(tags)
            print(f"开始搜图 - 关键词: '{search_keyword}', 模式: {mode}, 数量: {count}")
            
            # 执行搜索
            search_result = await self.search_illustrations(search_keyword)
            if not search_result:
                print(f"搜索失败: {search_keyword}")
                return None
            
            # 根据模式获取图片
            if mode == "random":
                images = await self._get_random_images(
                    search_result, count, min_quality_score, max_attempts
                )
            elif mode == "recent":
                images = await self._get_recent_popular_images(search_result, count)
            elif mode == "popular":
                images = await self._get_permanent_popular_images(search_result, count)
            else:
                images = []
            
            if not images:
                print(f"未找到符合条件的图片")
                return None
            
            # 构建返回结果
            result = {
                'search_info': {
                    'tags': tags,
                    'search_keyword': search_keyword,
                    'mode': mode,
                    'requested_count': count,
                    'actual_count': len(images),
                    'min_quality_score': min_quality_score if mode == "random" else None,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                'images': images,
                'statistics': {
                    'total_search_results': search_result.get('total', 0),
                    'popular_recent_count': len(search_result.get('popular', {}).get('recent', [])),
                    'popular_permanent_count': len(search_result.get('popular', {}).get('permanent', [])),
                    'regular_illust_count': len(search_result.get('illusts', []))
                }
            }
            
            print(f"搜图完成 - 找到 {len(images)} 张图片")
            return result
            
        except Exception as e:
            print(f"搜图异常: {e}")
            return None

    async def _get_random_images(self, 
                                search_result: Dict[str, Any], 
                                count: int, 
                                min_quality_score: float,
                                max_attempts: int) -> List[Dict[str, Any]]:
        """
        获取随机图片（带质量评分检查，支持小众tag降级策略）
        
        Args:
            search_result: 搜索结果
            count: 需要的图片数量
            min_quality_score: 最低质量评分
            max_attempts: 最大尝试次数
            
        Returns:
            符合条件的图片列表
        """
        try:
            images = []
            attempts = 0
            used_image_ids = set()
            failed_candidates = []  # 存储不符合要求的候选图片
            
            # 优先从热门作品中选择
            all_candidates = []
            
            # 添加热门作品到候选池
            popular_recent = search_result.get('popular', {}).get('recent', [])
            popular_permanent = search_result.get('popular', {}).get('permanent', [])
            regular_illusts = search_result.get('illusts', [])
            
            # 候选池优先级：热门近期 > 热门永久 > 普通作品
            all_candidates.extend(popular_recent)
            all_candidates.extend(popular_permanent)
            all_candidates.extend(regular_illusts)
            
            if not all_candidates:
                print("没有找到任何候选图片")
                return []
            
            print(f"候选图片池: {len(all_candidates)} 张（热门近期: {len(popular_recent)}, 热门永久: {len(popular_permanent)}, 普通: {len(regular_illusts)}）")
            
            # 第一阶段：尝试找到符合质量要求的图片
            while len(images) < count and attempts < max_attempts:
                attempts += 1
                
                # 随机选择候选图片
                if not all_candidates:
                    break
                
                candidate = random.choice(all_candidates)
                image_id = candidate.get('id')
                
                if not image_id or image_id in used_image_ids:
                    continue
                
                used_image_ids.add(image_id)
                
                print(f"尝试第 {attempts} 次 - 检查图片 ID: {image_id}")
                
                # 获取详细信息和质量评分
                quality_score = None
                try:
                    illust_details = await self.get_illust_details(image_id)
                    if illust_details:
                        quality_score = self.calculate_quality_score(illust_details)
                        print(f"质量评分: {quality_score['total_score']} ({quality_score['quality_level']})")
                    else:
                        print("获取图片详情失败，跳过质量评分")
                        quality_score = None
                except Exception as e:
                    print(f"质量评分计算异常: {e}")
                    quality_score = None
                
                # 检查质量评分
                if quality_score and quality_score['total_score'] >= min_quality_score:
                    # 构建图片信息
                    image_info = {
                        'id': image_id,
                        'title': candidate.get('title', ''),
                        'url': candidate.get('url', ''),
                        'tags': candidate.get('tags', []),
                        'userId': candidate.get('userId', ''),
                        'userName': candidate.get('userName', ''),
                        'pageCount': candidate.get('pageCount', 1),
                        'width': candidate.get('width', 0),
                        'height': candidate.get('height', 0),
                        'illustType': candidate.get('illustType', 0),
                        'xRestrict': candidate.get('xRestrict', 0),
                        'description': candidate.get('description', ''),
                        'createDate': candidate.get('createDate', ''),
                        'aiType': candidate.get('aiType', 0),
                        'profileImageUrl': candidate.get('profileImageUrl', ''),
                        'quality_score': quality_score,
                        'source': 'random_selection'
                    }
                    
                    images.append(image_info)
                    print(f"✅ 图片符合要求 - ID: {image_id}, 评分: {quality_score['total_score']}")
                else:
                    # 存储不符合要求的候选图片，用于降级处理
                    failed_candidates.append({
                        'candidate': candidate,
                        'quality_score': quality_score,
                        'reason': 'low_quality' if quality_score else 'no_score'
                    })
                    score_text = f"{quality_score['total_score']}" if quality_score else "无评分"
                    print(f"❌ 图片不符合要求 - ID: {image_id}, 评分: {score_text} < {min_quality_score}")
            
            # 第二阶段：如果没找到足够的高质量图片，启用降级策略
            if len(images) < count and failed_candidates:
                print(f"🔄 启用降级策略 - 高质量图片不足，从剩余候选中选择最佳图片")
                
                # 按质量评分排序失败的候选图片（有评分的优先）
                failed_candidates.sort(key=lambda x: (
                    0 if x['quality_score'] else 1,  # 有评分的优先
                    -(x['quality_score']['total_score'] if x['quality_score'] else 0)  # 按评分降序
                ))
                
                # 补充剩余需要的图片
                needed = count - len(images)
                for i, failed_item in enumerate(failed_candidates[:needed]):
                    candidate = failed_item['candidate']
                    quality_score = failed_item['quality_score']
                    
                    image_info = {
                        'id': candidate.get('id', ''),
                        'title': candidate.get('title', ''),
                        'url': candidate.get('url', ''),
                        'tags': candidate.get('tags', []),
                        'userId': candidate.get('userId', ''),
                        'userName': candidate.get('userName', ''),
                        'pageCount': candidate.get('pageCount', 1),
                        'width': candidate.get('width', 0),
                        'height': candidate.get('height', 0),
                        'illustType': candidate.get('illustType', 0),
                        'xRestrict': candidate.get('xRestrict', 0),
                        'description': candidate.get('description', ''),
                        'createDate': candidate.get('createDate', ''),
                        'aiType': candidate.get('aiType', 0),
                        'profileImageUrl': candidate.get('profileImageUrl', ''),
                        'quality_score': quality_score,
                        'source': 'fallback_selection'
                    }
                    
                    images.append(image_info)
                    score_text = f"{quality_score['total_score']}" if quality_score else "无评分"
                    print(f"🔄 降级选择 - ID: {candidate.get('id')}, 评分: {score_text} (原因: {failed_item['reason']})")
            
            # 第三阶段：如果仍然不足，直接从剩余候选中随机选择
            if len(images) < count:
                print(f"🔄 最终降级 - 仍然不足，从剩余候选中随机选择")
                
                # 获取未使用的候选图片
                remaining_candidates = [
                    candidate for candidate in all_candidates 
                    if candidate.get('id') not in [img['id'] for img in images]
                ]
                
                needed = count - len(images)
                selected = random.sample(remaining_candidates, min(needed, len(remaining_candidates)))
                
                for candidate in selected:
                    image_info = {
                        'id': candidate.get('id', ''),
                        'title': candidate.get('title', ''),
                        'url': candidate.get('url', ''),
                        'tags': candidate.get('tags', []),
                        'userId': candidate.get('userId', ''),
                        'userName': candidate.get('userName', ''),
                        'pageCount': candidate.get('pageCount', 1),
                        'width': candidate.get('width', 0),
                        'height': candidate.get('height', 0),
                        'illustType': candidate.get('illustType', 0),
                        'xRestrict': candidate.get('xRestrict', 0),
                        'description': candidate.get('description', ''),
                        'createDate': candidate.get('createDate', ''),
                        'aiType': candidate.get('aiType', 0),
                        'profileImageUrl': candidate.get('profileImageUrl', ''),
                        'quality_score': None,
                        'source': 'final_fallback'
                    }
                    
                    images.append(image_info)
                    print(f"🔄 最终选择 - ID: {candidate.get('id')}, 无质量评分")
            
            print(f"随机模式完成 - 尝试 {attempts} 次，找到 {len(images)} 张图片")
            
            # 统计不同来源的图片数量
            source_count = {}
            for img in images:
                source = img.get('source', 'unknown')
                source_count[source] = source_count.get(source, 0) + 1
            
            print(f"图片来源统计: {dict(source_count)}")
            
            return images
            
        except Exception as e:
            print(f"获取随机图片异常: {e}")
            return []

    async def _get_recent_popular_images(self, search_result: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """
        获取近日美图（从popular.recent中选择）
        
        Args:
            search_result: 搜索结果
            count: 需要的图片数量
            
        Returns:
            图片列表
        """
        try:
            popular_recent = search_result.get('popular', {}).get('recent', [])
            
            if not popular_recent:
                print("没有找到近日热门作品")
                return []
            
            print(f"近日热门作品池: {len(popular_recent)} 张")
            
            # 随机选择指定数量的图片
            selected_count = min(count, len(popular_recent))
            selected_images = random.sample(popular_recent, selected_count)
            
            # 构建图片信息
            images = []
            for candidate in selected_images:
                image_info = {
                    'id': candidate.get('id', ''),
                    'title': candidate.get('title', ''),
                    'url': candidate.get('url', ''),
                    'tags': candidate.get('tags', []),
                    'userId': candidate.get('userId', ''),
                    'userName': candidate.get('userName', ''),
                    'pageCount': candidate.get('pageCount', 1),
                    'width': candidate.get('width', 0),
                    'height': candidate.get('height', 0),
                    'illustType': candidate.get('illustType', 0),
                    'xRestrict': candidate.get('xRestrict', 0),
                    'description': candidate.get('description', ''),
                    'createDate': candidate.get('createDate', ''),
                    'aiType': candidate.get('aiType', 0),
                    'profileImageUrl': candidate.get('profileImageUrl', ''),
                    'quality_score': None,  # 热门作品不计算质量评分
                    'source': 'popular_recent'
                }
                images.append(image_info)
            
            print(f"近日美图模式完成 - 选择 {len(images)} 张图片")
            return images
            
        except Exception as e:
            print(f"获取近日美图异常: {e}")
            return []

    async def _get_permanent_popular_images(self, search_result: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """
        获取美图（从popular.permanent中选择）
        
        Args:
            search_result: 搜索结果
            count: 需要的图片数量
            
        Returns:
            图片列表
        """
        try:
            popular_permanent = search_result.get('popular', {}).get('permanent', [])
            
            if not popular_permanent:
                print("没有找到永久热门作品")
                return []
            
            print(f"永久热门作品池: {len(popular_permanent)} 张")
            
            # 随机选择指定数量的图片
            selected_count = min(count, len(popular_permanent))
            selected_images = random.sample(popular_permanent, selected_count)
            
            # 构建图片信息
            images = []
            for candidate in selected_images:
                image_info = {
                    'id': candidate.get('id', ''),
                    'title': candidate.get('title', ''),
                    'url': candidate.get('url', ''),
                    'tags': candidate.get('tags', []),
                    'userId': candidate.get('userId', ''),
                    'userName': candidate.get('userName', ''),
                    'pageCount': candidate.get('pageCount', 1),
                    'width': candidate.get('width', 0),
                    'height': candidate.get('height', 0),
                    'illustType': candidate.get('illustType', 0),
                    'xRestrict': candidate.get('xRestrict', 0),
                    'description': candidate.get('description', ''),
                    'createDate': candidate.get('createDate', ''),
                    'aiType': candidate.get('aiType', 0),
                    'profileImageUrl': candidate.get('profileImageUrl', ''),
                    'quality_score': None,  # 热门作品不计算质量评分
                    'source': 'popular_permanent'
                }
                images.append(image_info)
            
            print(f"美图模式完成 - 选择 {len(images)} 张图片")
            return images
            
        except Exception as e:
            print(f"获取美图异常: {e}")
            return []

    async def get_random_image(self, user_qq: Optional[str] = None, max_attempts: int = 5) -> Optional[Dict[str, Any]]:
        """
        获取随机图片推荐（保持向后兼容）
        
        Args:
            user_qq: 用户QQ号（可选，用于日志记录）
            max_attempts: 最大尝试次数（不同tag），默认5次
            
        Returns:
            图片推荐信息，包含tag、图片、质量评分等，失败返回None
        """
        try:
            user_info = f"用户 {user_qq}" if user_qq else "匿名用户"
            print(f"开始为{user_info}获取随机图片推荐")
            
            # 1. 获取可用tag
            available_tags = list(self.preferred_tags)
            if not available_tags:
                print("喜好tag池为空，无法获取图片推荐")
                return None
            
            # 2. 尝试多个tag，直到找到有热门作品的tag
            attempted_tags = []
            
            for attempt in range(max_attempts):
                # 从剩余tag中随机选择
                remaining_tags = [tag for tag in available_tags if tag not in attempted_tags]
                if not remaining_tags:
                    print("已尝试所有可用tag，都没有找到热门作品")
                    break
                
                selected_tag = random.choice(remaining_tags)
                attempted_tags.append(selected_tag)
                
                print(f"尝试第 {attempt + 1} 次，选中tag: {selected_tag}")
                
                # 3. 搜索该tag的热门作品
                search_result = await self.search_illustrations(selected_tag)
                if not search_result:
                    print(f"搜索tag '{selected_tag}' 失败，尝试下一个tag")
                    continue
                
                # 4. 检查是否有热门作品
                popular_images = search_result.get('popular', {}).get('recent', [])
                if not popular_images:
                    print(f"tag '{selected_tag}' 没有热门作品，尝试下一个tag")
                    continue
                
                print(f"tag '{selected_tag}' 找到热门作品 {len(popular_images)} 张")
                
                # 5. 从热门作品中随机选择图片
                selected_image = random.choice(popular_images)
                if not selected_image:
                    print("选择图片失败，尝试下一个tag")
                    continue
                
                # 6. 获取图片详细统计数据并计算质量评分
                quality_score = None
                try:
                    # 调用详情API获取完整统计数据
                    illust_id = selected_image.get('id')
                    if illust_id:
                        illust_details = await self.get_illust_details(illust_id)
                        if illust_details:
                            # 计算质量评分
                            quality_score = self.calculate_quality_score(illust_details)
                            print(f"质量评分: {quality_score['total_score']} ({quality_score['quality_level']})")
                        else:
                            print("获取图片详情失败，跳过质量评分")
                    else:
                        print("图片ID为空，跳过质量评分")
                except Exception as e:
                    print(f"质量评分计算异常: {e}")
                
                # 7. 返回结果（包含质量评分）
                result = {
                    'user_qq': user_qq,
                    'tag': selected_tag,
                    'image': selected_image,
                    'date': datetime.now().strftime("%Y-%m-%d"),
                    'available_tags_count': len(available_tags),
                    'available_images_count': len(popular_images),
                    'attempted_tags': attempted_tags,
                    'quality_score': quality_score
                }
                
                print(f"图片推荐获取成功: tag={selected_tag}, image_id={selected_image.get('id')}, 质量评分={quality_score['total_score'] if quality_score else 'N/A'}")
                return result
            
            # 如果所有尝试都失败了
            print(f"尝试了 {len(attempted_tags)} 个tag都没有找到热门作品: {', '.join(attempted_tags)}")
            return None
            
        except Exception as e:
            print(f"获取图片推荐异常: {e}")
            return None

    async def get_tag_latest_images(self, 
                                   tag: Union[str, List[str]], 
                                   count: int = 5,
                                   hours_limit: int = 24) -> Optional[Dict[str, Any]]:
        """
        获取某个标签的最新更新图片
        
        Args:
            tag: 搜索标签，可以是字符串（单tag）或列表（多tag）
            count: 返回图片数量，1-10张，默认5张
            hours_limit: 时间限制（小时），只获取指定小时内的更新，默认24小时
            
        Returns:
            最新图片结果字典，包含图片列表、统计信息等，失败返回None
        """
        try:
            # 参数验证
            if count < 1 or count > 10:
                print(f"图片数量必须在1-10之间，当前值: {count}")
                return None
            
            if hours_limit < 1 or hours_limit > 168:  # 最大7天
                print(f"时间限制必须在1-168小时之间，当前值: {hours_limit}")
                return None
            
            # 处理标签
            if isinstance(tag, str):
                tags = [tag.strip()] if tag.strip() else []
            elif isinstance(tag, list):
                tags = [tag.strip() for tag in tag if tag and tag.strip()]
            else:
                print("标签参数必须是字符串或字符串列表")
                return None
            
            if not tags:
                print("搜索标签不能为空")
                return None
            
            search_keyword = ' '.join(tags)
            print(f"开始获取标签最新图片 - 关键词: '{search_keyword}', 数量: {count}, 时间限制: {hours_limit}小时")
            
            # 计算时间阈值
            from datetime import datetime, timedelta
            time_threshold = datetime.now() - timedelta(hours=hours_limit)
            time_threshold_str = time_threshold.strftime("%Y-%m-%dT%H:%M:%S")
            
            print(f"时间阈值: {time_threshold_str} 之后的作品")
            
            # 搜索多页以获取足够的新作品
            all_images = []
            max_pages = 5  # 最多搜索5页
            page = 1
            
            while len(all_images) < count * 2 and page <= max_pages:  # 获取2倍数量以便筛选
                print(f"搜索第 {page} 页...")
                
                # 搜索当前页
                search_result = await self.search_illustrations(search_keyword, page=page)
                if not search_result:
                    print(f"第 {page} 页搜索失败")
                    break
                
                # 获取当前页的图片
                page_images = search_result.get('illusts', [])
                if not page_images:
                    print(f"第 {page} 页没有图片")
                    break
                
                print(f"第 {page} 页找到 {len(page_images)} 张图片")
                
                # 筛选时间范围内的图片
                for image in page_images:
                    create_date_str = image.get('createDate', '')
                    if not create_date_str:
                        continue
                    
                    try:
                        # 解析创建时间 - 处理带时区的时间字符串
                        if '+09:00' in create_date_str:
                            # Pixiv使用日本时间 (+09:00)
                            create_time = datetime.fromisoformat(create_date_str)
                        else:
                            # 处理其他格式的时间
                            create_time = datetime.fromisoformat(create_date_str.replace('Z', '+00:00'))
                        
                        # 确保时间对象有时区信息
                        if create_time.tzinfo is None:
                            create_time = create_time.replace(tzinfo=time_threshold.tzinfo)
                        
                        # 检查是否在时间范围内
                        if create_time >= time_threshold:
                            # 计算上传小时数
                            current_time = datetime.now(time_threshold.tzinfo)
                            hours_since_upload = (current_time - create_time).total_seconds() / 3600
                            image['hours_since_upload'] = hours_since_upload
                            all_images.append(image)
                            
                    except Exception as e:
                        print(f"解析时间失败: {create_date_str}, 错误: {e}")
                        continue
                
                # 如果当前页没有新图片，可能已经到了最早的页面
                if not any(img for img in page_images if img.get('createDate', '')):
                    print("没有找到有效的时间信息，停止搜索")
                    break
                
                page += 1
                
                # 短暂延迟避免请求过快
                await asyncio.sleep(0.1)
            
            if not all_images:
                print(f"在最近 {hours_limit} 小时内没有找到标签 '{search_keyword}' 的图片")
                return None
            
            print(f"总共找到 {len(all_images)} 张最新图片")
            
            # 按时间排序（最新的在前）
            all_images.sort(key=lambda x: x.get('createDate', ''), reverse=True)
            
            # 选择指定数量的图片
            selected_images = all_images[:count]
            
            # 为每张图片获取详细信息和质量评分
            enhanced_images = []
            for image in selected_images:
                try:
                    # 获取详细信息
                    illust_id = image.get('id')
                    quality_score = None
                    
                    if illust_id:
                        illust_details = await self.get_illust_details(illust_id)
                        if illust_details:
                            quality_score = self.calculate_quality_score(illust_details)
                    
                    # 构建增强的图片信息
                    enhanced_image = {
                        'id': image.get('id', ''),
                        'title': image.get('title', ''),
                        'url': image.get('url', ''),
                        'tags': image.get('tags', []),
                        'userId': image.get('userId', ''),
                        'userName': image.get('userName', ''),
                        'pageCount': image.get('pageCount', 1),
                        'width': image.get('width', 0),
                        'height': image.get('height', 0),
                        'illustType': image.get('illustType', 0),
                        'xRestrict': image.get('xRestrict', 0),
                        'description': image.get('description', ''),
                        'createDate': image.get('createDate', ''),
                        'aiType': image.get('aiType', 0),
                        'profileImageUrl': image.get('profileImageUrl', ''),
                        'hours_since_upload': image.get('hours_since_upload', 0),
                        'quality_score': quality_score,
                        'source': 'tag_latest'
                    }
                    
                    enhanced_images.append(enhanced_image)
                    
                except Exception as e:
                    print(f"处理图片 {image.get('id')} 时出错: {e}")
                    # 即使出错也添加基本信息
                    enhanced_images.append({
                        'id': image.get('id', ''),
                        'title': image.get('title', ''),
                        'url': image.get('url', ''),
                        'tags': image.get('tags', []),
                        'userId': image.get('userId', ''),
                        'userName': image.get('userName', ''),
                        'pageCount': image.get('pageCount', 1),
                        'width': image.get('width', 0),
                        'height': image.get('height', 0),
                        'illustType': image.get('illustType', 0),
                        'xRestrict': image.get('xRestrict', 0),
                        'description': image.get('description', ''),
                        'createDate': image.get('createDate', ''),
                        'aiType': image.get('aiType', 0),
                        'profileImageUrl': image.get('profileImageUrl', ''),
                        'hours_since_upload': image.get('hours_since_upload', 0),
                        'quality_score': None,
                        'source': 'tag_latest'
                    })
            
            # 构建返回结果
            result = {
                'search_info': {
                    'tags': tags,
                    'search_keyword': search_keyword,
                    'requested_count': count,
                    'actual_count': len(enhanced_images),
                    'hours_limit': hours_limit,
                    'time_threshold': time_threshold_str,
                    'total_candidates': len(all_images),
                    'pages_searched': page - 1,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                'images': enhanced_images,
                'statistics': {
                    'total_found': len(all_images),
                    'time_filtered': len(all_images),
                    'quality_scored': len([img for img in enhanced_images if img.get('quality_score')]),
                    'avg_hours_since_upload': sum(img.get('hours_since_upload', 0) for img in enhanced_images) / len(enhanced_images) if enhanced_images else 0
                }
            }
            
            print(f"标签最新图片获取完成 - 找到 {len(enhanced_images)} 张图片")
            return result
            
        except Exception as e:
            print(f"获取标签最新图片异常: {e}")
            return None

    async def get_author_images(self, 
                             user_id: str, 
                             mode: str = "recent", 
                             count: int = 3) -> Optional[Dict[str, Any]]:
        """
        获取特定作者的图片（支持作者ID或圈名）
        
        Args:
            user_id: 作者ID或圈名
            mode: 获取模式
                - "recent": 最新作品，按时间排序选择（默认）
                - "popular": 热门作品，按收藏数排序选择
                - "random": 随机选择（不检查质量评分，因为喜欢作者的用户想看所有更新）
            count: 返回图片数量，1-5张，默认3张
            
        Returns:
            作者图片结果字典，包含图片列表、作者信息等，失败返回None
        """
        try:
            # 参数验证
            if not user_id or not user_id.strip():
                print("作者ID/圈名不能为空")
                return None
            
            if count < 1 or count > 5:
                print(f"图片数量必须在1-5之间，当前值: {count}")
                return None
            
            if mode not in ["random", "recent", "popular"]:
                print(f"不支持的获取模式: {mode}，支持的模式: random, recent, popular")
                return None
            
            original_input = user_id.strip()
            user_id = str(user_id).strip()
            
            # 尝试通过圈名查找作者ID
            resolved_user_id = self.search_author_by_alias(user_id)
            if resolved_user_id:
                print(f"通过圈名 '{user_id}' 找到作者ID: {resolved_user_id}")
                user_id = resolved_user_id
                used_alias = True
            else:
                # 如果不是圈名，直接使用作为作者ID
                used_alias = False
            
            print(f"开始获取作者图片 - ID: {user_id}, 模式: {mode}, 数量: {count}")
            if used_alias:
                print(f"使用圈名查询: '{original_input}' -> ID: {user_id}")
            
            # 检查是否为喜欢作者
            is_favorite = user_id in self.favorite_authors
            author_info = self.favorite_authors.get(user_id, {})
            author_name = author_info.get('name', '未知作者')
            
            print(f"作者信息: {author_name} ({user_id}), 是否喜欢: {is_favorite}")
            
            # 获取作者信息和作品列表
            author_data = await self.get_author_profile(user_id)
            if not author_data:
                print(f"获取作者作品失败: 无数据")
                return None
            
            # 提取作者作品 - 从正确的API路径获取
            # 新的API返回格式：body.illusts 是一个字典，键为作品ID
            illusts_dict = author_data.get('illusts', {})
            illusts = list(illusts_dict.values()) if isinstance(illusts_dict, dict) else []
            if not illusts:
                print(f"作者 {author_name} 没有作品")
                return None
            
            print(f"作者 {author_name} 共有 {len(illusts)} 个作品")
            
            # 根据模式获取图片
            if mode == "random":
                images = await self._get_author_random_images(
                    illusts, count, min_quality_score=60.0, max_attempts=10
                )
            elif mode == "recent":
                images = await self._get_author_recent_images(illusts, count)
            elif mode == "popular":
                images = await self._get_author_popular_images(illusts, count)
            else:
                images = []
            
            if not images:
                print(f"未找到符合条件的作者图片")
                return None
            
            # 更新作者最后检查时间
            if is_favorite:
                self.update_author_last_check(user_id)
            
            # 构建返回结果
            result = {
                'author_info': {
                    'user_id': user_id,
                    'name': author_name,
                    'is_favorite': is_favorite,
                    'total_works': len(illusts),
                    'profile_image_url': author_data.get('image', ''),
                    'comment': author_data.get('comment', ''),
                    'followable': author_data.get('followable', False)
                },
                'search_info': {
                    'mode': mode,
                    'requested_count': count,
                    'actual_count': len(images),
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                'images': images
            }
            
            print(f"作者图片获取完成 - 找到 {len(images)} 张图片")
            return result
            
        except Exception as e:
            print(f"获取作者图片异常: {e}")
            return None

    async def _get_author_random_images(self, 
                                    illusts: List[Dict[str, Any]], 
                                    count: int,
                                    min_quality_score: float = 60.0,
                                    max_attempts: int = 10) -> List[Dict[str, Any]]:
        """
        获取作者随机图片（带质量评分检查）
        
        Args:
            illusts: 作者作品列表
            count: 需要的图片数量
            min_quality_score: 最低质量评分
            max_attempts: 最大尝试次数
            
        Returns:
            符合条件的图片列表
        """
        try:
            images = []
            attempts = 0
            used_image_ids = set()
            failed_candidates = []
            
            if not illusts:
                print("作者作品列表为空")
                return []
            
            print(f"作者作品池: {len(illusts)} 个作品")
            
            # 第一阶段：尝试找到符合质量要求的图片
            while len(images) < count and attempts < max_attempts:
                attempts += 1
                
                # 随机选择作品
                if not illusts:
                    break
                
                candidate = random.choice(illusts)
                image_id = candidate.get('id')
                
                if not image_id or image_id in used_image_ids:
                    continue
                
                used_image_ids.add(image_id)
                
                print(f"尝试第 {attempts} 次 - 检查作品 ID: {image_id}")
                
                # 获取详细信息和质量评分
                quality_score = None
                try:
                    illust_details = await self.get_illust_details(image_id)
                    if illust_details:
                        quality_score = self.calculate_quality_score(illust_details)
                        print(f"质量评分: {quality_score['total_score']} ({quality_score['quality_level']})")
                    else:
                        print("获取作品详情失败，跳过质量评分")
                        quality_score = None
                except Exception as e:
                    print(f"质量评分计算异常: {e}")
                    quality_score = None
                
                # 检查质量评分
                if quality_score and quality_score['total_score'] >= min_quality_score:
                    # 构建图片信息
                    image_info = {
                        'id': image_id,
                        'title': candidate.get('title', ''),
                        'url': candidate.get('url', ''),
                        'tags': candidate.get('tags', []),
                        'userId': candidate.get('userId', ''),
                        'userName': candidate.get('userName', ''),
                        'pageCount': candidate.get('pageCount', 1),
                        'width': candidate.get('width', 0),
                        'height': candidate.get('height', 0),
                        'illustType': candidate.get('illustType', 0),
                        'xRestrict': candidate.get('xRestrict', 0),
                        'description': candidate.get('description', ''),
                        'createDate': candidate.get('createDate', ''),
                        'aiType': candidate.get('aiType', 0),
                        'profileImageUrl': candidate.get('profileImageUrl', ''),
                        'quality_score': quality_score,
                        'source': 'author_random'
                    }
                    
                    images.append(image_info)
                    print(f"✅ 作品符合要求 - ID: {image_id}, 评分: {quality_score['total_score']}")
                else:
                    # 存储不符合要求的候选作品
                    failed_candidates.append({
                        'candidate': candidate,
                        'quality_score': quality_score,
                        'reason': 'low_quality' if quality_score else 'no_score'
                    })
                    score_text = f"{quality_score['total_score']}" if quality_score else "无评分"
                    print(f"❌ 作品不符合要求 - ID: {image_id}, 评分: {score_text} < {min_quality_score}")
            
            # 第二阶段：如果没找到足够的高质量图片，启用降级策略
            if len(images) < count and failed_candidates:
                print(f"🔄 启用降级策略 - 高质量作品不足，从剩余候选中选择最佳作品")
                
                # 按质量评分排序失败的候选作品
                failed_candidates.sort(key=lambda x: (
                    0 if x['quality_score'] else 1,  # 有评分的优先
                    -(x['quality_score']['total_score'] if x['quality_score'] else 0)  # 按评分降序
                ))
                
                # 补充剩余需要的图片
                needed = count - len(images)
                for i, failed_item in enumerate(failed_candidates[:needed]):
                    candidate = failed_item['candidate']
                    quality_score = failed_item['quality_score']
                    
                    image_info = {
                        'id': candidate.get('id', ''),
                        'title': candidate.get('title', ''),
                        'url': candidate.get('url', ''),
                        'tags': candidate.get('tags', []),
                        'userId': candidate.get('userId', ''),
                        'userName': candidate.get('userName', ''),
                        'pageCount': candidate.get('pageCount', 1),
                        'width': candidate.get('width', 0),
                        'height': candidate.get('height', 0),
                        'illustType': candidate.get('illustType', 0),
                        'xRestrict': candidate.get('xRestrict', 0),
                        'description': candidate.get('description', ''),
                        'createDate': candidate.get('createDate', ''),
                        'aiType': candidate.get('aiType', 0),
                        'profileImageUrl': candidate.get('profileImageUrl', ''),
                        'quality_score': quality_score,
                        'source': 'author_fallback'
                    }
                    
                    images.append(image_info)
                    score_text = f"{quality_score['total_score']}" if quality_score else "无评分"
                    print(f"🔄 降级选择 - ID: {candidate.get('id')}, 评分: {score_text} (原因: {failed_item['reason']})")
            
            # 第三阶段：如果仍然不足，直接从剩余作品中随机选择
            if len(images) < count:
                print(f"🔄 最终降级 - 仍然不足，从剩余作品中随机选择")
                
                # 获取未使用的作品
                remaining_illusts = [
                    illust for illust in illusts 
                    if illust.get('id') not in [img['id'] for img in images]
                ]
                
                needed = count - len(images)
                selected = random.sample(remaining_illusts, min(needed, len(remaining_illusts)))
                
                for candidate in selected:
                    image_info = {
                        'id': candidate.get('id', ''),
                        'title': candidate.get('title', ''),
                        'url': candidate.get('url', ''),
                        'tags': candidate.get('tags', []),
                        'userId': candidate.get('userId', ''),
                        'userName': candidate.get('userName', ''),
                        'pageCount': candidate.get('pageCount', 1),
                        'width': candidate.get('width', 0),
                        'height': candidate.get('height', 0),
                        'illustType': candidate.get('illustType', 0),
                        'xRestrict': candidate.get('xRestrict', 0),
                        'description': candidate.get('description', ''),
                        'createDate': candidate.get('createDate', ''),
                        'aiType': candidate.get('aiType', 0),
                        'profileImageUrl': candidate.get('profileImageUrl', ''),
                        'quality_score': None,
                        'source': 'author_final'
                    }
                    
                    images.append(image_info)
                    print(f"🔄 最终选择 - ID: {candidate.get('id')}, 无质量评分")
            
            print(f"作者随机模式完成 - 尝试 {attempts} 次，找到 {len(images)} 张图片")
            return images
            
        except Exception as e:
            print(f"获取作者随机图片异常: {e}")
            return []

    async def _get_author_recent_images(self, illusts: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
        """
        获取作者最新作品
        
        Args:
            illusts: 作者作品列表
            count: 需要的图片数量
            
        Returns:
            图片列表
        """
        try:
            # 按创建时间排序（最新的在前）
            sorted_illusts = sorted(
                illusts, 
                key=lambda x: x.get('createDate', ''), 
                reverse=True
            )
            
            # 选择最新的作品
            selected_count = min(count, len(sorted_illusts))
            selected_illusts = sorted_illusts[:selected_count]
            
            print(f"作者最新作品模式完成 - 选择 {len(selected_illusts)} 张最新作品")
            
            # 构建图片信息
            images = []
            for candidate in selected_illusts:
                image_info = {
                    'id': candidate.get('id', ''),
                    'title': candidate.get('title', ''),
                    'url': candidate.get('url', ''),
                    'tags': candidate.get('tags', []),
                    'userId': candidate.get('userId', ''),
                    'userName': candidate.get('userName', ''),
                    'pageCount': candidate.get('pageCount', 1),
                    'width': candidate.get('width', 0),
                    'height': candidate.get('height', 0),
                    'illustType': candidate.get('illustType', 0),
                    'xRestrict': candidate.get('xRestrict', 0),
                    'description': candidate.get('description', ''),
                    'createDate': candidate.get('createDate', ''),
                    'aiType': candidate.get('aiType', 0),
                    'profileImageUrl': candidate.get('profileImageUrl', ''),
                    'quality_score': None,  # 最新作品不计算质量评分
                    'source': 'author_recent'
                }
                images.append(image_info)
            
            return images
            
        except Exception as e:
            print(f"获取作者最新作品异常: {e}")
            return []

    async def _get_author_popular_images(self, illusts: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
        """
        获取作者热门作品
        
        Args:
            illusts: 作者作品列表
            count: 需要的图片数量
            
        Returns:
            图片列表
        """
        try:
            # 按收藏数排序（收藏数多的在前）
            sorted_illusts = sorted(
                illusts, 
                key=lambda x: x.get('bookmarkCount', 0), 
                reverse=True
            )
            
            # 选择最热门的作品
            selected_count = min(count, len(sorted_illusts))
            selected_illusts = sorted_illusts[:selected_count]
            
            print(f"作者热门作品模式完成 - 选择 {len(selected_illusts)} 张热门作品")
            
            # 构建图片信息
            images = []
            for candidate in selected_illusts:
                image_info = {
                    'id': candidate.get('id', ''),
                    'title': candidate.get('title', ''),
                    'url': candidate.get('url', ''),
                    'tags': candidate.get('tags', []),
                    'userId': candidate.get('userId', ''),
                    'userName': candidate.get('userName', ''),
                    'pageCount': candidate.get('pageCount', 1),
                    'width': candidate.get('width', 0),
                    'height': candidate.get('height', 0),
                    'illustType': candidate.get('illustType', 0),
                    'xRestrict': candidate.get('xRestrict', 0),
                    'description': candidate.get('description', ''),
                    'createDate': candidate.get('createDate', ''),
                    'aiType': candidate.get('aiType', 0),
                    'profileImageUrl': candidate.get('profileImageUrl', ''),
                    'quality_score': None,  # 热门作品不计算质量评分
                    'source': 'author_popular'
                }
                images.append(image_info)
            
            return images
            
        except Exception as e:
            print(f"获取作者热门作品异常: {e}")
            return []
