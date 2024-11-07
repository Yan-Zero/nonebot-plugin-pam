import ast
import itertools


from typing import Any
from typing import Callable
from typing import Awaitable
from typing import Coroutine

from nonebot.typing import T_State
from nonebot.adapters import Bot
from nonebot.adapters import Event


class CallException(Exception):
    message: str

    def __init__(self, message: str, *args: object) -> None:
        super().__init__(*args)


class AttrDict(dict):
    __lazy_load__: dict[str, Any]

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return None

        getattr()

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
        self.error = error
        _ = {}
        exec(
            compile(
                ast.Interactive(
                    body=[
                        ast.AsyncFunctionDef(
                            name="_",
                            args=ast.arguments(
                                posonlyargs=[],
                                args=[
                                    ast.arg(
                                        arg="l",
                                        annotation=ast.Name(id="dict", ctx=ast.Load()),
                                    )
                                ],
                                kwonlyargs=[],
                                kw_defaults=[],
                                defaults=[],
                            ),
                            body=[
                                ast.Expr(
                                    value=ast.Call(
                                        func=ast.Attribute(
                                            value=ast.Call(
                                                func=ast.Name(
                                                    id="locals", ctx=ast.Load()
                                                ),
                                                args=[],
                                                keywords=[],
                                            ),
                                            attr="update",
                                            ctx=ast.Load(),
                                        ),
                                        args=[ast.Name(id="l", ctx=ast.Load())],
                                        keywords=[],
                                    )
                                ),
                                ast.Return(value=...),
                            ],
                            decorator_list=[],
                            type_params=[],
                        )
                    ]
                ),
                filename="Checker",
                mode="single",
            ),
            _,
            _,
        )
        self.code = _["_"]

    def __call__(
        self, bot: Bot, event: Event, state: T_State, *args, **kwargs
    ) -> Coroutine[Any, Any, CallException | None]:
        _locals = {
            "bot": AttrDict(bot.__dict__),
            "event": AttrDict(event.__dict__),
            "state": AttrDict(state.__dict__),
            "user": AttrDict({"id": event.get_user_id()}),
            "group": AttrDict(),
        }
        locals()

        async def wrapper() -> None | CallException:
            try:
                from nonebot.adapters.onebot.v11 import GroupMessageEvent as V11GME

                if isinstance(event, V11GME):
                    _locals["group"] = AttrDict(
                        {
                            "id": event.group_id,
                        }
                    )
            except ImportError:
                pass

            if await self.code(_locals):
                ret = self.error
                if ret and not isinstance(ret, str):
                    ret = await ret(bot=bot, event=event, state=state, *args, **kwargs)
                return CallException(message=ret)

        return wrapper()


COMMAND_RULE: dict[str, dict[str, Callable[..., Awaitable[None | CallException]]]] = {
    "__all__": ...,
}
GLOBAL_RULE: dict[str, list[Awaitable[None | CallException]]] = {
    "__all__": [],
}


async def global_check(state: T_State, *args, **kwargs) -> CallException | None:
    for checker in itertools.chain(
        GLOBAL_RULE[c]
        for c in itertools.chain(
            {"__all__", state.get("_prefix", {}).get("_command", "__all__")}
        )
    ):
        if ret := await checker(state=state, *args, **kwargs):
            return ret
