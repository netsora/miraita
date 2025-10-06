from typing import Literal
from collections import deque

from nonebot import require
from nonebot.rule import to_me

require("nonebot_plugin_saa")
require("nonebot_plugin_alconna")
from nonebot_plugin_saa import Text
from arclet.alconna.base import Option
from arclet.alconna.core import Alconna
from arclet.alconna.args import Arg, Args
from arclet.alconna.arparma import Arparma
from arclet.alconna.typing import CommandMeta
from arclet.alconna.manager import command_manager
from nonebot_plugin_alconna import Match, on_alconna, store_true
from nonebot_plugin_alconna.extension import Extension, add_global_extension

from .config import Config

config = Config.load_config()

_help = Alconna(
    "help",
    Args["plugin?", str],
    Option("--hide", action=store_true, default=False, help_text="是否列出隐藏命令"),
    meta=CommandMeta(
        description="获取林汐帮助文档",
        usage="@bot /help",
        example="@bot /help",
        compact=True,
    ),
)

_statis = Alconna(
    "statis",
    Arg("type", Literal["show", "most", "least"], "most"),
    Args["count", int, config.message_count],
    meta=CommandMeta(
        description="命令统计",
        usage="@bot /statis most",
        example="@bot /statis most",
        compact=True,
    ),
)

record = deque(maxlen=256)


class HelperExtension(Extension):
    @property
    def priority(self) -> int:
        return 5

    @property
    def id(self) -> str:
        return "SoraBot:HelperExtension"

    async def parse_wrapper(self, bot, state, event, res: Arparma) -> None:
        if res.source != _statis.path:
            record.append((res.source, res.origin))


add_global_extension(HelperExtension())

help_cmd = on_alconna(_help, auto_send_output=True, rule=to_me())
statis_cmd = on_alconna(_statis, auto_send_output=True, rule=to_me())
statis_cmd.shortcut("消息统计", {"args": ["show"], "prefix": True})
statis_cmd.shortcut("命令统计", {"args": ["most"], "prefix": True})


@help_cmd.handle()
async def _(plugin: Match[str]):
    if plugin.available:
        plugin_help = command_manager.command_help(plugin.result)
        if plugin_help is None:
            await Text("唔...没有找到帮助呢").finish(at_sender=True)
        else:
            await Text(plugin_help).finish(at_sender=True)

    await Text(
        command_manager.all_command_help(show_index=True, namespace="Alconna")
    ).send(at_sender=True)
    await help_cmd.finish()


@statis_cmd.assign("type", "show")
async def statis_cmd_show(count: int):
    if not record:
        await statis_cmd.finish("暂无命令记录")

    await statis_cmd.finish(
        "最近的命令记录为：\n"
        + "\n".join([f"[{i}]: {record[i][1]}" for i in range(min(count, len(record)))])
    )


@statis_cmd.assign("type", "most")
async def statis_cmd_most(arp: Arparma):
    if not record:
        await statis_cmd.finish("暂无命令记录")

    length = len(record)
    table = {}
    for i, r in enumerate(record):
        source = r[0]
        if source not in table:
            table[source] = 0
        table[source] += i / length
    sort = sorted(table.items(), key=lambda x: x[1], reverse=True)
    sort = sort[: arp.query[int]("count")]
    await statis_cmd.finish(
        "以下按照命令使用频率排序\n"
        + "\n".join(f"[{k}] {v[0]}" for k, v in enumerate(sort))
    )


@statis_cmd.assign("type", "least")
async def statis_cmd_least(arp: Arparma):
    if not record:
        await statis_cmd.finish("暂无命令记录")
    length = len(record)
    table = {}
    for i, r in enumerate(record):
        source = r[0]
        if r[source] not in table:
            table[source] = 0
        table[source] += i / length
    sort = sorted(table.items(), key=lambda x: x[1], reverse=False)
    sort = sort[: arp.query[int]("count")]
    await statis_cmd.finish(
        "以下按照命令使用频率排序\n"
        + "\n".join(f"[{k}] {v[0]}" for k, v in enumerate(sort))
    )
