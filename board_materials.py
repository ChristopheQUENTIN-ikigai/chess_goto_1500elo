"""
board_materials.py — Board square colour palettes for different
"materials" the user can pick from in the splash menu settings page.

A "material" is just a (light_square, dark_square, border) triple. The
renderer in main.py reads these three colours every frame and draws
the board with them — no texture loading, no PNG assets. This keeps
the implementation simple and lets the player switch in real time
without any asset reloading.

Themes shipped:
    classical_wood — the traditional buff/brown wood look (default).
    marble         — cool blue-grey and ivory.
    carbon         — graphite black on dark slate.
    skull_bone     — bleached bone with weathered shadow.
    neon_plasma    — synthwave purple/cyan, glows on a dark frame.

The palettes are tuned to keep piece glyphs readable on both colours
(no light-on-light or dark-on-dark pairings). If you add new ones,
test by drawing both white and black pieces on each square colour.
"""
from dataclasses import dataclass


@dataclass
class BoardMaterial:
    key: str
    label: str
    light_sq: tuple        # RGBA
    dark_sq: tuple
    border: tuple
    bg: tuple              # window background tint when this material is active


_MATERIALS = [
    BoardMaterial(
        key="classical_wood",
        label="Classical Wood",
        light_sq=(240, 217, 181, 255),
        dark_sq=(181, 136, 99, 255),
        border=(60, 64, 72, 255),
        bg=(40, 44, 52, 255),
    ),
    BoardMaterial(
        key="marble",
        label="Marble",
        light_sq=(232, 232, 226, 255),    # ivory marble
        dark_sq=(86, 96, 110, 255),       # blue-grey marble
        border=(40, 44, 50, 255),
        bg=(28, 32, 38, 255),
    ),
    BoardMaterial(
        key="carbon",
        label="Carbon Fiber",
        light_sq=(80, 84, 92, 255),       # graphite
        dark_sq=(30, 32, 36, 255),        # near black
        border=(15, 16, 18, 255),
        bg=(22, 24, 28, 255),
    ),
    BoardMaterial(
        key="skull_bone",
        label="Alien Bone",
        light_sq=(228, 218, 198, 255),    # bleached bone
        dark_sq=(110, 88, 70, 255),       # weathered shadow
        border=(50, 38, 28, 255),
        bg=(34, 28, 22, 255),
    ),
    BoardMaterial(
        key="neon_plasma",
        label="Neon Plasma",
        light_sq=(60, 30, 90, 255),       # deep purple
        dark_sq=(15, 10, 30, 255),        # near black
        border=(255, 60, 220, 255),       # magenta neon frame
        bg=(8, 6, 16, 255),
    ),
]


_BY_KEY = {m.key: m for m in _MATERIALS}


def all_materials() -> list[BoardMaterial]:
    return list(_MATERIALS)


def get_material(key: str) -> BoardMaterial:
    """Return the material for `key`, falling back to classical_wood."""
    return _BY_KEY.get(key, _MATERIALS[0])


def material_keys() -> list[str]:
    return [m.key for m in _MATERIALS]
