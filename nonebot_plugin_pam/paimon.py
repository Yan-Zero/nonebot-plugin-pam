import itertools

from nonebot import on_command
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.adapters import Bot
from nonebot.adapters import Event
from nonebot.adapters import Message
from nonebot.permission import SUPERUSER

from .config import pam_config
from .checker import save
from .checker import Checker
from .checker import COMMAND_RULE

pm = on_command(
    "pm",
    permission=SUPERUSER,
)


@pm.handle()
async def _(bot: Bot, event: Event, _args: Message = CommandArg()):
    global COMMAND_RULE
    args = _args.extract_plain_text().split()

    if len(args) < 2:
        await pm.finish("好像，参数不对。")
    op = args.pop(0).lower()

    if op not in {"ban", "unban"}:
        await pm.finish("只能是 ban 和 unban 二选一。")

    plugins = []
    group = []
    user = []
    rate: float = 0
    status = "-p"
    try:
        c = ""
        while c := args.pop(0):
            if c in {"-g", "-u", "-x", "-w"}:
                status = c
                continue
            if status == "-p":
                if c == "all":
                    c = "__all__"
                plugins.append(c)
            elif status == "-g":
                group.append(c)
            elif status == "-u":
                user.append(c)
            elif status == "-x":
                if c in {"t", "f"}:
                    status = f"-x{c}"
                else:
                    await pm.finish("好像，不支持这个限流标识符？")
            elif status == "-xt":
                rate = float(c)
            elif status == "-xf":
                rate = 60 / float(c)
            elif status == "-w":
                logger.opt(colors=True).warning("-w 没有实现。")
            else:
                logger.opt(colors=True).warning(f"{status} 选项好像，没有见过？")
    except IndexError:
        pass
    except ValueError:
        await pm.finish("似乎，有类型错误？")

    if not plugins:
        await pm.finish("插件没有填写。")
    if "__all__" in plugins:
        plugins = ["__all__"]
    if "all" in user or not user:
        user = [True]
    if "all" in group or not group:
        group = [True]
    user = set(user)
    group = set(group)

    def v(checker: Checker) -> bool:
        if (
            not isinstance(checker, Checker)
            or "group_id" not in checker.gen
            or "user_id" not in checker.gen
            or "rate" not in checker.gen
        ):
            return True
        if checker.gen["rate"] > rate:
            return True
        if checker.gen["group_id"] not in group and True not in group:
            return True
        if checker.gen["user_id"] not in user and True not in user:
            return True
        return False

    prompt = []

    for plugin in plugins:
        if plugin not in COMMAND_RULE:
            COMMAND_RULE[plugin] = {"__all__": []}

        if op == "ban":
            COMMAND_RULE[plugin]["__all__"] = list(
                c for c in COMMAND_RULE[plugin]["__all__"] if v(c)
            )
            ratelimit = ""
            for g, u in itertools.product(group, user):
                rule = []
                uid = [plugin]
                if g is not True:
                    rule.append(f"group.id == {g}")
                    uid.append("user_{user.id}")
                if u is not True:
                    rule.append(f"user.id == {repr(u)}")
                    uid.append("group_{group.id}")
                rule = " and ".join(rule)
                if not rule:
                    rule = "True"
                if rate > 0:
                    ratelimit = "limit.Bucket(f" + repr("_".join(uid)) + f", {rate}, 1)"
                prompt.append(
                    "已关闭"
                    + (f"群 {g} 中" if g is not True else "")
                    + (f"用户 {u} 的" if u is not True else "")
                    + f"插件{plugin}"
                    + ("的限流 " + f"{rate} 分钟/次。" if rate > 0 else "。")
                )
                COMMAND_RULE[plugin]["__all__"].append(
                    Checker(
                        rule=rule,
                        ratelimit=ratelimit,
                        reason="你被限制了喵。" if pam_config.m_message else "",
                        gen={"group_id": g, "user_id": u, "rate": rate},
                    )
                )
        else:

            def p(c) -> bool:
                ret = v(c)
                if not ret:
                    g = c.gen["group_id"]
                    u = c.gen["user_id"]
                    r = c.gen["rate"]
                    prompt.append(
                        "已启用"
                        + (f"群 {g} 中" if g is not True else "")
                        + (f"用户 {u} 的" if u is not True else "")
                        + f"插件{plugin}"
                        + ("的限流 " + f"{r} 分钟/次。" if r > 0 else "。")
                    )
                return ret

            COMMAND_RULE[plugin]["__all__"] = list(
                c for c in COMMAND_RULE[plugin]["__all__"] if p(c)
            )

    ret = "\n".join(prompt).strip()
    if ret:
        await bot.send(event=event, message=ret)
    else:
        await bot.send(event=event, message="好像，没有改动。")

    save()
