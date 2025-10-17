from arclet.entari import BasicConfModel, plugin_config
from arclet.entari.config import model_field


class Config(BasicConfModel):
    no_waifu_prob: float = 0.2
    no_waifu_text: list[str] = model_field(
        default_factory=lambda: ["你没有娶到群友，强者注定孤独，加油！找不到对象.jpg"]
    )


config = plugin_config(Config)
