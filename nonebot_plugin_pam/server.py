"""
后台接口。
"""

import secrets

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from nonebot import get_app
from nonebot import get_driver
from nonebot.log import logger
from nonebot.plugin import get_loaded_plugins

from .config import pam_config
from .checker import save
from .checker import Checker
from .checker import COMMAND_RULE

AUTH_KEY = secrets.token_hex(32)
CACHE_PLUGIN = {}
DRIVER = get_driver()


def check_auth(r: Request) -> JSONResponse | None:
    global AUTH_KEY
    if r.headers.get("Authorization", None) != f"Bearer {AUTH_KEY}":
        return JSONResponse(
            {"success": False, "message": "Unauthorized"}, status_code=401
        )


@DRIVER.on_startup
async def _() -> None:
    try:
        app: FastAPI = get_app()
    except Exception as e:
        return logger.opt(colors=True).info("PAM WebUI 运行失败。", e)
    pam_url_prefix = "/pam"

    @app.route(f"{pam_url_prefix}/api/plugins", methods=["POST", "GET"])
    async def get_plugins(r: Request) -> JSONResponse:
        global CACHE_PLUGIN
        if ret := check_auth(r):
            return ret
        if CACHE_PLUGIN:
            return JSONResponse({"success": True, "data": CACHE_PLUGIN})

        for p in get_loaded_plugins():
            name = p.name or p.module_name
            if not name:
                continue
            if p.metadata:
                CACHE_PLUGIN[name] = {
                    "name": p.metadata.name,
                    "usage": p.metadata.usage,
                    "type": p.metadata.type,
                    "homepage": p.metadata.homepage,
                    "supported_adapters": (
                        list(p.metadata.supported_adapters)
                        if p.metadata.supported_adapters
                        else []
                    ),
                }
            else:
                CACHE_PLUGIN[name] = {
                    "name": p.name,
                    "usage": "暂无说明",
                    "type": None,
                    "homepage": None,
                    "supported_adapters": [],
                }
        return JSONResponse({"success": True, "data": CACHE_PLUGIN})

    @app.post(f"{pam_url_prefix}/api/fetch")
    async def get_data(r: Request) -> JSONResponse:
        global COMMAND_RULE
        if ret := check_auth(r):
            return ret
        d: dict = await r.json()
        if not isinstance(d, dict) or "plugin" not in d:
            return JSONResponse(
                {"success": False, "message": "Invalid data format"}, status_code=400
            )
        plugin = d["plugin"]
        if plugin not in COMMAND_RULE:
            data = {}
        else:
            data = {
                command: [
                    {
                        "rule": checker.rule,
                        "ratelimit": checker.ratelimit,
                        "reason": checker.reason,
                        "gen": checker.gen,
                    }
                    for checker in checkers
                ]
                for command, checkers in COMMAND_RULE[plugin].items()
            }
        return JSONResponse({"success": True, "data": data})

    @app.post(f"{pam_url_prefix}/api/remove")
    async def _remove(r: Request) -> JSONResponse:
        global COMMAND_RULE
        if ret := check_auth(r):
            return ret
        try:
            data = await r.json()
            if (
                not isinstance(data, dict)
                or "plugin" not in data
                or "command" not in data
            ):
                return JSONResponse(
                    {"success": False, "message": "Invalid data format"},
                    status_code=400,
                )
            plugin = data["plugin"]
            command = data["command"]
            if plugin not in COMMAND_RULE or command not in COMMAND_RULE[plugin]:
                return JSONResponse(
                    {"success": False, "message": "Plugin or command not found"},
                    status_code=404,
                )
            index = data["index"]
            if len(COMMAND_RULE[plugin][command]) < index:
                return JSONResponse(
                    {"success": False, "message": "Index out of range"},
                    status_code=404,
                )
            COMMAND_RULE[plugin][command].pop(index)
        except Exception as e:
            return JSONResponse({"success": False, "message": str(e)}, status_code=400)
        save()
        return JSONResponse({"success": True})

    @app.post(f"{pam_url_prefix}/api/add")
    async def _add(r: Request) -> JSONResponse:
        global COMMAND_RULE
        if ret := check_auth(r):
            return ret

        try:
            data = await r.json()
            if (
                not isinstance(data, dict)
                or "plugin" not in data
                or "command" not in data
            ):
                return JSONResponse(
                    {"success": False, "message": "Invalid data format"},
                    status_code=400,
                )
            plugin = data["plugin"]
            command = data["command"]
            index = data["index"]
            checker = data["checker"]

            if plugin not in COMMAND_RULE:
                COMMAND_RULE[plugin] = {"__all__": []}
            if command not in COMMAND_RULE[plugin]:
                COMMAND_RULE[plugin][command] = []
            COMMAND_RULE[plugin][command].insert(index, Checker(**checker))
        except Exception as e:
            return JSONResponse({"success": False, "message": str(e)}, status_code=400)
        save()
        return JSONResponse({"success": True})

    @app.route(f"{pam_url_prefix}/api/auth", methods=["POST", "GET"])
    async def authenticate(r: Request) -> JSONResponse:

        if r.method == "GET":
            if check_auth(r):
                return JSONResponse(
                    {"success": False, "message": "Please use post to login."},
                    status_code=401,
                )
            else:
                return JSONResponse({"success": True})

        data = await r.json()
        username = data.get("username")
        password = data.get("password")
        if username == pam_config.pam_username and password == pam_config.pam_password:
            return JSONResponse({"success": True, "auth_key": AUTH_KEY})
        else:
            return JSONResponse(
                {"success": False, "message": "Invalid credentials"}, status_code=401
            )

    @app.route(f"{pam_url_prefix}/*", methods=["GET"])
    async def react(r: Request) -> Response:
        return JSONResponse(
            {"success": False, "message": str(NotImplementedError())}, status_code=501
        )

    logger.opt(colors=True).info(
        f"PAM WebUI 地址为<m>http://{DRIVER.config.host}:{DRIVER.config.port}{pam_url_prefix}</m>",
    )
