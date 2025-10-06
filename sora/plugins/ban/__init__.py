from nonebot import require
from nonebot.rule import to_me
from nonebot.internal.adapter import Bot

require("nonebot_plugin_saa")
require("nonebot_plugin_alconna")
from nonebot_plugin_saa import Text
from arclet.alconna.args import Args
from arclet.alconna.base import Option
from arclet.alconna.core import Alconna
from arclet.alconna.typing import CommandMeta
from nonebot_plugin_alconna import Match, on_alconna
from nonebot_plugin_alconna.uniseg.segment import At

from sora.log import logger
from sora.database import Ban, User
from sora.permission import ADMIN, HELPER

ban = on_alconna(
    Alconna(
        "ban",
        Option(
            "add",
            Args["target", At | int]["hours?", int]["minutes?", int],
            help_text="封禁用户",
        ),
        Option("remove", Args["target", At | int], help_text="解封用户"),
        Option("-l|--list", help_text="查询所有被封禁用户"),
        meta=CommandMeta(
            description="你被逮捕了！丢进小黑屋！",
            usage="@bot /ban <at | user_id> [小时] [分钟]",
            example="""
            @bot /ban add @user
            @bot /ban add 2023081136 2
            @bot /ban add @user 2 30
            @bot /ban remove @user
            @bot /ban -l
            """,
            compact=True,
        ),
    ),
    priority=5,
    block=True,
    rule=to_me(),
    permission=ADMIN | HELPER,
)


@ban.assign("add")
async def add(
    bot: Bot,
    target: At | int,
    hours: Match[int],
    minutes: Match[int],
):
    if isinstance(target, At):
        pid = target.target
        if pid == bot.self_id:
            await Text("不要禁我，会把我弄哭的哦").finish(at_sender=True)
        if not await User.check_exists(bot.adapter.get_name(), pid):
            await Text("您@的用户还未注册喔").finish(at_sender=True)
        uid = (await User.get_user_by_pid(pid)).uid
    else:
        uid = str(target)

    user_name = (await User.get_user_by_uid(uid)).user_name

    if hours.available:
        if minutes.available:
            minutes_result = minutes.result
        else:
            minutes_result = 0
        hours_result = hours.result
        logger.info(
            f"封禁目标：{uid}({user_name})，时长：{hours_result}小时{minutes_result}分钟"
        )
        await Ban.ban(uid, duration=convert_to_seconds(hours_result, minutes_result))
        await Text(
            f"已成功封禁用户：{uid}({user_name})，时长：{hours_result}小时{minutes_result}分钟"
        ).send(at_sender=True)
    else:
        logger.info(f"永久封禁目标：{uid}({user_name})")
        await Ban.ban(uid, duration=-1)
        await Text(f"已永久封禁用户：{uid}({user_name})").send(at_sender=True)

    await ban.finish()


@ban.assign("remove")
async def unban(
    bot: Bot,
    target: At | int,
    hours: Match[int],
    minutes: Match[int],
):
    if isinstance(target, At):
        pid = target.target
        if not await User.check_exists(bot.adapter.get_name(), pid):
            await Text("您@的用户还未注册喔").finish(at_sender=True)
        uid = (await User.get_user_by_pid(pid)).uid
    else:
        uid = str(target)

    user_name = (await User.get_user_by_uid(uid)).user_name

    if hours.available:
        if minutes.available:
            minutes_result = minutes.result
        else:
            minutes_result = 0
        hours_result = hours.result
        logger.info(
            f"封禁目标：{uid}({user_name})，时长：{hours_result}小时{minutes_result}分钟"
        )
        await Ban.unban(uid)
        await Text(
            f"已成功封禁用户：{uid}({user_name})，时长：{hours_result}小时{minutes_result}分钟"
        ).send(at_sender=True)
    else:
        logger.info(f"永久封禁目标：{uid}({user_name})")
        await Ban.unban(uid)
        await Text(f"已永久封禁用户：{uid}({user_name})").send(at_sender=True)

    await ban.finish()


@ban.assign("list")
async def list():
    ban_users = await Ban.all()
    if ban_users:
        message = "\n".join(
            [
                f"ID: {ban_user.id}\n"
                f"用户ID: {ban_user.uid}\n"
                f"封禁开始时间: {ban_user.ban_time}\n"
                f"封禁时长: {ban_user.duration}\n"
                for ban_user in ban_users
            ]
        )
    else:
        message = "当前还没有被封禁用户呢"
    await Text(message).finish(at_sender=True)


def convert_to_seconds(hours: int, minutes: int):
    total_minutes = hours * 60 + minutes
    total_seconds = total_minutes * 60
    return total_seconds
