"""
config.py
Game configuration and constants
"""

from dataclasses import dataclass

# Window settings
WIDTH = 960
HEIGHT = 640
FPS = 60

# Colors
WHITE = (255, 255, 255)
BG = (18, 18, 24)
UI_BG = (24, 25, 29)
UI_BG_LIGHT = (32, 33, 37)
UI_BG_DARK = (16, 17, 21)
UI_ACCENT = (88, 95, 247)
UI_ACCENT_LIGHT = (108, 115, 255)
ATT_COL = (66, 134, 244)
ATT_COL_LIGHT = (86, 154, 255)
DEF_COL = (255, 85, 100)
DEF_COL_LIGHT = (255, 105, 120)
BROWN = (79, 84, 92)
YELLOW = (255, 188, 61)
GRAY = (142, 146, 151)
SUCCESS_LIGHT = (66, 233, 135)
DANGER_LIGHT = (255, 91, 107)

# Map settings
MAP_W, MAP_H = 32, 20
TILE = 32
MAP_TOP = 56

# Asset settings
ASSET_PATHS = {
    "Knight": "Assets/knight.png",
    "Ranger": "Assets/ranger.png",
    "Wizard": "Assets/wizard.png"
}

SPRITE_SIZE = 56

@dataclass
class GameConfig:
    FPS: int = 60
    WIN_SCORE: int = 10
    SIDE_SWAP_ROUND: int = 7
    BOMB_TIMER_MS: int = 10000
    FREEZE_TIME_MS: int = 3000
    ROUND_END_WAIT_MS: int = 3000
    PLANT_TIME_MS: int = 3000
    DEFUSE_TIME_MS: int = 4000

CONFIG = GameConfig()