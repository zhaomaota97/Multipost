"""平台发布器注册表。"""
from .weixin_channels import WeixinChannelsPublisher
from .douyin import DouyinPublisher
from .xiaohongshu import XiaohongshuPublisher

PUBLISHERS = {
    p.platform_key: p
    for p in (WeixinChannelsPublisher, DouyinPublisher, XiaohongshuPublisher)
}


def get_publisher(platform_key: str):
    cls = PUBLISHERS.get(platform_key)
    if cls is None:
        raise KeyError(f"未知平台: {platform_key}")
    return cls()


def platform_list():
    return [
        {"key": cls.platform_key, "name": cls.platform_name}
        for cls in PUBLISHERS.values()
    ]
