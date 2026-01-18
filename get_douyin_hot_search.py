"""
获取抖音热搜榜
"""
import json
import re
from typing import Optional, Dict, Any, List

from ys_bot.plugins.nonebot_plugin_announcement.an_utils import get_common_headers, make_request, print_hot_list
from . import an_utils

def get_douyin_api_configs() -> List[Dict[str, Any]]:
    """
    返回抖音API配置列表

    Returns:
        API配置列表，每个配置包含url和params
    """
    return [
        {
            'url': "https://www.douyin.com/aweme/v1/web/hot/search/list/",
            'params': {
                'device_platform': 'webapp',
                'aid': '6383',
                'channel': 'channel_pc_web',
                'detail_list': '1',
            }
        },
        {
            'url': "https://api.douyin.com/web/api/v1/hot/search/list/",
            'params': {}
        }
    ]


def get_douyin_headers() -> Dict[str, str]:
    """
    返回抖音专用请求头

    Returns:
        抖音请求头字典
    """
    headers = get_common_headers()
    headers.update({
        'Referer': 'https://www.douyin.com/',
        'Origin': 'https://www.douyin.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Upgrade-Insecure-Requests': '1',
    })
    return headers


def get_douyin_hot_search() -> Optional[Dict[str, Any]]:
    """
    获取抖音热搜数据

    Returns:
        热搜数据字典或None
    """
    try:
        headers = get_douyin_headers()
        api_configs = get_douyin_api_configs()

        for i, config in enumerate(api_configs, 1):
            data = make_request(config['url'], headers, config['params'])

            if data:
                return data

        raise Exception("所有API请求均失败")

    except Exception as e:
        raise Exception(f"获取抖音热搜数据失败: {str(e)}")


def parse_douyin_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    解析抖音热搜数据，返回统一格式的列表

    Args:
        data: 原始数据

    Returns:
        统一格式的热搜列表
    """
    if not data:
        return []

    hot_list = []

    # 格式1：标准格式
    if 'data' in data and 'word_list' in data['data']:
        hot_list = data['data']['word_list']
    # 格式2：其他可能格式
    elif 'data' in data and 'list' in data['data']:
        hot_list = data['data']['list']
    # 格式3：直接是列表
    elif isinstance(data.get('data'), list):
        hot_list = data['data']
    # 格式4：尝试查找所有可能的热搜字段
    else:
        hot_list = search_hot_items(data)

    return hot_list


def search_hot_items(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    在响应中搜索热搜数据

    Args:
        data: 原始数据

    Returns:
        热搜列表
    """
    try:
        data_str = json.dumps(data, ensure_ascii=False)

        # 搜索包含热度的字段
        word_patterns = [
            r'"word"\s*:\s*"([^"]+)"',
            r'"title"\s*:\s*"([^"]+)"',
            r'"name"\s*:\s*"([^"]+)"',
        ]

        for pattern in word_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                return [{'word': match} for match in matches[:20]]

        return []
    except Exception:
        return []


def get_douyin_hot_search_list() -> List[Dict[str, Any]]:
    """
    获取抖音热搜列表（主函数）

    Returns:
        统一格式的热搜列表
    """
    try:
        data = get_douyin_hot_search()

        if not data:
            return []

        hot_list = parse_douyin_data(data)

        if not hot_list:
            return []

        result_list = []
        for i, item in enumerate(hot_list[:10], 1):
            if isinstance(item, dict):
                word = item.get('word') or item.get('title') or item.get('name') or '未知'
                hot_value = item.get('hot_value') or item.get('hotValue') or item.get('value') or ''
                label = item.get('label') or item.get('tag') or ''

                # 格式化热度值
                if hot_value and isinstance(hot_value, (int, float)):
                    hot_value_str = f"{hot_value:,}"
                else:
                    hot_value_str = str(hot_value) if hot_value else ''

                result_list.append({
                    'rank': i,
                    'word': word,
                    'hot_value': hot_value_str,
                    'label': label
                })
            else:
                result_list.append({
                    'rank': i,
                    'word': str(item)[:50],
                    'hot_value': '',
                    'label': ''
                })

        return result_list

    except Exception as e:
        raise Exception(f"解析抖音热搜数据失败: {str(e)}")


if __name__ == "__main__":
    try:
        result = get_douyin_hot_search_list()
        if result:
            print_hot_list('douyin', result)
        else:
            print("未获取到抖音热搜数据")
    except Exception as e:
        print(f"错误: {str(e)}")