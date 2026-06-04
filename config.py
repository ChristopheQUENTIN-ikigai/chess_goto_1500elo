"""
config.py — Central configuration for Chess Game v1.0
Human vs AI with Prolog-Janus chess reasoning.
Settings mapped as 'config.sys' style parameters.
"""
import os
import subprocess

# ── Auto-detect screen size ──────────────────────────────────────────
def _detect_screen():
    """Try to detect screen resolution; fallback to 1280x800."""
    try:
        out = subprocess.check_output(["xrandr"], stderr=subprocess.DEVNULL).decode()
        for line in out.splitlines():
            if "*" in line:
                res = line.split()[0]
                w, h = res.split("x")
                return int(w), int(h)
    except Exception:
        pass
    return 1280, 800

SCREEN_W, SCREEN_H = _detect_screen()
DEFAULT_SCREEN_W = min(SCREEN_W, 1280)
DEFAULT_SCREEN_H = min(SCREEN_H, 800)
WINDOW_TITLE = "Chess — Human vs AI (Prolog-Janus)"
START_FULLSCREEN = False

# ── Key Mappings (config.sys style) ──────────────────────────────────
KEY_FULLSCREEN = "f"        # Toggle fullscreen
KEY_EXIT = "escape"         # Exit application
KEY_HELP = "h"              # Show help overlay
KEY_NEW_GAME = "n"          # New game
KEY_UNDO = "u"              # Undo move
KEY_HINT = "i"              # Show hint

# ── Colors ───────────────────────────────────────────────────────────
COLOR_LIGHT_SQ   = (240, 217, 181, 255)
COLOR_DARK_SQ    = (181, 136, 99, 255)
COLOR_SELECTED   = (246, 246, 105, 180)
COLOR_LEGAL_MOVE = (100, 200, 100, 140)
COLOR_LAST_MOVE  = (255, 140, 0, 170)      # orange overlay for last-played squares
COLOR_THREAT     = (220, 50, 50, 140)
COLOR_CHECK      = (255, 0, 0, 200)
COLOR_BG         = (40, 44, 52, 255)
COLOR_PANEL_BG   = (50, 55, 65, 240)
COLOR_BOARD_BORDER = (60, 64, 72, 255)
COLOR_TEXT        = (220, 220, 220, 255)
COLOR_TEXT_DIM    = (150, 150, 150, 255)
COLOR_ACCENT     = (86, 156, 214, 255)
COLOR_EVAL_WHITE = (245, 245, 245, 255)
COLOR_EVAL_BLACK = (30, 30, 30, 255)
COLOR_BTN_BG     = (70, 80, 95, 255)
COLOR_BTN_HOVER  = (90, 105, 125, 255)
COLOR_BTN_ACTIVE = (60, 130, 200, 255)
COLOR_BTN_TEXT   = (230, 230, 230, 255)
COLOR_ARROW_BEST = (50, 200, 80, 180)

# Piece colors
COLOR_WHITE_PIECE = (255, 255, 255, 255)
COLOR_BLACK_PIECE = (50, 50, 50, 255)

# ── AI Styles ────────────────────────────────────────────────────────
AI_STYLES = {
    "normal":     {"label": "Normal",     "desc": "Balanced play"},
    "aggressive": {"label": "Aggressive", "desc": "Sharp, tactical, seeks initiative"},
    "defensive":  {"label": "Defensive",  "desc": "Solid, cautious, avoids risk"},
    "beginner":   {"label": "Beginner",   "desc": "Weak play for learning"},
}

