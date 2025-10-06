"""
该钩子为事件预处理钩子
用来在处理事件前先判断用户是否存在
如果不存在则自动为其注册账号
"""

import inspect

from nonebot import require
from nonebot.params import Depends
from nonebot.internal.adapter import Bot
from nonebot.message import run_preprocessor
from nonebot.adapters.qq.exception import AuditException

require("nonebot_plugin_saa")
require("nonebot_plugin_userinfo")
from nonebot_plugin_userinfo import UserInfo, EventUserInfo
from nonebot_plugin_saa import MessageFactory, PlatformTarget, extract_target

from sora.log import logger
from sora.database import Bind, Sign, User
from sora.utils.api import generate_id, random_text


@run_preprocessor
async def _(
    bot: Bot,
    user: UserInfo = EventUserInfo(),
    target: PlatformTarget = Depends(extract_target),
):
    uid = generate_id()
    pid = user.user_id
    user_name = user.user_name
    platform = bot.adapter.get_name()
    exist = await User.check_exists(platform, pid)

    if not exist:
        if await User.check_username(user_name):
            user_name += random_text(2)

        userinfo: User = await User.create_user(uid, user_name)
        await Sign.create(uid=uid)
        await Bind.create(uid=uid, platform=platform, pid=pid, info=userinfo)

        logger.success(f"用户 {user_name}({uid}) 账号信息初始化成功！")

        try:
            await MessageFactory(
                inspect.cleandoc(
                    f"""
                    第一次使用林汐？
                    我们已为您注册全新的账户！
                    - 用户名：{user_name}（lv.1）
                    - ID：{uid}
                    顺便奖励您 50 枚硬币。
                    『提示』如果您在其它平台已有账户，可发送 /bind 指令绑定！
                    """
                )
            ).send_to(target, bot)
        except AuditException:
            pass
