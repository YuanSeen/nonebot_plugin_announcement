"""
通用工具模块
包含网络请求、错误处理等通用功能
"""
import requests
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any


def make_request(
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 10
) -> Optional[Dict[str, Any]]:
    """
    发送HTTP GET请求并返回JSON数据

    Args:
        url: 请求URL
        headers: 请求头
        params: 查询参数
        timeout: 超时时间

    Returns:
        JSON数据字典或None
    """
    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
    except json.JSONDecodeError:
        print("JSON解析错误")
    except Exception as e:
        print(f"请求异常: {e}")

    return None


def format_time() -> str:
    """
    返回格式化的当前时间

    Returns:
        格式化的时间字符串
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def print_separator(length: int = 50, char: str = "=") -> None:
    """
    打印分隔线

    Args:
        length: 分隔线长度
        char: 分隔线字符
    """
    print(char * length)


def print_hot_item(rank: int, word: str, hot_value: str = "", label: str = "") -> None:
    """
    格式化打印热搜项目

    Args:
        rank: 排名
        word: 热搜词
        hot_value: 热度值
        label: 标签
    """
    rank_str = f"{rank:2d}"
    label_display = f"[{label}]" if label else ""
    hot_display = f"🔥 {hot_value}" if hot_value else ""

    print(f"{rank_str}. {word} {label_display} {hot_display}")


def get_common_headers() -> Dict[str, str]:
    """
    返回通用的请求头

    Returns:
        通用请求头字典
    """
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
    }


def print_hot_list(platform: str, hot_list: list, include_rank0: bool = False) -> None:
    """
    统一格式打印热搜列表

    Args:
        platform: 平台名称
        platform_icon: 平台图标
        hot_list: 热搜列表，每个元素包含 'rank', 'word', 'hot_value', 'label'
        include_rank0: 是否包含第0条（用于微博置顶）
    """
    platform_icons = {
        'weibo': '',
        'bilibili': '',
        'douyin': ''
    }

    icon = platform_icons.get(platform, '')

    print(f"{icon} {platform}热搜榜 {format_time()}")
    print_separator(60)

    if include_rank0:
        print(" 置顶热搜：")
        print_separator(60, "-")

        # 查找第0条（置顶）
        for item in hot_list:
            if item.get('rank', 1) == 0:
                word = item.get('word', '未知')
                hot_value = item.get('hot_value', '')
                label = item.get('label', '')
                print_hot_item(0, word, hot_value, label)
                break

        print(f"\n {platform}热搜TOP{len([item for item in hot_list if item.get('rank', 1) > 0])}:")
    else:
        print(f" {platform}热搜TOP{len(hot_list)}:")

    print_separator(60, "-")

    # 打印普通热搜（排除第0条）
    for item in hot_list:
        rank = item.get('rank', 0)
        if rank > 0:  # 只打印rank大于0的
            word = item.get('word', '未知')
            hot_value = item.get('hot_value', '')
            label = item.get('label', '')
            print_hot_item(rank, word, hot_value, label)