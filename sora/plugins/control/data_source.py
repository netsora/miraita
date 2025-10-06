import os
import platform
from pathlib import Path

from sora.log import logger
from sora.config import bot_config
from sora.hook import on_bot_connect


@on_bot_connect
async def remind():
    if str(platform.system()).lower() != "windows":
        restart = Path() / "restart.sh"
        if not restart.exists():
            with open(restart, "w", encoding="utf8") as f:
                f.write(
                    "pid=$(netstat -tunlp | grep "
                    + str(bot_config.port)
                    + " | awk '{print $7}')\n"
                    "pid=${pid%/*}\n"
                    "kill -9 $pid\n"
                    "sleep 3\n"
                    "python3 bot.py"
                )
            os.system("chmod +x ./restart.sh")
            logger.info(
                "配置", "已自动生成 restart.sh 重启脚本，请检查脚本是否与本地指令符合.."
            )
