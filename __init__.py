"""热搜插件主模块"""
import time
from typing import Dict, List, Tuple

from nonebot import on_command
from nonebot.exception import FinishedException
from nonebot.params import CommandArg
from nonebot.adapters import Message, Event
from nonebot.plugin import PluginMetadata
from nonebot import get_plugin_config
from nonebot.log import logger

from .config import Config
from .get_bilibili_hot_search import get_bilibili_hot_search
from .get_weibo_hot_search import get_weibo_hot_search
from .get_douyin_hot_search import get_douyin_hot_search_list as get_douyin_hot_search

# 获取配置
config = get_plugin_config(Config)

# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="热搜查询",
    description="查询B站、微博、抖音等平台的热搜榜单",
    usage="""使用方式：
    B站热搜 [数量] - 查询B站热搜
    微博热搜 [数量] - 查询微博热搜
    抖音热搜 [数量] - 查询抖音热搜
    热搜状态 - 查看插件状态""",
    config=Config,
)

# 命令响应器
bilibili_hot = on_command("B站热搜", aliases={"b站热搜", "bilibili热搜"}, priority=10, block=True)
weibo_hot = on_command("微博热搜", aliases={"微博热搜榜","weibo热搜"}, priority=10, block=True)
douyin_hot = on_command("抖音热搜", aliases={"抖音热搜榜","douyin热搜"}, priority=10, block=True)
status_cmd = on_command("热搜状态", priority=10, block=True)

# 冷却时间存储 - 使用群号和QQ号
cooldown_data: Dict[str, Dict[str, float]] = {
    "group": {},      # 群聊冷却时间 {群号: 最后请求时间}
    "private": {}     # 私聊冷却时间 {QQ号: 最后请求时间}
}


class CooldownManager:
    """冷却时间管理器"""

    @staticmethod
    def get_identifiers(event: Event) -> Tuple[str, str]:
        """获取会话标识符"""
        try:
            # 获取用户ID
            user_id = str(event.get_user_id())

            # 判断是否是群聊
            if hasattr(event, "group_id") and event.group_id:
                group_id = str(event.group_id)
                return group_id, user_id
            else:
                return "", user_id  # 私聊时群号为空
        except Exception:
            return "", ""

    @staticmethod
    def check_cooldown(event: Event) -> Tuple[bool, int]:
        """检查冷却时间"""
        group_id, user_id = CooldownManager.get_identifiers(event)

        # 判断会话类型
        if group_id:  # 群聊
            session_type = "group"
            session_key = group_id  # 群聊按群号冷却
        else:  # 私聊
            session_type = "private"
            session_key = user_id  # 私聊按QQ号冷却

        now = time.time()
        last_time = cooldown_data[session_type].get(session_key, 0)

        if now - last_time < config.cooldown_time:
            remaining = int(config.cooldown_time - (now - last_time))
            return False, remaining

        return True, 0

    @staticmethod
    def update_cooldown(event: Event):
        """更新冷却时间"""
        group_id, user_id = CooldownManager.get_identifiers(event)

        # 判断会话类型
        if group_id:  # 群聊
            session_type = "group"
            session_key = group_id
        else:  # 私聊
            session_type = "private"
            session_key = user_id

        cooldown_data[session_type][session_key] = time.time()

    @staticmethod
    def clear_expired():
        """清理过期的冷却记录"""
        now = time.time()
        for session_type in cooldown_data:
            expired_keys = [
                key for key, last_time in cooldown_data[session_type].items()
                if now - last_time > config.cooldown_time * 10
            ]
            for key in expired_keys:
                del cooldown_data[session_type][key]


class HotSearchFormatter:
    """热搜格式化器"""

    @staticmethod
    def format_hot_search(platform: str, hot_list: List[Dict], count: int = 10) -> str:
        """格式化热搜列表为消息字符串"""
        platform_names = {
            "bilibili": " B站热搜",
            "weibo": " 微博热搜",
            "douyin": " 抖音热搜"
        }

        platform_name = platform_names.get(platform, platform)

        # 过滤空列表
        if not hot_list:
            return f"{platform_name} - 暂无数据"

        # 限制显示数量
        display_list = hot_list[:count]

        # 构建消息
        lines = [f"{platform_name} TOP{len(display_list)}"]
        lines.append("=" * 30)

        for item in display_list:
            rank = item.get('rank', 0)
            word = item.get('word', '未知')
            # hot_value = item.get('hot_value', '')
            label = item.get('label', '')

            # 处理微博置顶
            if rank == 0:
                rank_str = "置顶"
            else:
                rank_str = f"{rank:2d}"

            # 构建单条格式
            line_parts = [f"{rank_str}. {word}"]

            if config.show_label and label:
                line_parts.append(f"[{label}]")

            # if config.show_hot_value and hot_value:
            #     line_parts.append(f"{hot_value}")

            lines.append(" ".join(line_parts))

        return "\n".join(lines)


