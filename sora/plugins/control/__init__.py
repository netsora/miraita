import os
import asyncio
import platform

from nonebot import require
from nonebot.rule import to_me

require("nonebot_plugin_saa")
require("nonebot_plugin_alconna")
from nonebot_plugin_saa import Text
from arclet.alconna.args import Args
from arclet.alconna.core import Alconna
from arclet.alconna.typing import CommandMeta
from nonebot_plugin_alconna.uniseg import UniMessage
from nonebot_plugin_alconna import Match, MultiVar, AlconnaMatcher, on_alconna

from sora.config import bot_config
from sora.version import __version__
from sora.permission import ADMIN, HELPER
from sora.utils.helpers import HandleCancellation
from sora.utils.update import CheckUpdate, update

nickname = list(bot_config.nickname)

update_cmd = on_alconna(
    Alconna(
        "更新",
        meta=CommandMeta(
            description="更新林汐",
            usage="@bot /更新",
            example="@bot /更新",
            compact=True,
        ),
    ),
    permission=ADMIN | HELPER,
    rule=to_me(),
    priority=1,
    block=True,
)
check_update_cmd = on_alconna(
    Alconna(
        "检查更新",
        meta=CommandMeta(
            description="检查更新",
            usage="@bot /检查林汐版本",
            example="@bot /检查更新",
            compact=True,
        ),
    ),
    permission=ADMIN | HELPER,
    rule=to_me(),
    priority=1,
    block=True,
)

reboot = on_alconna(
    Alconna(
        "reboot",
        meta=CommandMeta(
            description="重启林汐",
            usage="@bot /reboot",
            example="@bot /reboot",
            compact=True,
        ),
    ),
    permission=ADMIN | HELPER,
    rule=to_me(),
    priority=1,
    block=True,
)
run_cmd = on_alconna(
    Alconna(
        "cmd",
        Args["cmd?", MultiVar(str, "*")],
        meta=CommandMeta(
            description="运行终端命令",
            usage="@bot /cmd",
            example="@bot /cmd",
            compact=True,
        ),
    ),
    permission=ADMIN,
    rule=to_me(),
    priority=1,
    block=True,
)


@update_cmd.handle()
async def _():
    await update_cmd.send(f"{nickname[0]}开始更新", at_sender=True)
    result = await update()
    await Text(result).send(at_sender=True)
    await update_cmd.finish()


@check_update_cmd.handle()
async def _():
    latest_version, update_time = await CheckUpdate.show_latest_version()
    if latest_version and update_time:
        if latest_version != __version__:
            await Text(
                f"新版本已发布, 请更新\n最新版本: {latest_version} 更新时间: {update_time}"
            ).send(at_sender=True)
        else:
            await Text("当前已是最新版本").send(at_sender=True)
    await check_update_cmd.finish()


@reboot.handle()
async def _():
    await Text(f"开始重启{nickname[0]}..请稍等...").send(at_sender=True)
    if str(platform.system()).lower() == "windows":
        import sys

        python = sys.executable
        os.execl(python, python, *sys.argv)
    else:
        os.system("./restart.sh")


@run_cmd.handle()
async def _(matcher: AlconnaMatcher, cmd: Match[tuple[str, ...]]):
    if cmd.available:
        cmd_result = " ".join(cmd.result)
        matcher.set_path_arg("cmd", cmd_result)


@run_cmd.got_path(
    "cmd",
    prompt=UniMessage.template(
        "{:At(user, $event.get_user_id())} 请输入你要运行的命令"
    ),
    parameterless=[HandleCancellation("已取消")],
)
async def _(cmd: str):
    await Text(f"开始执行 {cmd}").send(at_sender=True)
    p = await asyncio.subprocess.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await p.communicate()
    try:
        result = (stdout or stderr).decode("utf-8")
    except Exception:
        result = str(stdout or stderr)
    await Text(f"{cmd}\n运行结果：\n{result}").send(at_sender=True)
    await run_cmd.finish()