AI_OPENINGS = {
    "any":            {"label": "Any",        "white": [], "black": []},
    # Classical Open / Semi-Open
    "italian":        {"label": "Italian",    "white": ["e2e4","g1f3","f1c4"], "black": ["e7e5","b8c6","f8c5"]},
    "ruy_lopez":      {"label": "Ruy Lopez",  "white": ["e2e4","g1f3","f1b5"], "black": ["e7e5","b8c6","a7a6"]},
    "scotch":         {"label": "Scotch",     "white": ["e2e4","g1f3","d2d4"], "black": ["e7e5","b8c6","e5d4"]},
    "kings_gambit":   {"label": "King's Gambit", "white": ["e2e4","f2f4"], "black": ["e7e5","e5f4"]},
    "vienna":         {"label": "Vienna",     "white": ["e2e4","b1c3"], "black": ["e7e5","g8f6"]},
    "sicilian":       {"label": "Sicilian",   "white": ["e2e4"], "black": ["c7c5"]},
    "sicilian_najdorf":{"label":"Sicilian Najdorf","white":["e2e4","g1f3","d2d4","f3d4","b1c3"],
                                              "black":["c7c5","d7d6","c5d4","g8f6","a7a6"]},
    "french":         {"label": "French",     "white": ["e2e4","d2d4"], "black": ["e7e6","d7d5"]},
    "caro_kann":      {"label": "Caro-Kann",  "white": ["e2e4","d2d4"], "black": ["c7c6","d7d5"]},
    "scandinavian":   {"label": "Scandinavian","white":["e2e4"], "black": ["d7d5"]},
    "pirc":           {"label": "Pirc",       "white": ["e2e4","d2d4","b1c3"], "black": ["d7d6","g8f6","g7g6"]},
    "modern":         {"label": "Modern",     "white": ["e2e4","d2d4"], "black": ["g7g6","f8g7"]},
    "alekhine":       {"label": "Alekhine",   "white": ["e2e4","e4e5"], "black": ["g8f6","f6d5"]},
    # Closed / Queen's Pawn / Indian
    "queens_gambit":  {"label": "QG",         "white": ["d2d4","c2c4"], "black": ["d7d5"]},
    "qgd":            {"label": "QGD",        "white": ["d2d4","c2c4","b1c3"], "black": ["d7d5","e7e6","g8f6"]},
    "slav":           {"label": "Slav",       "white": ["d2d4","c2c4","b1c3"], "black": ["d7d5","c7c6","g8f6"]},
    "london":         {"label": "London",     "white": ["d2d4","c1f4","e2e3"], "black": ["d7d5","g8f6"]},
    "colle":          {"label": "Colle",      "white": ["d2d4","g1f3","e2e3"], "black": ["d7d5","g8f6","e7e6"]},
    "torre":          {"label": "Torre",      "white": ["d2d4","g1f3","c1g5"], "black": ["g8f6","e7e6","d7d5"]},
    "trompowsky":     {"label": "Trompowsky", "white": ["d2d4","c1g5"], "black": ["g8f6"]},
    "kings_indian":   {"label": "KID",        "white": ["d2d4","c2c4","b1c3"], "black": ["g8f6","g7g6","f8g7"]},
    "nimzo_indian":   {"label": "Nimzo-Indian","white":["d2d4","c2c4","b1c3"], "black": ["g8f6","e7e6","f8b4"]},
    "grunfeld":       {"label": "Grunfeld",   "white": ["d2d4","c2c4","b1c3"], "black": ["g8f6","g7g6","d7d5"]},
    "benoni":         {"label": "Benoni",     "white": ["d2d4","c2c4","d4d5"],
                                              "black": ["g8f6","c7c5","e7e6"]},
    "dutch":          {"label": "Dutch",      "white": ["d2d4"],               "black": ["f7f5"]},
    # Gambits (white) and counter-gambits (black)
    "evans_gambit":   {"label": "Evans Gambit","white":["e2e4","g1f3","f1c4","b2b4"],
                                              "black":["e7e5","b8c6","f8c5","c5b4"]},
    "danish_gambit":  {"label": "Danish Gambit","white":["e2e4","d2d4","c2c3"],
                                              "black":["e7e5","e5d4","d4c3"]},
    "smith_morra":    {"label": "Smith-Morra","white":["e2e4","d2d4","c2c3"],
                                              "black":["c7c5","c5d4","d4c3"]},
    "latvian_gambit": {"label": "Latvian Gambit","white":["e2e4","g1f3"],
                                              "black":["e7e5","f7f5"]},
    "budapest":       {"label": "Budapest Gambit","white":["d2d4","c2c4"],
                                              "black":["g8f6","e7e5"]},
    "benko":          {"label": "Benko Gambit","white":["d2d4","c2c4","d4d5"],
                                              "black":["g8f6","c7c5","b7b5"]},
    "albin":          {"label": "Albin Counter-Gambit","white":["d2d4","c2c4"],
                                              "black":["d7d5","e7e5"]},
    # Flank
    "english":        {"label": "English",    "white": ["c2c4"], "black": ["e7e5"]},
    "reti":           {"label": "Reti",       "white": ["g1f3","c2c4"], "black": ["d7d5"]},
    "bird":           {"label": "Bird",       "white": ["f2f4"], "black": ["d7d5"]},
}

# ── Openings Table (White rows × Black columns) ──────────────────────
# Used by the "Openings Table" menu to show which White opening systems
# typically meet which Black defenses and what named line results.
OPENINGS_TABLE_WHITE = [
    "1.e4",
    "1.d4",
    "1.c4",
    "1.Nf3",
    "1.f4",
]
OPENINGS_TABLE_BLACK_VS_E4 = ["1...e5", "1...c5", "1...e6", "1...c6", "1...d5", "1...d6", "1...Nf6", "1...g6"]
OPENINGS_TABLE_BLACK_VS_D4 = ["1...d5", "1...Nf6", "1...f5", "1...e6", "1...c5", "1...g6"]
OPENINGS_TABLE_BLACK_VS_C4 = ["1...e5", "1...Nf6", "1...c5", "1...e6"]
OPENINGS_TABLE_BLACK_VS_NF3 = ["1...d5", "1...Nf6", "1...c5"]
OPENINGS_TABLE_BLACK_VS_F4 = ["1...d5", "1...Nf6", "1...e5"]