async def get_count_from_args(args: Message) -> int:
    """从命令参数中提取数量"""
    try:
        if args:
            count = int(str(args).strip())
            if 1 <= count <= 20:  # 限制1-20条
                return count
    except ValueError:
        pass
    return config.default_count


@bilibili_hot.handle()
async def handle_bilibili_hot(event: Event, args: Message = CommandArg()):
    """处理B站热搜命令"""
    if not config.enable_bilibili:
        await bilibili_hot.finish("B站热搜功能已禁用")

    # 检查冷却
    can_send, remaining = CooldownManager.check_cooldown(event)
    if not can_send:
        await bilibili_hot.finish(f"冷却中，请等待 {remaining} 秒")

    # 获取数量
    count = await get_count_from_args(args)

    try:
        # 获取热搜数据
        hot_list = get_bilibili_hot_search()

        if not hot_list:
            await bilibili_hot.finish("获取B站热搜失败，请稍后重试")

        # 格式化消息
        message = HotSearchFormatter.format_hot_search("bilibili", hot_list, count)

        # 更新冷却时间
        CooldownManager.update_cooldown(event)

        await bilibili_hot.finish(message)
    except  FinishedException:
        raise
    except Exception as e:
        logger.error(f"获取B站热搜失败: {e}")
        await bilibili_hot.finish("获取B站热搜时出现错误")


@weibo_hot.handle()
async def handle_weibo_hot(event: Event, args: Message = CommandArg()):
    """处理微博热搜命令"""
    if not config.enable_weibo:
        await weibo_hot.finish("微博热搜功能已禁用")

    # 检查冷却
    can_send, remaining = CooldownManager.check_cooldown(event)
    if not can_send:
        await weibo_hot.finish(f"冷却中，请等待 {remaining} 秒")

    # 获取数量
    count = await get_count_from_args(args)

    try:
        # 获取热搜数据
        hot_list = get_weibo_hot_search()

        if not hot_list:
            await weibo_hot.finish("获取微博热搜失败，请稍后重试")

        # 如果不包含置顶热搜，过滤掉第0条
        if not config.include_top_weibo:
            hot_list = [item for item in hot_list if item.get('rank', 0) > 0]

        # 格式化消息
        message = HotSearchFormatter.format_hot_search("weibo", hot_list, count)

        # 更新冷却时间
        CooldownManager.update_cooldown(event)

        await weibo_hot.finish(message)
    except  FinishedException:
        raise
    except Exception as e:
        logger.error(f"获取微博热搜失败: {e}")
        await weibo_hot.finish("获取微博热搜时出现错误")


@douyin_hot.handle()
async def handle_douyin_hot(event: Event, args: Message = CommandArg()):
    """处理抖音热搜命令"""
    if not config.enable_douyin:
        await douyin_hot.finish("抖音热搜功能已禁用")

    # 检查冷却
    can_send, remaining = CooldownManager.check_cooldown(event)
    if not can_send:
        await douyin_hot.finish(f"冷却中，请等待 {remaining} 秒")

    # 获取数量
    count = await get_count_from_args(args)

    try:
        # 获取热搜数据
        hot_list = get_douyin_hot_search()

        if not hot_list:
            await douyin_hot.finish("获取抖音热搜失败，请稍后重试")

        # 格式化消息
        message = HotSearchFormatter.format_hot_search("douyin", hot_list, count)

        # 更新冷却时间
        CooldownManager.update_cooldown(event)

        await douyin_hot.finish(message)
    except  FinishedException:
        raise
    except Exception as e:
        logger.error(f"获取抖音热搜失败: {e}")
        await douyin_hot.finish("获取抖音热搜时出现错误")


@status_cmd.handle()
async def handle_status():
    """处理状态查询命令"""
    status_lines = [
        " 热搜插件状态",
        "=" * 20,
        f"• B站热搜: {' 启用' if config.enable_bilibili else ' 禁用'}",
        f"• 微博热搜: {' 启用' if config.enable_weibo else ' 禁用'}",
        f"• 抖音热搜: {' 启用' if config.enable_douyin else ' 禁用'}",
        f"• 冷却时间: {config.cooldown_time}秒",
        f"• 默认条数: {config.default_count}条",
        f"• 显示热度: {'是' if config.show_hot_value else '否'}",
        f"• 显示标签: {'是' if config.show_label else '否'}",
        f"• 微博置顶: {'包含' if config.include_top_weibo else '不包含'}",
    ]

    await status_cmd.finish("\n".join(status_lines))


# 定时清理过期的冷却记录
import nonebot
from nonebot import require

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler


@scheduler.scheduled_job("interval", minutes=10)
async def clear_expired_cooldown():
    """定时清理过期的冷却记录"""
    CooldownManager.clear_expired()
    logger.debug("已清理过期的冷却记录")