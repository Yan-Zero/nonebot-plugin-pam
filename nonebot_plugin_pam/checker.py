import ast
import pathlib
import warnings
import itertools
import functools

from typing import Any
from typing import Callable
from typing import Awaitable
from typing import Coroutine

import yaml

from nonebot.typing import T_State
from nonebot.adapters import Bot
from nonebot.adapters import Event
from nonebot.exception import IgnoredException
from nonebot.permission import SUPERUSER

from .utils import AwaitAttrDict
from .ratelimit import Bucket


class Checker:
    rule_code: Callable[[dict], Awaitable]
    """编译后的代码"""
    reason_code: Callable[[dict], Awaitable[str]]
    """编译后的代码"""
    limit_code: Callable[[dict], Awaitable[str]]

    reason: str
    """生成错误提示，并发送给用户。"""
    rule: str
    """匹配的规则。True或者其他什么等价的，就抛出 IgnoredException。"""
    ratelimit: str
    """限速。True或者其他什么等价的，就抛出 IgnoredException。"""

    gen: dict
    """机器生成用来标记的，为空则表示处于高级模式（必须手动到./data/pam下面修改）"""

    def __init__(
        self,
        rule: str,
        ratelimit: str = "",
        reason: str = "",
        gen: dict = None,
        **kwargs,
    ) -> None:
        """
        Args:
            checker: 检查的代码。
            error: 生成错误提示，并发送给用户。或者就是错误提示的文本。设置为 None 或者空文本则是不发送。
        """
        self.reason = reason.strip()
        self.rule = rule.strip()
        self.ratelimit = ratelimit.strip()
        self.gen = gen or {}
        self.compile()

    def compile(self) -> None:
        class Attri2Await(ast.NodeTransformer):
            def visit_Call(self, node):
                if isinstance(node.func, ast.Attribute):
                    node.func.marked = True
                super().generic_visit(node)
                return node

            def visit_Attribute(self, node):
                super().generic_visit(node)
                if hasattr(node, "marked"):
                    return node
                if isinstance(node.value, ast.Subscript) and hasattr(
                    node.value, "marked"
                ):
                    return ast.Await(value=node)
                return node

            def visit_Name(self, node):
                super().generic_visit(node)
                ret = ast.Subscript(
                    value=ast.Name(id="kwargs", ctx=ast.Load()),
                    slice=ast.Constant(value=node.id),
                    ctx=node.ctx,
                )
                if not hasattr(__builtins__, node.id) or node.id in {
                    "re",
                }:
                    ret.marked = True
                return ret

        def c(_ast: ast.mod) -> Callable[[dict], Awaitable]:
            code = ast.Interactive(
                body=[
                    ast.AsyncFunctionDef(
                        name="_",
                        args=ast.arguments(
                            posonlyargs=[],
                            args=[],
                            kwonlyargs=[],
                            kw_defaults=[],
                            kwarg=ast.arg(arg="kwargs"),
                            defaults=[],
                        ),
                        body=[
                            ast.Return(value=Attri2Await().visit(_ast).body[0].value)
                        ],
                        decorator_list=[],
                        type_params=[],
                    )
                ]
            )
            ast.fix_missing_locations(code)
            _ = {}
            exec(
                compile(
                    code,
                    filename="Checker",
                    mode="single",
                ),
                _,
                _,
            )
            return _["_"]

        if not (self.rule or self.ratelimit):
            raise ValueError("Rule 和 Ratelimit 都为空")

        self.rule_code = c(
            ast.parse(
                self.rule or "False",
                filename="Checker",
                mode="single",
            )
        )

        self.reason_code = c(
            ast.parse(
                f"f{repr(self.reason)}",
                filename="f-string",
                mode="single",
            )
        )

        self.limit_code = c(
            ast.parse(
                self.limit_code or "False",
                filename="Checker",
                mode="single",
            )
        )

    def __call__(
        self, bot: Bot, event: Event, state: T_State, *args, plugin: dict = {}, **kwargs
    ) -> Coroutine[Any, Any, IgnoredException | None]:
        _limit = Bucket()
        _pbuid = f"{event.get_user_id()}_{plugin['name']}"
        _buid = f"{_pbuid}_{plugin['command']}"
        _kwargs = {
            "bot": AwaitAttrDict(bot),
            "bucket": AwaitAttrDict(
                {
                    "uid": _buid,
                    "bucket": functools.partial(
                        _limit.bucket,
                        _buid,
                    ),
                    "status": functools.partial(
                        _limit.status,
                        _buid,
                    ),
                }
            ),
            "event": AwaitAttrDict(event),
            "state": AwaitAttrDict(state),
            "user": AwaitAttrDict(
                {
                    "id": event.get_user_id(),
                    "superuser": SUPERUSER(bot=bot, event=event),
                }
            ),
            "group": AwaitAttrDict(),
            "plugin": AwaitAttrDict(plugin),
            "re": __import__("re"),
            "limit": AwaitAttrDict(Bucket()),
            "int": int,
            "str": str,
            "datetime": __import__("datetime").datetime,
            "IgnoredException": IgnoredException,
        }
        _kwargs["plugin"].bucket = AwaitAttrDict(
            {
                "uid": _pbuid,
                "bucket": functools.partial(
                    _limit.bucket,
                    _pbuid,
                ),
                "status": functools.partial(
                    _limit.status,
                    _pbuid,
                ),
            }
        )
        try:
            _kwargs["message"] = event.get_plaintext()
        except Exception:
            _kwargs["message"] = ""

        async def call_api(bot: Bot, api: str, data: dict, key: str = ""):
            ret = await bot.call_api(api=api, **data)
            if key and key in ret:
                return ret[key]

        async def wrapper() -> None | IgnoredException:
            try:
                from nonebot.adapters.onebot.v11 import GroupMessageEvent as V11GME
                from nonebot.adapters.onebot.v11 import MessageEvent as V11ME

                if isinstance(event, V11ME):
                    _kwargs["user"].name = event.sender.nickname

                if isinstance(event, V11GME):
                    _kwargs["group"] = AwaitAttrDict(
                        {
                            "id": event.group_id,
                            "name": call_api(
                                bot,
                                "get_group_info",
                                {"group_id": event.group_id},
                                "group_name",
                            ),
                        }
                    )

                    async def get_name() -> str | None:
                        r = await bot.get_group_member_info(
                            group_id=event.group_id, user_id=event.sender.user_id
                        )
                        if r["card"]:
                            return r["card"]
                        return event.sender.nickname

                    _kwargs["user"].name = get_name()

            except ImportError:
                pass

            if ret := await self.rule_code(**_kwargs):
                return (
                    IgnoredException(reason=await self.reason_code(**_kwargs))
                    if not isinstance(ret, IgnoredException)
                    else ret
                )
            if ret := await self.limit_code(**_kwargs):
                return (
                    IgnoredException(reason=await self.reason_code(**_kwargs))
                    if not isinstance(ret, IgnoredException)
                    else ret
                )

        return wrapper()


