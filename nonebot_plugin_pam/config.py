from pydantic import BaseModel
from pydantic import Field
from nonebot import get_plugin_config


class Config(BaseModel):
    m_message: bool = Field(default=True)

    pam_username: str = Field(default="admin")
    pam_password: str = Field(default="114514.1919810")

    redis_url: str = Field(default="")


pam_config = get_plugin_config(Config)
