from nonebot import get_driver
from nonebot.typing import T_State
from nonebot.plugin import PluginMetadata
from nonebot.matcher import Matcher
from nonebot.message import run_preprocessor
from nonebot.adapters import Bot
from nonebot.adapters import Event

from .server import APP
from .config import Config
from .config import pam_config
from .checker import COMMAND_RULE
from .checker import global_check


__plugin_meta__ = PluginMetadata(
    name="权限控制",
    description="对功能进行权限控制以及调用次数限制",
    usage=("通过 Web UI 管理或者命令行的权限控制工具。"),
    type="application",
    homepage="https://github.com/Yan-Zero/nonebot-plugin-pam",
    config=Config,
    supported_adapters=None,
)


@get_driver().on_startup
async def _() -> None:
    # APP.run(host=pam_config.pam_host, port=pam_config.pam_port)
    ...


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

    if result := await global_check(bot=bot, event=event, matcher=matcher, state=state):
        if result.message:
            await bot.send(event=event, message=result.message)
        raise result

    if plugin not in COMMAND_RULE:
        return
    if not (_prefix := state.get("_prefix", None)):
        return
    if not (_command := _prefix.get("command", None)):
        return

    plugin = COMMAND_RULE[plugin]

    if result := await plugin["__all__"](
        bot=bot, event=event, matcher=matcher, state=state
    ):
        if result.message:
            await bot.send(event=event, message=result.message)
        raise result
    if _command[0] not in plugin:
        return
    if result := await plugin[_command[0]](
        bot=bot, event=event, matcher=matcher, state=state
    ):
        if result.message:
            await bot.send(event=event, message=result.message)
        raise result
