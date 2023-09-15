from typing import Set

from nonebot import get_driver
from pydantic import BaseModel


class ConfigModel(BaseModel):
    superusers: Set[str]


config: ConfigModel = ConfigModel.parse_obj(get_driver().config.dict())
