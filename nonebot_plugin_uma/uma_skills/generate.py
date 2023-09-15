from typing import List, Tuple, Union

from fuzzywuzzy import process
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot_plugin_htmlrender import md_to_pic

from ..utils import md_escape
from .data_source import SkillConfigDict, SkillInfoDict


def create_msg(skill_name: str, f_data: SkillConfigDict):
    skill_trans: SkillInfoDict = f_data["skills"][skill_name]
    return (
        f"技能名：{skill_name}\n"
        f"中文名：{skill_trans['中文名']}\n"
        f"稀有度：{skill_trans['稀有度']}\n"
        f"颜色：{skill_trans['颜色']}\n"
        f"繁中译名：{skill_trans['繁中译名']}\n"
        f"条件限制：{skill_trans['条件限制']}\n"
        f"技能数值：{skill_trans['技能数值']}\n"
        f"持续时间：{skill_trans['持续时间']}\n"
        f"需要PT：{skill_trans['需要PT']}\n"
        f"评价分：{skill_trans['评价分']}\n"
        f"PT评价比：{skill_trans['PT评价比']}\n"
        f"触发条件：{skill_trans['触发条件']}\n"
        f"技能类型：{skill_trans['技能类型']}"
    )


# 获取马娘技能内容
async def get_skill_info(skill_name: str, f_data: SkillConfigDict) -> str:
    jp_name_list = list(f_data["skills"].keys())

    # 若名字在日文名里
    if skill_name in jp_name_list:
        return create_msg(skill_name, f_data)

    cn_name_dict = f_data["cn_name_dict"]
    tw_name_dict = f_data["tw_name_dict"]
    cn_name_list = list(cn_name_dict.keys())
    tw_name_list = list(tw_name_dict.keys())

    # 若名字在中文名里
    if skill_name in cn_name_list:
        jp_name_tmp = cn_name_dict[skill_name]
        return create_msg(jp_name_tmp, f_data)

    # 若名字在繁中文名里
    if skill_name in tw_name_list:
        jp_name_tmp = tw_name_dict[skill_name]
        return create_msg(jp_name_tmp, f_data)

    # 如果都不在，就进行相似度检测
    # 全部中日名字的列表，去重
    all_name_list = list(set(jp_name_list + cn_name_list + tw_name_list))
    res = process.extractOne(skill_name, all_name_list)
    if not res:
        return "未找到相关技能"

    skill_name = res[0]
    score = res[1]
    return f"未找到相关技能，您有{score}%的可能在查询技能：{skill_name}"


SkillInfoType = List[Tuple[str, SkillInfoDict]]


# 生成图片
async def create_img(title: str, info_data: SkillInfoType) -> bytes:
    if not info_data:
        raise ValueError("info_data is empty")

    table_head = ["技能名", *list(info_data[0][1].keys())]
    table_rows = [
        [
            name,
            trans["中文名"],
            trans["稀有度"].replace("·", ""),
            trans["颜色"],
            trans["繁中译名"],
            trans["条件限制"],
            trans["技能数值"],
            trans["持续时间"],
            trans["评价分"],
            trans["需要PT"],
            trans["PT评价比"],
            trans["触发条件"],
            trans["技能类型"],
        ]
        for name, trans in info_data
    ]

    title = md_escape(title)
    table_head_md = f"|{'|'.join(table_head)}|"
    table_align_md = f"|{'|'.join([':-:' for _ in table_head])}|"
    table_rows_md = "\n".join(
        [f"|{'|'.join([md_escape(i) for i in row])}|" for row in table_rows],
    )
    extra_html = "<style>.markdown-body { max-width: 100% !important; }</style>"
    md = f"# {title}\n\n{table_head_md}\n{table_align_md}\n{table_rows_md}\n\n{extra_html}"
    return await md_to_pic(md, width=1800, type="jpeg")


# 获取马娘技能列表
async def get_skill_list(
    rarity: str,
    limit: str,
    color: str,
    skill_type_list: list,
    f_data: SkillConfigDict,
) -> Union[str, MessageSegment]:
    infos: List[Tuple[str, SkillInfoDict]] = []

    skills = f_data["skills"]
    for skill_jp_name in skills:
        skill_trans = skills[skill_jp_name]

        # 如果前面三个值为空就等于当前稀有度，以便过判断
        rarity_tmp = rarity if rarity else skill_trans["稀有度"]
        limit_tmp = limit if limit else skill_trans["条件限制"]
        color_tmp = color if color else skill_trans["颜色"]

        # 当前技能类型列表
        skill_type_text = (
            skill_trans["技能类型"]
            .replace("条件1: ", "、")
            .replace("条件2: ", "、")
            .replace("条件3: ", "、")
        )
        currrent_type_list = []
        for tp in skill_type_text.split("、"):
            if tp and (tp not in currrent_type_list):
                currrent_type_list.append(tp)

        # 类型列表为空就等于当前列表
        type_list_tmp = skill_type_list if skill_type_list else currrent_type_list

        # 判断条件
        if (
            rarity_tmp == skill_trans["稀有度"]
            and limit_tmp == skill_trans["条件限制"]
            and color_tmp == skill_trans["颜色"]
            and all(elem in currrent_type_list for elem in type_list_tmp)
        ):
            infos.append((skill_jp_name, skill_trans))

    # 如果未找到任何数据
    if not infos:
        return "没有搜索出任何马娘技能呢，请确保你输入的检索条件正确且无冲突！"

    # 如果结果就一个就不需要合成图片了
    if len(infos) == 1:
        return create_msg(infos[0][0], f_data)

    name_list = []
    for name in [rarity, limit, color, *skill_type_list]:
        if name and (name not in name_list):
            name_list.append(name)
    title = f"检索：{' + '.join(name_list)} 的结果"

    return MessageSegment.image(await create_img(title, infos))
