"""
后台接口。
"""

import sanic.response as response

from sanic import Sanic
from sanic.request import Request
from sanic.response.types import HTTPResponse

APP = Sanic("NonebotPAM")


@APP.route("v1/reload", methods=["GET", "POST"])
async def reload(r: Request) -> HTTPResponse:
    return response.json({"status": str(NotImplementedError())}, status=503)
