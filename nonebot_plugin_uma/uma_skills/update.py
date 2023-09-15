from nonebot import get_driver, logger
from nonebot_plugin_apscheduler import scheduler

from .data_source import judge_update, update_info


async def do_update():
    flag = await judge_update()
    if not flag:
        logger.info("马娘技能没有更新")
        return

    logger.info("马娘技能检测到更新，正在开始更新")
    try:
        await update_info()
    except Exception:
        logger.exception("马娘技能信息刷新失败")
    else:
        logger.success("马娘技能信息刷新完成")


driver = get_driver()
driver.on_startup(do_update)

# 每小时自动更新
scheduler.add_job(do_update, "cron", hour="*")
