import json

import anyio
from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from ..config import config
from ..resource import SKILLS_CONFIG_PATH
from . import update as update
from .data_source import SKILLS_HELP_PATH, update_info
from .generate import get_skill_info, get_skill_list

# 分类
rarity = ["普通", "传说", "独特", "普通·继承", "独特·继承", "剧情", "活动"]
limit = ["通用", "短距离", "英里", "中距离", "长距离", "泥地", "逃马", "先行", "差行", "追马"]
color = ["绿色", "紫色", "黄色", "蓝色", "红色"]
skill_type = [
    "被动（速度）",
    "被动（耐力）",
    "被动（力量）",
    "被动（毅力）",
    "被动（智力）",
    "耐力恢复",
    "速度",
    "加速度",
    "出闸",
    "视野",
    "切换跑道",
    "妨害（速度）",
    "妨害（加速度）",
    "妨害（心态）",
    "妨害（智力）",
    "妨害（耐力恢复）",
    "妨害（视野）",
    "(未知)",
]
params = rarity + limit + color + skill_type


full_skill_help = on_command("马娘技能帮助")


@full_skill_help.handle()
async def get_help(matcher: Matcher):
    pic = await anyio.Path(SKILLS_HELP_PATH).read_bytes()
    await matcher.finish(MessageSegment.image(pic))


pfx_skill_query = on_command("查技能")


@pfx_skill_query.handle()
async def check_skill(matcher: Matcher, arg_msg: Message = CommandArg()):
    alltext = arg_msg.extract_plain_text().replace(")", "）").replace("(", "（")
    skill_list = alltext.split()
    if not skill_list:
        await matcher.finish("请在指令后添加需要查询的内容")

    f_data = json.loads(await anyio.Path(SKILLS_CONFIG_PATH).read_text(encoding="u8"))

    if len(skill_list) == 1 and not all(elem in params for elem in skill_list):
        # 按技能名查询
        skill_name = skill_list[0]
        msg = await get_skill_info(skill_name, f_data)

    else:
        # 多于一个参数或在参数列表中就按分类查询
        skill_list = list(set(skill_list))  # 去重
        rarity_list, limit_list, color_list, skill_type_list = [], [], [], []
        for param in skill_list:
            if param in rarity:
                rarity_list.append(param)
            elif param in limit:
                limit_list.append(param)
            elif param in color:
                color_list.append(param)
            elif param in skill_type:
                skill_type_list.append(param)

        # 未识别出技能类型
        if not (rarity_list + limit_list + color_list + skill_type_list):
            await matcher.finish("没有识别出任何检索条件呢")

        # 当 稀有度 或 条件限制 或 颜色 不止一个参数输入时，那返回必然无结果
        if len(rarity_list) > 1 or len(limit_list) > 1 or len(color_list) > 1:
            await matcher.finish("没有搜索出任何马娘技能呢，请确保你输入的检索条件正确且无冲突！")

        msg = await get_skill_list(
            rarity_list[0] if rarity_list else "",
            limit_list[0] if limit_list else "",
            color_list[0] if color_list else "",
            skill_type_list,
            f_data,
        )
    await matcher.finish(msg)


full_skill_update = on_command("手动更新马娘技能")


# 手动更新本地数据
@full_skill_update.handle()
async def force_update(matcher: Matcher, ev: MessageEvent):
    if ev.get_user_id() not in config.superusers:
        msg = "很抱歉您没有权限进行此操作，该操作仅限维护组"
        await matcher.finish(msg)

    try:
        await update_info()
    except Exception as e:
        logger.exception("马娘技能信息刷新失败")
        await matcher.finish(f"马娘技能信息刷新失败：{e}")
    else:
        await matcher.finish("马娘技能信息刷新完成")
