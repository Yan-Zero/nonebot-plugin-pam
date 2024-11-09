from nonebot.typing import T_State
from nonebot.plugin import PluginMetadata
from nonebot.matcher import Matcher
from nonebot.message import run_preprocessor
from nonebot.adapters import Bot
from nonebot.adapters import Event

from .config import Config
from .checker import plugin_check
from .checker import global_check

from .paimon import pm
from .server import AUTH_KEY
from .command import COMMAND_RULE


__plugin_meta__ = PluginMetadata(
    name="权限控制",
    description="对功能进行权限控制以及调用次数限制",
    usage=("通过 Web UI 管理或者命令行的权限控制工具。"),
    type="application",
    homepage="https://github.com/Yan-Zero/nonebot-plugin-pam",
    config=Config,
    supported_adapters=None,
)


@run_preprocessor
async def _(
    bot: Bot,
    event: Event,
    matcher: Matcher,
    state: T_State,
):
    plugin = matcher.plugin_id
    if plugin is None or plugin == __name__:
        return
    plugin_info = {"name": plugin}

    if result := await global_check(
        bot=bot, event=event, matcher=matcher, state=state, plugin_info=plugin_info
    ):
        if result.reason:
            await bot.send(event=event, message=result.reason)
        raise result

    if result := await plugin_check(
        plugin=plugin,
        bot=bot,
        event=event,
        matcher=matcher,
        state=state,
        plugin_info=plugin_info,
    ):
        if result.reason:
            await bot.send(event=event, message=result.reason)
        raise result
