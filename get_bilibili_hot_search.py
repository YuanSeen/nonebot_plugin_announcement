"""
获取B站热搜榜
"""
from ys_bot.plugins.nonebot_plugin_announcement.an_utils import get_common_headers, make_request, print_hot_list
from . import an_utils

def get_bilibili_hot_search() -> list:
    """
    获取B站热搜榜前十

    Returns:
        热搜列表
    """
    try:
        url = "https://api.bilibili.com/x/web-interface/search/square?limit=10"

        headers = get_common_headers()
        headers['Referer'] = 'https://www.bilibili.com/'

        data = make_request(url, headers)

        if not data:
            return []

        if data.get('code') != 0:
            raise Exception(f"API返回错误: {data.get('code')} - {data.get('message', '未知错误')}")

        hot_searches = data.get('data', {}).get('trending', {}).get('list', [])[:10]

        result_list = []
        for i, item in enumerate(hot_searches, 1):
            result_list.append({
                'rank': i,
                'word': item.get('keyword', '未知'),
                'hot_value': '',
                'label': ''
            })

        return result_list

    except Exception as e:
        raise Exception(f"获取B站热搜失败: {str(e)}")


if __name__ == "__main__":
    try:
        result = get_bilibili_hot_search()
        if result:
            print_hot_list('bilibili', result)
        else:
            print("未获取到B站热搜数据")
    except Exception as e:
        print(f"错误: {str(e)}")