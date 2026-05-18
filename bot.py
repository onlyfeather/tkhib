import os

import nonebot
from nonebot.adapters.console import Adapter as ConsoleAdapter
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter


nonebot.init(log_level=os.getenv("LOG_LEVEL", "INFO"))
driver = nonebot.get_driver()
driver.register_adapter(ConsoleAdapter)
driver.register_adapter(OneBotV11Adapter)
nonebot.load_from_toml("pyproject.toml")


if __name__ == "__main__":
    nonebot.run()
