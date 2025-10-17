from pathlib import Path
from typing import Literal, TypeAlias

from miraita.configs import FONT_DIR, IMAGE_DIR

Color: TypeAlias = Literal[
    "cpu", "ram", "swap", "disk", "nickname", "details", "transparent"
]

cpu_color: tuple[int, int, int, int] = (84, 173, 255, 255)
ram_color: tuple[int, int, int, int] = (255, 179, 204, 255)
swap_color: tuple[int, int, int, int] = (251, 170, 147, 255)
disk_color: tuple[int, int, int, int] = (184, 170, 159, 255)
transparent_color: tuple[int, int, int, int] = (0, 0, 0, 0)
details_color: tuple[int, int, int, int] = (184, 170, 159, 255)
nickname_color: tuple[int, int, int, int] = (84, 173, 255, 255)

marker_img_path: Path = IMAGE_DIR / "status" / "badge.png"
bg_img_path: Path = IMAGE_DIR / "status" / "background.png"

baotu_font_path: Path = FONT_DIR / "status" / "baotu.ttf"
spicy_font_path: Path = FONT_DIR / "status" / "SpicyRice-Regular.ttf"
adlam_font_path: Path = FONT_DIR / "status" / "ADLaMDisplay-Regular.ttf"


def get_color(color: Color) -> tuple[int, int, int, int]:
    return globals()[f"{color}_color"]
