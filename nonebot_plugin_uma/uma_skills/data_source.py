import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, TypedDict

import anyio
from bs4 import BeautifulSoup
from httpx import AsyncClient

from ..resource import SKILLS_CONFIG_PATH

SKILL_URL = "https://wiki.biligame.com/umamusume/技能速查表"
UPDATE_URL = "https://wiki.biligame.com/umamusume/index.php?title=技能速查表&action=history"

SKILLS_HELP_PATH = Path(__file__).parent / "res" / "uma_skills_help.png"


class SkillInfoDict(TypedDict):
    中文名: str
    稀有度: str
    颜色: str
    繁中译名: str
    条件限制: str
    技能数值: str
    持续时间: str
    评价分: str
    需要PT: str
    PT评价比: str
    触发条件: str
    技能类型: str


class SkillConfigDict(TypedDict):
    last_time: str
    cn_name_dict: Dict[str, str]
    tw_name_dict: Dict[str, str]
    skills: Dict[str, SkillInfoDict]


# 获取最新的更新时间
async def get_update_time():
    async with AsyncClient() as client:
        resp = await client.get(UPDATE_URL, timeout=10)
        text = resp.text
    soup = BeautifulSoup(text, "lxml")

    time_anchor = soup.find("a", {"class": "mw-changeslist-date"})
    assert time_anchor
    last_time_tmp = time_anchor.text.replace(" ", "")

    group = re.search(
        r"^([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日\S*([0-9]{2}):([0-9]{2})$",
        last_time_tmp,
    )
    assert group
    year, month, day, hour, minute = (int(x) for x in group.groups())
    return datetime(year, month, day, hour, minute)


# 23-04-03新版更新数据
async def update_info():
    async with AsyncClient() as client:
        resp = await client.get(SKILL_URL, timeout=10)
        text = resp.text
    soup = BeautifulSoup(text, "lxml")

    res_tag = soup.find("div", {"id": "jn-json"})
    assert res_tag
    data_list_str = (
        res_tag.text.replace(" ", "")
        .replace("<br/>", "")
        .replace("&#160;", "_")
        .replace(",]", "]")
    )
    data_list = json.loads(data_list_str)

    last_time = str(await get_update_time())  # 最新版的更新时间
    cn_name_dict = {}
    tw_name_dict = {}
    skills = {}

    f_data: SkillConfigDict = {
        "last_time": last_time,
        "cn_name_dict": cn_name_dict,
        "tw_name_dict": tw_name_dict,
        "skills": skills,
    }

    for data in data_list:
        rarity = data["5"]
        skill_name_jp = data["1"]
        skill_name_cn = data["4"]
        skill_name_tw = data["21"]

        # 额外处理一下继承技能
        if rarity == "普通·继承":
            skill_name_jp = "继承技/" + skill_name_jp
            skill_name_cn = "继承技/" + skill_name_cn
            skill_name_tw = "继承技/" + skill_name_tw

        # 注：嘉年华活动技能就不做额外处理了，仅保留最新的
        each_tr_dict: SkillInfoDict = {
            "中文名": skill_name_cn,
            "稀有度": rarity,
            "颜色": data["7"],
            "繁中译名": skill_name_tw,
            "条件限制": data["6"],
            "技能数值": data["12"],
            "持续时间": data["13"],
            "评价分": data["18"],
            "需要PT": data["19"],
            "PT评价比": data["20"],
            "触发条件": data["10"],
            "技能类型": data["11"],
        }

        cn_name_dict[skill_name_cn] = skill_name_jp
        tw_name_dict[skill_name_tw] = skill_name_jp
        skills[skill_name_jp] = each_tr_dict

    # 都做完了再写入
    path = anyio.Path(SKILLS_CONFIG_PATH)
    await path.write_text(
        json.dumps(f_data, ensure_ascii=False, indent=2),
        encoding="u8",
    )


# 判断是否有更新
async def judge_update():
    path = anyio.Path(SKILLS_CONFIG_PATH)
    if not (await path.exists()):
        return True

    f_data: SkillConfigDict = json.loads(
        await path.read_text(encoding="u8"),
    )
    set_time = datetime.strptime(f_data["last_time"], "%Y-%m-%d %H:%M:%S")
    last_time = await get_update_time()
    return last_time > set_time
