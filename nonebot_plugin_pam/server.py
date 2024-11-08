"""
后台接口。
"""

import secrets

import sanic.response as response

from sanic import Sanic
from sanic.request import Request
from sanic.response.types import HTTPResponse

# if __name__ == "__main__":
from utils import AttrDict

pam_config = AttrDict(
    {
        "pam_host": "127.0.0.1",
        "pam_port": 8000,
        "pam_username": "admin",
        "pam_password": "114514.1919810",
    }
)
# else:
#     from .config import pam_config

APP = Sanic("NonebotPAM")
AUTH_KEY = secrets.token_hex(32)


@APP.route("v1/reload", methods=["GET", "POST"])
async def reload(r: Request) -> HTTPResponse:
    return response.json({"status": str(NotImplementedError())}, status=503)


@APP.route("/api/auth", methods=["POST", "GET"])
async def authenticate(r: Request) -> HTTPResponse:
    if r.method == "GET":
        if r.headers.get("Authorization", None) == f"Bearer {AUTH_KEY}":
            return response.json({"success": True})
        else:
            return response.json(
                {"success": False, "message": "Please use post to login."}, status=401
            )

    data = r.json
    username = data.get("username")
    password = data.get("password")
    if username == pam_config.pam_username and password == pam_config.pam_password:
        return response.json({"success": True, "auth_key": AUTH_KEY})
    else:
        return response.json(
            {"success": False, "message": "Invalid credentials"}, status=401
        )


if __name__ == "__main__":
    APP.run(host=pam_config.pam_host, port=pam_config.pam_port)
