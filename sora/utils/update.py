import re
from pathlib import Path

from git.repo import Repo
from nonebot.utils import run_sync
from git.exc import GitCommandError, InvalidGitRepositoryError

from sora.log import logger
from sora.config import bot_config
from sora.version import __version__

from .requests import AsyncHttpx

REPO_COMMITS_URL = "https://api.github.com/repos/netsora/SoraBot/commits"
REPO_RELEASE_URL = "https://api.github.com/repos/netsora/SoraBot/releases"


@run_sync
def update():
    try:
        repo = Repo(Path().absolute())
    except InvalidGitRepositoryError:
        return "没有发现git仓库，无法通过git更新，请手动下载最新版本的文件进行替换。"
    logger.info("更新", "开始执行<m>git pull</m>更新操作")
    origin = repo.remotes.origin
    try:
        origin.pull()
        msg = f"""更新完成，版本：{__version__}\n可使用命令 [@bot /重启] 重启{bot_config.nickname}"""
    except GitCommandError as e:
        if "timeout" in e.stderr or "unable to access" in e.stderr:
            msg = "更新失败，连接git仓库超时，请重试或修改源为代理源后再重试。"
        elif "Your local changes" in e.stderr:
            pyproject_file = Path().parent / "pyproject.toml"
            pyproject_raw_content = pyproject_file.read_text(encoding="utf-8")
            if raw_plugins_load := re.search(
                r"^plugins = \[.+]$", pyproject_raw_content, flags=re.M
            ):
                pyproject_new_content = pyproject_raw_content.replace(
                    raw_plugins_load.group(), "plugins = []"
                )
                logger.info(
                    "更新", f"检测到已安装插件：{raw_plugins_load.group()}，暂时重置"
                )
            else:
                pyproject_new_content = pyproject_raw_content
            pyproject_file.write_text(pyproject_new_content, encoding="utf-8")
            try:
                origin.pull()
                msg = f"""更新完成，版本：{__version__}\n可使用命令 [@bot /重启] 重启{bot_config.nickname}"""
            except GitCommandError as e:
                if "timeout" in e.stderr or "unable to access" in e.stderr:
                    msg = "更新失败，连接git仓库超时，请重试或修改源为代理源后再重试。"
                elif " Your local changes" in e.stderr:
                    msg = f"更新失败，本地修改过文件导致冲突，请解决冲突后再更新。\n{e.stderr}"
                else:
                    msg = f"更新失败，错误信息：{e.stderr}，请尝试手动进行更新"
            finally:
                if raw_plugins_load:
                    pyproject_new_content = pyproject_file.read_text(encoding="utf-8")
                    pyproject_new_content = re.sub(
                        r"^plugins = \[.*]$",
                        raw_plugins_load.group(),
                        pyproject_new_content,
                    )
                    pyproject_new_content = pyproject_new_content.replace(
                        "plugins = []", raw_plugins_load.group()
                    )
                    pyproject_file.write_text(pyproject_new_content, encoding="utf-8")
                    logger.info(
                        "更新", f"更新结束，还原插件：{raw_plugins_load.group()}"
                    )
            return msg
        else:
            msg = f"更新失败，错误信息：{e.stderr}，请尝试手动进行更新"
    return msg


class CheckUpdate:
    @staticmethod
    async def _get_commits_info() -> dict:
        req = await AsyncHttpx.get(REPO_COMMITS_URL)
        return req.json()

    @staticmethod
    async def _get_release_info() -> dict:
        req = await AsyncHttpx.get(REPO_RELEASE_URL)
        return req.json()

    @classmethod
    async def show_latest_commit_info(cls) -> str:
        try:
            data = await cls._get_commits_info()
        except Exception:
            logger.error("更新", "获取最新推送信息失败...")
            return ""

        try:
            commit_data: dict = data[0]
        except Exception:
            logger.error("更新", "检查更新失败，频率过高")
            return ""

        c_info = commit_data["commit"]
        c_msg = c_info["message"]
        c_sha = commit_data["sha"][0:5]
        c_time = c_info["author"]["date"]

        return f"Latest commit {c_msg} | sha: {c_sha} | time: {c_time}"

    @classmethod
    async def show_latest_version(cls) -> tuple:
        try:
            data = await cls._get_release_info()
        except Exception:
            logger.error("更新", "获取发布列表失败...")
            return "", ""

        try:
            release_data: dict = data[0]
        except Exception:
            logger.error("更新", "检查更新失败，频率过高")
            return "", ""

        l_v = release_data["tag_name"]
        l_v_t = release_data["published_at"]
        return l_v, l_v_t
