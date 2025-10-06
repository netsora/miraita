from nonebot import require
from httpx import ConnectError

require("nonebot_plugin_saa")
require("nonebot_plugin_alconna")

from arclet.alconna.args import Args
from arclet.alconna.base import Option
from arclet.alconna.core import Alconna
from arclet.alconna.typing import MultiVar, CommandMeta
from nonebot_plugin_alconna import Match, Query, on_alconna, store_true
from nonebot_plugin_saa import Text, Image, MessageFactory, AggregatedMessageFactory

from sora.log import logger
from sora.utils.requests import AsyncHttpx

URL: str = "https://api.lolicon.app/setu/v2?r18={r18}&num={num}&tag={tag}"

setu = on_alconna(
    Alconna(
        "setu",
        Args["count", int, 1],
        Option(
            "-r|--r18", action=store_true, default=False, help_text="是否开启 R18 模式"
        ),
        Option("-t|--tags", Args["tags", MultiVar(str, "*")], help_text="指定标签"),
        meta=CommandMeta(
            description="谁不喜欢看色图呢？",
            usage="/setu",
            example="/色图",
            compact=True,
        ),
    ),
    priority=50,
    block=True,
)


def wrapper(slot: int | str, content: str | None) -> str | None:
    if slot == 0:
        if not content:
            return "1"
        if content == "点":
            import random

            return str(random.randint(1, 5))
    return content


setu.shortcut(
    r"(?:要|我要|给我|来|抽)(点|\d*)(?:张|个|份|幅)?(?:色|涩|瑟)图",
    command="setu {0} -t",
    fuzzy=True,
    wrapper=wrapper,
)

setu.shortcut(
    r"(?:要|我要|给我|来|抽)(点|\d*)(?:张|个|份|幅)?(.+?)的?(?:色|涩|瑟)图",
    command="setu {0}",
    arguments=["tags", "{1}"],
    fuzzy=True,
    wrapper=wrapper,
)


@setu.handle()
async def setu_(
    count: int, tags: Match[tuple[str, ...]], r18: Query[bool] = Query("r18.value")
):
    tags_result = "|".join(tags.result) if tags.available else ""
    r18_result = 1 if r18.result else 0

    url = URL.format(r18=str(r18_result), num=str(count), tag=tags_result)

    try:
        messages = []

        res = await AsyncHttpx.get(url)
        parsed_data = res.json()

        if count == 1:
            title = parsed_data["data"][0]["title"]
            original = parsed_data["data"][0]["urls"]["original"]
            await MessageFactory([Text(title), Image(original)]).finish(at_sender=True)

        for item in parsed_data["data"]:
            title = item["title"]
            original = item["urls"]["original"]

            message = MessageFactory([Text(title), Image(original)])
            messages.append(message)

        await AggregatedMessageFactory(messages).send()

    except ConnectError:
        logger.error("网络错误")
