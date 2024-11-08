import asyncio

from typing import Self
from typing import Hashable
from datetime import datetime
from nonebot import require

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler  # noqa: E402


class Bucket:
    __bucket__: dict[Hashable, int]
    __time__: dict[Hashable, datetime]
    __rate__: dict[Hashable, float]
    __lock__: asyncio.Lock

    def __new__(cls) -> Self:
        if not hasattr(cls, "ins"):
            cls.ins = super(Bucket, cls).__new__(cls)
            cls.ins.__bucket__ = {}
            cls.ins.__time__ = {}
            cls.ins.__rate__ = {}
            cls.ins.__lock__ = asyncio.Lock()
        return cls.ins

    def bucket(self, key, rate: float = 60, max: int = 3) -> bool:
        """每次调用会消耗令牌，并且返回是否可以继续调用"""
        if key not in self.__bucket__:
            self.__bucket__[key] = max
            self.__time__[key] = datetime.now()
            self.__rate__[key] = rate
            scheduler.add_job(
                func=self.register,
                trigger="interval",
                seconds=rate,
                args=(key, max),
            )

        if self.__bucket__[key] > 0:
            self.__bucket__[key] -= 1
            return False
        return True

    def status(self, key) -> float:
        """返回剩余时间等待时间。单位 s"""
        __now__ = datetime.now()
        return (
            max(
                self.__rate__[key]
                - (__now__ - self.__time__.get(key, __now__)).microseconds,
                0,
            )
            / 1000.0
        )

    async def register(self, key, max: int) -> None:
        """注册一个令牌桶"""
        async with self.__lock__:
            if self.__bucket__[key] >= max:
                return
            self.__bucket__[key] += 1
            self.__time__[key] = datetime.now()