COMMAND_RULE: dict[
    str, dict[str, list[Callable[..., Awaitable[None | IgnoredException]]]]
] = ...


def reload() -> None:
    global COMMAND_RULE
    COMMAND_RULE = {
        "__all__": {
            "__all__": [],
        },
    }
    for file in pathlib.Path("./data/pam").glob("*.yaml"):
        COMMAND_RULE[file.stem] = {
            "__all__": [],
        }

        with open(file, "r", encoding="utf-8") as f:
            _data: dict[str, list[dict[str, str]]] = yaml.safe_load(f)
            if not isinstance(_data, dict):
                continue

            for command, checkers in _data.items():
                if command not in COMMAND_RULE[file.stem]:
                    COMMAND_RULE[file.stem][command] = []
                for checker in checkers:
                    if not isinstance(checker, dict):
                        continue

                    try:
                        c = Checker(
                            rule=checker.get("rule", ""),
                            ratelimit=checker.get("ratelimit", ""),
                            reason=checker.get("reason", ""),
                            gen=checker.get("gen", {}),
                        )
                    except ValueError:
                        warnings.warn(f"规则为空: {file} {command}")
                        continue
                    COMMAND_RULE[file.stem][command].append(c)

    for file in pathlib.Path("./data/pam").glob("*/*.yaml"):
        plugin = file.parent.stem
        if plugin not in COMMAND_RULE:
            COMMAND_RULE[plugin] = {
                "__all__": [],
            }

        with open(file, "r", encoding="utf-8") as f:
            _data: dict[str, list[dict[str, str]]] = yaml.safe_load(f)
            if not isinstance(_data, dict):
                continue

            for command, checkers in _data.items():
                if command not in COMMAND_RULE[plugin]:
                    COMMAND_RULE[plugin][command] = []
                for checker in checkers:
                    if not isinstance(checker, dict):
                        continue

                    try:
                        c = Checker(
                            rule=checker.get("rule", ""),
                            ratelimit=checker.get("ratelimit", ""),
                            reason=checker.get("reason", ""),
                            gen=checker.get("gen", {}),
                        )
                    except ValueError:
                        warnings.warn(f"规则为空: {file} {command}")
                        continue
                    COMMAND_RULE[file.stem][command].append(c)


def save() -> None:
    # 清空 ./data/pam/

    for file in itertools.chain(
        pathlib.Path("./data/pam").glob("*/*.yaml"),
        pathlib.Path("./data/pam").glob("*.yaml"),
    ):
        file.unlink()

    for p in COMMAND_RULE:
        file_name = f"./data/pam/{p}.yaml"
        if not pathlib.Path(file_name).parent.exists():
            pathlib.Path(file_name).parent.mkdir(parents=True)

        with open(file_name, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                {
                    command: [
                        {
                            "rule": checker.rule,
                            "ratelimit": checker.ratelimit,
                            "reason": checker.reason,
                            "gen": checker.gen,
                        }
                        for checker in checkers
                    ]
                    for command, checkers in COMMAND_RULE[p].items()
                },
                f,
                allow_unicode=True,
            )


async def plugin_check(
    plugin: str, state: T_State, *args, plugin_info=None, **kwargs
) -> IgnoredException | None:
    if plugin not in COMMAND_RULE:
        return None
    command = state.get("_prefix", {}).get("command", None)
    if not plugin_info:
        plugin_info = {}
    plugin_info["command"] = command
    command = command[0] if command else "__all__"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        for checker in itertools.chain(
            *(
                COMMAND_RULE[plugin].get(c, [])
                for c in itertools.chain({"__all__", command})
            )
        ):
            if ret := await checker(state=state, plugin=plugin_info, *args, **kwargs):
                return ret


reload()
global_check = functools.partial(plugin_check, plugin="__all__")
