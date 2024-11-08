from pydantic import BaseModel
from pydantic import Field
from nonebot import get_plugin_config


class Config(BaseModel):
    pam_host: str = Field(default="127.0.0.1")
    pam_port: int = Field(default=19198)
    m_message: bool = Field(default=True)

    pam_username: str = Field(default="admin")
    pam_password: str = Field(default="114514.1919810")


pam_config = get_plugin_config(Config)
