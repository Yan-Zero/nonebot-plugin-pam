import ast
import itertools
import functools


from typing import Any
from typing import Callable
from typing import Awaitable
from typing import Coroutine

from nonebot.typing import T_State
from nonebot.adapters import Bot
from nonebot.adapters import Event
from nonebot.exception import IgnoredException


class AwaitAttrDict(dict):
    def __getattr__(self, name):
        async def _(d):
            return d

        try:
            if isinstance(ret := self[name], Coroutine):
                return ret
            return _(ret)
        except KeyError:
            return _(None)

    def __setattr__(self, name, value):
        self[name] = value


class Checker:
    code: Callable[[dict], Awaitable]
    error: str | Callable[..., Awaitable[str]]
    """生成错误提示，并发送给用户。"""

    def __init__(
        self, checker: str, error: str | Callable[..., Awaitable[str]]
    ) -> None:
        """
        Args:
            checker: 检查的代码。
            error: 生成错误提示，并发送给用户。或者就是错误提示的文本。设置为 None 或者空文本则是不发送。
        """

        class Attri2Await(ast.NodeTransformer):
            def visit_Attribute(self, node):
                return ast.Await(value=node)

        class Name2Subscript(ast.NodeTransformer):
            def visit_Name(self, node):
                return ast.Subscript(
                    value=ast.Name(id="kwargs", ctx=ast.Load()),
                    slice=ast.Constant(value=node.id),
                    ctx=node.ctx,
                )

        self.error = error
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
                                Name2Subscript().visit(
                                    ast.parse(
                                        checker, filename="Checker", mode="single"
                                    )
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
        self.code = _["_"]

    def __call__(
        self, bot: Bot, event: Event, state: T_State, *args, **kwargs
    ) -> Coroutine[Any, Any, IgnoredException | None]:
        _kwargs = {
            "bot": AwaitAttrDict(bot.__dict__),
            "event": AwaitAttrDict(event.__dict__),
            "state": AwaitAttrDict(state),
            "user": AwaitAttrDict({"id": event.get_user_id()}),
            "group": AwaitAttrDict(),
        }

        async def wrapper() -> None | IgnoredException:
            try:
                from nonebot.adapters.onebot.v11 import GroupMessageEvent as V11GME

                if isinstance(event, V11GME):
                    _kwargs["group"] = AwaitAttrDict(
                        {
                            "id": event.group_id,
                        }
                    )
            except ImportError:
                pass

            if await self.code(**_kwargs):
                ret = self.error
                if ret and not isinstance(ret, str):
                    ret = await ret(bot=bot, event=event, state=state, *args, **kwargs)
                return IgnoredException(reason=ret)

        return wrapper()


COMMAND_RULE: dict[
    str, dict[str, list[Callable[..., Awaitable[None | IgnoredException]]]]
] = {
    "__all__": {
        "__all__": [],
    },
}


async def plugin_check(
    plugin: str, state: T_State, *args, **kwargs
) -> IgnoredException | None:
    if plugin not in COMMAND_RULE:
        return None
    for checker in itertools.chain(
        *(
            COMMAND_RULE[plugin][c]
            for c in itertools.chain(
                {"__all__", state.get("_prefix", {}).get("_command", "__all__")}
            )
        )
    ):
        if ret := await checker(state=state, *args, **kwargs):
            return ret


global_check = functools.partial(plugin_check, plugin="__all__")
