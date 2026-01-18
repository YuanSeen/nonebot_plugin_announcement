"""
获取微博热搜榜
"""
from ys_bot.plugins.nonebot_plugin_announcement import an_utils


def get_weibo_hot_search() -> list:
    """
    获取微博热搜榜

    Returns:
        热搜列表
    """
    try:
        url = "https://weibo.com/ajax/side/hotSearch"

        headers = an_utils.get_common_headers()
        headers['Referer'] = 'https://s.weibo.com/'

        data = an_utils.make_request(url, headers)

        if not data:
            return []

        # 获取热搜列表
        hot_searches = data.get('data', {}).get('realtime', [])

        if not hot_searches:
            return []

        # 处理置顶热搜
        hotgov = data.get('data', {}).get('hotgov', {})
        result_list = []

        # 如果有置顶热搜，作为第0条
        if hotgov:
            result_list.append({
                'rank': 0,
                'word': hotgov.get('word', ''),
                'hot_value': hotgov.get('num', ''),
                'label': '置顶'
            })

        # 处理普通热搜
        for i, item in enumerate(hot_searches[:10], 1):
            result_list.append({
                'rank': i,
                'word': item.get('word', ''),
                'hot_value': item.get('num', ''),
                'label': item.get('label_name', '')
            })

        return result_list

    except Exception as e:
        raise Exception(f"获取微博热搜失败: {str(e)}")


if __name__ == "__main__":
    try:
        result = get_weibo_hot_search()
        if result:
            an_utils.print_hot_list('weibo', result, include_rank0=any(item['rank'] == 0 for item in result))
        else:
            print("未获取到微博热搜数据")
    except Exception as e:
        print(f"错误: {str(e)}")