#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Cookie保存和用户信息验证功能
"""

import asyncio
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spiderPixiv import PixivSpider


async def test_cookie_save_and_verify():
    """测试Cookie保存和用户信息验证"""
    
    print("=" * 60)
    print("Cookie保存和用户信息验证测试")
    print("=" * 60)
    
    # 创建爬虫实例
    spider = PixivSpider(cookie_file="pixiv_cookie.pkl")
    
    # 用户输入Cookie字符串
    print("请输入从浏览器复制的Cookie字符串:")
    print("(提示: 在Pixiv网站登录后，按F12打开开发者工具，")
    print("       在Network标签页找到任意请求，复制Cookie头)")
    test_cookie = input("Cookie: ").strip()
    
    # 用户输入用户ID
    print("\n请输入用户ID:")
    test_user_id = input("用户ID: ").strip()
    
    if not test_cookie:
        print("✗ Cookie不能为空")
        return
    
    print("\n1. 测试第一次保存Cookie和用户ID")
    print("-" * 40)
    
    # 第一次保存Cookie和用户ID
    save_result = spider.save_cookie(
        cookie_string=test_cookie,
        user_id=test_user_id
    )
    
    if save_result:
        print("✓ Cookie和用户ID保存成功")
    else:
        print("✗ Cookie和用户ID保存失败")
        return
    
    print("\n2. 验证保存的数据")
    print("-" * 40)
    
    # 加载并验证保存的Cookie
    load_result = spider.load_cookie()
    if load_result:
        print(f"✓ Cookie加载成功")
        print(f"  - 用户ID: {spider.user_id}")
        print(f"  - 登录状态: {spider.is_logged_in}")
        print(f"  - 完整Cookie: {spider.full_cookie[:50]}...")
    else:
        print("✗ Cookie加载失败")
        return
    
    print("\n3. 测试用户信息API访问")
    print("-" * 40)
    
    # 使用异步上下文管理器
    try:
        async with spider:
            # 获取当前用户信息
            print("获取当前用户信息...")
            current_user_info = await spider.get_user_info()
            
            if current_user_info:
                print("✓ 当前用户信息获取成功")
                print(f"  - 用户名: {current_user_info.get('body', {}).get('name', '未知')}")
                print(f"  - 用户ID: {current_user_info.get('body', {}).get('userId', '未知')}")
                print(f"  - 头像: {current_user_info.get('body', {}).get('image', '无')}")
            else:
                print("✗ 当前用户信息获取失败")
            
            # 获取指定用户信息
            print(f"\n获取指定用户信息 (ID: {test_user_id})...")
            specified_user_info = await spider.get_user_info(user_id=test_user_id)
            
            if specified_user_info:
                print("✓ 指定用户信息获取成功")
                print(f"  - 用户名: {specified_user_info.get('body', {}).get('name', '未知')}")
                print(f"  - 用户ID: {specified_user_info.get('body', {}).get('userId', '未知')}")
                print(f"  - 头像: {specified_user_info.get('body', {}).get('image', '无')}")
            else:
                print("✗ 指定用户信息获取失败")
                
    except Exception as e:
        print(f"✗ API访问过程中发生异常: {e}")
    
    print("\n4. 测试更新Cookie（保留用户ID）")
    print("-" * 40)
    
    # 模拟更新Cookie（保留现有用户ID）
    new_cookie = "PHPSESSID=new_session_67890; login_ever=yes; p_ab_d_id=0987654321; p_ab_id=2; privacy_policy_agreement=1; device_token=new_device_token"
    
    update_result = spider.save_cookie(
        cookie_string=new_cookie,
        keep_existing_id=True  # 保留现有用户ID
    )
    
    if update_result:
        print("✓ Cookie更新成功（保留用户ID）")
        print(f"  - 用户ID: {spider.user_id}")
        print(f"  - 新Cookie: {spider.full_cookie[:50]}...")
    else:
        print("✗ Cookie更新失败")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


def test_manual_input():
    """手动输入测试"""
    print("=" * 60)
    print("手动输入Cookie和用户ID测试")
    print("=" * 60)
    
    spider = PixivSpider(cookie_file="pixiv_cookie.pkl")
    
    # 手动输入Cookie
    print("\n请输入从浏览器复制的Cookie字符串:")
    print("(提示: 在Pixiv网站登录后，按F12打开开发者工具，")
    print("       在Network标签页找到任意请求，复制Cookie头)")
    cookie_input = input("Cookie: ").strip()
    
    # 手动输入用户ID
    user_id_input = input("\n请输入用户ID: ").strip()
    
    if not cookie_input:
        print("✗ Cookie不能为空")
        return
    
    print("\n保存Cookie和用户ID...")
    save_result = spider.save_cookie(
        cookie_string=cookie_input,
        user_id=user_id_input if user_id_input else None
    )
    
    if save_result:
        print("✓ 保存成功")
        
        # 验证API访问
        print("\n验证API访问...")
        
        async def verify_api():
            async with spider:
                if user_id_input:
                    user_info = await spider.get_user_info(user_id=user_id_input)
                else:
                    user_info = await spider.get_user_info()
                
                if user_info:
                    print("✓ API访问成功")
                    body = user_info.get('body', {})
                    if body:
                        print(f"  - 用户名: {body.get('name', '未知')}")
                        print(f"  - 用户ID: {body.get('userId', '未知')}")
                    else:
                        print("  - 响应格式异常")
                    return True
                else:
                    print("✗ API访问失败")
                    return False
        
        # 运行异步验证
        success = asyncio.run(verify_api())
        
        if success:
            print("\n✓ 所有测试通过！Cookie和用户ID配置正确")
        else:
            print("\n✗ 测试失败，请检查Cookie和用户ID是否正确")
    else:
        print("✗ 保存失败")


if __name__ == "__main__":
    print("Cookie保存和用户信息验证测试")
    print("=" * 60)
    print("请使用真实的Pixiv Cookie和用户ID进行测试")
    print("=" * 60)
    
    # 直接运行手动输入测试
    test_manual_input()
