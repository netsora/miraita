import asyncio
from pathlib import Path
from typing import Any, cast
from asyncio.exceptions import TimeoutError

import httpx
import aiofiles
from retrying import retry
from httpx import Response, ConnectTimeout
from nonebot.adapters.telegram import Bot as TGBot
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    DownloadColumn,
    TransferSpeedColumn,
)

from sora.log import logger
from sora.utils.utils import get_local_proxy
from sora.utils.user_agent import get_user_agent


class AsyncHttpx:
    proxy = {"http://": get_local_proxy(), "https://": get_local_proxy()}

    @classmethod
    @retry(stop_max_attempt_number=3)
    async def get(
        cls,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        verify: bool = True,
        use_proxy: bool = True,
        proxy: dict[str, str] | None = None,
        timeout: int | None = 30,
        **kwargs,
    ) -> Response:
        """
        说明:
            Get
        参数:
            :param url: url
            :param params: params
            :param headers: 请求头
            :param cookies: cookies
            :param verify: verify
            :param use_proxy: 使用默认代理
            :param proxy: 指定代理
            :param timeout: 超时时间
        """
        if not headers:
            headers = get_user_agent()

        proxy_ = proxy if proxy else cls.proxy if use_proxy else None
        async with httpx.AsyncClient(proxies=proxy_, verify=verify) as client:  # type: ignore
            return await client.get(
                url,
                params=params,
                headers=headers,
                cookies=cookies,
                timeout=timeout,
                **kwargs,
            )

    @classmethod
    async def post(
        cls,
        url: str,
        *,
        data: dict[str, str] | None = None,
        content: Any = None,
        files: Any = None,
        verify: bool = True,
        use_proxy: bool = True,
        proxy: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        timeout: int | None = 30,
        **kwargs,
    ) -> Response:
        """
        说明:
            Post
        参数:
            :param url: url
            :param data: data
            :param content: content
            :param files: files
            :param use_proxy: 是否默认代理
            :param proxy: 指定代理
            :param json: json
            :param params: params
            :param headers: 请求头
            :param cookies: cookies
            :param timeout: 超时时间
        """
        if not headers:
            headers = get_user_agent()
        proxy_ = proxy if proxy else cls.proxy if use_proxy else None
        async with httpx.AsyncClient(proxies=proxy_, verify=verify) as client:  # type: ignore
            return await client.post(
                url,
                content=content,
                data=data,
                files=files,
                json=json,
                params=params,
                headers=headers,
                cookies=cookies,
                timeout=timeout,
                **kwargs,
            )

    @classmethod
    async def download_file(
        cls,
        url: str,
        path: str | Path,
        *,
        params: dict[str, str] | None = None,
        verify: bool = True,
        use_proxy: bool = True,
        proxy: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        timeout: int | None = 30,
        stream: bool = False,
        **kwargs,
    ) -> bool:
        """
        说明:
            下载文件
        参数:
            :param url: url
            :param path: 存储路径
            :param params: params
            :param verify: verify
            :param use_proxy: 使用代理
            :param proxy: 指定代理
            :param headers: 请求头
            :param cookies: cookies
            :param timeout: 超时时间
            :param stream: 是否使用流式下载（流式写入+进度条，适用于下载大文件）
        """
        if isinstance(path, str):
            path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            for _ in range(3):
                if not stream:
                    try:
                        content = (
                            await cls.get(
                                url,
                                params=params,
                                headers=headers,
                                cookies=cookies,
                                use_proxy=use_proxy,
                                proxy=proxy,
                                timeout=timeout,
                                **kwargs,
                            )
                        ).content
                        async with aiofiles.open(path, "wb") as wf:
                            await wf.write(content)
                            logger.success(
                                "请求", f"下载 {url} 成功！Path：{path.absolute()}"
                            )
                        return True
                    except (TimeoutError, ConnectTimeout):
                        pass
                else:
                    if not headers:
                        headers = get_user_agent()
                    proxy_ = proxy if proxy else cls.proxy if use_proxy else None
                    try:
                        async with httpx.AsyncClient(proxies=proxy_, verify=verify) as client:  # type: ignore
                            async with client.stream(
                                "GET",
                                url,
                                params=params,
                                headers=headers,
                                cookies=cookies,
                                timeout=timeout,
                                **kwargs,
                            ) as response:
                                logger.info(
                                    "请求",
                                    f"开始下载 {path.name} 到 Path: {path.absolute()}",
                                )
                                async with aiofiles.open(path, "wb") as wf:
                                    total = int(response.headers["Content-Length"])
                                    with Progress(
                                        TextColumn(path.name),
                                        "[progress.percentage]{task.percentage:>3.0f}%",
                                        BarColumn(bar_width=None),
                                        DownloadColumn(),
                                        TransferSpeedColumn(),
                                    ) as progress:
                                        download_task = progress.add_task(
                                            "Download", total=total
                                        )
                                        async for chunk in response.aiter_bytes():
                                            await wf.write(chunk)
                                            await wf.flush()
                                            progress.update(
                                                download_task,
                                                completed=response.num_bytes_downloaded,
                                            )
                                    logger.success(
                                        "请求",
                                        f"下载 {url} 成功！Path：{path.absolute()}",
                                    )
                        return True
                    except (TimeoutError, ConnectTimeout):
                        pass
            else:
                logger.error("请求", f"下载 {url} 下载超时！Path：{path.absolute()}")
        except Exception as e:
            logger.error(
                "请求", f"下载 {url} 未知错误 {type(e)}：{e} | Path：{path.absolute()}"
            )
        return False

    @classmethod
    async def gather_download_file(
        cls,
        url_list: list[str],
        path_list: list[str | Path],
        *,
        limit_async_number: int | None = None,
        params: dict[str, str] | None = None,
        use_proxy: bool = True,
        proxy: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        timeout: int | None = 30,
        **kwargs,
    ) -> list[bool]:
        """
        说明:
            分组同时下载文件
        参数:
            :param url_list: url列表
            :param path_list: 存储路径列表
            :param limit_async_number: 限制同时请求数量
            :param params: params
            :param use_proxy: 使用代理
            :param proxy: 指定代理
            :param headers: 请求头
            :param cookies: cookies
            :param timeout: 超时时间
        """
        if n := len(url_list) != len(path_list):
            raise UrlPathNumberNotEqual(
                f"Url数量与Path数量不对等，Url：{len(url_list)}，Path：{len(path_list)}"
            )
        if limit_async_number and n > limit_async_number:
            m = float(n) / limit_async_number
            x = 0
            j = limit_async_number
            _split_url_list = []
            _split_path_list = []
            for _ in range(int(m)):
                _split_url_list.append(url_list[x:j])
                _split_path_list.append(path_list[x:j])
                x += limit_async_number
                j += limit_async_number
            if int(m) < m:
                _split_url_list.append(url_list[j:])
                _split_path_list.append(path_list[j:])
        else:
            _split_url_list = [url_list]
            _split_path_list = [path_list]
        tasks = []
        result_ = []
        for x, y in zip(_split_url_list, _split_path_list):
            for url, path in zip(x, y):
                tasks.append(
                    asyncio.create_task(
                        cls.download_file(
                            url,
                            path,
                            params=params,
                            headers=headers,
                            cookies=cookies,
                            use_proxy=use_proxy,
                            timeout=timeout,
                            proxy=proxy,
                            **kwargs,
                        )
                    )
                )
            _x = await asyncio.gather(*tasks)  # type: ignore
            result_ = result_ + list(_x)
            tasks.clear()
        return result_

    @classmethod
    async def download_telegram_file(
        cls,
        url: str,
        path: str | Path,
        bot: TGBot,
    ) -> bool:
        res = await bot.get_file(file_id=url)
        file_path = cast(str, res.file_path)

        turl = f"{bot.bot_config.api_server}file/bot{bot.bot_config.token}/{file_path}"
        return await cls.download_file(turl, path)


class UrlPathNumberNotEqual(Exception):
    pass


class BrowserIsNone(Exception):
    pass
