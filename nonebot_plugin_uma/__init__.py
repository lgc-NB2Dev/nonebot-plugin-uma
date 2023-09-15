from nonebot.plugin import PluginMetadata, require

require("nonebot_plugin_apscheduler")

from . import __main__ as __main__  # noqa: E402
from .config import ConfigModel  # noqa: E402

__version__ = "0.1.0"
__plugin_meta__ = PluginMetadata(
    name="UMA Plugin",
    description="赛马娘 QQ 机器人插件 NoneBot2 移植版",
    usage="待补充",
    type="application",
    homepage="https://github.com/lgc-NB2Dev/nonebot-plugin-uma",
    config=ConfigModel,
    supported_adapters={"~onebot.v11"},
    extra={"License": "MIT", "Author": "Perseus037 & student_2333"},
)
