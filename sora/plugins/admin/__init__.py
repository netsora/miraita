from nonebot import require
from nonebot.rule import to_me

require("nonebot_plugin_saa")
require("nonebot_plugin_alconna")

from nonebot_plugin_saa import Text
from nonebot_plugin_alconna import (
    Args,
    Query,
    Option,
    Alconna,
    Subcommand,
    CommandMeta,
    namespace,
    on_alconna,
)

from sora.log import logger
from sora.hook import on_startup
from sora.utils.api import random_text
from sora.utils.annotated import UserInfo
from sora.permission import get_admin_list, get_helper_list

from .utils import check_permission

authorize: str = ""

__usage__ = """
USER
查看 Bot管理员 列表：/admin -l

BOT_ADMIN
初始化权限：/admin -i <token>
增加管理员：/admin add -a <user_id>
增加协助者：/admin add -h <user_id>
取消管理员：/admin remove -a <user_id>
取消协助者：/admin remove -h <user_id>
"""

with namespace("Sora") as ns:
    ns.builtin_option_name["help"] = {"--h", "--help"}
    admin = on_alconna(
        Alconna(
            "admin",
            Option("-l|--list", help_text="查看 Bot管理员 列表"),
            Option("-i|--init", Args["token", str], help_text="初始化权限"),
            Subcommand(
                "add",
                Option("-a|--admin", Args["target?", int], help_text="增加 Bot管理员"),
                Option("-h|--helper", Args["target?", int], help_text="增加 Bot协助者"),
            ),
            Subcommand(
                "remove",
                Option("-a|--admin", Args["target?", int], help_text="取消 Bot管理员"),
                Option("-h|--helper", Args["target?", int], help_text="取消 Bot协助者"),
            ),
            meta=CommandMeta(
                description="Bot管理员相关指令",
                usage=__usage__,
                example="/admin -l",
                compact=True,
            ),
        ),
        priority=5,
        block=True,
        rule=to_me(),
    )
admin.shortcut(
    r"(添加|增加)管理员\s+(\d+)",
    command="admin add --admin",
    arguments=["{1}"],
    fuzzy=True,
    prefix=True,
)
admin.shortcut(
    r"(添加|增加)协助者\s+(\d+)",
    command="admin add --helper",
    arguments=["{1}"],
    fuzzy=True,
    prefix=True,
)
admin.shortcut(
    r"(移除|取消)管理员\s+(\d+)",
    command="admin remove --admin",
    arguments=["{1}"],
    fuzzy=True,
    prefix=True,
)
admin.shortcut(
    r"(移除|取消)协助者\s+(\d+)",
    command="admin remove --helper",
    arguments=["{1}"],
    fuzzy=True,
    prefix=True,
)


@admin.assign("list")
async def list():
    admin_list = await get_admin_list()
    helper_list = await get_helper_list()

    await Text(f"Bot管理员列表：\n{admin_list}\nBot协助者列表：\n{helper_list}").send(
        at_sender=True
    )
    await admin.finish()


@admin.assign("init")
async def init(user: UserInfo, token: str):
    global authorize
    if token == authorize:
        await user.filter(uid=user.uid).update(permission="ADMIN")
        await Text("已成功授权 Bot管理员 权限").send(at_sender=True)
    else:
        await Text("token不对呢，返回控制台检查一下吧").send(at_sender=True)
    await admin.finish()


@admin.assign("add")
async def add(
    user: UserInfo,
    admin_target: Query[int] = Query("add.admin.target"),
    helper_target: Query[int] = Query("add.helper.target"),
):
    if not await check_permission(user.uid, "ADMIN"):
        await Text("权限不足，需 Bot管理员 权限").send(at_sender=True)
        await admin.finish()

    if admin_target.available:
        if await user.filter(bind__uid=str(admin_target.result)).exists():
            await user.filter(uid=admin_target.result).update(permission="ADMIN")
            await Text(f"已成功增加 Bot管理员：{admin_target.result}").send(
                at_sender=True
            )

        elif admin_target.result == 0:
            ...

        else:
            await Text(f"用户 {admin_target.result} 不存在").send(at_sender=True)

    if helper_target.available:
        if await user.filter(bind__uid=str(admin_target.result)).exists():
            await user.filter(uid=helper_target.result).update(permission="HELPER")
            await Text(f"已成功增加 Bot协助者：{helper_target.result}").send(
                at_sender=True
            )

        elif helper_target.result == 0:
            ...

        else:
            await Text(f"用户 {helper_target.result} 不存在").send(at_sender=True)

    await admin.finish()


@admin.assign("remove")
async def remove(
    user: UserInfo,
    admin_target: Query[int] = Query("remove.admin.target"),
    helper_target: Query[int] = Query("remove.helper.target"),
):
    if not await check_permission(user.uid, "ADMIN"):
        await Text("权限不足，需 Bot管理员 权限").send(at_sender=True)
        await admin.finish()

    if admin_target.available:
        if await user.filter(bind__uid=str(admin_target.result)).exists():
            await user.filter(uid=admin_target.result).update(permission="NORMAL")
            await Text(f"已取消 {admin_target.result} 的 Bot管理员 身份").send(
                at_sender=True
            )

        elif admin_target.result == 0:
            ...

        else:
            await Text(f"用户 {admin_target.result} 不存在").send(at_sender=True)

    if helper_target.available:
        if await user.filter(bind__uid=str(admin_target.result)).exists():
            await user.filter(uid=helper_target.result).update(permission="NORMAL")
            await Text(f"已取消 {helper_target.result} 的 Bot协助者 身份").send(
                at_sender=True
            )

        elif helper_target.result == 0:
            ...

        else:
            await Text(f"用户 {helper_target.result} 不存在").send(at_sender=True)

    await admin.finish()


@on_startup
async def atuhorize_admin():
    if not await get_admin_list():
        global authorize
        authorize = random_text(20)
        logger.info(f"已自动生成授权token：{authorize}")
        logger.info(f"在任意平台发送 /admin -i {authorize} 即可获取 Bot管理员 权限")
