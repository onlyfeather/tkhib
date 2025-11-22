import asyncio
import json
import base64
import httpx
import pickle
import os
import random
from ddddocr import DdddOcr
from typing import Optional, Dict, Any, List, Set, Union
from io import BytesIO


class PixivSpider:
    """Pixiv爬虫类，支持验证码登录"""
    
    def __init__(self, token_file: str = "pixiv_token.pkl"):
        self.session = None
        self.ocr = DdddOcr(show_ad=False)
        self.base_url = "https://api.pixivic.com"
        self.token_file = token_file
        self.authorization_token = None
        self.is_logged_in = False
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Content-Type': 'application/json',
            'Origin': 'https://www.pixivic.com',
            'Referer': 'https://www.pixivic.com/'
        }
        
        # Tag池配置
        self.preferred_tags_file = "preferred_tags.pkl"
        self.blocked_tags_file = "blocked_tags.pkl"
        self.preferred_tags: Set[str] = set()
        self.blocked_tags: Set[str] = set()
        
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
        
    def load_token(self) -> bool:
        """加载Authorization Token和用户ID"""
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'rb') as f:
                    token_data = pickle.load(f)
                    self.authorization_token = token_data.get('token')
                    self.user_id = token_data.get('id')
                    self.is_logged_in = bool(self.authorization_token)
                print(f"已加载Token: {'有效' if self.authorization_token else '无效'}")
                if self.user_id:
                    print(f"已加载用户ID: {self.user_id}")
                return True
            except Exception as e:
                print(f"加载Token失败: {e}")
                return False
        return False
    
    def save_token(self, token: str, user_id: Optional[str] = None) -> bool:
        """保存Authorization Token和用户ID"""
        try:
            token_data = {'token': token}
            if user_id:
                token_data['id'] = user_id
                self.user_id = user_id
            
            with open(self.token_file, 'wb') as f:
                pickle.dump(token_data, f)
            self.authorization_token = token
            self.is_logged_in = True
            print("Token保存成功")
            return True
        except Exception as e:
            print(f"保存Token失败: {e}")
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
    
    def filter_illustrations_by_tags(self, illustrations_data: Dict[str, Any]) -> Dict[str, Any]:
        """根据厌恶tag池过滤图片"""
        try:
            if not isinstance(illustrations_data, dict) or "data" not in illustrations_data:
                return illustrations_data
            
            if not self.blocked_tags:
                print("厌恶tag池为空，跳过过滤")
                return illustrations_data
            
            filtered_data = []
            filtered_count = 0
            
            for illust in illustrations_data["data"]:
                # 获取图片的tags
                illust_tags = set()
                if 'tags' in illust:
                    tags_data = illust['tags']
                    # 处理不同类型的tags数据
                    if isinstance(tags_data, list):
                        for tag in tags_data:
                            if isinstance(tag, str):
                                illust_tags.add(tag.strip().lower())
                            elif isinstance(tag, dict):
                                # 如果tag是字典，尝试获取多个字段
                                tag_name = None
                                if 'name' in tag:
                                    tag_name = str(tag['name']).strip().lower()
                                    illust_tags.add(tag_name)
                                if 'tag' in tag:
                                    tag_name = str(tag['tag']).strip().lower()
                                    illust_tags.add(tag_name)
                                if 'translatedName' in tag:
                                    translated_name = str(tag['translatedName']).strip().lower()
                                    illust_tags.add(translated_name)
                                # 如果都没有，尝试转换为字符串
                                if not tag_name:
                                    tag_str = str(tag).strip().lower()
                                    illust_tags.add(tag_str)
                    elif isinstance(tags_data, str):
                        # 如果tags是字符串，按逗号分割
                        illust_tags = {tag.strip().lower() for tag in tags_data.split(',')}
                    else:
                        print(f"未知的tags数据类型: {type(tags_data)}")
                
                # 检查是否包含厌恶tag（使用完全匹配，忽略大小写）
                has_blocked_tag = False
                matched_blocked_tag = None
                for blocked_tag in self.blocked_tags:
                    blocked_tag_lower = blocked_tag.strip().lower()
                    for illust_tag in illust_tags:
                        # 使用完全匹配：只有当厌恶tag与图片tag完全相同时才过滤
                        if blocked_tag_lower == illust_tag.lower():
                            has_blocked_tag = True
                            matched_blocked_tag = blocked_tag
                            print(f"过滤图片: {illust.get('title', '无标题')} - 完全匹配厌恶tag: {blocked_tag}")
                            break
                    if has_blocked_tag:
                        break
                
                if not has_blocked_tag:
                    filtered_data.append(illust)
                else:
                    filtered_count += 1
            
            print(f"过滤完成: 过滤了 {filtered_count} 张图片，保留 {len(filtered_data)} 张")
            
            # 返回过滤后的数据
            result = illustrations_data.copy()
            result["data"] = filtered_data
            return result
            
        except Exception as e:
            print(f"过滤图片异常: {e}")
            return illustrations_data
    
    def validate_image_tags(self, image_data: Dict[str, Any], search_tags: Union[str, List[str]]) -> bool:
        """
        验证图片是否包含搜索标签（支持多tag搜索）
        
        Args:
            image_data: 图片数据
            search_tags: 搜索的标签，可以是字符串（单tag）或列表（多tag）
            
        Returns:
            True如果图片包含搜索标签，False否则
        """
        try:
            # 处理搜索标签
            if isinstance(search_tags, str):
                search_tags_list = [search_tags] if search_tags and search_tags.strip() else []
            elif isinstance(search_tags, list):
                search_tags_list = [tag for tag in search_tags if tag and tag.strip()]
            else:
                search_tags_list = []
            
            if not search_tags_list:
                return True  # 如果没有搜索标签，默认通过
            
            # 提取图片的tags
            image_tags = set()
            if 'tags' in image_data:
                tags_data = image_data['tags']
                # 处理不同类型的tags数据
                if isinstance(tags_data, list):
                    for tag in tags_data:
                        if isinstance(tag, str):
                            image_tags.add(tag.strip().lower())
                        elif isinstance(tag, dict):
                            # 如果tag是字典，尝试获取多个字段
                            if 'name' in tag:
                                image_tags.add(str(tag['name']).strip().lower())
                            if 'tag' in tag:
                                image_tags.add(str(tag['tag']).strip().lower())
                            if 'translatedName' in tag:
                                image_tags.add(str(tag['translatedName']).strip().lower())
                            # 如果都没有，尝试转换为字符串
                            else:
                                image_tags.add(str(tag).strip().lower())
                elif isinstance(tags_data, str):
                    image_tags = {tag.strip().lower() for tag in tags_data.split(',')}
            
            # 检查是否匹配所有搜索标签（AND逻辑）
            matched_tags = []
            for search_tag in search_tags_list:
                search_tag_lower = search_tag.strip().lower()
                found_match = False
                
                for image_tag in image_tags:
                    if search_tag_lower == image_tag.lower():
                        matched_tags.append(search_tag)
                        found_match = True
                        break
                
                if not found_match:
                    print(f"✗ 标签不匹配: {image_data.get('title', '无标题')} - 搜索标签'{search_tag}' 未在图片标签中找到")
                    print(f"   图片标签: {list(image_tags)}")
                    return False
            
            # 所有搜索标签都匹配
            print(f"✓ 标签匹配: {image_data.get('title', '无标题')} - 匹配搜索标签: {matched_tags}")
            return True
            
        except Exception as e:
            print(f"验证图片标签异常: {e}")
            return False  # 出错时默认不通过，确保质量

    def get_tag_pools_info(self) -> Dict[str, Any]:
        """获取tag池信息"""
        return {
            'preferred_tags': list(self.preferred_tags),
            'blocked_tags': list(self.blocked_tags),
            'preferred_count': len(self.preferred_tags),
            'blocked_count': len(self.blocked_tags)
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 加载已保存的Token
        self.load_token()
        
        # 加载tag池配置
        self.load_tag_pools()
        
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
    
    async def get_verification_code(self) -> Optional[Dict[str, Any]]:
        """
        获取验证码
        
        Returns:
            包含vid和imageBase64的字典，失败返回None
        """
        try:
            if not self.session:
                raise RuntimeError("Session not initialized")
                
            url = f"{self.base_url}/verificationCode"
            response = await self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            print(f"验证码获取响应: {data}")
            
            if data.get("message") == "验证码获取成功" and "data" in data:
                return data["data"]
            else:
                print(f"验证码获取失败: {data}")
                return None
                
        except Exception as e:
            print(f"获取验证码异常: {e}")
            return None
    
    def recognize_captcha(self, image_base64: str) -> Optional[str]:
        """
        识别验证码
        
        Args:
            image_base64: base64编码的图片数据
            
        Returns:
            识别出的验证码字符串，失败返回None
        """
        try:
            # 解码base64图片
            image_data = base64.b64decode(image_base64)
            
            # 使用ddddocr识别
            result = self.ocr.classification(image_data)
            
            # 确保返回字符串类型
            if isinstance(result, str):
                print(f"验证码识别结果: {result}")
                return result
            else:
                print(f"验证码识别结果类型错误: {type(result)}")
                return str(result) if result else None
            
        except Exception as e:
            print(f"验证码识别异常: {e}")
            return None
    
    async def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        执行登录流程（支持验证码识别重试）
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            登录成功返回token信息，失败返回None
        """
        max_retries = 10
        
        for attempt in range(max_retries):
            try:
                print(f"开始登录流程... (第 {attempt + 1}/{max_retries} 次尝试)")
                
                # 1. 获取验证码
                print("1. 获取验证码...")
                captcha_data = await self.get_verification_code()
                if not captcha_data:
                    print("获取验证码失败")
                    continue
                
                vid = captcha_data.get("vid")
                image_base64 = captcha_data.get("imageBase64")
                
                if not vid or not image_base64:
                    print("验证码数据不完整")
                    continue
                
                print(f"验证码VID: {vid}")
                
                # 2. 识别验证码
                print("2. 识别验证码...")
                captcha_value = self.recognize_captcha(image_base64)
                if not captcha_value:
                    print(f"验证码识别失败 (第 {attempt + 1} 次尝试)")
                    if attempt < max_retries - 1:
                        print("准备重试...")
                        continue
                    else:
                        print("已达到最大重试次数，登录失败")
                        return None
                
                print(f"识别的验证码: {captcha_value}")
                
                # 3. 执行登录
                print("3. 执行登录...")
                login_url = f"{self.base_url}/users/token?vid={vid}&value={captcha_value}"
                login_data = {
                    "username": username,
                    "password": password
                }
                
                if not self.session:
                    raise RuntimeError("Session not initialized")
                    
                response = await self.session.post(login_url, json=login_data)
                response.raise_for_status()
                
                login_result = response.json()
                print(f"登录响应: {login_result}")
                
                # 检查登录是否成功
                if login_result.get("message") == "登录成功":
                    # 从响应头中获取authorization token
                    token = response.headers.get('authorization') or response.headers.get('Authorization')
                    
                    # 从响应数据中获取id
                    user_id = None
                    if "data" in login_result and isinstance(login_result["data"], dict):
                        user_id = login_result["data"].get("id")
                    
                    if token:
                        # 保存token和用户ID
                        self.save_token(token, user_id)
                        print(f"成功保存token: {token[:50]}...")
                        print(f"Token数据结构: {token}")
                        
                        # 如果有id，也保存id信息
                        if user_id:
                            print(f"用户ID: {user_id}")
                    else:
                        print("未在响应头中找到authorization token")
                        print(f"响应头内容: {dict(response.headers)}")
                        
                    self.is_logged_in = True
                    print("登录成功！")
                    
                    # 返回包含token和id的数据
                    result_data = {"token": token}
                    if user_id:
                        result_data["id"] = user_id
                    return result_data
                else:
                    print(f"登录失败: {login_result.get('message', '未知错误')}")
                    if attempt < max_retries - 1:
                        print("准备重试...")
                        continue
                    else:
                        print("已达到最大重试次数，登录失败")
                        return None
                        
            except Exception as e:
                print(f"登录过程异常 (第 {attempt + 1} 次尝试): {e}")
                if attempt < max_retries - 1:
                    print("准备重试...")
                    continue
                else:
                    print("已达到最大重试次数，登录失败")
                    return None
        
        return None
    
    async def get_user_info(self, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取用户信息（需要token）
        
        Args:
            token: 登录获得的token，如果为None则使用保存的token
            
        Returns:
            用户信息字典，失败返回None
        """
        try:
            # 使用传入的token或保存的token
            use_token = token or self.authorization_token
            if not use_token:
                print("没有可用的token")
                return None
                
            # 使用保存的用户ID或传入的token对应的用户ID
            user_id = getattr(self, 'user_id', None)
            if not user_id:
                print("没有可用的用户ID")
                return None
                
            # 设置认证头
            headers = self.headers.copy()
            headers['Authorization'] = use_token
            
            url = f"{self.base_url}/users/{user_id}"
            
            if not self.session:
                raise RuntimeError("Session not initialized")
                
            response = await self.session.get(url, headers=headers)
            response.raise_for_status()
            
            user_info = response.json()
            print(f"用户信息: {user_info}")
            
            return user_info
            
        except Exception as e:
            print(f"获取用户信息异常: {e}")
            return None
    
    async def search_illustrations(self, tag: Union[str, List[str]], page: int = 1, page_size: int = 30) -> Optional[Dict[str, Any]]:
        """
        根据tag搜索图片（支持多tag搜索）
        
        Args:
            tag: 搜索标签，可以是字符串（单tag）或列表（多tag）
            page: 页码，默认为1
            page_size: 每页数量，默认为30
            
        Returns:
            图片数据字典，失败返回None
        """
        try:
            # 检查是否有可用的token
            if not self.authorization_token:
                print("没有可用的authorization token，无法搜索图片")
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
            
            # 构建URL
            url = f"{self.base_url}/illustrations"
            params = {
                'illustType': 'illust',
                'searchType': 'original',
                'maxSanityLevel': 3,
                'page': page,
                'keyword': search_keyword,
                'pageSize': page_size
            }
            
            # 设置认证头
            headers = self.headers.copy()
            headers['Authorization'] = self.authorization_token
            
            if not self.session:
                raise RuntimeError("Session not initialized")
            
            print(f"搜索图片 - 关键词: '{search_keyword}', 页码: {page}, 每页数量: {page_size}")
            print(f"请求URL: {url}")
            print(f"请求参数: {params}")
            print(f"使用Authorization: {self.authorization_token[:50]}...")
            
            response = await self.session.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            illustrations_data = response.json()
            print(f"搜索结果: {illustrations_data}")
            
            return illustrations_data
            
        except Exception as e:
            print(f"搜索图片异常: {e}")
            return None
    
    async def search_illustrations_with_filter(self, tag: Optional[Union[str, List[str]]] = None, page: int = 1, page_size: int = 30, 
                                        apply_filter: bool = True) -> Optional[Dict[str, Any]]:
        """
        搜索图片并应用tag过滤（支持多tag搜索）
        
        Args:
            tag: 搜索标签，可以是字符串（单tag）、列表（多tag），如果为None则从喜好tag池随机选择
            page: 页码，默认为1
            page_size: 每页数量，默认为30
            apply_filter: 是否应用厌恶tag过滤，默认为True
            
        Returns:
            过滤后的图片数据字典，失败返回None
        """
        try:
            # 如果没有指定tag，从喜好tag池随机选择
            if not tag:
                random_tag = self.get_random_preferred_tag()
                if not random_tag:
                    print("无法从喜好tag池中选择tag，使用默认标签")
                    tag = "风景"
                else:
                    tag = random_tag
                    print(f"从喜好tag池随机选择: {tag}")
            
            # 搜索图片
            illustrations_data = await self.search_illustrations(tag, page, page_size)
            if not illustrations_data:
                return None
            
            # 应用tag过滤
            if apply_filter:
                filtered_data = self.filter_illustrations_by_tags(illustrations_data)
                return filtered_data
            else:
                print("跳过tag过滤")
                return illustrations_data
                
        except Exception as e:
            print(f"搜索并过滤图片异常: {e}")
            return None
    
    async def get_daily_image(self, page_size: int = 10) -> Optional[Dict[str, Any]]:
        """
        获取每日一图（从喜好tag池随机选择tag并过滤）
        
        Args:
            page_size: 搜索的图片数量，默认为10张
            
        Returns:
            随机选择的图片信息，失败返回None
        """
        try:
            print("=== 每日一图功能 ===")
            
            # 先获取要使用的tag
            search_tag = self.get_random_preferred_tag()
            if not search_tag:
                print("无法从喜好tag池中选择tag，使用默认标签")
                search_tag = "风景"
            
            print(f"使用搜索标签: {search_tag}")
            
            # 搜索并过滤图片
            filtered_data = await self.search_illustrations_with_filter(
                tag=search_tag,  # 使用确定的tag
                page=1,
                page_size=page_size,
                apply_filter=True  # 应用厌恶tag过滤
            )
            
            if not filtered_data or not filtered_data.get("data"):
                print("未获取到有效图片数据")
                return None
            
            # 从过滤后的图片中随机选择一张
            available_images = filtered_data["data"]
            if not available_images:
                print("过滤后没有可用图片")
                return None
            
            selected_image = random.choice(available_images)
            print(f"随机选择图片: {selected_image.get('title', '无标题')}")
            
            # 提取图片URL
            image_urls = self.extract_original_urls({"data": [selected_image]}, reconstruct_domain=True)
            
            if image_urls:
                return {
                    'image_info': selected_image,
                    'urls': image_urls[0] if image_urls else None,
                    'search_tag': search_tag  # 使用实际搜索的tag
                }
            else:
                print("提取图片URL失败")
                return None
                
        except Exception as e:
            print(f"获取每日一图异常: {e}")
            return None
    
    async def search_with_tag_management(self, tag: Optional[str] = None, use_filter: bool = True, 
                                   page_size: int = 30) -> Optional[list]:
        """
        完整的搜索流程，包含tag池管理和过滤
        
        Args:
            tag: 搜索标签，如果为None则从喜好tag池随机选择
            use_filter: 是否使用厌恶tag过滤
            page_size: 每页数量
            
        Returns:
            提取后的图片URL列表
        """
        try:
            # 搜索并过滤
            filtered_data = await self.search_illustrations_with_filter(
                tag=tag,
                page=1,
                page_size=page_size,
                apply_filter=use_filter
            )
            
            if not filtered_data:
                return None
            
            # 提取URL
            image_urls = self.extract_original_urls(filtered_data, reconstruct_domain=True)
            
            return image_urls
            
        except Exception as e:
            print(f"完整搜索流程异常: {e}")
            return None
    
    async def get_random_images_by_multi_tags(self, tags: List[str], count: int, use_filter: bool = True, reject_manga: bool = False) -> Optional[List[Dict[str, Any]]]:
        """
        根据多个tag获取指定数量的随机图片（专门的多tag搜索方法）
        
        Args:
            tags: 搜索标签列表
            count: 需要的图片数量
            use_filter: 是否使用厌恶tag过滤，默认为True
            reject_manga: 是否拒绝组图，仅接受单图，默认为True
            
        Returns:
            随机选择的图片信息列表，每个元素包含图片信息和URL，失败返回None
        """
        try:
            print(f"=== 多tag随机图片功能 ===")
            print(f"搜索标签: {tags}, 需要数量: {count}, 拒绝组图: {reject_manga}")
            
            # 参数验证
            if not tags or not isinstance(tags, list):
                print("搜索标签必须是非空列表")
                return None
            
            # 过滤空标签
            valid_tags = [tag.strip() for tag in tags if tag and tag.strip()]
            if not valid_tags:
                print("没有有效的搜索标签")
                return None
            
            print(f"有效搜索标签: {valid_tags}")
            
            # 调用通用的随机图片方法
            return await self.get_random_images_by_tag(
                tag=valid_tags,
                count=count,
                use_filter=use_filter,
                reject_manga=reject_manga
            )
            
        except Exception as e:
            print(f"多tag随机图片异常: {e}")
            return None

    async def get_random_images_by_tag(self, tag: Union[str, List[str]], count: int, use_filter: bool = True, reject_manga: bool = False) -> Optional[List[Dict[str, Any]]]:
        """
        根据指定tag获取指定数量的随机图片（批量获取+随机选择优化版，支持多tag搜索）
        
        Args:
            tag: 搜索标签，可以是字符串（单tag）或列表（多tag）
            count: 需要的图片数量
            use_filter: 是否使用厌恶tag过滤，默认为True
            reject_manga: 是否拒绝组图，仅接受单图，默认为True
            
        Returns:
            随机选择的图片信息列表，每个元素包含图片信息和URL，失败返回None
        """
        try:
            print(f"=== 获取随机图片功能（批量优化模式） ===")
            print(f"搜索标签: {tag}, 需要数量: {count}, 拒绝组图: {reject_manga}")
            
            # 参数验证
            if isinstance(tag, str):
                if not tag or not tag.strip():
                    print("搜索标签不能为空")
                    return None
            elif isinstance(tag, list):
                if not tag or not any(t and t.strip() for t in tag):
                    print("搜索标签列表不能为空")
                    return None
            else:
                print("搜索标签类型错误")
                return None
            
            if count <= 0:
                print("图片数量必须大于0")
                return None
            
            # 限制最大数量
            max_count = 50
            if count > max_count:
                print(f"图片数量过多，限制为最大值: {max_count}")
                count = max_count
            
            # 计算需要获取的批量数据量
            # 为了确保有足够的图片选择，获取数量是需求的3-5倍
            batch_multiplier = 4 if reject_manga else 2  # 如果拒绝组图，需要更多候选；允许组图时减少候选
            batch_size = min(count * batch_multiplier, 100)  # 最多获取100张
            
            print(f"批量获取策略: 目标{count}张，批量获取{batch_size}张候选")
            
            # 随机选择几个页码进行批量获取
            # 根据需要的批量大小决定页数
            pages_needed = max(1, (batch_size + 29) // 30)  # 每页最多30张
            max_page = 100  # 初始页码估计
            
            all_images = []
            collected_ids = set()  # 用于去重
            retry_count = 0
            max_retries = 20  # 最大重试次数
            previous_batch_start = 0  # 记录上一轮的图片数量
            sequential_mode = False  # 标记是否进入顺序遍历模式
            current_sequential_page = 1  # 顺序遍历的当前页码
            
            while len(all_images) < batch_size and retry_count < max_retries:
                page_success = False  # 标记本轮是否成功获取到图片
                
                for page_num in range(pages_needed):
                    if len(all_images) >= batch_size:
                        break
                        
                    # 根据模式选择页码
                    if sequential_mode:
                        # 顺序遍历模式：从第1页开始依次遍历
                        page_to_fetch = current_sequential_page
                        print(f"顺序遍历第 {page_num + 1}/{pages_needed} 页，页码: {page_to_fetch}")
                        current_sequential_page += 1
                    else:
                        # 随机选择页码，避免重复
                        page_to_fetch = random.randint(1, max_page)
                        print(f"随机获取第 {page_num + 1}/{pages_needed} 页，页码: {page_to_fetch} (最大页码: {max_page})")
                    
                    try:
                        # 批量搜索
                        search_data = await self.search_illustrations_with_filter(
                            tag=tag,
                            page=page_to_fetch,
                            page_size=30,  # 每页获取30张（最大值）
                            apply_filter=use_filter
                        )
                        
                        if not search_data or not search_data.get("data"):
                            print(f"第 {page_to_fetch} 页未获取到有效数据")
                            continue
                        
                        page_images = search_data["data"]
                        if not page_images:
                            print(f"第 {page_to_fetch} 页没有图片")
                            continue
                        
                        print(f"第 {page_to_fetch} 页获取到 {len(page_images)} 张图片")
                        page_success = True  # 标记成功获取到数据
                        
                        # 处理当前页的图片
                        for image_data in page_images:
                            image_id = image_data.get('id')
                            
                            # 去重检查
                            if image_id and image_id in collected_ids:
                                continue
                            
                            # 验证图片是否包含搜索标签
                            if not self.validate_image_tags(image_data, tag):
                                print(f"跳过不匹配标签的图片: {image_data.get('title', '无标题')} (搜索标签: {tag})")
                                continue
                            
                            # 检查是否为组图
                            page_count = image_data.get('pageCount', 1)
                            is_manga = page_count > 1
                            
                            if reject_manga and is_manga:
                                print(f"跳过组图: {image_data.get('title', '无标题')} (共{page_count}页)")
                                continue
                            
                            # 提取图片URL信息
                            image_urls = self.extract_original_urls({"data": [image_data]}, reconstruct_domain=True)
                            
                            if not image_urls:
                                print(f"提取URL失败: {image_data.get('title', '无标题')}")
                                continue
                            
                            # 创建图片信息
                            image_info = {
                                'image_data': image_data,
                                'urls': image_urls[0],
                                'search_tag': tag,
                                'page_found': page_to_fetch,
                                'batch_page': page_num + 1
                            }
                            
                            all_images.append(image_info)
                            if image_id:
                                collected_ids.add(image_id)
                    
                    except Exception as e:
                        print(f"搜索第 {page_to_fetch} 页时发生异常: {e}")
                        continue  # 异常时跳过当前页，继续下一页
                
                # 检查本轮是否添加了图片，如果没有则缩小最大页码范围
                current_batch_start = len(all_images)
                if current_batch_start == previous_batch_start and retry_count < max_retries - 1:
                    old_max_page = max_page
                    max_page = max(1, max_page // 2)  # 确保max_page至少为1
                    print(f"本轮未添加任何新图片，缩小页码范围至 {max_page}")
                    
                    # 如果页码缩小到1，说明图片比较少，切换到顺序遍历模式
                    if max_page == 1 and old_max_page > 1:
                        sequential_mode = True
                        current_sequential_page = 1
                        print("页码范围缩小至1，切换到顺序遍历模式，从第1页开始遍历所有图片")
                    
                    retry_count += 1
                previous_batch_start = current_batch_start
                
                # 如果已经收集到足够的候选图片，提前结束
                if len(all_images) >= batch_size:
                    print(f"已收集到足够的候选图片 ({len(all_images)}张)，提前结束批量获取")
                    break
                
                # 检查是否需要重试
                if len(all_images) < batch_size:
                    if retry_count < max_retries:
                        retry_count += 1
                        if not page_success:
                            # 如果本轮完全没有获取到数据，缩小页码范围
                            max_page = max(1, max_page // 2)  # 确保max_page至少为1
                            print(f"本轮未获取到有效数据，缩小页码范围至 {max_page}，第 {retry_count} 次重试")
                        else:
                            print(f"当前轮次收集 {len(all_images)} 张，未达到目标 {batch_size} 张，第 {retry_count} 次重试")
                    else:
                        print(f"已达到最大重试次数 {max_retries}，结束批量获取")
                        break
                else:
                    break  # 达到目标，结束循环
            
            if not all_images:
                print("批量获取未获取到任何有效图片")
                return None
            
            print(f"批量获取完成，共收集到 {len(all_images)} 张候选图片")
            
            # 随机选择指定数量的图片
            if len(all_images) <= count:
                # 如果候选图片不够，全部返回
                selected_images = all_images
                print(f"候选图片数量不足，返回全部 {len(all_images)} 张")
            else:
                # 随机选择
                selected_images = random.sample(all_images, count)
                print(f"从 {len(all_images)} 张候选图片中随机选择了 {count} 张")
            
            # 为选中的图片添加选择信息
            for i, image_info in enumerate(selected_images, 1):
                image_info['selection_rank'] = i
                image_info['total_candidates'] = len(all_images)
                print(f"选中第 {i} 张: {image_info['urls'].get('title', '无标题')} - {image_info['urls'].get('artist', '未知作者')}")
            
            print(f"随机图片获取完成！批量获取 {pages_needed} 页，候选 {len(all_images)} 张，选中 {len(selected_images)} 张")
            
            return selected_images
            
        except Exception as e:
            print(f"获取随机图片异常: {e}")
            return None
    
    def reconstruct_url_domain(self, original_url: str, new_domain: str = "i.yuki.sh") -> str:
        """
        重构图片链接的域名
        
        Args:
            original_url: 原始图片链接
            new_domain: 新的域名，默认为 i.yuki.sh
            
        Returns:
            重构后的图片链接
        """
        try:
            if not original_url:
                return original_url
                
            # 解析URL，提取协议、路径等部分
            if original_url.startswith('http://'):
                protocol = 'http://'
                url_without_protocol = original_url[7:]
            elif original_url.startswith('https://'):
                protocol = 'https://'
                url_without_protocol = original_url[8:]
            else:
                # 如果没有协议，假设是https
                protocol = 'https://'
                url_without_protocol = original_url
            
            # 找到第一个斜杠的位置，分离域名和路径
            slash_index = url_without_protocol.find('/')
            if slash_index != -1:
                path = url_without_protocol[slash_index:]
                # 重构为新的域名
                new_url = f"{protocol}{new_domain}{path}"
            else:
                # 如果没有路径，直接替换域名
                new_url = f"{protocol}{new_domain}"
            
            return new_url
            
        except Exception as e:
            print(f"重构URL域名异常: {e}")
            return original_url

    def extract_original_urls(self, illustrations_data: Dict[str, Any], reconstruct_domain: bool = True) -> list:
        """
        从搜索结果中提取所有original链接，支持组图
        
        Args:
            illustrations_data: 搜索返回的数据
            reconstruct_domain: 是否重构域名为 i.yuki.sh，默认为 True
            
        Returns:
            包含图片信息和重构后链接的列表，组图会返回多个URL
        """
        original_urls = []
        
        try:
            if isinstance(illustrations_data, dict) and "data" in illustrations_data:
                for illust in illustrations_data["data"]:
                    title = illust.get('title', '无标题')
                    
                    # 正确提取作者信息 - 从artistPreView字段获取
                    artist_info = illust.get('artistPreView', {})
                    if isinstance(artist_info, dict):
                        artist_name = artist_info.get('name', '未知作者')
                        artist_id = artist_info.get('id')
                    else:
                        # 兼容旧的artist字段
                        artist_data = illust.get('artist', {})
                        if isinstance(artist_data, dict):
                            artist_name = artist_data.get('name', '未知作者')
                            artist_id = artist_data.get('id')
                        else:
                            artist_name = '未知作者'
                            artist_id = None
                    
                    illust_id = illust.get('id', '未知ID')
                    page_count = illust.get('pageCount', 1)  # 获取页数，默认为1
                    
                    # 提取图片的tags
                    illust_tags = set()
                    if 'tags' in illust:
                        tags_data = illust['tags']
                        # 处理不同类型的tags数据
                        if isinstance(tags_data, list):
                            for tag in tags_data:
                                if isinstance(tag, str):
                                    illust_tags.add(tag.strip())
                                elif isinstance(tag, dict):
                                    # 如果tag是字典，尝试获取多个字段
                                    if 'name' in tag:
                                        illust_tags.add(str(tag['name']).strip())
                                    if 'tag' in tag:
                                        illust_tags.add(str(tag['tag']).strip())
                                    if 'translatedName' in tag:
                                        illust_tags.add(str(tag['translatedName']).strip())
                                    # 如果都没有，尝试转换为字符串
                                    else:
                                        illust_tags.add(str(tag).strip())
                        elif isinstance(tags_data, str):
                            illust_tags = {tag.strip() for tag in tags_data.split(',')}
                    
                    # 检查是否为组图
                    is_manga = page_count > 1
                    
                    if is_manga:
                        print(f"检测到组图: {title} - {artist_name} (共{page_count}页)")
                        # 组图处理：获取所有页面的图片
                        manga_urls = []
                        if 'imageUrls' in illust and isinstance(illust['imageUrls'], list):
                            for page_data in illust['imageUrls']:
                                if isinstance(page_data, dict) and 'original' in page_data:
                                    original_url = page_data['original']
                                    reconstructed_url = None
                                    if original_url and reconstruct_domain:
                                        reconstructed_url = self.reconstruct_url_domain(original_url)
                                    else:
                                        reconstructed_url = original_url
                                    
                                    manga_urls.append({
                                        'page': len(manga_urls) + 1,
                                        'original_url': original_url,
                                        'reconstructed_url': reconstructed_url
                                    })
                        
                        # 为组图创建一个包含所有页面URL的条目
                        if manga_urls:
                            image_info = {
                                'id': illust_id,
                                'title': title,
                                'artist': artist_name,
                                'artist_id': artist_id,
                                'is_manga': True,
                                'page_count': page_count,
                                'pages': manga_urls,
                                'tags': illust_tags  # 添加tags信息
                            }
                            original_urls.append(image_info)
                            
                            print(f"   提取到 {len(manga_urls)} 个图片URL")
                            for page_info in manga_urls:
                                print(f"     第{page_info['page']}页: {page_info['original_url']}")
                                if reconstruct_domain:
                                    print(f"     重构: {page_info['reconstructed_url']}")
                        else:
                            print(f"   组图但未找到图片URL: {title}")
                    else:
                        # 单图处理
                        original_url = None
                        if 'imageUrls' in illust and isinstance(illust['imageUrls'], list) and len(illust['imageUrls']) > 0:
                            image_url_obj = illust['imageUrls'][0]
                            if isinstance(image_url_obj, dict) and 'original' in image_url_obj:
                                original_url = image_url_obj['original']
                        
                        # 重构域名
                        reconstructed_url = None
                        if original_url and reconstruct_domain:
                            reconstructed_url = self.reconstruct_url_domain(original_url)
                        else:
                            reconstructed_url = original_url
                        
                        image_info = {
                            'id': illust_id,
                            'title': title,
                            'artist': artist_name,
                            'artist_id': artist_id,
                            'is_manga': False,
                            'page_count': 1,
                            'original_url': original_url,
                            'reconstructed_url': reconstructed_url,
                            'tags': illust_tags  # 添加tags信息
                        }
                        
                        if original_url:
                            original_urls.append(image_info)
                            print(f"提取到单图: {title} - {artist_name}")
                            print(f"   原始链接: {original_url}")
                            if reconstruct_domain:
                                print(f"   重构链接: {reconstructed_url}")
                        else:
                            print(f"未找到原图链接: {title} - {artist_name}")
                        
        except Exception as e:
            print(f"提取original链接异常: {e}")
            
        return original_urls
