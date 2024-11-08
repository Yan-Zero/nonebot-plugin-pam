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

from .ratelimit import Bucket


class AwaitAttrDict:
    obj: Any

    def __getattr__(self, name):
        async def _(d):
            return d

        try:
            if hasattr(self.obj, name):
                ret = getattr(self.obj, name)
            else:
                ret = self[name]
            if isinstance(ret, Coroutine):
                return ret
            elif isinstance(ret, Callable):
                return ret
            return _(ret)
        except KeyError:
            return _(None)

    def __setattr__(self, name, value):
        if isinstance(self.obj, dict):
            self.obj[name] = value
        else:
            self.obj.__dict__[name] = value

    def __getitem__(self, key):
        if isinstance(self.obj, dict):
            return self.obj[key]
        else:
            return self.obj.__dict__[key]

    def __setitem__(self, key, value):
        if isinstance(self.obj, dict):
            self.obj[key] = value
        else:
            self.obj.__dict__[key] = value

    def __init__(self, obj: Any = None) -> None:
        super().__setattr__("obj", obj or {})


class Checker:
    rule_code: Callable[[dict], Awaitable]
    """编译后的代码"""
    reason_code: Callable[[dict], Awaitable[str]]
    """编译后的代码"""

    reason: str
    """生成错误提示，并发送给用户。"""
    rule: str
    """匹配的规则。True或者其他什么等价的，就抛出 IgnoredException。"""

    def __init__(self, rule: str, reason: str, **kwargs) -> None:
        """
        Args:
            checker: 检查的代码。
            error: 生成错误提示，并发送给用户。或者就是错误提示的文本。设置为 None 或者空文本则是不发送。
        """
        self.reason = reason
        self.rule = rule
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
                        ast.Return(
                            value=Attri2Await()
                            .visit(
                                ast.parse(self.rule, filename="Checker", mode="single")
                            )
                            .body[0]
                            .value
                        )
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
        self.rule_code = _["_"]

        _ = {}
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
                        ast.Return(
                            value=Attri2Await()
                            .visit(
                                ast.parse(
                                    f"f{repr(self.reason)}",
                                    filename="f-string",
                                    mode="single",
                                )
                            )
                            .body[0]
                            .value
                        )
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
        self.reason_code = _["_"]

    def __call__(
        self, bot: Bot, event: Event, state: T_State, *args, plugin: dict = {}, **kwargs
    ) -> Coroutine[Any, Any, IgnoredException | None]:
        _limit = Bucket()
        _buid = f"{event.get_user_id()}_{plugin['name']}_{plugin['command']}"
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
                    "superuser": SUPERUSER(bot=Bot, event=event),
                }
            ),
            "group": AwaitAttrDict(),
            "plugin": AwaitAttrDict(plugin),
            "re": __import__("re"),
            "limit": AwaitAttrDict(Bucket()),
            "int": int,
            "str": str,
            "datetime": __import__("datetime").datetime,
        }

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

            if await self.rule_code(**_kwargs):
                return IgnoredException(reason=await self.reason_code(**_kwargs))

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

                    rule = " and ".join(
                        _
                        for _ in [
                            f'({checker["rule"]})' if "rule" in checker else "",
                            (
                                f'({checker["ratelimit"]})'
                                if "ratelimit" in checker
                                else ""
                            ),
                        ]
                        if _
                    )
                    if not rule:
                        warnings.warn(f"规则为空: {file} {command}")
                        continue

                    COMMAND_RULE[file.stem][command].append(
                        Checker(rule=rule, reason=checker.get("reason", ""))
                    )

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

                    rule = " and ".join(
                        _
                        for _ in [
                            f'({checker["rule"]})' if "rule" in checker else "",
                            (
                                f'({checker["ratelimit"]})'
                                if "ratelimit" in checker
                                else ""
                            ),
                        ]
                        if _
                    )
                    if not rule:
                        warnings.warn(f"规则为空: {file} {command}")
                        continue

                    COMMAND_RULE[plugin][command].append(
                        Checker(
                            rule=rule,
                            reason=checker.get("reason", ""),
                        )
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
