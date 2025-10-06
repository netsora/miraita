import inspect
from datetime import date, datetime

from nonebot import require
from nonebot.rule import to_me
from tortoise.expressions import F
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

from sora.utils.annotated import UserInfo
from sora.database.models import Sign, User

from .config import GameConfig

sign_config = (GameConfig.load_config("game")).sign

sign = on_alconna(
    Alconna(
        "sign",
        Option("info", Args["target?", At | int], alias={"信息"}, help_text="签到信息"),
        meta=CommandMeta(
            description="每日打卡",
            usage="签到：@bot /签到\n签到信息：@bot /签到信息 [At]\n当日签到排行：@bot /签到排行",
            example="@bot /签到",
            compact=True,
        ),
    ),
    priority=20,
    rule=to_me(),
)

sign.shortcut("签到", prefix=True)


@sign.assign("$main")
async def _(user: UserInfo):
    uid = user.uid
    signInfo = await Sign.get_sign_info(uid)

    if signInfo is None:
        last_sign = None
        total_days = continuous_days = 0
    else:
        last_sign = signInfo.last_sign
        total_days = signInfo.total_days
        continuous_days = signInfo.continuous_days

    if last_sign is not None and last_sign.date() == date.today():
        await Text("您今日已经签到过了，不可重复签到").finish(at_sender=True)

    if last_sign is not None and abs((date.today() - last_sign.date()).days) == 1:
        continuous_days += 1
        extra_coin = int(continuous_days * 1.5)
        msg = (
            f"你当前连续签到 {str(continuous_days)} 天，额外奖励 {extra_coin} 枚硬币。"
        )
        await User.reward(uid, reward={"coin": extra_coin})
        await Sign.filter(uid=uid).update(continuous_days=F("continuous_days") + 1)
    else:
        msg = "你当前连续签到 0 天，"
        extra_coin = 0
        await Sign.filter(uid=uid).update(continuous_days=0)

    amount = await User.reward(uid, reward=sign_config.rewards)
    await Sign.filter(uid=uid).update(
        total_days=total_days + 1, last_sign=datetime.now()
    )

    sign_coin = amount["coin"] + extra_coin
    sign_exp = amount["exp"]
    sign_favor = amount["favor"]

    await Text(
        inspect.cleandoc(
            f"""
            签到成功！
            {msg}历史最高 {str(total_days + 1)} 天。
            ——————————————
            ۞≡==——☚◆☛——==≡۞
            ➢[金币+{sign_coin}]
                    —— Now: {user.coin + sign_coin}
            ➢[好感+{sign_favor}]
                    —— Now: {user.favor + sign_favor}
            ➢[经验+{sign_exp}]
                    —— Now: {user.exp + sign_exp}
            ۞≡==——☚◆☛——==≡۞
            —————————————
            """
        )
    ).send(at_sender=True)


@sign.assign("info")
async def _(bot: Bot, target: Match[At | int], userInfo: UserInfo):
    if target.available:
        if isinstance(target.result, At):
            pid = target.result.target
            if not await User.check_exists(bot.adapter.get_name(), pid):
                await Text("您@的用户还未注册喔").finish(at_sender=True)
            target_id = (await User.get_user_by_pid(pid)).uid
            target_user = await User.get_user_by_uid(target_id)
        else:
            target_id = str(target.result)
            target_user = await User.get_user_by_uid(target_id)
        call = target_user.user_name
    else:
        target_id = userInfo.uid
        call = "您"

    signInfo = await Sign.get_sign_info(target_id)

    if signInfo is None:
        await Text("你还没有签到过喔").finish(at_sender=True)

    await Text(
        f"{call}当前连续签到 {signInfo.continuous_days} 天，累计 {signInfo.total_days} 天"
    ).send(at_sender=True)
    await sign.finish()
