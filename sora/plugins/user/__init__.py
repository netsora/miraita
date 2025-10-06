import inspect

import pandas as pd
from nonebot import require
from nonebot.rule import to_me
from nonebot.internal.adapter.bot import Bot
from nonebot.internal.adapter.event import Event

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
from sora.utils.api import random_text
from sora.utils.annotated import UserInfo
from sora.database.models import Bind, User

from .model import token_manager, validate_token

__usage__ = """
绑定：@bot /bind <token>
获取token：@bot /bind -t [自定义token]
取消绑定：@bot /bind -r
绑定列表：@bot /bind -l

（指令别名：/bind）
（注：所有 token 均为 一次性token，使用过后需重新生成）
"""

__example__ = """
假如您希望在QQ频道绑定群聊中的账号数据，则您应该在群聊中输入
> 用户：@bot /bind -t [可以在此处自定义 token]
> Bot：已为您生成一次性token：sora/123456

然后，您需要复制此token，来到QQ频道
> 用户：@bot /bind sora/123456
> Bot：绑定成功
"""

bind = on_alconna(
    Alconna(
        "bind",
        Args["input_token?", str],
        Option("-t|--token", Args["token?", str], help_text="生成token"),
        Option(
            "-l|--list",
            Args["target?", At],
            alias={"列表", "信息"},
            help_text="查询绑定信息",
        ),
        Option("-r|--rebind", alias={"取消"}, help_text="取消绑定"),
        meta=CommandMeta(
            description="将不同平台的用户数据绑定",
            usage=__usage__,
            example=__example__,
            compact=True,
        ),
    ),
    priority=5,
    block=True,
    rule=to_me(),
)
bind.shortcut("绑定", command="bind", prefix=True)
bind.shortcut("rebind", command="bind --rebind", prefix=True)

user = on_alconna(
    Alconna(
        "user",
        Args["target?", At | int],
        meta=CommandMeta(
            description="查询用户信息",
            usage="@bot /user [@|uid]",
            example="""
            @bot /user @Komorebi
            @bot /user 123456789
            """,
            compact=True,
        ),
    )
)


@bind.assign("$main")
async def bind_(userInfo: UserInfo, input_token: Match[str]):
    if input_token.available:
        validation_result = validate_token(input_token.result)
        if validation_result.is_valid and validation_result.uid is not None:
            await Bind.bind(origin_uid=userInfo.uid, bind_uid=validation_result.uid)
            bindUserInfo = await User.get_user_by_uid(validation_result.uid)
            await Text(
                inspect.cleandoc(
                    f"""
                绑定成功\n
                已将 {userInfo.user_name}({userInfo.uid}) 与 {bindUserInfo.user_name}({bindUserInfo.uid}) 绑定
                """
                )
            ).send(at_sender=True)
            logger.debug(
                f"{userInfo.user_name}({userInfo.uid}) 与 {bindUserInfo.user_name}({bindUserInfo.uid}) 绑定"
            )
        else:
            await Text("绑定失败，密钥错误！").send(at_sender=True)
    else:
        await Text("格式错误。输入 /help 绑定 查看其详细用法").send(at_sender=True)
    token_manager.remove_token(validation_result.uid)  # type: ignore

    await bind.finish()


@bind.assign("token")
async def token_(user: UserInfo, token: Match[str]):
    if token.available:
        if token.result == "random":
            random_token = random_text(15, prefix="Sora/")
            token_manager.add_token(user.uid, random_token)
            await Text(f"已为您生成一次性token：{random_token}").send(at_sender=True)
        else:
            token_manager.add_token(user.uid, token.result)
            await Text(f"一次性token设置成功：{token.result}").send(at_sender=True)
    else:
        random_token = random_text(15, prefix="Sora/")
        token_manager.add_token(user.uid, random_token)
        await Text(f"已为您生成一次性token：{random_token}").send(at_sender=True)
    await bind.finish()


@bind.assign("list")
async def bind_list_(event: Event, target: Match[At]):
    if target.available:
        bindInfo = await Bind.get_user_bind(pid=target.result.target)
        df = pd.DataFrame(bindInfo)
        await Text(df.to_string(index=False)).send(at_sender=True)
        await bind.finish()

    bindInfo = await Bind.get_user_bind(pid=event.get_user_id())
    df = pd.DataFrame(bindInfo)
    await Text(df.to_string(index=False)).send(at_sender=True)
    await bind.finish()


@bind.assign("rebind")
async def rebind(bot: Bot, userInfo: UserInfo):
    uid = userInfo.uid
    origin_uid = (await Bind.get(uid=uid, platform=bot.type)).origin_uid
    if origin_uid is None:
        await Text("您还未绑定过其他账号").finish(at_sender=True)
    await Bind.cancel(origin_uid, uid, platform=bot.type)
    await Text("已取消绑定").send(at_sender=True)
    await bind.finish()


@user.handle()
async def user_(bot: Bot, event: Event, target: Match[At | int]):
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
    else:
        target_user = await User.get_user_by_event(event)

    bind_info = await Bind.get(uid=target_user.uid, platform=bot.type)

    await Text(
        inspect.cleandoc(
            f"""
        平台名：{bind_info.platform}
        用户ID：{bind_info.uid}
        平台ID：{bind_info.pid}
        用户名：{target_user.user_name}
        注册时间：{(target_user.register_time).strftime('%Y-%m-%d %H:%M:%S')}
        """
        )
    ).finish()
