from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters import Bot
from nonebot.adapters import Event
from nonebot.adapters import Message
from nonebot.permission import SUPERUSER

from .checker import save
from .checker import reload
from .checker import Checker
from .checker import COMMAND_RULE


@on_command(
    (
        "pam",
        "reload",
    ),
    permission=SUPERUSER,
).handle()
async def _(bot: Bot, event: Event):
    reload()
    await bot.send(event=event, message="已重新加载规则。")


@on_command(
    (
        "pam",
        "list",
    ),
    permission=SUPERUSER,
).handle()
async def _(bot: Bot, event: Event, _args: Message = CommandArg()):
    global COMMAND_RULE
    plugin_name = _args.extract_plain_text().split(maxsplit=2)
    if len(plugin_name) < 1:
        return await bot.send(event=event, message="插件名字？")
    if plugin_name[0] not in COMMAND_RULE:
        return await bot.send(
            event=event, message=plugin_name[0] + " 这个插件还没有设置规则哦。"
        )
    if len(plugin_name) == 2:
        if plugin_name[1] not in COMMAND_RULE[plugin_name[0]]:
            return await bot.send(
                event=event,
                message=plugin_name[0] + f" 的 {plugin_name[1]} 还没有设置规则哦。",
            )
        return await bot.send(
            event=event,
            message=plugin_name[0]
            + f" 的 {plugin_name[1]} 的规则是:\n"
            + "\n".join(
                map(
                    lambda x: "- "
                    + (
                        (f"rule: {x.rule}\n" if x.rule else "")
                        + (f"  ratelimit: {x.ratelimit}\n" if x.ratelimit else "")
                        + (f"  reason: {x.reason}" if x.reason else "")
                    ).strip(),
                    COMMAND_RULE[plugin_name[0]][plugin_name[1]],
                )
            ),
        )

    ret = ""
    for c, v in COMMAND_RULE[plugin_name[0]].items():
        if not v:
            continue
        ret += f"  {c}:\n" + "\n".join(
            map(
                lambda y: "  - "
                + (
                    (f"rule: {y.rule}\n" if y.rule else "")
                    + (f"    ratelimit: {y.ratelimit}\n" if y.ratelimit else "")
                    + (f"    reason: {y.reason}" if y.reason else "")
                ).strip(),
                v,
            )
        )
    if not ret:
        return await bot.send(
            event=event, message=plugin_name[0] + " 这个插件还没有设置规则哦。"
        )

    return await bot.send(
        event=event,
        message=plugin_name[0] + ":\n" + ret,
    )


@on_command(
    (
        "pam",
        "set",
    ),
    permission=SUPERUSER,
).handle()
async def _(bot: Bot, event: Event, _args: Message = CommandArg()):
    global COMMAND_RULE
    plugin_name = _args.extract_plain_text().split(maxsplit=2)
    if len(plugin_name) != 3:
        return await bot.send(
            event=event,
            message="格式不对，应该是\n/pam.set <plugin> <command>\nrule=<rule>\nratelimit=<ratelimit>\nreason=<reason>",
        )
    if plugin_name[0] not in COMMAND_RULE:
        COMMAND_RULE[plugin_name[0]] = {"__all__": []}
    plugin = COMMAND_RULE[plugin_name[0]]
    print(plugin_name[2])
    try:
        args = {
            k: v
            for k, v in map(
                lambda x: x.split("=", maxsplit=1), plugin_name[2].split("\n")
            )
        }
        print(args)
        if plugin_name[1] not in plugin:
            plugin[plugin_name[1]] = []
        plugin[plugin_name[1]].append(
            Checker(
                rule=args.get("rule", ""),
                ratelimit=args.get("ratelimit", ""),
                reason=args.get("reason", ""),
            )
        )
    except Exception as e:
        return await bot.send(event=event, message=f"设置规则时出错：{e}")
    save()
    await bot.send(
        event=event,
        message=f"已设置 {plugin_name[0]} 的 {plugin_name[1]} 的规则。",
    )