# Cell = (short name, ECO hint). "" means rare / not classified.
OPENINGS_TABLE_CELLS = {
    # 1.e4 x ...
    ("1.e4", "1...e5"):  ("Open Game (Italian/Ruy/Scotch)", "C20–C99"),
    ("1.e4", "1...c5"):  ("Sicilian Defense",                "B20–B99"),
    ("1.e4", "1...e6"):  ("French Defense",                  "C00–C19"),
    ("1.e4", "1...c6"):  ("Caro-Kann Defense",               "B10–B19"),
    ("1.e4", "1...d5"):  ("Scandinavian Defense",            "B01"),
    ("1.e4", "1...d6"):  ("Pirc Defense",                    "B07–B09"),
    ("1.e4", "1...Nf6"): ("Alekhine Defense",                "B02–B05"),
    ("1.e4", "1...g6"):  ("Modern Defense",                  "B06"),
    # 1.d4 x ...
    ("1.d4", "1...d5"):  ("Closed Game (QG, Slav, London)",  "D00–D69"),
    ("1.d4", "1...Nf6"): ("Indian Defenses (KID/Nimzo/Grünfeld)", "E00–E99"),
    ("1.d4", "1...f5"):  ("Dutch Defense",                   "A80–A99"),
    ("1.d4", "1...e6"):  ("Queen's Pawn / French-like",      "A40/D30"),
    ("1.d4", "1...c5"):  ("Benoni / Old Benoni",             "A43–A79"),
    ("1.d4", "1...g6"):  ("Modern / King's Fianchetto",      "A40"),
    # 1.c4 x ...
    ("1.c4", "1...e5"):  ("English, Reversed Sicilian",      "A20–A29"),
    ("1.c4", "1...Nf6"): ("English, Indian systems",         "A15–A19"),
    ("1.c4", "1...c5"):  ("Symmetrical English",             "A30–A39"),
    ("1.c4", "1...e6"):  ("English, Agincourt",              "A13"),
    # 1.Nf3 x ...
    ("1.Nf3","1...d5"):  ("Reti Opening",                    "A04–A09"),
    ("1.Nf3","1...Nf6"): ("King's Indian Attack / Reti",     "A05"),
    ("1.Nf3","1...c5"):  ("Anti-Sicilian / transpositions",  "A04"),
    # 1.f4 x ...
    ("1.f4", "1...d5"):  ("Bird's Opening",                  "A02–A03"),
    ("1.f4", "1...Nf6"): ("Bird's, Nimzowitsch-like",        "A02"),
    ("1.f4", "1...e5"):  ("From's Gambit",                   "A02"),
}

# ── Piece Info ───────────────────────────────────────────────────────
UNICODE_PIECES = {
    "K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙",
    "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟",
}
PIECE_VALUES = {"pawn": 1, "knight": 3, "bishop": 3, "rook": 5, "queen": 9, "king": 0}
FILE_LABELS = "abcdefgh"
RANK_LABELS = "12345678"

# ── Paths ────────────────────────────────────────────────────────────
PROLOG_RULES_PATH = os.path.join(os.path.dirname(__file__), "data", "chess_rules.pl")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets", "textures")

# PGN save/load directory — relative to the current working directory
# (per project spec: './pgn_losses')
PGN_DIR = os.path.join(os.getcwd(), "pgn_losses")

# ── Eval Graph Colors ────────────────────────────────────────────────
COLOR_GRAPH_BG       = (28, 32, 40, 255)
COLOR_GRAPH_GRID     = (60, 66, 78, 255)
COLOR_GRAPH_AXIS     = (120, 130, 145, 255)
COLOR_GRAPH_LINE     = (235, 235, 240, 255)   # main eval line
COLOR_GRAPH_FILL_W   = (230, 230, 235, 90)    # white-advantage fill
COLOR_GRAPH_FILL_B   = (20, 22, 28, 180)      # black-advantage fill
COLOR_GRAPH_DELTA_GOOD = (80, 200, 120, 255)
COLOR_GRAPH_DELTA_BAD  = (220, 90, 90, 255)
COLOR_GRAPH_ZERO     = (160, 160, 170, 255)

# ── Menu / Splash Colors ─────────────────────────────────────────────
COLOR_MENU_BG        = (18, 22, 30, 250)
COLOR_MENU_TITLE     = (220, 200, 120, 255)
COLOR_MENU_SUBTITLE  = (160, 180, 210, 255)
COLOR_MENU_BTN_BG    = (55, 65, 85, 255)
COLOR_MENU_BTN_HOVER = (85, 110, 150, 255)

# ── Text input widget colors ────────────────────────────────────────
COLOR_INPUT_BG         = (30, 34, 42, 255)
COLOR_INPUT_BG_FOCUS   = (42, 48, 62, 255)
COLOR_INPUT_BORDER     = (70, 80, 100, 255)
COLOR_INPUT_BORDER_FC  = (120, 170, 220, 255)
COLOR_INPUT_TEXT       = (230, 230, 235, 255)
COLOR_INPUT_PLACEHOLDER = (110, 115, 125, 255)
