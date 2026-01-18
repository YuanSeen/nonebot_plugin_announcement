from pydantic import BaseModel, Field


class Config(BaseModel):
    """热搜插件配置"""

    # 冷却时间配置（秒）
    cooldown_time: int = Field(default=10, description="命令冷却时间（秒）")

    # 默认显示条数
    default_count: int = Field(default=10, description="默认显示热搜条数")

    # 各平台配置
    enable_bilibili: bool = Field(default=True, description="是否启用B站热搜")
    enable_weibo: bool = Field(default=True, description="是否启用微博热搜")
    enable_douyin: bool = Field(default=True, description="是否启用抖音热搜")

    # 显示格式配置
    show_hot_value: bool = Field(default=True, description="是否显示热度值")
    show_label: bool = Field(default=True, description="是否显示标签")
    include_top_weibo: bool = Field(default=True, description="是否包含微博置顶热搜")

    # 网络请求配置
    request_timeout: int = Field(default=10, description="请求超时时间（秒）")
    max_retries: int = Field(default=2, description="最大重试次数")