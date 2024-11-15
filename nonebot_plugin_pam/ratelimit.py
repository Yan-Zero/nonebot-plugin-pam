import asyncio

from typing import Self
from typing import Hashable
from datetime import datetime
from nonebot import require
from nonebot.log import logger

from .config import pam_config

MODE = "Redis" if pam_config.redis_url else "APScheduler"

if MODE == "Redis":
    import redis

    REDIS = redis.from_url(pam_config.redis_url, decode_responses=True)
    if all(
        module["name"] != "redis-cell"
        for module in REDIS.execute_command("MODULE LIST")
    ):
        MODE = "APScheduler"
        logger.opt(colors=True).warning(
            "Redis 模块 [redis-cell] 未安装，将启用 Apscheduler 模式。"
        )
    else:

        class Bucket:
            __command__: dict[Hashable, str]

            def __new__(cls) -> Self:
                if not hasattr(cls, "ins"):
                    cls.ins = super(Bucket, cls).__new__(cls)
                return cls.ins

            def bucket(
                self,
                key,
                period: int = 60,
                max_burst: int = 3,
                count_pre_period: int = 1,
            ) -> bool:
                """每次调用会消耗令牌，并且返回是否可以继续调用"""
                if hash(key) not in self.__command__:
                    self.__command__[hash(key)] = (
                        f"CL.THROTTLE {hash(key)} {max_burst - 1} {count_pre_period} {period} 1"
                    )
                return bool(REDIS.execute_command(self.__command__[hash(key)])[0])

            def status(self, key) -> float:
                """返回剩余时间等待时间。单位 s"""
                if hash(key) not in self.__command__:
                    return 0
                return REDIS.execute_command(self.__command__[hash(key)])[3]

            async def refresh(self, key, max: int) -> None:
                """注册一个令牌桶"""
                pass


if MODE == "APScheduler":
    require("nonebot_plugin_apscheduler")
    from nonebot_plugin_apscheduler import scheduler  # noqa: E402

    class Bucket:
        __bucket__: dict[Hashable, int]
        __time__: dict[Hashable, datetime]
        __period__: dict[Hashable, float]
        __lock__: asyncio.Lock

        def __new__(cls) -> Self:
            if not hasattr(cls, "ins"):
                cls.ins = super(Bucket, cls).__new__(cls)
                cls.ins.__bucket__ = {}
                cls.ins.__time__ = {}
                cls.ins.__period__ = {}
                cls.ins.__lock__ = asyncio.Lock()
            return cls.ins

        def bucket(
            self,
            key,
            period: int = 60,
            max_burst: int = 3,
            count_pre_period: int = 1,
        ) -> bool:
            """每次调用会消耗令牌，并且返回是否可以继续调用"""
            if key not in self.__bucket__:
                self.__bucket__[key] = max_burst
                self.__time__[key] = datetime.now()
                self.__period__[key] = period
                scheduler.add_job(
                    func=self.refresh,
                    trigger="interval",
                    seconds=period,
                    args=(key, max_burst, count_pre_period),
                )

            if self.__bucket__[key] > 0:
                self.__bucket__[key] -= 1
                return False
            return True

        def status(self, key) -> float:
            """返回剩余时间等待时间。单位 s"""
            __now__ = datetime.now()
            return max(
                self.__period__[key]
                - (__now__ - self.__time__.get(key, __now__)).seconds,
                0,
            )

        async def refresh(self, key, max: int, count_pre_period: int = 1) -> None:
            """注册一个令牌桶"""
            async with self.__lock__:
                if self.__bucket__[key] >= max:
                    return
                self.__bucket__[key] += count_pre_period
                self.__time__[key] = datetime.now()


logger.opt(colors=True).info(f"使用 {MODE} 模式")
