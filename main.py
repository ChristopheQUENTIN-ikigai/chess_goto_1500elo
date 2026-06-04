"""
main.py — Chess Game v1.0
Human vs AI with Prolog-Janus reasoning.
Arcade 3.x API — XYWH, draw_rect_filled, draw_lbwh_rectangle_filled,
shape_list.ShapeElementList, Camera2D, self.background_color.
Auto-generated piece textures (Unicode glyphs).
Keys: F=fullscreen, ESC=exit, H=help, N=new game, U=undo, I=hint.
"""

import arcade
import arcade.key
from arcade import XYWH, LBWH
import chess
import chess.pgn
import io
import threading
import math
import os
import datetime
import glob
import time
from typing import Optional

# tkinter file/save dialogs are imported lazily inside the handlers so
# a missing tk install doesn't prevent the game from starting.

from config import (
    WINDOW_TITLE, DEFAULT_SCREEN_W, DEFAULT_SCREEN_H,
    COLOR_LIGHT_SQ, COLOR_DARK_SQ, COLOR_SELECTED, COLOR_LEGAL_MOVE,
    COLOR_LAST_MOVE, COLOR_THREAT, COLOR_CHECK, COLOR_BG, COLOR_PANEL_BG,
    COLOR_BOARD_BORDER, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_ACCENT,
    COLOR_EVAL_WHITE, COLOR_EVAL_BLACK,
    COLOR_BTN_BG, COLOR_BTN_HOVER, COLOR_BTN_ACTIVE, COLOR_BTN_TEXT,
    COLOR_ARROW_BEST,
    COLOR_MENU_BG, COLOR_MENU_TITLE, COLOR_MENU_SUBTITLE,
    COLOR_MENU_BTN_BG, COLOR_MENU_BTN_HOVER,
    UNICODE_PIECES, FILE_LABELS, RANK_LABELS,
    AI_STYLES, AI_OPENINGS, PGN_DIR,
    OPENINGS_TABLE_WHITE,
    OPENINGS_TABLE_BLACK_VS_E4, OPENINGS_TABLE_BLACK_VS_D4,
    OPENINGS_TABLE_BLACK_VS_C4, OPENINGS_TABLE_BLACK_VS_NF3,
    OPENINGS_TABLE_BLACK_VS_F4,
    OPENINGS_TABLE_CELLS,
    KEY_FULLSCREEN, KEY_EXIT, KEY_HELP, KEY_NEW_GAME, KEY_UNDO, KEY_HINT,
)
from chess_engine import ChessEngine
from prolog_reasoner import PrologReasoner, PT
from animation import MoveAnimator
from ai_profiles import ProfiledAI, PROFILES
from opening_teacher import OpeningTeacher, OPENING_LIBRARY
from eval_tracker import EvalTracker
from ui_widgets import TextInputBox, EvalGraph
from master_games import MASTER_GAMES, all_players, by_player
from openings_catalog import (
    entries_for_side, find_entry, resolve_famous_game,
)
from variations_pgn import get_variation_game
from imbalances_tutorial import (
    LESSONS as IMBALANCE_LESSONS,
    PARTS as IMBALANCE_PARTS,
    PART_DESCRIPTIONS as IMBALANCE_PART_DESCRIPTIONS,
    lessons_for_part as imbalance_lessons_for_part,
    find_lesson as find_imbalance_lesson,
)
from avatar_gen import get_avatar
import piece_textures
import board_materials

# ── Arcade 3.x Cheat Sheet (applied throughout) ─────────────────────
# draw_rect_filled(XYWH(cx, cy, w, h), color)
# draw_rect_outline(XYWH(cx, cy, w, h), color, border_width)
# draw_lbwh_rectangle_filled(left, bottom, w, h, color)
# draw_lbwh_rectangle_outline(left, bottom, w, h, color, border_width)  -- convenience
# shape_list.ShapeElementList, shape_list.create_rectangle_filled
# Camera2D() with .position, .use()
# self.background_color = color
# Camera2D.viewport = LBWH(...)  -- Rect, not tuple
# match_window() for resize

# ── Layout constants ─────────────────────────────────────────────────
# Widened window: board (left) | button panel (mid) | eval-graph + text inputs (right)
WIN_W = 1480
WIN_H = 860

BOARD_SIZE = 640
SQ = BOARD_SIZE // 8  # 80
BX = 30               # board left
BY = 110              # board bottom (leaves room for inputs at bottom)

# Mid panel: buttons + info
PANEL_X = BX + BOARD_SIZE + 30
PANEL_W = 170

# Eval bar (slim vertical bar, right of board, as before)
EVAL_X = BX + BOARD_SIZE + 8
EVAL_W = 14

# Right-side graph panel
GRAPH_X = PANEL_X + PANEL_W + 16
GRAPH_Y = BY + 190                       # leave more room for text inputs below
GRAPH_W = WIN_W - GRAPH_X - 20
GRAPH_H = BOARD_SIZE - 190

# Text input region (FEN + PGN) — below the graph, right side.
# Taller boxes and a bigger gap between them make the labels above
# each input clearly separate from the previous box's content, which
# is what the "avoid overlap" readability fix targets.
FEN_INPUT_X = GRAPH_X
FEN_INPUT_Y = BY + 128
FEN_INPUT_W = GRAPH_W
FEN_INPUT_H = 28

PGN_INPUT_X = GRAPH_X
PGN_INPUT_Y = BY + 58
PGN_INPUT_W = GRAPH_W
PGN_INPUT_H = 28

BTN_X = PANEL_X + 8
BTN_W = PANEL_W - 16
BTN_H = 19
BTN_GAP = 2
BTN_Y0 = BY + BOARD_SIZE - 10

# ── Avatar panels ──────────────────────────────────────────────────
# Two avatar cards in the top band above the board (the space between
# the top of the board and the window top). Each card shows avatar +
# name + "to move" indicator. Left card = bottom-of-board player
# (White when not flipped, Black when flipped); right card = top-of-
# board player. Arranging them visually matches their board position:
# left card represents the side "closer" to the player logically.
AV_SIZE = 44          # avatar disc diameter, px
AV_CARD_W = 270
AV_CARD_H = 58
AV_CARD_GAP = 16
AV_BAND_Y = BY + BOARD_SIZE + 28   # card bottom
# Two cards centered under the full board width
_total_w = AV_CARD_W * 2 + AV_CARD_GAP
AV_LEFT_CARD_X = BX + (BOARD_SIZE - _total_w) // 2
AV_RIGHT_CARD_X = AV_LEFT_CARD_X + AV_CARD_W + AV_CARD_GAP

BUTTONS = [
    ("Hint",       "hint"),
    ("Threats",    "threats"),
    ("Pawn Info",  "pawns"),
    ("Castle",     "castle"),
    ("Opening",    "opening"),
    ("Learn Open", "learn_opening"),
    ("Undo",       "undo"),
    ("New Game",   "new_game"),
    ("Color",      "toggle_color"),
    ("Flip Board", "flip_board"),
    ("Flip Team",  "flip_team"),
    ("AI Level",   "cycle_ai_level"),
    ("AI Opening", "cycle_ai_opening"),
    ("Enforce Move",     "enforce_move"),
    ("Enforce Sequence", "enforce_sequence"),
    ("Free AI",          "free_ai"),
    ("Copy FEN",   "copy_fen"),
    ("Copy PGN",   "copy_pgn"),
    ("Save PGN",   "save_pgn"),
    ("Load PGN",   "load_pgn"),
    ("Menu",       "menu"),
]

STYLE_KEYS = list(AI_STYLES.keys())
OPEN_KEYS = list(AI_OPENINGS.keys())


def _draw_outline_lbwh(left, bottom, w, h, color, border_width=1):
    """Draw rectangle outline from left-bottom-width-height using Arcade 3.x XYWH."""
    cx = left + w / 2
    cy = bottom + h / 2
    arcade.draw_rect_outline(XYWH(cx, cy, w, h), color, border_width)


def _wrap(text, mc=38):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > mc:
            if cur:
                lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    if cur:
        lines.append(cur)
    return lines or [""]


class ChessGame(arcade.Window):
    """Main chess window — Arcade 3.x API."""

    def __init__(self):
        super().__init__(WIN_W, WIN_H, WINDOW_TITLE,
                         fullscreen=False, resizable=True)
        # Arcade 3.x: set background_color on the Window instance
        self.background_color = COLOR_BG

        # ── App state machine ─────────────────────────────────────────
        # "menu"    — splash/main menu
        # "game"    — normal play
        # "credits" — credits overlay
        # "masters" — master games browser
        self.app_state = "menu"

        # Modules
        self.engine = ChessEngine()
        self.reasoner = PrologReasoner()
        self.animator = MoveAnimator()
        self.profiled_ai = ProfiledAI("intermediate")
        self.eval_tracker = EvalTracker()

        # Ensure PGN directory exists (./pgn_losses)
        os.makedirs(PGN_DIR, exist_ok=True)

        # State
        self.sel: Optional[int] = None
        self.legal: list[int] = []
        self.threats: set[int] = set()
        self.show_threats = False
        self.info: list[str] = ["Welcome! Play chess against AI.",
                                "Press H for help."]
        self.hover: Optional[str] = None
        self.arrows: list[tuple[int, int, tuple]] = []
        self.show_help = False
        self.ai_profile_i = 2  # Start at "intermediate"
        self.ai_profile_keys = list(PROFILES.keys())

        # Opening teacher
        self.teacher = OpeningTeacher()
        self.show_opening_menu = False
        self.opening_menu_scroll = 0

        # Drag
        self.dragging = False
        self.drag_sq: Optional[int] = None
        self.dmx = self.dmy = 0.0

        # Game
        self.player_color: bool = chess.WHITE
        self.thinking = False
        self.style_i = 0
        self.open_i = 0

        self.engine.ai_color = chess.BLACK
        self.engine.set_ai_style("normal")

        # ── FEN / PGN text inputs ────────────────────────────────────
        self.fen_input = TextInputBox(
            FEN_INPUT_X, FEN_INPUT_Y, FEN_INPUT_W, FEN_INPUT_H,
            placeholder="Paste FEN here and press Enter…  (e.g. rnbqkbnr/… w KQkq - 0 1)",
            label="Load position from FEN (Ctrl+V to paste, Enter to apply):",
            max_chars=128,
            on_submit=self._load_from_fen,
        )
        self.pgn_input = TextInputBox(
            PGN_INPUT_X, PGN_INPUT_Y, PGN_INPUT_W, PGN_INPUT_H,
            placeholder="Paste PGN here and press Enter…  (full game or moves only)",
            label="Load game from PGN (Ctrl+V to paste, Enter to apply):",
            max_chars=8192,
            on_submit=self._load_from_pgn_text,
        )

        # ── Eval graph widget ────────────────────────────────────────
        self.eval_graph = EvalGraph(
            GRAPH_X, GRAPH_Y, GRAPH_W, GRAPH_H,
            title="Evaluation plot (cp per ply)",
        )

        # ── Masters browser state ────────────────────────────────────
        self._masters_rects: list[tuple[int, int, int, int, int]] = []
        # v10: vertical scroll offset for the masters list. Positive =
        # scrolled down (later entries visible); zero = top of list.
        # Updated by on_mouse_scroll while app_state == "masters".
        self._masters_scroll: int = 0
        self._menu_rects: list[tuple[str, int, int, int, int]] = []

        # ── Loaded-game replay state (mouse-wheel scrolls through plies) ──
        # When a PGN is pasted, a master game is loaded, or a PGN file is
        # opened, we stash the move list here and expose `ply_index` so
        # that on_mouse_scroll can step backward/forward through the game.
        self.loaded_moves: list[chess.Move] = []
        self.loaded_start_fen: str = chess.STARTING_FEN
        self.ply_index: int = 0          # how many loaded plies are applied
        self.loaded_label: str = ""      # source description for the info panel
        # Player names for the currently-loaded game (master or pasted
        # PGN). When these are set, _draw_avatars_in_game uses them as
        # 'master' role avatars instead of Human/AI. Cleared on
        # new_game.
        self.loaded_white_name: str = ""
        self.loaded_black_name: str = ""

        # ── Openings table state ─────────────────────────────────────
        # Which White first-move row is currently selected in the
        # Openings Table view. 0 = 1.e4, 1 = 1.d4, etc.
        self.openings_table_white_i: int = 0
        self._openings_table_row_rects: list[tuple[int, int, int, int, int]] = []
        # Side filter for the per-side "White Openings" / "Black
        # Openings" list view (app_state == "openings_list").
        # Value is "white" or "black".
        self.openings_view_side: str = "white"
        self._openings_list_rects: list[tuple[str, int, int, int, int]] = []
        # Opening-detail view (app_state == "opening_detail"): which
        # catalog entry's detail page is showing, identified by slug.
        # The side comes from openings_view_side, so (side, slug)
        # uniquely locates the entry in OPENING_CATALOG.
        self.opening_detail_slug: str = ""
        self._opening_detail_game_rects: list = []
        # v8: variations state. Click-rects for variation cards on
        # the detail page, and click-rect for the "View all variations"
        # button. Both populated by _draw_opening_detail and consumed
        # by _handle_opening_detail_click.
        self._opening_detail_variation_rects: list = []
        self._opening_detail_satellite_btn_rect: tuple = ()
        # v8: Satellite view (app_state == "variations_satellite"):
        # one mini-board per variation of the current entry. All
        # boards step forward in lockstep on right-arrow.
        # _satellite_ply_index is the global step counter; each
        # board renders min(ply, len(its_moves)) plies.
        # _satellite_zoom_level: 0=widest grid, higher=fewer columns.
        self._satellite_ply_index: int = 0
        self._satellite_zoom_level: int = 0
        self._satellite_board_rects: list = []   # list of (variation, lbwh)
        # v8: navigation memory — when a game is loaded from the
        # opening-detail flow, ESC/Backspace return here instead of
        # all the way to the menu. Tuple format: (state_name, ...args)
        # where args are the state-specific fields to restore. None
        # means "no memorized return; ESC goes to menu (legacy)".
        self._game_return_state: Optional[tuple] = None

        # ── v12: Imbalances tutorial state ────────────────────────────
        # Three-screen tutorial inspired by Jeremy Silman's "How to
        # Reassess Your Chess, 4th Edition":
        #   "imbalances"        — list view: 9 book parts on the left,
        #                         lessons within the selected part on
        #                         the right
        #   "imbalance_lesson"  — detail view for one lesson: title,
        #                         key idea, plan, and (when present)
        #                         a small board preview of the
        #                         illustrative FEN. Optional "Open on
        #                         main board" button hands the
        #                         position to the game state for
        #                         further play / analysis.
        # Selected part index — which of imbalances_tutorial.PARTS is
        # showing its lessons in the right pane. 0 by default.
        self._imbalance_part_i: int = 0
        # Vertical scroll offset for the right-side lesson list when
        # a part has more lessons than fit on screen.
        self._imbalance_scroll: int = 0
        # Slug of the currently-open lesson (used in the
        # "imbalance_lesson" state).
        self._imbalance_lesson_slug: str = ""
        # Click rects for parts (left pane) and lessons (right pane).
        # Populated by _draw_imbalances_browser; consumed by
        # _handle_imbalances_click. Tuple format:
        #   parts:    (index, lbwh)
        #   lessons:  (slug,  lbwh)
        self._imbalance_part_rects: list = []
        self._imbalance_lesson_rects: list = []
        # Click rect for the "Open on main board" button on a lesson's
        # detail page. Empty tuple when no FEN is attached.
        self._imbalance_open_btn_rect: tuple = ()

        # ── AI control: enforce-move / enforce-sequence / free-AI ────
        # self.enforced_ai_moves is a FIFO queue of chess.Move objects the
        # AI MUST play on its next turns (one per turn). An empty queue
        # means the AI is autonomous. "Free AI" clears the queue. Entries
        # that turn out to be illegal at play time are skipped with a log
        # line; the AI then falls back to its normal search for that turn.
        self.enforced_ai_moves: list[chess.Move] = []
        # When the user clicks "Enforce Move", we enter a modal pick mode:
        # the next two board clicks pick from/to squares for the AI's next
        # move. enforce_pick_from holds the selected from-square (or None).
        self.enforce_pick_mode: bool = False
        self.enforce_pick_from: Optional[int] = None
        # When the user clicks "Enforce Sequence", we show a small modal
        # overlay with a text input that accepts a UCI/SAN list.
        self.show_sequence_modal: bool = False
        self.sequence_input = TextInputBox(
            0, 0, 10, 10,  # real geometry set when shown
            placeholder="e.g. e2e4 g1f3 f1c4  or  e4 Nf3 Bc4",
            label="Enter mandatory AI moves (space-separated, UCI or SAN):",
            max_chars=512,
            on_submit=self._submit_enforced_sequence,
        )

        # ── Minimum AI turn delay ────────────────────────────────────
        # The AI must never visibly play instantly after the human —
        # 0.5 s minimum so the player has time to register the board
        # change. We stamp the request time in _after_move and the
        # worker sleeps until the deadline before pushing its move.
        self._ai_go_requested_at: float = 0.0
        self.MIN_AI_DELAY = 0.5

        # ── AI move hand-off (worker thread → main thread) ───────────
        # CRITICAL (v12 fix): the AI search runs in a background worker,
        # but board mutation (board.push) and animation creation
        # (animator.start_* allocate arcade.Sprite objects into
        # OpenGL-backed SpriteLists) MUST happen on the main/GL thread.
        # The worker now only *computes* a move and publishes it here;
        # on_update consumes it on the main thread. Guarded by a lock so
        # the single-producer/single-consumer handoff is race-free.
        self._ai_move_lock = threading.Lock()
        self._ai_result_ready: bool = False
        self._ai_result_move: Optional[chess.Move] = None
        self._ai_result_elapsed: float = 0.0

        # ── Cached PGN/FEN strings for display ───────────────────────
        # Recomputed only when the engine board changes (via _analyze).
        self._display_fen: str = ""
        self._display_pgn_short: str = ""

        # ── Toast popup ──────────────────────────────────────────────
        # Brief centered notification used by Copy FEN / Copy PGN and
        # other ephemeral status messages. (text, expires_at_wallclock).
        # None when nothing is showing.
        self._toast: Optional[tuple[str, float]] = None
        self.TOAST_DURATION = 1.8  # seconds visible (including fade)

        # ── Board orientation ────────────────────────────────────────
        # Flip Board button toggles this. When True, the board is drawn
        # with rank 8 on bottom and file h on left — i.e. Black's POV.
        # The actual chess.Board state is unchanged; this is display-only.
        self.board_flipped: bool = False

        # ── Avatar sprite list ───────────────────────────────────────
        # Arcade 3.x requires textures to be drawn through a SpriteList.
        # We create one persistent list and swap sprites in/out per
        # frame in _draw_avatar_card. Sprites created once per
        # (name, size) pair get cached on self._avatar_sprites.
        self._avatar_sprite_list = arcade.SpriteList()
        self._avatar_sprites: dict[str, arcade.Sprite] = {}

        # ── v9: Piece sprite list ────────────────────────────────────
        # v10 hot-fix: a single Sprite cannot occupy two positions in
        # the same frame — every square that needs a piece needs its
        # OWN Sprite instance, even when several pieces share a texture
        # (eight pawns, two knights, two rooks, two bishops…). The old
        # cache keyed by (theme, symbol, side, size) handed back the
        # SAME Sprite object to multiple callers, so successive
        # `sp.position = (cx, cy)` assignments overwrote each other and
        # only the LAST iterated piece for a given texture rendered.
        # The fix: cache by board square, so each of the 64 squares
        # gets its own Sprite. Texture lookup is still cached upstream
        # in piece_textures — only the Sprite wrappers are duplicated,
        # which is cheap (one PyGLet vertex buffer per sprite).
        # Same pattern as the avatar sprite list — Arcade 3.x can only
        # draw textures through a SpriteList. We park the unused
        # sprites off-screen each frame, position the ones we want to
        # show, then draw the list once.
        self._piece_sprite_list = arcade.SpriteList()
        self._piece_sprites: dict[str, arcade.Sprite] = {}

        # ── v12 perf: cached board background ────────────────────────
        # The border + 64 checkered squares are static; they only change
        # when the board material or the board geometry changes. We build
        # them once into a single GPU-batched ShapeElementList (one draw
        # call) instead of issuing 65 immediate-mode rectangle calls every
        # frame. Rebuilt lazily when the cache key changes.
        self._board_bg_shapes = None
        self._board_bg_key = None

        # ── v9: Piece-theme & board-material settings ────────────────
        # User-facing presentation settings, persisted to
        # ~/.config/chess-v9/settings.json so a chosen theme survives
        # restart. Defaults preserve v8 behaviour (classical pieces,
        # classical wood board) so existing users see no visual change.
        # The Settings page on the splash menu mutates these at runtime;
        # the renderer reads them every frame.
        self.piece_theme: str = "classical"
        self.board_material_key: str = "classical_wood"
        # piece_style is the binary "Classical / Fancy" radio. When
        # "classical", piece_theme is forced to "classical" and the
        # fancy theme picker is disabled. When "fancy", piece_theme is
        # one of the fancy sub-themes.
        self.piece_style: str = "classical"
        # Fancy theme is remembered separately so the user can flip
        # between classical and fancy without losing their pick.
        self.fancy_theme: str = "roman"
        # ── v10: Gender overlay ──────────────────────────────────────
        # When enabled, every flanked piece (R/B/N/P) gets a small
        # corner glyph: ♂ (U+2642) for kingside pieces, ♀ (U+2640) for
        # queenside pieces. This is an alternative landmark to the
        # _k/_q sprite differentiation the user asked for: the overlay
        # is purely additive (drawn on top of the existing sprites)
        # and can be toggled live with the 'O' key, or set as a
        # default in Settings. King and Queen are unique pieces and
        # never receive an overlay — there is no "kingside king".
        self.gender_overlay_enabled: bool = False
        self._settings_load()
        # Make sure all placeholder PNGs exist on disk.
        try:
            piece_textures.ensure_all_placeholders()
        except Exception as e:
            print(f"[settings] could not pre-generate placeholders: {e}")

        # Click rects for the Settings page (populated on draw, consumed
        # on click). Each entry is (action_id, lbwh) where action_id
        # encodes which option was clicked (e.g. "style:classical",
        # "theme:roman", "material:marble").
        self._settings_rects: list[tuple[str, int, int, int, int]] = []

        self._analyze()

    # ── Settings persistence ────────────────────────────────────────
    def _settings_path(self) -> str:
        """~/.config/chess-v9/settings.json — same convention as other
        Linux config files. We don't follow XDG_CONFIG_HOME exactly to
        keep this simple; ~/.config is the de-facto default."""
        return os.path.expanduser("~/.config/chess-v9/settings.json")

    def _settings_load(self) -> None:
        """Load persisted settings if the file exists. Silently falls
        back to defaults on any error — this is presentation-only state,
        a missing or corrupt file is not fatal."""
        path = self._settings_path()
        if not os.path.isfile(path):
            return
        try:
            import json
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            theme = data.get("piece_theme")
            if theme in piece_textures.available_themes():
                self.piece_theme = theme
                # Derive style/fancy_theme from piece_theme.
                if theme == "classical":
                    self.piece_style = "classical"
                else:
                    self.piece_style = "fancy"
                    self.fancy_theme = theme
            mat = data.get("board_material_key")
            if mat in board_materials.material_keys():
                self.board_material_key = mat
            # v10: gender overlay flag (defaults to False if absent —
            # this preserves the v9 visual exactly for users who
            # haven't opted in).
            go = data.get("gender_overlay")
            if isinstance(go, bool):
                self.gender_overlay_enabled = go
        except Exception as e:
            print(f"[settings] failed to load {path}: {e}")

    def _settings_save(self) -> None:
        """Persist current settings. Ignored on any I/O error."""
        path = self._settings_path()
        try:
            import json
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "piece_theme": self.piece_theme,
                    "board_material_key": self.board_material_key,
                    "gender_overlay": self.gender_overlay_enabled,
                }, f, indent=2)
        except Exception as e:
            print(f"[settings] failed to save {path}: {e}")

    # ── Coordinate helpers ────────────────────────────────────────────
    def _disp_file(self, sq) -> int:
        """Display column (0..7 left-to-right) for a square, respecting
        the board_flipped flag. When flipped, file a appears on the
        right and file h on the left."""
        f = chess.square_file(sq)
        return (7 - f) if self.board_flipped else f

    def _disp_rank(self, sq) -> int:
        """Display row (0..7 bottom-to-top) for a square, respecting
        the board_flipped flag. When flipped, rank 1 appears on top
        and rank 8 on the bottom."""
        r = chess.square_rank(sq)
        return (7 - r) if self.board_flipped else r

    def _s2p(self, sq):
        """Chess square index → pixel center, respecting flip."""
        return (BX + self._disp_file(sq) * SQ + SQ // 2,
                BY + self._disp_rank(sq) * SQ + SQ // 2)

    def _s2lb(self, sq):
        """Chess square index → pixel left-bottom of its square,
        respecting flip. Use for draw_lbwh_rectangle_filled."""
        return (BX + self._disp_file(sq) * SQ,
                BY + self._disp_rank(sq) * SQ)

    def _p2s(self, x, y):
        """Pixel → chess square index or None, respecting flip."""
        f_disp = int((x - BX) / SQ)
        r_disp = int((y - BY) / SQ)
        if not (0 <= f_disp <= 7 and 0 <= r_disp <= 7):
            return None
        f = (7 - f_disp) if self.board_flipped else f_disp
        r = (7 - r_disp) if self.board_flipped else r_disp
        return chess.square(f, r)

    def _btn_at(self, x, y):
        for i, (_, act) in enumerate(BUTTONS):
            by = BTN_Y0 - i * (BTN_H + BTN_GAP)
            if BTN_X <= x <= BTN_X + BTN_W and by <= y <= by + BTN_H:
                return act
        return None

    # ── Drawing ───────────────────────────────────────────────────────
    def on_draw(self):
        self.clear()

        if self.app_state == "menu":
            self._draw_menu()
            return
        if self.app_state == "credits":
            self._draw_credits()
            return
        if self.app_state == "settings":
            self._draw_settings()
            return
        if self.app_state == "masters":
            self._draw_masters_browser()
            return
        if self.app_state == "openings_table":
            self._draw_openings_table()
            return
        if self.app_state == "openings_list":
            self._draw_openings_list()
            return
        if self.app_state == "opening_detail":
            self._draw_opening_detail()
            return
        if self.app_state == "variations_satellite":
            self._draw_variations_satellite()
            return
        if self.app_state == "imbalances":
            self._draw_imbalances_browser()
            return
        if self.app_state == "imbalance_lesson":
            self._draw_imbalance_lesson()
            return

        # Default: game
        self._draw_game()

    def _board_background(self):
        """Return the cached board background (border + 64 squares) as a
        single GPU-batched ShapeElementList, rebuilding it only when the
        board material or geometry changes.

        This replaces 65 per-frame immediate-mode rectangle draws with one
        batched draw call — the bulk of the static board's render cost.
        """
        import arcade.shape_list as _sl
        key = (self.board_material_key, BX, BY, SQ, BOARD_SIZE)
        if self._board_bg_shapes is not None and self._board_bg_key == key:
            return self._board_bg_shapes

        shapes = _sl.ShapeElementList()
        # Border (was draw_lbwh_rectangle_filled(BX-3, BY-3, +6, +6)).
        bw = BOARD_SIZE + 6
        shapes.append(_sl.create_rectangle_filled(
            BX - 3 + bw / 2, BY - 3 + bw / 2, bw, bw, COLOR_BOARD_BORDER))
        # 64 squares from the live material.
        mat = board_materials.get_material(self.board_material_key)
        light, dark = mat.light_sq, mat.dark_sq
        for r in range(8):
            for f in range(8):
                c = light if (f + r) % 2 == 1 else dark
                shapes.append(_sl.create_rectangle_filled(
                    BX + f * SQ + SQ / 2, BY + r * SQ + SQ / 2, SQ, SQ, c))

        self._board_bg_shapes = shapes
        self._board_bg_key = key
        return shapes

    def _draw_game(self):

        # Board border + squares — v12: one batched draw call from a
        # cached ShapeElementList instead of 65 immediate-mode rectangles
        # every frame. Rebuilt only when material/geometry changes.
        self._board_background().draw()

        # Last move highlight
        lm = self.engine.last_move()
        if lm:
            for s in (lm.from_square, lm.to_square):
                lx, ly = self._s2lb(s)
                arcade.draw_lbwh_rectangle_filled(
                    lx, ly, SQ, SQ, COLOR_LAST_MOVE)

        # Selected square
        if self.sel is not None:
            lx, ly = self._s2lb(self.sel)
            arcade.draw_lbwh_rectangle_filled(
                lx, ly, SQ, SQ, COLOR_SELECTED)

        # Legal move indicators
        for s in self.legal:
            cx, cy = self._s2p(s)
            if self.engine.board.piece_at(s):
                arcade.draw_circle_outline(cx, cy, SQ * 0.44, COLOR_LEGAL_MOVE, 3)
            else:
                arcade.draw_circle_filled(cx, cy, SQ * 0.14, COLOR_LEGAL_MOVE)

        # Threat squares
        if self.show_threats:
            for s in self.threats:
                lx, ly = self._s2lb(s)
                arcade.draw_lbwh_rectangle_filled(
                    lx, ly, SQ, SQ, COLOR_THREAT)

        # Check indicator
        if self.engine.is_check():
            ks = self.engine.get_king_square(self.engine.board.turn)
            if ks is not None:
                cx, cy = self._s2p(ks)
                arcade.draw_circle_filled(cx, cy, SQ * 0.47, COLOR_CHECK)

        # Arrows (hint)
        for fsq, tsq, col in self.arrows:
            x1, y1 = self._s2p(fsq)
            x2, y2 = self._s2p(tsq)
            arcade.draw_line(x1, y1, x2, y2, col, 3)
            dx, dy = x2 - x1, y2 - y1
            d = math.hypot(dx, dy)
            if d > 1:
                ux, uy = dx / d, dy / d
                hl, hw = SQ * 0.28, SQ * 0.16
                bx_, by_ = x2 - ux * hl, y2 - uy * hl
                nx, ny = -uy, ux
                arcade.draw_triangle_filled(
                    x2, y2,
                    bx_ + nx * hw, by_ + ny * hw,
                    bx_ - nx * hw, by_ - ny * hw, col)

        # Pieces — v9: textured sprites from piece_textures.
        # Park all piece sprites off-screen, then position the ones
        # that should appear this frame; SpriteList drawn at the end.
        # v10: each square has its own dedicated Sprite slot so
        # multiple pieces sharing the same texture (e.g. eight pawns)
        # all render correctly. Slot key = "sq:<square_index>".
        self._park_all_piece_sprites()
        sprite_size = max(16, int(SQ * 0.92))
        anim_sqs = self.animator.animating_squares
        for sq in chess.SQUARES:
            if self.dragging and sq == self.drag_sq:
                continue
            if sq in anim_sqs:
                continue  # Being animated, don't draw static
            p = self.engine.board.piece_at(sq)
            if not p:
                continue
            cx, cy = self._s2p(sq)
            sh = piece_textures.flank_for_square(sq)
            sp = self._get_piece_sprite(
                f"sq:{sq}",
                p.symbol(), self.piece_theme, sh, sprite_size)
            sp.position = (cx, cy)

        # Draw active animations on top of everything
        if self.animator.active:
            self.animator.draw(SQ)

        # Drag ghost — v9: textured sprite at mouse position. Uses a
        # dedicated sprite slot ("drag") so it doesn't collide with
        # the static board sprite that pieces under animation share.
        if self.dragging and self.drag_sq is not None:
            p = self.engine.board.piece_at(self.drag_sq)
            if p:
                sh = piece_textures.flank_for_square(self.drag_sq)
                # Slightly larger than on-board to read as "lifted"
                ghost_size = max(16, int(SQ * 1.05))
                sp = self._get_piece_sprite(
                    "drag",
                    p.symbol(), self.piece_theme, sh, ghost_size)
                sp.position = (self.dmx, self.dmy)

        # Draw the piece sprite list (covers all positioned pieces +
        # drag ghost). Animations were already drawn above; the drag
        # ghost goes on top so the player sees their drag clearly.
        self._piece_sprite_list.draw()

        # ── v10: Gender overlay (♂ kingside / ♀ queenside) ───────────
        # Drawn AFTER the sprite list so the glyph sits on top of the
        # piece artwork. Only flanked pieces (R/B/N/P) get a glyph —
        # the king and queen are unique pieces with no flank to
        # distinguish. Squares being animated are skipped because the
        # animator owns its own sprite stack and we don't have a clean
        # way to follow a sliding piece's pixel position from here;
        # the glyph reappears on its destination square once the
        # animation lands. The drag ghost gets its own glyph via the
        # second branch below, so the user can see the flank marker
        # while lifting a piece.
        if self.gender_overlay_enabled:
            self._draw_gender_overlay(SQ)

        # Coordinates
        for i in range(8):
            # When flipped, files run h..a and ranks 8..1
            file_idx = (7 - i) if self.board_flipped else i
            rank_idx = (7 - i) if self.board_flipped else i
            arcade.draw_text(FILE_LABELS[file_idx],
                             BX + i * SQ + SQ // 2, BY - 18,
                             COLOR_TEXT_DIM, font_size=11, anchor_x="center")
            arcade.draw_text(RANK_LABELS[rank_idx],
                             BX - 16, BY + i * SQ + SQ // 2 - 6,
                             COLOR_TEXT_DIM, font_size=11, anchor_x="center")

        # Eval bar (thin vertical, right of board)
        arcade.draw_lbwh_rectangle_filled(EVAL_X, BY, EVAL_W, BOARD_SIZE, COLOR_EVAL_BLACK)
        cp = self.engine.get_eval_cp()
        pct = 1.0 / (1.0 + 10 ** (-cp / 400))
        pct = max(0.02, min(0.98, pct))
        if self.board_flipped:
            # Fill from the top so White's advantage grows toward White's
            # pieces, which are now at the top of the screen.
            white_h = int(BOARD_SIZE * pct)
            arcade.draw_lbwh_rectangle_filled(
                EVAL_X, BY + BOARD_SIZE - white_h,
                EVAL_W, white_h, COLOR_EVAL_WHITE)
        else:
            arcade.draw_lbwh_rectangle_filled(
                EVAL_X, BY, EVAL_W, int(BOARD_SIZE * pct), COLOR_EVAL_WHITE)
        etxt = f"{cp / 100:+.1f}"
        arcade.draw_text(etxt, EVAL_X + EVAL_W // 2, BY + BOARD_SIZE + 5,
                         COLOR_TEXT, font_size=9, anchor_x="center")

        # Eval graph (right side panel)
        self.eval_graph.draw(self.eval_tracker)

        # FEN / PGN text inputs (right side, below graph)
        self.fen_input.draw()
        self.pgn_input.draw()

        # Right panel
        arcade.draw_lbwh_rectangle_filled(PANEL_X, BY, PANEL_W, BOARD_SIZE, COLOR_PANEL_BG)
        _draw_outline_lbwh(
            PANEL_X, BY, PANEL_W, BOARD_SIZE, COLOR_ACCENT, 1)

        # Buttons
        for i, (lbl, act) in enumerate(BUTTONS):
            by_ = BTN_Y0 - i * (BTN_H + BTN_GAP)
            dl = lbl
            if act == "toggle_color":
                dl = "Play: White" if self.player_color == chess.WHITE else "Play: Black"
            elif act == "cycle_ai_level":
                pkey = self.ai_profile_keys[self.ai_profile_i]
                dl = "AI: " + PROFILES[pkey].name[:16]
            elif act == "cycle_ai_opening":
                dl = "Op: " + AI_OPENINGS[OPEN_KEYS[self.open_i]]["label"]
            bg = (COLOR_BTN_HOVER if self.hover == act
                  else (COLOR_BTN_ACTIVE if act == "threats" and self.show_threats
                        else COLOR_BTN_BG))
            arcade.draw_lbwh_rectangle_filled(BTN_X, by_, BTN_W, BTN_H, bg)
            _draw_outline_lbwh(BTN_X, by_, BTN_W, BTN_H, COLOR_ACCENT, 1)
            arcade.draw_text(dl[:20], BTN_X + BTN_W // 2, by_ + 7,
                             COLOR_BTN_TEXT, font_size=10, anchor_x="center")

        # Info panel
        iy = BTN_Y0 - len(BUTTONS) * (BTN_H + BTN_GAP) - 15
        prolog_tag = " [Prolog]" if self.reasoner.prolog_available else " [Python]"
        arcade.draw_text("Info" + prolog_tag, PANEL_X + 8, iy, COLOR_ACCENT,
                         font_size=12, bold=True)
        iy -= 6
        arcade.draw_line(PANEL_X + 8, iy, PANEL_X + PANEL_W - 8, iy, COLOR_ACCENT, 1)
        iy -= 14
        for msg in self.info[:12]:
            for ln in _wrap(msg, max(22, PANEL_W // 7)):
                if iy < BY + 10:
                    break
                arcade.draw_text(ln, PANEL_X + 8, iy, COLOR_TEXT, font_size=9)
                iy -= 14

        # Move list
        mvs = self.engine.move_history_san()
        if mvs:
            my = BY + 55
            arcade.draw_text("Moves:", PANEL_X + 8, my, COLOR_ACCENT,
                             font_size=10, bold=True)
            my -= 14
            buf = ""
            for i, san in enumerate(mvs):
                if i % 2 == 0:
                    buf += f"{i // 2 + 1}."
                buf += f"{san} "
                if len(buf) > 32:
                    arcade.draw_text(buf.strip(), PANEL_X + 8, my,
                                     COLOR_TEXT_DIM, font_size=8)
                    my -= 12
                    buf = ""
                    if my < BY + 5:
                        break
            if buf.strip():
                arcade.draw_text(buf.strip(), PANEL_X + 8, my,
                                 COLOR_TEXT_DIM, font_size=8)

        # ── Avatar cards (above the board) ───────────────────────────
        self._draw_avatars_in_game()

        # ── Current FEN / PGN display strip ──────────────────────────
        # Below the board (above the status bar) so the user can always
        # see the exact position and movetext. These are read-only;
        # editing is still done via the TextInputBox widgets on the right.
        strip_y = 28
        strip_h = 48
        arcade.draw_lbwh_rectangle_filled(0, strip_y, self.width, strip_h, (24, 28, 36, 255))
        arcade.draw_line(0, strip_y + strip_h, self.width, strip_y + strip_h,
                         COLOR_ACCENT, 1)
        # Labels
        arcade.draw_text("FEN:", 10, strip_y + strip_h - 14,
                         COLOR_ACCENT, font_size=9, bold=True)
        arcade.draw_text("PGN:", 10, strip_y + 4,
                         COLOR_ACCENT, font_size=9, bold=True)
        # Values — truncate to fit the window width
        max_chars = max(40, (self.width - 70) // 6)
        fen_show = self._display_fen[:max_chars]
        pgn_show = self._display_pgn_short
        if len(pgn_show) > max_chars:
            # Show the tail (latest moves) since that's what the user cares about
            pgn_show = "… " + pgn_show[-(max_chars - 2):]
        arcade.draw_text(fen_show, 48, strip_y + strip_h - 14,
                         COLOR_TEXT, font_size=9)
        arcade.draw_text(pgn_show or "(no moves yet)",
                         48, strip_y + 4,
                         COLOR_TEXT if pgn_show else COLOR_TEXT_DIM, font_size=9)

        # Status bar
        t = "White" if self.engine.is_white_turn() else "Black"
        st = f"{t} to move"
        if self.teacher.active and not self.teacher.completed:
            line = self.teacher.current_line
            step = self.teacher.current_step
            total = len(line.moves_san) if line else 0
            st = f"LEARNING: {line.name if line else '?'} — Step {step}/{total}"
        elif self.teacher.active and self.teacher.completed:
            st = f"Opening complete! Press New Game to play."
        elif self.engine.is_checkmate():
            winner = "Black" if self.engine.is_white_turn() else "White"
            st = f"Checkmate! {winner} wins."
        elif self.engine.is_stalemate():
            st = "Stalemate — Draw"
        elif self.engine.is_game_over():
            st = f"Game over: {self.engine.game_result()}"
        elif self.thinking:
            st += " | AI thinking..."
        # Show AI enforcement state in the status bar
        if self.enforce_pick_mode:
            st += "  |  ENFORCE MOVE: click AI piece, then destination  (ESC cancels)"
        elif self.enforced_ai_moves:
            queue_str = " ".join(m.uci() for m in self.enforced_ai_moves[:5])
            more = "" if len(self.enforced_ai_moves) <= 5 else f" (+{len(self.enforced_ai_moves)-5})"
            st += f"  |  AI-forced queue: {queue_str}{more}"
        arcade.draw_lbwh_rectangle_filled(0, 0, self.width, 25, (30, 33, 40, 255))
        arcade.draw_text(st, 10, 6, COLOR_TEXT, font_size=11)
        arcade.draw_text("ESC=Exit  F=Fullscreen  H=Help",
                         self.width - 260, 6, COLOR_TEXT_DIM, font_size=9)

        # Help overlay
        if self.show_help:
            self._draw_help()

        if self.show_opening_menu:
            self._draw_opening_menu()

        # Teaching mode: highlight expected move squares
        if self.teacher.active and self.teacher.hint_square_from is not None:
            for sq in [self.teacher.hint_square_from, self.teacher.hint_square_to]:
                if sq is not None:
                    lx, ly = self._s2lb(sq)
                    arcade.draw_lbwh_rectangle_filled(
                        lx, ly, SQ, SQ, (100, 255, 100, 80))

        # Enforce-move pick mode: highlight the chosen from-square
        if self.enforce_pick_mode and self.enforce_pick_from is not None:
            lx, ly = self._s2lb(self.enforce_pick_from)
            arcade.draw_lbwh_rectangle_filled(
                lx, ly, SQ, SQ, (255, 100, 255, 120))

        # Enforce-sequence modal
        if self.show_sequence_modal:
            self._draw_sequence_modal()

        # Toast popup (always last so it renders on top)
        self._draw_toast()

    def _draw_help(self):
        """Draw help overlay."""
        # Semi-transparent background
        arcade.draw_lbwh_rectangle_filled(
            50, 100, self.width - 100, self.height - 200, (20, 20, 30, 220))
        _draw_outline_lbwh(
            50, 100, self.width - 100, self.height - 200, COLOR_ACCENT, 2)

        y = self.height - 140
        arcade.draw_text("CHESS — Help", self.width // 2, y, COLOR_ACCENT,
                         font_size=20, anchor_x="center", bold=True)
        y -= 40
        help_lines = [
            "KEYBOARD SHORTCUTS — IN-GAME:",
            f"  {KEY_EXIT.upper()} — Back to menu (or close menu items)",
            f"  {KEY_FULLSCREEN.upper()} — Toggle fullscreen",
            f"  {KEY_HELP.upper()} — Toggle this help",
            f"  {KEY_NEW_GAME.upper()} — New game",
            f"  {KEY_UNDO.upper()} — Undo last move",
            f"  {KEY_HINT.upper()} — Show hint (best move)",
            "  O — Toggle gender overlay (♂ kingside / ♀ queenside)",
            "",
            "REPLAY NAVIGATION (after loading a PGN or master game):",
            "  Scroll wheel UP    — step forward one ply",
            "  Scroll wheel DOWN  — step back one ply",
            "  0 (zero)           — jump to start position (ply 0)",
            "  9 (nine)           — jump to final position (last ply)",
            "  Make a move while scrolled back → forks the game.",
            "",
            "MASTER-GAMES LIST (scrolling):",
            "  Scroll wheel / ↑↓  — one row at a time",
            "  PgUp / PgDn        — one page at a time",
            "  Home / End         — top / bottom of the list",
            "  ESC                — back to main menu",
            "",
            "VARIATIONS SATELLITE VIEW:",
            "  ← / →              — step every mini-board back / forward",
            "  Home or 0          — reset all boards to ply 0",
            "  Scroll wheel       — zoom in / out",
            "",
            "HOW TO PLAY:",
            "  Click a piece to select, then click destination.",
            "  Or drag and drop pieces.",
            "  The AI plays the opposite color automatically.",
            "",
            "LOADING POSITIONS:",
            "  FEN input — paste a FEN and press Enter to set a position.",
            "  PGN input — paste a game (full PGN or just movetext).",
            "",
            "BUTTONS (right panel):",
            "  Hint — show best move suggestion",
            "  Threats — highlight threatened squares",
            "  Pawn Info — pawn structure analysis (Prolog)",
            "  Castle — castling advice (Prolog)",
            "  Opening — current opening classification (Prolog)",
            "  AI Opening — force AI into a specific opening",
            "     Info panel shows the next forced moves (UCI).",
            "  AI Level / Color — change AI difficulty or side",
            "",
            "MAIN MENU also has:",
            "  Master Games — replay Tal, Capablanca, Fischer, …",
            "  Openings Table — White openings × Black defenses",
            "",
            f"Press {KEY_HELP.upper()} to close this help.",
        ]
        for line in help_lines:
            arcade.draw_text(line, 80, y, COLOR_TEXT, font_size=11)
            y -= 18

    def _draw_opening_menu(self):
        """Draw the opening selection overlay."""
        mx, my = 60, 60
        mw, mh = self.width - 120, self.height - 120
        arcade.draw_lbwh_rectangle_filled(mx, my, mw, mh, (20, 25, 35, 235))
        _draw_outline_lbwh(mx, my, mw, mh, COLOR_ACCENT, 2)

        y = my + mh - 40
        arcade.draw_text("SELECT OPENING TO LEARN", self.width // 2, y,
                         COLOR_ACCENT, font_size=18, anchor_x="center", bold=True)
        y -= 15
        arcade.draw_text("Click an opening to start guided practice. ESC to cancel.",
                         self.width // 2, y, COLOR_TEXT_DIM, font_size=10, anchor_x="center")
        y -= 25

        # Draw opening list as clickable rows
        self._opening_menu_rects = []  # Store hit regions
        row_h = 52
        for i, opening in enumerate(OPENING_LIBRARY):
            ry = y - i * row_h
            if ry < my + 20:
                break

            # Row background
            bg = (50, 60, 80, 200) if i % 2 == 0 else (40, 50, 70, 200)
            arcade.draw_lbwh_rectangle_filled(mx + 15, ry - row_h + 8, mw - 30, row_h - 4, bg)

            # Difficulty badge
            diff_colors = {"beginner": (80, 200, 80), "intermediate": (200, 180, 60), "advanced": (220, 80, 80)}
            dc = diff_colors.get(opening.difficulty, (150, 150, 150))
            arcade.draw_text(f"[{opening.difficulty[:3].upper()}]",
                             mx + 25, ry - 14, dc, font_size=9)

            # Name and ECO
            arcade.draw_text(f"{opening.name}",
                             mx + 80, ry - 12, (240, 240, 240), font_size=13, bold=True)
            arcade.draw_text(f"[{opening.eco}]  {opening.moves_san[0]} ...",
                             mx + 80, ry - 30, COLOR_TEXT_DIM, font_size=10)

            # Themes
            themes_str = ", ".join(t.replace("_", " ") for t in opening.themes[:3])
            arcade.draw_text(themes_str, mx + 350, ry - 14, (140, 180, 220), font_size=9)

            # Store clickable region
            self._opening_menu_rects.append((i, mx + 15, ry - row_h + 8, mw - 30, row_h - 4))

    def _handle_opening_menu_click(self, x, y) -> bool:
        """Check if click hit an opening in the menu. Returns True if handled."""
        if not hasattr(self, '_opening_menu_rects'):
            return False
        for idx, rx, ry, rw, rh in self._opening_menu_rects:
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                self.show_opening_menu = False
                self.sel = None
                self.legal = []
                self.arrows = []
                self.animator.clear()

                # Start teaching — teacher resets its own board
                self.teacher.start(idx, self.player_color)
                # Sync engine board immediately
                self.engine.board = self.teacher.board.copy()
                self.info = self.teacher.messages[-8:]

                name = OPENING_LIBRARY[idx].name
                print(f"[Teacher] Started: {name} "
                      f"({len(OPENING_LIBRARY[idx].moves_san)} moves)")
                return True
        return False

    # ── Enforce-sequence modal ────────────────────────────────────────
    def _draw_sequence_modal(self):
        """Small modal overlay with a text input for entering a list of
        mandatory AI moves. Accepts UCI (e2e4) or SAN (e4) tokens
        separated by whitespace. Submitted moves go into
        self.enforced_ai_moves as a FIFO queue consumed by _ai_go.

        Geometry is computed here (not at __init__ time) so it recenters
        when the window is resized.
        """
        mw, mh = 620, 200
        mx = (self.width - mw) // 2
        my = (self.height - mh) // 2
        # Dimmed backdrop
        arcade.draw_lbwh_rectangle_filled(
            0, 0, self.width, self.height, (0, 0, 0, 160))
        # Modal
        arcade.draw_lbwh_rectangle_filled(
            mx, my, mw, mh, (30, 35, 46, 250))
        _draw_outline_lbwh(mx, my, mw, mh, COLOR_ACCENT, 2)
        # Title
        arcade.draw_text("ENFORCE AI MOVE SEQUENCE",
                         mx + mw // 2, my + mh - 28,
                         COLOR_ACCENT, font_size=14,
                         anchor_x="center", bold=True)
        arcade.draw_text(
            "Mandatory next AI moves, in order. UCI (e2e4) or SAN (Nf3) tokens, space-separated.",
            mx + 14, my + mh - 52, COLOR_TEXT_DIM, font_size=9)
        arcade.draw_text(
            "Enter applies the queue. ESC cancels. Current queue length: "
            f"{len(self.enforced_ai_moves)}",
            mx + 14, my + mh - 68, COLOR_TEXT_DIM, font_size=9)

        # Position the shared text input widget inside the modal
        input_left = mx + 14
        input_bottom = my + mh // 2 - 20
        input_w = mw - 28
        input_h = 28
        self.sequence_input.left = input_left
        self.sequence_input.bottom = input_bottom
        self.sequence_input.width = input_w
        self.sequence_input.height = input_h
        self.sequence_input.draw()

        # Hint footer
        arcade.draw_text(
            "Click the input to focus. Ctrl+V to paste. Ctrl+A to clear.",
            mx + 14, my + 14, COLOR_TEXT_DIM, font_size=9)

    # ── Input handling ────────────────────────────────────────────────
    def on_key_press(self, key, mod):
        # Menu / credits / masters / openings_table — ESC returns to game; letter shortcuts only in game
        if self.app_state in ("menu", "credits", "masters", "openings_table",
                              "openings_list", "opening_detail",
                              "variations_satellite",
                              "imbalances", "imbalance_lesson"):
            # Backspace = "back one level" universal navigation. Same
            # ladder as ESC except that ESC from the menu closes the
            # app; Backspace from the menu does nothing (a beginner
            # accidentally pressing Backspace shouldn't quit).
            if key == arcade.key.BACKSPACE:
                if self.app_state == "menu":
                    return  # noop, don't close on Backspace
                self._navigate_back_one_level()
                return
            if key == arcade.key.ESCAPE:
                if self.app_state == "menu":
                    self.close()
                else:
                    self._navigate_back_one_level()
            # v8: satellite view — right arrow steps every board
            # forward; left arrow steps back; scroll wheel zooms via
            # on_mouse_scroll.
            if self.app_state == "variations_satellite":
                if key == arcade.key.RIGHT:
                    self._satellite_ply_index += 1
                elif key == arcade.key.LEFT:
                    self._satellite_ply_index = max(
                        0, self._satellite_ply_index - 1)
                elif key == arcade.key.HOME or key == arcade.key.KEY_0:
                    self._satellite_ply_index = 0
            # v10: masters list — keyboard scrolling. Render-time
            # clamp catches over-scroll; we only enforce the lower
            # bound (>= 0) here. PageUp/PageDown moves a page; Home /
            # End jump to the ends.
            if self.app_state == "masters":
                if key == arcade.key.UP:
                    self._masters_scroll = max(0, self._masters_scroll - 1)
                elif key == arcade.key.DOWN:
                    self._masters_scroll += 1
                elif key == arcade.key.PAGEUP:
                    self._masters_scroll = max(0, self._masters_scroll - 8)
                elif key == arcade.key.PAGEDOWN:
                    self._masters_scroll += 8
                elif key == arcade.key.HOME:
                    self._masters_scroll = 0
                elif key == arcade.key.END:
                    # Render-time clamp will pin to the true max.
                    self._masters_scroll = 9999
            # v12: imbalances browser — UP/DOWN cycles the selected
            # part on the left pane (changing the part resets scroll);
            # PageUp/PageDown scrolls the lesson list on the right.
            if self.app_state == "imbalances":
                n_parts = len(IMBALANCE_PARTS)
                if key == arcade.key.UP:
                    self._imbalance_part_i = (
                        self._imbalance_part_i - 1) % n_parts
                    self._imbalance_scroll = 0
                elif key == arcade.key.DOWN:
                    self._imbalance_part_i = (
                        self._imbalance_part_i + 1) % n_parts
                    self._imbalance_scroll = 0
                elif key == arcade.key.PAGEUP:
                    self._imbalance_scroll = max(
                        0, self._imbalance_scroll - 4)
                elif key == arcade.key.PAGEDOWN:
                    self._imbalance_scroll += 4
                elif key == arcade.key.HOME:
                    self._imbalance_scroll = 0
                elif key == arcade.key.END:
                    self._imbalance_scroll = 9999  # clamped at draw
            return

        # Text inputs grab keys first (arrow paste, enter-submit, backspace, etc.)
        if self.fen_input.on_key_press(key, mod):
            return
        if self.pgn_input.on_key_press(key, mod):
            return
        # Sequence modal: its text input absorbs keys when it's open
        if self.show_sequence_modal:
            if key == arcade.key.ESCAPE:
                self.show_sequence_modal = False
                self.sequence_input.focused = False
                self.sequence_input.text = ""
                self.info = ["Enforce-sequence cancelled."]
                return
            if self.sequence_input.on_key_press(key, mod):
                return

        if key == arcade.key.ESCAPE or key == arcade.key.BACKSPACE:
            if self.enforce_pick_mode:
                # Cancel the enforce-move picker
                self.enforce_pick_mode = False
                self.enforce_pick_from = None
                self.info = ["Enforce-move cancelled."]
                return
            if self.show_opening_menu:
                self.show_opening_menu = False
                return
            if self.teacher.active:
                self.teacher.stop()
                self.info = ["Teaching mode ended. Press New Game to play."]
                return
            # v8: if this game was loaded from the opening-detail flow,
            # return there. Otherwise legacy behavior: ESC → menu.
            if self._game_return_state is not None:
                target = self._game_return_state
                self._game_return_state = None  # consume on use
                self.app_state = target[0]
                return
            self.app_state = "menu"
            return
        elif key == arcade.key.F:
            self.set_fullscreen(not self.fullscreen)
        elif key == arcade.key.H:
            self.show_help = not self.show_help
        elif key == arcade.key.N:
            self._do("new_game")
        elif key == arcade.key.U:
            self._do("undo")
        elif key == arcade.key.I:
            self._do("hint")
        elif key == arcade.key.O:
            # v10: toggle gender overlay (♂ kingside / ♀ queenside)
            # live during play. Persist the new state so it survives
            # restart, matching the behaviour of all other Settings.
            self.gender_overlay_enabled = not self.gender_overlay_enabled
            self._settings_save()
            self._show_toast(
                "Gender overlay: ON  (♂ kingside / ♀ queenside)"
                if self.gender_overlay_enabled
                else "Gender overlay: OFF")
        elif key in (arcade.key.KEY_0, arcade.key.NUM_0):
            # Rewind a loaded PGN / master game to ply 0 (starting
            # position). Scroll-wheel up from there steps forward.
            # No-op when no game is loaded for replay.
            if self.loaded_moves:
                self.ply_index = 0
                self._rebuild_from_ply_index()
                self._show_toast("Rewound to start — scroll to replay")
        elif key in (arcade.key.KEY_9, arcade.key.NUM_9):
            # Jump to the final ply of a loaded PGN / master game —
            # the symmetric counterpart to "0" (rewind to start).
            # Useful for reaching the end position of a long replay
            # without scrolling through every move. No-op when no
            # game is loaded.
            if self.loaded_moves:
                target = len(self.loaded_moves)
                if self.ply_index != target:
                    self.ply_index = target
                    self._rebuild_from_ply_index()
                    self._show_toast(
                        f"Jumped to final position — ply {target}/{target}")
                else:
                    self._show_toast("Already at final ply")

    def on_text(self, text):
        """Arcade 3.x text input callback — character-by-character."""
        if self.app_state != "game":
            return
        if self.fen_input.focused:
            self.fen_input.on_text(text)
        elif self.pgn_input.focused:
            self.pgn_input.on_text(text)
        elif self.show_sequence_modal and self.sequence_input.focused:
            self.sequence_input.on_text(text)

    def on_mouse_press(self, x, y, btn, mod):
        if btn != arcade.MOUSE_BUTTON_LEFT:
            return

        # ── Non-game states ──────────────────────────────────────────
        if self.app_state == "menu":
            self._handle_menu_click(x, y)
            return
        if self.app_state == "credits":
            # any click closes credits
            self.app_state = "menu"
            return
        if self.app_state == "settings":
            self._handle_settings_click(x, y)
            return
        if self.app_state == "masters":
            self._handle_masters_click(x, y)
            return
        if self.app_state == "openings_table":
            self._handle_openings_table_click(x, y)
            return
        if self.app_state == "openings_list":
            self._handle_openings_list_click(x, y)
            return
        if self.app_state == "opening_detail":
            self._handle_opening_detail_click(x, y)
            return
        if self.app_state == "variations_satellite":
            self._handle_variations_satellite_click(x, y)
            return
        if self.app_state == "imbalances":
            self._handle_imbalances_click(x, y)
            return
        if self.app_state == "imbalance_lesson":
            self._handle_imbalance_lesson_click(x, y)
            return

        # ── Game state ───────────────────────────────────────────────
        # Sequence modal absorbs clicks (for input focus / click-outside to close)
        if self.show_sequence_modal:
            mw, mh = 620, 200
            mx = (self.width - mw) // 2
            my = (self.height - mh) // 2
            if mx <= x <= mx + mw and my <= y <= my + mh:
                self.sequence_input.on_mouse_press(x, y)
                return
            # Click outside modal: defocus but keep modal open so the user
            # can try again; ESC is the explicit cancel.
            self.sequence_input.focused = False
            return

        # Text inputs get first dibs on mouse for focus
        fen_hit = self.fen_input.on_mouse_press(x, y)
        pgn_hit = self.pgn_input.on_mouse_press(x, y)
        if fen_hit:
            self.pgn_input.focused = False
            return
        if pgn_hit:
            self.fen_input.focused = False
            return
        # Click elsewhere → defocus both
        self.fen_input.focused = False
        self.pgn_input.focused = False

        # Eval graph: click to jump the replay cursor to that ply. Only
        # meaningful when a PGN / master game is loaded for replay — in
        # that case we re-seed ply_index and rebuild. When no game is
        # loaded but there's live history, we could step the engine
        # back via undo, but that's fragile across board.pop() edge
        # cases — so we stick to loaded-game replay jumps.
        if self.eval_graph.contains(x, y):
            ply = self.eval_graph.ply_at(x, y)
            if ply is not None and self.loaded_moves:
                # eval_tracker history entry index maps to move stack:
                # history[0] = starting position, history[1] = after
                # ply 1, etc. So jumping to history-index i means
                # playing exactly i moves from the start → ply_index = i.
                target = max(0, min(len(self.loaded_moves), ply))
                if target != self.ply_index:
                    self.ply_index = target
                    self._rebuild_from_ply_index()
                return
            # If no game is loaded, just absorb the click so it doesn't
            # fall through to square-selection logic behind the graph.
            if ply is not None:
                self.info = [
                    "Load a PGN or master game to enable click-to-jump.",
                    "Scroll wheel also steps through loaded games.",
                ]
                return

        if self.show_help:
            self.show_help = False
            return

        if self.show_opening_menu:
            if self._handle_opening_menu_click(x, y):
                return
            # Click outside menu = close
            self.show_opening_menu = False
            return

        act = self._btn_at(x, y)
        if act:
            self._do(act)
            return

        # ── Enforce-move pick mode: capture two board clicks ──────────
        # First click = AI piece to move (must be AI color, must have at
        # least one legal move from that square). Second click = the
        # destination. We *queue* the resulting move on enforced_ai_moves
        # rather than play it immediately — the AI will pull it out on
        # its next turn.
        if self.enforce_pick_mode:
            sq = self._p2s(x, y)
            if sq is None:
                return
            board = self.engine.board
            ai_color = self.engine.ai_color
            if self.enforce_pick_from is None:
                # Picking the from-square
                p = board.piece_at(sq)
                if not p or p.color != ai_color:
                    self.info = [
                        f"Pick an AI ({'White' if ai_color == chess.WHITE else 'Black'}) piece.",
                        "Click a piece of the AI's color, then its destination.",
                    ]
                    return
                # Only accept pieces that have at least one conceivable move
                # on this position (even if it's not the AI's turn yet, we
                # validate against a probe board where it is the AI's turn).
                if not self._ai_has_any_move_from(sq):
                    self.info = ["That piece has no legal move for the AI.",
                                 "Pick another piece."]
                    return
                self.enforce_pick_from = sq
                self.info = [
                    f"From {chess.square_name(sq)} — now click the destination.",
                    "ESC to cancel.",
                ]
                return
            else:
                # Picking the to-square
                fr = self.enforce_pick_from
                if sq == fr:
                    # Click on same square: cancel from-selection
                    self.enforce_pick_from = None
                    self.info = ["From-square cleared. Pick an AI piece."]
                    return
                move = self._build_enforced_move(fr, sq)
                if move is None:
                    self.info = [
                        f"{chess.square_name(fr)}→{chess.square_name(sq)} "
                        f"is not a legal AI move.",
                        "Pick another destination, or ESC to cancel.",
                    ]
                    return
                # Queue it
                self.enforced_ai_moves.append(move)
                self.enforce_pick_mode = False
                self.enforce_pick_from = None
                self.info = [
                    f"AI forced: {move.uci()} (queued).",
                    f"Queue length: {len(self.enforced_ai_moves)}",
                    "The AI will play this on its next turn.",
                ]
                # If it's already the AI's turn (user picked after own
                # move already triggered AI), _ai_go is already running
                # and will consume the queue.
                return

        if self.engine.is_game_over() or self.thinking:
            return

        sq = self._p2s(x, y)
        if sq is None:
            self.sel = None
            self.legal = []
            return

        # Teaching mode: check if move matches expected opening move
        if self.teacher.active and not self.teacher.completed:
            # Sync board from teacher (authoritative source)
            board = self.teacher.board

            if self.sel is not None and sq in self.legal:
                # Player is attempting a move
                ok = self.teacher.try_player_move(self.sel, sq)
                if ok:
                    # Move accepted — teacher auto-played opponent's reply
                    # Board sync happens in on_update
                    self.sel = None
                    self.legal = []
                    print(f"[Teacher] Step {self.teacher.current_step}/{len(self.teacher.current_line.moves_san)}")
                    return
                else:
                    # Wrong move — keep selection, show error
                    self.info = self.teacher.messages[-4:]
                    return

            # Piece selection in teaching mode — use teacher's board
            p = board.piece_at(sq)
            if p and p.color == board.turn and board.turn == self.teacher.player_color:
                self.sel = sq
                self.legal = [m.to_square for m in board.legal_moves
                              if m.from_square == sq]
            else:
                self.sel = None
                self.legal = []
            return  # Don't fall through to normal play

        p = self.engine.board.piece_at(sq)
        if p and p.color == self.engine.board.turn:
            self.sel = sq
            self.legal = [m.to_square for m in self.engine.get_legal_moves()
                          if m.from_square == sq]
            self.dragging = True
            self.drag_sq = sq
            self.dmx, self.dmy = x, y
        elif self.sel is not None and sq in self.legal:
            self._do_player_move(self.sel, sq)
            self.sel = None
            self.legal = []
        else:
            self.sel = None
            self.legal = []

    def on_mouse_motion(self, x, y, dx, dy):
        self._hover_mx = x
        self._hover_my = y
        self.hover = self._btn_at(x, y)
        if self.dragging:
            self.dmx, self.dmy = x, y

    def on_mouse_drag(self, x, y, dx, dy, btn, mod):
        if self.dragging:
            self.dmx, self.dmy = x, y

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """Step through a loaded PGN / master-game ply by ply, OR
        zoom in/out of the satellite view.

        scroll_y > 0 (wheel up)   = step forward / zoom in
        scroll_y < 0 (wheel down) = step back / zoom out
        """
        # v8: satellite view — wheel changes zoom level. Higher zoom
        # means fewer columns (boards grow); zoom 0 is widest grid.
        if self.app_state == "variations_satellite":
            if scroll_y > 0:
                self._satellite_zoom_level = min(
                    3, self._satellite_zoom_level + 1)
            elif scroll_y < 0:
                self._satellite_zoom_level = max(
                    0, self._satellite_zoom_level - 1)
            return

        # v10: masters browser — wheel scrolls the list (one row per
        # notch). Convention is wheel-up = move toward the top of the
        # list (smaller scroll offset), matching every other scrollable
        # list in this app.
        if self.app_state == "masters":
            if scroll_y > 0:
                self._masters_scroll = max(0, self._masters_scroll - 1)
            elif scroll_y < 0:
                self._masters_scroll += 1
                # Render-time clamp keeps the upper bound honest, so we
                # don't need to know rows_fit here.
            return

        # v12: imbalances browser — wheel scrolls the right-pane
        # lesson list. Same wheel-up = up convention as everywhere
        # else; render-time clamp pins the lower/upper bounds.
        if self.app_state == "imbalances":
            if scroll_y > 0:
                self._imbalance_scroll = max(0, self._imbalance_scroll - 1)
            elif scroll_y < 0:
                self._imbalance_scroll += 1
            return

        if self.app_state != "game":
            return
        if not self.loaded_moves:
            return
        if self.thinking or self.teacher.active:
            return
        if self.fen_input.focused or self.pgn_input.focused:
            return

        # Normalise: scroll_y is usually ±1 per notch; some trackpads
        # emit fractional values. Use sign only.
        step = 1 if scroll_y > 0 else -1
        new_idx = self.ply_index + step
        new_idx = max(0, min(len(self.loaded_moves), new_idx))
        if new_idx == self.ply_index:
            return
        self.ply_index = new_idx
        self._rebuild_from_ply_index()

    def _rebuild_from_ply_index(self):
        """Rebuild the engine board + eval tracker from loaded_moves[:ply_index].

        Called by on_mouse_scroll when the user steps through a loaded
        game. We rebuild from the stored starting FEN rather than undoing
        a single move because:
          - eval_tracker has no random-access trim; .pop() works backward
            but is awkward when scrolling forward.
          - chess.Board.pop() only works if the move stack matches, which
            is fragile.
        Rebuilding is O(ply_index) which is negligible for any human game.
        """
        try:
            board = chess.Board(self.loaded_start_fen)
        except ValueError:
            board = chess.Board()

        self.eval_tracker.reset()
        for i, move in enumerate(self.loaded_moves[:self.ply_index]):
            if move not in board.legal_moves:
                # Shouldn't happen — moves were validated at load time.
                break
            mover = board.turn
            board.push(move)
            # Temporarily swap engine board so get_eval_cp() sees the
            # position we're rebuilding to.
            prior = self.engine.board
            self.engine.board = board
            cp = self.engine.get_eval_cp()
            self.engine.board = prior
            self.eval_tracker.record(
                ply=len(board.move_stack),
                cp=cp,
                mover=mover,
            )

        self.engine.board = board
        self.sel = None
        self.legal = []
        self.arrows = []
        self.dragging = False
        self.drag_sq = None
        self.animator.clear()
        self._analyze()

        # Overlay ply counter on info panel (preserve the first info line
        # from _analyze so opening classification still shows)
        total = len(self.loaded_moves)
        header = [f"Ply {self.ply_index}/{total}  —  {self.loaded_label or 'loaded game'}",
                  "Wheel up = forward, down = back"]
        # Keep at most 5 of the analyze lines beneath
        self.info = header + self.info[:5]

    def on_mouse_release(self, x, y, btn, mod):
        if btn != arcade.MOUSE_BUTTON_LEFT or not self.dragging:
            return
        self.dragging = False
        tgt = self._p2s(x, y)
        if (tgt is not None and self.drag_sq is not None
                and tgt in self.legal and tgt != self.drag_sq):
            # Teaching mode drag-and-drop
            if self.teacher.active and not self.teacher.completed:
                ok = self.teacher.try_player_move(self.drag_sq, tgt)
                if ok:
                    self.sel = None
                    self.legal = []
                    self.drag_sq = None
                    return
                else:
                    self.info = self.teacher.messages[-4:]
                    self.drag_sq = None
                    return
            # Normal game
            self._do_player_move(self.drag_sq, tgt)
            self.sel = None
            self.legal = []
            self.drag_sq = None
            return
        self.drag_sq = None

    def _do_player_move(self, from_sq: int, to_sq: int):
        """Execute a player move with logging."""
        board = self.engine.board
        moving = board.piece_at(from_sq)
        captured = board.piece_at(to_sq)
        mover_color = board.turn  # color that is *about to* move

        # If the player moves while scrolled to the middle of a loaded
        # game, treat that as forking: drop the remainder of loaded_moves
        # beyond the current ply, so scroll can't resurrect stale plies.
        if self.loaded_moves and self.ply_index < len(self.loaded_moves):
            self.loaded_moves = self.loaded_moves[:self.ply_index]
            self.loaded_label = (self.loaded_label + " (forked)").strip()

        # Detect castling before try_move (needs the king still on its
        # origin square to check file distance).
        is_castle = (moving and moving.piece_type == chess.KING
                     and abs(chess.square_file(from_sq)
                             - chess.square_file(to_sq)) > 1)

        if self.engine.try_move(from_sq, to_sq):
            # ── Animate the player's move too ───────────────────────
            # This matches the AI's animation and gives the player the
            # same 'piece slides to destination' feedback instead of
            # instant teleportation.
            if is_castle:
                if chess.square_file(to_sq) == 6:
                    rook_from = chess.square(7, chess.square_rank(to_sq))
                    rook_to = chess.square(5, chess.square_rank(to_sq))
                else:
                    rook_from = chess.square(0, chess.square_rank(to_sq))
                    rook_to = chess.square(3, chess.square_rank(to_sq))
                self.animator.start_castle(
                    from_sq, to_sq,
                    rook_from, rook_to,
                    moving.color == chess.WHITE,
                    BX, BY, SQ, duration=0.4,
                    flipped=self.board_flipped,
                    theme=self.piece_theme)
            elif moving:
                self.animator.start_move(
                    from_sq, to_sq,
                    moving.symbol(),
                    moving.color == chess.WHITE,
                    BX, BY, SQ,
                    is_capture=captured is not None,
                    captured_symbol=captured.symbol() if captured else "",
                    captured_is_white=captured.color == chess.WHITE if captured else False,
                    duration=0.35,
                    flipped=self.board_flipped,
                    theme=self.piece_theme)

            # Check pulse for the opponent's king, if our move gives check
            if self.engine.is_check():
                ks = self.engine.get_king_square(self.engine.board.turn)
                if ks is not None:
                    self.animator.start_check_pulse(
                        ks, BX, BY, SQ, flipped=self.board_flipped)

            # Record eval point (push already happened inside try_move)
            self.eval_tracker.record(
                ply=len(board.move_stack),
                cp=self.engine.get_eval_cp(),
                mover=mover_color,
            )
            # If we were inside a loaded game, keep ply_index in sync
            # with the engine's move stack.
            if self.loaded_moves:
                self.ply_index = min(self.ply_index + 1, len(self.loaded_moves))
            # Log to terminal
            san_list = self.engine.move_history_san()
            last_san = san_list[-1] if san_list else "?"
            move_num = (len(board.move_stack) + 1) // 2
            print(f"  Player: {move_num}. {last_san}")
            self._after_move()

    def on_update(self, delta_time: float):
        """Arcade 3.x update tick — advance animations and sync teaching board."""
        self.animator.update(delta_time)

        # ── Apply a finished AI search on the MAIN thread ───────────
        # The background worker only computes the move; we push it and
        # build its sliding animation here, where the OpenGL context
        # lives. (This is what makes AI pieces slide instead of teleport.)
        pending = None
        elapsed = 0.0
        consumed = False
        with self._ai_move_lock:
            if self._ai_result_ready:
                pending = self._ai_result_move
                elapsed = self._ai_result_elapsed
                self._ai_result_ready = False
                self._ai_result_move = None
                consumed = True
        if consumed:
            self._apply_ai_move(pending, elapsed)

        self._update_toast()

        # Keep engine board in sync with teacher board during teaching.
        # Only during active game state — we must not stomp the board
        # when the user is on the menu / masters / openings_table screens.
        if self.teacher.active and self.app_state == "game":
            self.engine.board = self.teacher.board.copy()
            # Update info panel with latest teacher messages
            if self.teacher.messages:
                # Only show last 8 messages to avoid overflow
                self.info = self.teacher.messages[-8:]

    # ── Game logic ────────────────────────────────────────────────────
    def _after_move(self):
        self.arrows = []
        self._analyze()
        # If a forced opening is selected, append the next expected AI
        # moves so the user can verify the AI is following it.
        if self.engine.ai_opening != "any":
            preview = self._ai_opening_preview()
            if preview:
                self.info.append(f"AI next (forced): {', '.join(preview[:3])}")
        if self.engine.is_game_over():
            res = self.engine.game_result()
            if res:
                self.info.insert(0, f"Game over: {res}")
        elif self.engine.board.turn != self.player_color:
            self._ai_go()

    def _ai_opening_book_move(self, board) -> Optional[chess.Move]:
        """Return the next forced book move for the AI in the selected
        opening, or None if: no opening forced, we've run out of book,
        or the book move isn't legal in this position.

        The book tables in AI_OPENINGS are aligned by ply index for each
        side — the N-th AI move is the N-th UCI in its color's list.
        We count how many of the AI's *own* plies have been played so
        far and pick the next one.
        """
        key = self.engine.ai_opening
        if key == "any":
            return None
        book = AI_OPENINGS.get(key)
        if not book:
            return None
        ai_color = self.engine.ai_color
        if board.turn != ai_color:
            return None
        uci_list = book["white"] if ai_color == chess.WHITE else book["black"]
        # Count AI plies that have been played. The AI moves on its
        # color's turns, so it's the number of moves in the stack where
        # the mover equals ai_color.
        ai_plies_done = sum(
            1 for i, _ in enumerate(board.move_stack)
            # On ply i the mover was WHITE if i is even, BLACK if odd
            if (i % 2 == 0) == (ai_color == chess.WHITE)
        )
        if ai_plies_done >= len(uci_list):
            return None
        try:
            m = chess.Move.from_uci(uci_list[ai_plies_done])
        except ValueError:
            return None
        return m if m in board.legal_moves else None

    def _ai_opening_preview(self) -> list[str]:
        """Return a list of the next 1-3 forced moves (in UCI) that the
        AI is expected to play under the current opening selection. Used
        to display 'next mandatory moves' in the info panel so the user
        can verify the AI is following the chosen opening."""
        key = self.engine.ai_opening
        if key == "any":
            return []
        book = AI_OPENINGS.get(key)
        if not book:
            return []
        ai_color = self.engine.ai_color
        uci_list = book["white"] if ai_color == chess.WHITE else book["black"]
        board = self.engine.board
        ai_plies_done = sum(
            1 for i, _ in enumerate(board.move_stack)
            if (i % 2 == 0) == (ai_color == chess.WHITE)
        )
        remaining = uci_list[ai_plies_done:ai_plies_done + 3]
        return remaining

    def _ai_go(self):
        self.thinking = True
        # Stamp the request time; the worker will sleep until the
        # MIN_AI_DELAY deadline is reached before pushing its move.
        # This keeps the AI's move visually distinct from the human's —
        # never instant teleportation in the same frame.
        self._ai_go_requested_at = time.time()

        def go():
            import time as _time
            board = self.engine.board

            # ── AI reasoning log ──────────────────────────────────
            profile = self.profiled_ai.profile
            turn_str = "White" if board.turn == chess.WHITE else "Black"
            move_num = len(board.move_stack) // 2 + 1
            print(f"\n{'='*50}")
            print(f"  AI TURN — Move {move_num} ({turn_str})")
            print(f"  Profile: {profile.name} (~{profile.elo_estimate} ELO)")
            print(f"  Depth: {profile.depth} | Quiescence: {profile.quiescence_depth}")
            print(f"  Style: aggr={profile.aggression:.1f} "
                  f"rand={profile.randomness:.2f} "
                  f"blunder={profile.blunder_rate:.0%}")
            print(f"  FEN: {board.fen()}")

            t0 = _time.time()

            # ── AI move source priority ────────────────────────────
            # 1. Enforced queue (user-picked "enforce move" or
            #    "enforce sequence") — highest priority; pop one.
            # 2. Opening book (if an opening is forced).
            # 3. ProfiledAI search.
            m = None
            source = ""
            # 1. Enforced queue
            while self.enforced_ai_moves:
                candidate = self.enforced_ai_moves[0]
                if candidate in board.legal_moves:
                    m = self.enforced_ai_moves.pop(0)
                    source = "enforced"
                    print(f"  Enforced: playing queued move {m.uci()} "
                          f"(remaining queue: {len(self.enforced_ai_moves)})")
                    break
                else:
                    # Illegal in current position (probably because the
                    # human diverged from what the user assumed). Drop
                    # it with a log line and try the next token. This is
                    # the honest behavior — we don't silently play a
                    # different legal-looking move.
                    dead = self.enforced_ai_moves.pop(0)
                    print(f"  Enforced: dropping illegal queued move "
                          f"{dead.uci()} — position diverged.")
                    continue

            # 2. Opening book enforcement
            if m is None:
                book_move = self._ai_opening_book_move(board)
                if book_move is not None:
                    m = book_move
                    source = "book"
                    print(f"  Book:     playing forced opening move "
                          f"({AI_OPENINGS[self.engine.ai_opening]['label']})")

            # 3. ProfiledAI search
            if m is None:
                m = self.profiled_ai.get_move(board)
                source = "search"
            elapsed = _time.time() - t0

            # ── Minimum AI-turn delay ──────────────────────────────
            # Don't let the AI push its move in the same frame the human
            # made theirs. 0.5 s minimum visible delay.
            deadline = self._ai_go_requested_at + self.MIN_AI_DELAY
            remaining = deadline - _time.time()
            if remaining > 0:
                _time.sleep(remaining)

            if m and m in board.legal_moves:
                san = board.san(m)
                # Capture info (read-only — board is NOT pushed here).
                captured = board.piece_at(m.to_square)
                moving = board.piece_at(m.from_square)
                is_castle = (moving and moving.piece_type == chess.KING
                             and abs(chess.square_file(m.from_square)
                                     - chess.square_file(m.to_square)) > 1)

                from ai_profiles import evaluate_with_profile
                eval_before = evaluate_with_profile(board, profile)

                print(f"  Decision: {san} (UCI: {m.uci()})")
                print(f"  Eval: {eval_before/100:+.2f} | "
                      f"Nodes: {self.profiled_ai.nodes_searched} | "
                      f"Time: {elapsed:.2f}s")
                if captured:
                    print(f"  Capture: {PT.get(captured.piece_type, '?')}")
                if is_castle:
                    side = "kingside" if chess.square_file(m.to_square) == 6 else "queenside"
                    print(f"  Castling: {side}")
                print(f"{'='*50}")
            else:
                print(f"  Decision: NO MOVE FOUND")
                print(f"{'='*50}")
                m = None

            # ── Hand the move off to the MAIN thread ───────────────
            # IMPORTANT: we deliberately do NOT call board.push() or any
            # animator.start_* here. Those mutate the shared board and
            # allocate arcade.Sprite objects into OpenGL-backed
            # SpriteLists, which is only safe on the main/GL thread.
            # Doing it on this worker raced the renderer and the freshly
            # created sliding sprite never rendered — that was the cause
            # of AI pieces appearing to teleport. on_update() picks this
            # up and applies it via _apply_ai_move() on the next tick.
            with self._ai_move_lock:
                self._ai_result_move = m
                self._ai_result_elapsed = elapsed
                self._ai_result_ready = True

        threading.Thread(target=go, daemon=True).start()

    def _apply_ai_move(self, m: Optional[chess.Move], elapsed: float = 0.0):
        """Apply a computed AI move on the MAIN (GL) thread.

        This is the other half of the teleport fix: the background worker
        only *finds* the move; here — on the thread that owns the OpenGL
        context — we push it on the board, record the eval point, and
        create the sliding-piece animation. Because the sprite is now
        built on the GL thread it renders correctly and the piece slides
        smoothly instead of jumping.
        """
        board = self.engine.board
        self.thinking = False

        if not (m and m in board.legal_moves):
            # Nothing to play (no move found, or the position somehow
            # changed underneath us). Just refresh analysis.
            self._analyze()
            return

        captured = board.piece_at(m.to_square)
        moving = board.piece_at(m.from_square)
        is_castle = (moving and moving.piece_type == chess.KING
                     and abs(chess.square_file(m.from_square)
                             - chess.square_file(m.to_square)) > 1)

        mover_color = board.turn
        board.push(m)

        # Record eval tracker point (after the push, like the human path).
        self.eval_tracker.record(
            ply=len(board.move_stack),
            cp=self.engine.get_eval_cp(),
            mover=mover_color,
        )

        # ── Start the themed sliding animation ──────────────────────
        # Pass the active piece theme so the sliding sprite uses the same
        # art as the static board (no Unicode-glyph mismatch, no pop when
        # the slide ends).
        if is_castle:
            if chess.square_file(m.to_square) == 6:
                rook_from = chess.square(7, chess.square_rank(m.to_square))
                rook_to = chess.square(5, chess.square_rank(m.to_square))
            else:
                rook_from = chess.square(0, chess.square_rank(m.to_square))
                rook_to = chess.square(3, chess.square_rank(m.to_square))
            self.animator.start_castle(
                m.from_square, m.to_square,
                rook_from, rook_to,
                moving.color == chess.WHITE,
                BX, BY, SQ, duration=0.4,
                flipped=self.board_flipped,
                theme=self.piece_theme)
        elif moving:
            self.animator.start_move(
                m.from_square, m.to_square,
                moving.symbol(),
                moving.color == chess.WHITE,
                BX, BY, SQ,
                is_capture=captured is not None,
                captured_symbol=captured.symbol() if captured else "",
                captured_is_white=captured.color == chess.WHITE if captured else False,
                duration=0.35,
                flipped=self.board_flipped,
                theme=self.piece_theme)

        # Check pulse on the (now) side-to-move's king if we gave check.
        if self.engine.is_check():
            ks = self.engine.get_king_square(board.turn)
            if ks is not None:
                self.animator.start_check_pulse(
                    ks, BX, BY, SQ, flipped=self.board_flipped)

        self._analyze()

    def _analyze(self):
        """Run Prolog-based and Python analysis."""
        warnings = self.reasoner.analyze(self.engine.board)
        self.threats = self.reasoner.get_threat_squares()

        # Opening classification
        opening = self.reasoner.classify_opening(self.engine.move_history_uci())

        # Build info messages
        self.info = []
        if opening:
            self.info.append(f"Opening: {opening.name} [{opening.eco}]")
            self.info.append(f"Plan: {opening.plan}")

        if self.engine.is_checkmate():
            self.info.insert(0, "Checkmate!")
        elif self.engine.is_stalemate():
            self.info.insert(0, "Stalemate — Draw.")
        elif self.engine.is_check():
            self.info.insert(0, "Check!")

        for w in sorted(warnings, key=lambda x: {"critical": 0, "high": 1,
                                                   "medium": 2}.get(x.severity, 9))[:5]:
            self.info.append(w.details)

        # Update cached FEN / compact PGN for the on-screen display
        self._display_fen = self.engine.board.fen()
        self._display_pgn_short = self._build_short_pgn()

    def _build_short_pgn(self) -> str:
        """Build a compact PGN movetext string like '1. e4 e5 2. Nf3 Nc6 ...'
        from the current board's move stack. No headers, no result marker
        — this is for on-screen display, not export. Save PGN writes a
        full PGN via chess.pgn.Game."""
        mvs = self.engine.move_history_san()
        if not mvs:
            return ""
        parts = []
        for i, san in enumerate(mvs):
            if i % 2 == 0:
                parts.append(f"{i // 2 + 1}.")
            parts.append(san)
        return " ".join(parts)

    def _first_move_label(self, uci: str, is_black: bool = False) -> str:
        """Fallback name for a single first move when the classifier
        can't identify a named opening. Maps familiar first moves to
        their colloquial names."""
        u = uci.lower()
        white_names = {
            "e2e4": "1. e4 (King's Pawn)",
            "d2d4": "1. d4 (Queen's Pawn)",
            "c2c4": "1. c4 (English)",
            "g1f3": "1. Nf3 (Reti/KIA)",
            "f2f4": "1. f4 (Bird)",
            "b2b3": "1. b3 (Larsen)",
            "g2g3": "1. g3 (King's Fianchetto)",
            "b1c3": "1. Nc3 (Van Geet)",
        }
        black_vs_e4 = {
            "e7e5": "1...e5 (Open Game)",
            "c7c5": "1...c5 (Sicilian)",
            "e7e6": "1...e6 (French)",
            "c7c6": "1...c6 (Caro-Kann)",
            "d7d5": "1...d5 (Scandinavian)",
            "d7d6": "1...d6 (Pirc)",
            "g8f6": "1...Nf6 (Alekhine)",
            "g7g6": "1...g6 (Modern)",
        }
        black_vs_d4 = {
            "d7d5": "1...d5 (Closed Game)",
            "g8f6": "1...Nf6 (Indian systems)",
            "f7f5": "1...f5 (Dutch)",
            "e7e6": "1...e6 (French-like)",
            "c7c5": "1...c5 (Benoni)",
            "g7g6": "1...g6 (Modern)",
        }
        if not is_black:
            return white_names.get(u, f"1. {uci}")
        # For Black we don't know White's first move here; default to
        # the e4-response dictionary which covers the most cases, then
        # fall back to d4.
        if u in black_vs_e4:
            return black_vs_e4[u]
        if u in black_vs_d4:
            return black_vs_d4[u]
        return f"1... {uci}"

    def _do(self, act):
        if act == "hint":
            best = self.engine.get_best_move_san()
            self.info = [f"Hint: Consider {best}"]
            self.arrows = []
            # Try to show arrow
            try:
                board_copy = self.engine.board.copy()
                move = board_copy.parse_san(best)
                self.arrows = [(move.from_square, move.to_square, COLOR_ARROW_BEST)]
                self.sel = move.from_square
                self.legal = [move.to_square]
            except:
                pass
            # Also surface potential discovered-check opportunities for
            # the side to move, so the hint doubles as a teaching tool.
            # We only show up to two ideas to keep the info panel
            # uncluttered, and prefer double-checks first.
            try:
                board = self.engine.board
                side = board.turn
                opps = self.reasoner.find_discovered_check_opportunities(
                    board, side)
                if opps:
                    # Double-checks before single discovered checks
                    opps_sorted = sorted(
                        opps,
                        key=lambda o: (not o["gives_direct_check"],
                                       o["san"]))
                    self.info.append("")
                    self.info.append("Discovered-check ideas for you:")
                    for opp in opps_sorted[:2]:
                        tag = " (double check!)" if opp["gives_direct_check"] else ""
                        rev_piece = board.piece_at(opp["revealer"])
                        rev_name = PT[rev_piece.piece_type] if rev_piece else "piece"
                        self.info.append(
                            f"  • {opp['san']}: reveals {rev_name}@"
                            f"{chess.square_name(opp['revealer'])}{tag}"
                        )
                    self.info.append(
                        "Tip: align a long-range piece behind a blocker, then move the blocker.")
            except Exception as e:
                print(f"[Hint] discovered-check scan failed: {e}")
        elif act == "threats":
            self.show_threats = not self.show_threats
            if self.show_threats:
                ws = self.reasoner.last_warnings
                if ws:
                    # Put discovered-check warnings first — they're the
                    # most urgent and easiest to miss visually.
                    ws_sorted = sorted(
                        ws,
                        key=lambda w: (w.threat_type != "discovered_check",
                                       {"critical": 0, "high": 1,
                                        "medium": 2}.get(w.severity, 9)))
                    self.info = [w.details for w in ws_sorted[:8]]
                else:
                    self.info = ["No immediate threats detected."]
                # Extra proactive scan: explicitly call out whether ANY
                # discovered-check could land against us next turn,
                # even if analyze() already included it — users asked
                # specifically to be warned about these.
                try:
                    incoming = self.reasoner.find_discovered_check_opportunities(
                        self.engine.board, not self.engine.board.turn)
                    if incoming:
                        n = len(incoming)
                        self.info.insert(
                            0,
                            f"⚠ {n} discovered-check pattern"
                            f"{'s' if n > 1 else ''} possible against you next turn!")
                except Exception as e:
                    print(f"[Threats] discovered-check scan failed: {e}")
            else:
                self.info = ["Threat display off."]
        elif act == "pawns":
            color = self.player_color
            advice = self.reasoner.get_pawn_structure_advice(
                self.engine.board, color)
            self.info = ["Pawn Structure Analysis:"] + advice
        elif act == "castle":
            color = self.player_color
            advice = self.reasoner.get_castling_advice(
                self.engine.board, color)
            self.info = ["Castling Advice:", advice]
        elif act == "opening":
            # Distinguish White's opening (first + odd half-moves) from
            # Black's defense (even half-moves). We classify twice: once
            # using only White's plies, once using the full move list.
            # The first tells us "what White chose"; the second tells us
            # "the combined named line (which names the defense)".
            uci_all = self.engine.move_history_uci()
            uci_white_only = uci_all[::2]  # even indices = White plies

            op_full = self.reasoner.classify_opening(uci_all)
            op_white = self.reasoner.classify_opening(uci_white_only) if uci_white_only else None

            self.info = ["Opening analysis:"]
            if uci_white_only:
                if op_white:
                    self.info.append(
                        f"White: {op_white.name} [{op_white.eco}]")
                else:
                    # Fall back to naming the first White move directly.
                    self.info.append(
                        f"White: {self._first_move_label(uci_white_only[0])}")
            else:
                self.info.append("White: (no moves yet)")

            # Black's defense: only report if at least one Black ply has
            # been played AND the full classification differs from the
            # White-only classification (otherwise it's just "same family").
            if len(uci_all) >= 2:
                if op_full and (not op_white or op_full.name != op_white.name):
                    self.info.append(
                        f"Black: {op_full.name} [{op_full.eco}]")
                elif op_full:
                    self.info.append(
                        f"Black: following the same line ({op_full.name})")
                else:
                    # Name by Black's first reply
                    self.info.append(
                        f"Black: {self._first_move_label(uci_all[1], is_black=True)}")
            else:
                self.info.append("Black: (no response yet)")

            # Plan/themes from the most specific classification we have
            best = op_full or op_white
            if best:
                if best.plan:
                    self.info.append(f"Plan: {best.plan}")
                if best.themes:
                    self.info.append(
                        f"Themes: {', '.join(str(t) for t in best.themes)}")

            # Also get Prolog opening advice for the player's color
            mn = len(self.engine.board.move_stack) // 2 + 1
            color_str = "white" if self.player_color == chess.WHITE else "black"
            prolog_advice = self.reasoner.get_opening_advice(mn, color_str)
            self.info += prolog_advice
        elif act == "learn_opening":
            if self.teacher.active:
                self.teacher.stop()
                self.info = ["Teaching stopped."]
            else:
                self.show_opening_menu = True
                self.info = ["Select an opening to learn..."]
        elif act == "undo":
            # Undo both player and AI moves
            if self.engine.undo():
                self.eval_tracker.pop()
            if self.engine.undo():
                self.eval_tracker.pop()
            self.sel = None
            self.legal = []
            self.arrows = []
            self._analyze()
        elif act == "new_game":
            if self.teacher.active:
                self.teacher.stop()
            self.engine.reset()
            self.eval_tracker.reset()
            self.sel = None
            self.legal = []
            self.threats = set()
            self.show_threats = False
            self.dragging = False
            self.drag_sq = None
            self.arrows = []
            # Clear any loaded-game replay state
            self.loaded_moves = []
            self.ply_index = 0
            self.loaded_label = ""
            self.loaded_start_fen = chess.STARTING_FEN
            self.loaded_white_name = ""
            self.loaded_black_name = ""
            # Clear AI enforcement state — a new game is a clean slate.
            self.enforced_ai_moves = []
            self.enforce_pick_mode = False
            self.enforce_pick_from = None
            self.info = ["New game! Good luck!"]
            if self.player_color == chess.BLACK:
                self._ai_go()
        elif act == "toggle_color":
            self.player_color = not self.player_color
            self.engine.ai_color = not self.player_color
            self.info = [
                f"Play as {'White' if self.player_color == chess.WHITE else 'Black'}.",
                "Press New Game to apply."]
        elif act == "cycle_ai_level":
            self.ai_profile_i = (self.ai_profile_i + 1) % len(self.ai_profile_keys)
            pkey = self.ai_profile_keys[self.ai_profile_i]
            self.profiled_ai = ProfiledAI(pkey)
            p = PROFILES[pkey]
            self.info = [f"AI: {p.name} (~{p.elo_estimate} ELO)",
                         p.description]
        elif act == "cycle_ai_opening":
            self.open_i = (self.open_i + 1) % len(OPEN_KEYS)
            k = OPEN_KEYS[self.open_i]
            self.engine.set_ai_opening(k)
            preview = self._ai_opening_preview()
            info = [f"AI Opening: {AI_OPENINGS[k]['label']}"]
            if k == "any":
                info.append("No forced opening — AI plays freely.")
            elif preview:
                info.append(f"Next {len(preview)} forced moves (UCI):")
                info.append(", ".join(preview))
            else:
                info.append("Book exhausted — AI plays freely now.")
            info.append("Press New Game to restart under this opening.")
            self.info = info
        elif act == "save_pgn":
            self._save_pgn()
        elif act == "load_pgn":
            self._load_pgn()
        elif act == "copy_fen":
            self._copy_fen()
        elif act == "copy_pgn":
            self._copy_pgn()
        elif act == "flip_board":
            self.board_flipped = not self.board_flipped
            side = "Black's POV" if self.board_flipped else "White's POV"
            self._show_toast(f"Board flipped — {side}")
            self.info = [f"Board orientation: {side}."]
        elif act == "flip_team":
            # Swap which color the human plays *immediately*, mid-game.
            # Distinct from "Color" (which only queues a side-swap that
            # takes effect on New Game) and from "Flip Board" (which
            # only rotates the view without touching any game state).
            # The engine keeps the current position and move stack —
            # only the ownership of the two sides changes, so whichever
            # side is to move next is now controlled by the other
            # player. The board view is also flipped so the human's
            # new pieces stay on the bottom.
            self.player_color = not self.player_color
            self.engine.ai_color = not self.player_color
            self.board_flipped = (self.player_color == chess.BLACK)
            # Cancel any enforce-move picker state — it referenced the
            # old AI color and would be nonsensical after the swap.
            self.enforce_pick_mode = False
            self.enforce_pick_from = None
            self.sel = None
            self.legal = []
            self.arrows = []
            new_side = "White" if self.player_color == chess.WHITE else "Black"
            self._show_toast(f"Swapped — you now play {new_side}")
            self.info = [
                f"You are now playing {new_side}.",
                "The position is unchanged; only sides swapped.",
            ]
            # If it's now the AI's turn, let it think and move.
            if self.engine.board.turn == self.engine.ai_color and not self.engine.is_game_over():
                self._ai_go()
        elif act == "enforce_move":
            self._start_enforce_move()
        elif act == "enforce_sequence":
            self._start_enforce_sequence()
        elif act == "free_ai":
            self._free_ai()
        elif act == "menu":
            self.app_state = "menu"
            self.show_help = False
            self.show_opening_menu = False

    # ── AI enforcement helpers ────────────────────────────────────────
    def _start_enforce_move(self):
        """Enter modal pick mode. Two subsequent board clicks pick the
        AI's next move (from-square, then to-square). Cancels any
        existing sequence queue so the user's intent is unambiguous."""
        if self.engine.is_game_over():
            self.info = ["Game is over — no AI move to enforce."]
            return
        # Preserve any already-queued moves by default — user can click
        # Free AI first if they want a clean slate.
        self.enforce_pick_mode = True
        self.enforce_pick_from = None
        ai_color_str = "White" if self.engine.ai_color == chess.WHITE else "Black"
        self.info = [
            f"Enforce AI move: click an AI ({ai_color_str}) piece,",
            "then click the destination square.",
            "ESC cancels. The move will be queued for the AI's next turn.",
        ]

    def _start_enforce_sequence(self):
        """Open the sequence modal. The user types a whitespace-separated
        list of UCI (e2e4) or SAN (Nf3) tokens which are parsed into a
        FIFO queue of chess.Move objects."""
        if self.engine.is_game_over():
            self.info = ["Game is over — no AI moves to enforce."]
            return
        self.show_sequence_modal = True
        self.sequence_input.text = ""
        self.sequence_input.focused = True
        self.info = [
            "Enforce-sequence modal open.",
            "Type moves and press Enter.",
        ]

    def _free_ai(self):
        """Clear any enforced move or queue — the AI becomes autonomous
        again on its next turn."""
        had = self.enforced_ai_moves or self.enforce_pick_mode
        self.enforced_ai_moves = []
        self.enforce_pick_mode = False
        self.enforce_pick_from = None
        if had:
            self.info = ["AI freed — autonomous on next turn."]
        else:
            self.info = ["AI was already autonomous."]

    def _ai_has_any_move_from(self, sq: int) -> bool:
        """Return True if the AI has at least one legal move from `sq`
        assuming it is the AI's turn. We check against a probe board
        whose turn is flipped to the AI's color — this lets the user
        pre-pick the AI's response before the AI's turn arrives."""
        board = self.engine.board
        ai_color = self.engine.ai_color
        piece = board.piece_at(sq)
        if not piece or piece.color != ai_color:
            return False
        # If it's already the AI's turn, use the real legal_moves.
        if board.turn == ai_color:
            return any(m.from_square == sq for m in board.legal_moves)
        # Otherwise, probe with turn flipped. This isn't perfectly accurate
        # for positions where the human's move radically changes the board
        # (captures, discovered checks), but it's a useful sanity filter.
        probe = board.copy()
        probe.turn = ai_color
        try:
            return any(m.from_square == sq for m in probe.legal_moves)
        except Exception:
            return False

    def _build_enforced_move(self, fr: int, to: int) -> Optional[chess.Move]:
        """Build a chess.Move from (fr, to) and validate it against a
        probe board where it is the AI's turn. Auto-queens pawn promotions
        so the user doesn't have to pick. Returns None if no legal move
        connects the two squares for the AI."""
        board = self.engine.board
        ai_color = self.engine.ai_color
        probe = board.copy()
        if probe.turn != ai_color:
            probe.turn = ai_color
        # Try plain move first
        m = chess.Move(fr, to)
        if m in probe.legal_moves:
            return m
        # Try with queen promotion
        mq = chess.Move(fr, to, promotion=chess.QUEEN)
        if mq in probe.legal_moves:
            return mq
        return None

    def _submit_enforced_sequence(self, text: str):
        """Callback from the sequence input: parse space-separated tokens
        into chess.Move objects by replaying them on a probe board. UCI
        and SAN are both accepted. The first token that fails to parse
        stops the queue (we honor everything up to that point and warn
        about the tail in the info panel)."""
        tokens = text.replace(",", " ").split()
        if not tokens:
            self.info = ["Sequence was empty — nothing queued."]
            self.show_sequence_modal = False
            self.sequence_input.focused = False
            return

        # Probe from the current position, AI color first regardless of
        # whose turn it actually is. If the sequence describes a pure AI
        # plan (only AI plies), each token must be legal in turn as the
        # AI; we force probe.turn = ai_color at the start and re-force
        # it after every push so that Human plies in the probe never
        # block the parse.
        board = self.engine.board
        ai_color = self.engine.ai_color
        probe = board.copy()
        probe.turn = ai_color
        queued: list[chess.Move] = []
        failed_at: Optional[int] = None
        fail_token: str = ""

        for i, tok in enumerate(tokens):
            m: Optional[chess.Move] = None
            # Try UCI
            try:
                cand = chess.Move.from_uci(tok)
                if cand in probe.legal_moves:
                    m = cand
            except ValueError:
                pass
            # Try SAN
            if m is None:
                try:
                    m = probe.parse_san(tok)
                except Exception:
                    m = None
            if m is None or m not in probe.legal_moves:
                failed_at = i
                fail_token = tok
                break
            queued.append(m)
            probe.push(m)
            # Force probe back to AI's turn so the next token is parsed
            # as an AI move (we're enforcing an AI-move sequence, not a
            # full game script).
            probe.turn = ai_color

        # Apply the queue
        self.enforced_ai_moves = queued
        self.show_sequence_modal = False
        self.sequence_input.focused = False
        self.sequence_input.text = ""

        if failed_at is not None:
            self.info = [
                f"Queued {len(queued)} move(s).",
                f"Stopped at token #{failed_at + 1}: '{fail_token}' — not legal.",
                "Remaining tokens were discarded.",
            ]
        else:
            self.info = [
                f"Queued {len(queued)} move(s) for the AI.",
                "They will be played in order on the AI's next turns.",
                "Use 'Free AI' to cancel.",
            ]


    # ── Menu / Splash / Credits / Masters ──────────────────────────
    def _draw_menu(self):
        """Main menu + splash screen."""
        arcade.draw_lbwh_rectangle_filled(0, 0, self.width, self.height, COLOR_MENU_BG)

        # Decorative board corner glyph (big pawn)
        cx = self.width // 2
        arcade.draw_text("♚",
                         cx, self.height - 190, COLOR_MENU_TITLE,
                         font_size=110, anchor_x="center")

        # Title
        arcade.draw_text("CHESS",
                         cx, self.height - 260, COLOR_MENU_TITLE,
                         font_size=56, anchor_x="center", bold=True)
        arcade.draw_text("Human vs AI — Prolog-Janus reasoning",
                         cx, self.height - 300, COLOR_MENU_SUBTITLE,
                         font_size=14, anchor_x="center")
        arcade.draw_text("v1.1 — with eval tracking & master games",
                         cx, self.height - 322, COLOR_TEXT_DIM,
                         font_size=10, anchor_x="center")

        # Menu buttons
        entries = [
            ("play",      "Play",                    "Start or continue a game"),
            ("masters",   "Master Games",            "Replay Tal, Capablanca, Fischer, Kasparov, Carlsen…"),
            ("imbalances", "Reassess Your Chess Through Imbalances",
             "Silman-inspired positional tutorial in 64 lessons"),
            ("openings_white", "White Openings",     "Named openings from White's perspective"),
            ("openings_black", "Black Openings",     "Named defenses from Black's perspective"),
            ("table",     "Openings Matrix Tables",  "White openings × Black defenses cross-table"),
            ("settings",  "Settings",                "Piece style, theme, and board material"),
            ("credits",   "Credits",                 "About this project"),
            ("quit",      "Quit",                    "Exit the application"),
        ]
        btn_w, btn_h = 360, 42
        gap = 10
        total_h = len(entries) * (btn_h + gap) - gap
        start_y = self.height // 2 + total_h // 2 - 60

        self._menu_rects = []
        mx, my = self._mouse_xy()
        for i, (action, label, sub) in enumerate(entries):
            by = start_y - i * (btn_h + gap)
            bx = cx - btn_w // 2
            hover = (bx <= mx <= bx + btn_w and by <= my <= by + btn_h)
            bg = COLOR_MENU_BTN_HOVER if hover else COLOR_MENU_BTN_BG
            arcade.draw_lbwh_rectangle_filled(bx, by, btn_w, btn_h, bg)
            arcade.draw_rect_outline(
                XYWH(bx + btn_w / 2, by + btn_h / 2, btn_w, btn_h),
                COLOR_ACCENT, 1)
            arcade.draw_text(label, cx, by + btn_h - 24, COLOR_TEXT,
                             font_size=16, anchor_x="center", bold=True)
            arcade.draw_text(sub, cx, by + 6, COLOR_TEXT_DIM,
                             font_size=9, anchor_x="center")
            self._menu_rects.append((action, bx, by, btn_w, btn_h))

        arcade.draw_text("ESC to quit  •  click Play to begin",
                         cx, 30, COLOR_TEXT_DIM,
                         font_size=10, anchor_x="center")

    def _mouse_xy(self):
        """Best-effort mouse position (Arcade 3.x exposes via window._mouse_x?)."""
        mx = getattr(self, "_hover_mx", -1)
        my = getattr(self, "_hover_my", -1)
        return mx, my

    def _handle_menu_click(self, x, y):
        for action, bx, by, bw, bh in self._menu_rects:
            if bx <= x <= bx + bw and by <= y <= by + bh:
                if action == "play":
                    # Enter game mode with a clean slate. Without this,
                    # state left over from another mode (master-game
                    # replay, opening teacher, loaded PGN, eval history,
                    # stale selection/arrows) would follow the user into
                    # the new game. Routing through "new_game" reuses the
                    # single canonical reset (engine, eval tracker, teacher,
                    # loaded-game replay state, AI enforcement, and UI
                    # selection/drag/threat/arrow state) and also kicks off
                    # the AI's first move when the player is Black.
                    self.app_state = "game"
                    self._do("new_game")
                elif action == "masters":
                    self.app_state = "masters"
                    # v10: always start at the top of the masters list
                    # whether the user is opening it for the first time
                    # or re-opening it after a back-navigation.
                    self._masters_scroll = 0
                elif action == "table":
                    self.app_state = "openings_table"
                    self.openings_table_white_i = 0  # default row
                elif action == "openings_white":
                    # Dedicated view: just the White first-move rows
                    # with their named openings, no Black defense
                    # columns. Reuses the openings_table state but
                    # flagged via openings_view_side.
                    self.app_state = "openings_list"
                    self.openings_view_side = "white"
                elif action == "openings_black":
                    self.app_state = "openings_list"
                    self.openings_view_side = "black"
                elif action == "imbalances":
                    # v12: open the Silman-inspired imbalances tutorial
                    self.app_state = "imbalances"
                    # Reset position whenever we enter from the menu —
                    # users opening it fresh expect to see the first
                    # part (Concept of Imbalances) at the top.
                    self._imbalance_part_i = 0
                    self._imbalance_scroll = 0
                elif action == "credits":
                    self.app_state = "credits"
                elif action == "settings":
                    self.app_state = "settings"
                elif action == "quit":
                    self.close()
                return

    def _draw_credits(self):
        """Credits / about overlay."""
        arcade.draw_lbwh_rectangle_filled(0, 0, self.width, self.height, COLOR_MENU_BG)
        cx = self.width // 2

        arcade.draw_text("CREDITS",
                         cx, self.height - 110, COLOR_MENU_TITLE,
                         font_size=36, anchor_x="center", bold=True)

        lines = [
            "",
            "CHESS — Human vs AI",
            "A study project in chess reasoning & UI design.",
            "",
            "Core libraries:",
            "   python-chess     — board model and move validation",
            "   arcade 3.x       — 2D rendering and input",
            "   janus-swi        — Prolog bridge (optional)",
            "",
            "Modules:",
            "   chess_engine.py     — minimax + alpha-beta AI",
            "   ai_profiles.py      — difficulty profiles (~400 to ~1800 ELO)",
            "   prolog_reasoner.py  — threat / pawn / castling analysis",
            "   opening_teacher.py  — guided opening practice",
            "   eval_tracker.py     — per-move cp and delta history",
            "   master_games.py     — Tal, Capablanca, Karpov, Kasparov,",
            "                          Fischer, Carlsen, Silman.",
            "",
            "PGN is saved to  ./pgn_losses/",
            "",
            "Built with patience. Improved with honest feedback.",
            "",
            "— click anywhere or press ESC to return —",
        ]

        y = self.height - 160
        for line in lines:
            col = COLOR_TEXT if not line.startswith("   ") else COLOR_TEXT_DIM
            if line.endswith(":"):
                col = COLOR_ACCENT
            arcade.draw_text(line, cx, y, col,
                             font_size=13, anchor_x="center")
            y -= 22

    # ── v9: Settings page ────────────────────────────────────────────
    def _draw_settings(self):
        """Settings page: piece style (Classical/Fancy), fancy theme
        (Roman / Fantasy / Sci-fi / Steampunk / Cyberpunk — only enabled
        when style = Fancy), and board material (Wood / Marble / Carbon /
        Bone / Plasma). Mutates self.piece_theme,
        self.board_material_key, self.piece_style, self.fancy_theme.

        Click rects for every option are written to self._settings_rects
        as (action_id, lbwh) tuples; _handle_settings_click reads these.
        action_id is one of:
            "style:classical" | "style:fancy"
            "theme:roman" | "theme:fantasy" | "theme:scifi" | ...
            "material:classical_wood" | "material:marble" | ...
            "back"
        """
        arcade.draw_lbwh_rectangle_filled(
            0, 0, self.width, self.height, COLOR_MENU_BG)
        cx = self.width // 2

        # Title
        arcade.draw_text("SETTINGS",
                         cx, self.height - 80, COLOR_MENU_TITLE,
                         font_size=42, anchor_x="center", bold=True)
        arcade.draw_text(
            "Visual presentation — pieces, themes, and board material.",
            cx, self.height - 118, COLOR_MENU_SUBTITLE,
            font_size=12, anchor_x="center")
        arcade.draw_text(
            "Click an option to apply. ESC or Backspace returns to menu.",
            cx, self.height - 138, COLOR_TEXT_DIM,
            font_size=10, anchor_x="center")

        self._settings_rects = []
        mx, my = self._mouse_xy()

        # Layout constants
        row_w = 720
        row_x = cx - row_w // 2
        row_h = 92
        gap = 18
        first_y = self.height - 200

        # ── Row 1: Piece style (Classical / Fancy) ────────────────────
        y1 = first_y - row_h
        self._draw_settings_row_bg(row_x, y1, row_w, row_h)
        arcade.draw_text("Piece style", row_x + 18, y1 + row_h - 26,
                         COLOR_ACCENT, font_size=14, bold=True)
        arcade.draw_text(
            "Classical = traditional set. Fancy = themed sub-set.",
            row_x + 18, y1 + 8, COLOR_TEXT_DIM, font_size=10)
        # Two big buttons inside the row
        opts1 = [
            ("style:classical", "Classical",
             self.piece_style == "classical"),
            ("style:fancy", "Fancy",
             self.piece_style == "fancy"),
        ]
        self._draw_settings_options(opts1, row_x + 200, y1 + 24,
                                    btn_w=220, btn_h=48, mx=mx, my=my)

        # ── Row 2: Fancy theme picker ─────────────────────────────────
        y2 = y1 - row_h - gap
        self._draw_settings_row_bg(row_x, y2, row_w, row_h)
        title2_color = (COLOR_ACCENT if self.piece_style == "fancy"
                        else COLOR_TEXT_DIM)
        arcade.draw_text("Fancy theme", row_x + 18, y2 + row_h - 26,
                         title2_color, font_size=14, bold=True)
        arcade.draw_text(
            "Active when style = Fancy. Replace PNGs in "
            "assets/textures/pieces/{theme}/ with your own art.",
            row_x + 18, y2 + 8, COLOR_TEXT_DIM, font_size=9)
        # Five fancy options laid out as small buttons
        fancy_opts = [
            ("theme:roman",     "Roman"),
            ("theme:fantasy",   "Fantasy"),
            ("theme:scifi",     "Sci-Fi"),
            ("theme:steampunk", "Steampunk"),
            ("theme:cyberpunk", "Cyberpunk"),
        ]
        opts2 = [(aid, label, self.piece_style == "fancy" and
                  self.fancy_theme == aid.split(":", 1)[1])
                 for aid, label in fancy_opts]
        self._draw_settings_options(
            opts2, row_x + 130, y2 + 24,
            btn_w=104, btn_h=44, mx=mx, my=my,
            disabled=(self.piece_style != "fancy"),
            gap_x=6)

        # ── Row 3: Board material ─────────────────────────────────────
        y3 = y2 - row_h - gap
        self._draw_settings_row_bg(row_x, y3, row_w, row_h)
        arcade.draw_text("Board material", row_x + 18, y3 + row_h - 26,
                         COLOR_ACCENT, font_size=14, bold=True)
        arcade.draw_text(
            "Square palette — pure colour, no asset reload.",
            row_x + 18, y3 + 8, COLOR_TEXT_DIM, font_size=10)
        mat_opts = []
        for m in board_materials.all_materials():
            aid = f"material:{m.key}"
            mat_opts.append(
                (aid, m.label, self.board_material_key == m.key))
        self._draw_settings_options(
            mat_opts, row_x + 150, y3 + 24,
            btn_w=104, btn_h=44, mx=mx, my=my, gap_x=6)

        # ── Row 4: Gender overlay (♂ kingside / ♀ queenside) ─────────
        # Optional landmark to distinguish kingside vs queenside
        # pieces. Press 'O' in-game to toggle live; this row sets the
        # default. Drawn as a small ♂ / ♀ glyph badge on each flanked
        # piece (R/B/N/P) — kings and queens never get one.
        y4 = y3 - row_h - gap
        self._draw_settings_row_bg(row_x, y4, row_w, row_h)
        arcade.draw_text("Gender overlay",
                         row_x + 18, y4 + row_h - 26,
                         COLOR_ACCENT, font_size=14, bold=True)
        arcade.draw_text(
            "Adds ♂ (kingside) / ♀ (queenside) glyphs on each piece. "
            "Toggle live in-game with the 'O' key.",
            row_x + 18, y4 + 8, COLOR_TEXT_DIM, font_size=9)
        gender_opts = [
            ("gender:off", "Off",
             not self.gender_overlay_enabled),
            ("gender:on", "On  ♂ ♀",
             self.gender_overlay_enabled),
        ]
        self._draw_settings_options(
            gender_opts, row_x + 200, y4 + 24,
            btn_w=220, btn_h=48, mx=mx, my=my)

        # ── Back button ──────────────────────────────────────────────
        back_w, back_h = 160, 40
        back_x = cx - back_w // 2
        # Lower the back button slightly so it doesn't crowd the new
        # 4th settings row on smaller windows.
        back_y = 30
        hover = (back_x <= mx <= back_x + back_w and
                 back_y <= my <= back_y + back_h)
        bg = COLOR_MENU_BTN_HOVER if hover else COLOR_MENU_BTN_BG
        arcade.draw_lbwh_rectangle_filled(back_x, back_y, back_w, back_h, bg)
        arcade.draw_rect_outline(
            XYWH(back_x + back_w / 2, back_y + back_h / 2, back_w, back_h),
            COLOR_ACCENT, 1)
        arcade.draw_text("Back to menu", back_x + back_w // 2,
                         back_y + back_h // 2 - 8,
                         COLOR_TEXT, font_size=13, anchor_x="center", bold=True)
        self._settings_rects.append(
            ("back", back_x, back_y, back_w, back_h))

        # Status / current state line
        status = (
            f"Current: piece_theme = {self.piece_theme!r}    "
            f"board_material = {self.board_material_key!r}    "
            f"gender_overlay = {self.gender_overlay_enabled}"
        )
        arcade.draw_text(status, cx, 8, COLOR_TEXT_DIM,
                         font_size=10, anchor_x="center")

    def _draw_settings_row_bg(self, lx, by, w, h):
        """Decorative row background — slightly darker plate with
        accent border. Shared between the three settings rows."""
        arcade.draw_lbwh_rectangle_filled(
            lx, by, w, h, (32, 36, 44, 220))
        arcade.draw_rect_outline(
            XYWH(lx + w / 2, by + h / 2, w, h),
            (90, 100, 120, 255), 1)

    def _draw_settings_options(self, opts, lx, by, btn_w, btn_h,
                               mx, my, disabled=False, gap_x=12):
        """Draw a horizontal row of selectable option buttons. Each
        opt is (action_id, label, is_active). Active option gets a
        green border; hover gets a brighter background; disabled rows
        are dim and not clickable."""
        x = lx
        for aid, label, active in opts:
            hover = (x <= mx <= x + btn_w and by <= my <= by + btn_h
                     and not disabled)
            if disabled:
                bg = (40, 44, 52, 200)
                fg = (110, 110, 120, 255)
                border = (70, 75, 85, 255)
                bw = 1
            elif active:
                bg = (50, 78, 60, 240)
                fg = COLOR_TEXT
                border = (120, 200, 120, 255)
                bw = 2
            elif hover:
                bg = COLOR_MENU_BTN_HOVER
                fg = COLOR_TEXT
                border = COLOR_ACCENT
                bw = 1
            else:
                bg = COLOR_MENU_BTN_BG
                fg = COLOR_TEXT
                border = COLOR_ACCENT
                bw = 1
            arcade.draw_lbwh_rectangle_filled(x, by, btn_w, btn_h, bg)
            arcade.draw_rect_outline(
                XYWH(x + btn_w / 2, by + btn_h / 2, btn_w, btn_h),
                border, bw)
            arcade.draw_text(label, x + btn_w // 2,
                             by + btn_h // 2 - 7,
                             fg, font_size=12, anchor_x="center", bold=active)
            if not disabled:
                self._settings_rects.append((aid, x, by, btn_w, btn_h))
            x += btn_w + gap_x

    def _handle_settings_click(self, x, y):
        """Apply the option clicked, then save settings to disk so the
        choice survives restart. Texture cache is cleared on theme
        change so the next frame rebuilds with the new artwork."""
        for action, bx, by, bw, bh in self._settings_rects:
            if not (bx <= x <= bx + bw and by <= y <= by + bh):
                continue
            if action == "back":
                self.app_state = "menu"
                return
            if action == "style:classical":
                self.piece_style = "classical"
                self.piece_theme = "classical"
            elif action == "style:fancy":
                self.piece_style = "fancy"
                # Restore last fancy choice (or default to roman).
                self.piece_theme = self.fancy_theme
            elif action.startswith("theme:"):
                # Only effective when style = fancy; if user clicks a
                # disabled theme button the rect won't have been
                # registered, so we won't get here.
                theme = action.split(":", 1)[1]
                self.fancy_theme = theme
                if self.piece_style == "fancy":
                    self.piece_theme = theme
            elif action.startswith("material:"):
                key = action.split(":", 1)[1]
                self.board_material_key = key
            elif action.startswith("gender:"):
                # v10: explicit toggle from the settings page. Note we
                # skip the texture-cache flush below because the
                # overlay is a separate post-pass and doesn't touch
                # piece textures at all — the next frame just reads
                # the new flag and draws (or doesn't draw) the glyphs.
                self.gender_overlay_enabled = (
                    action.split(":", 1)[1] == "on")
                self._settings_save()
                return

            # Theme/material changes invalidate the piece-texture cache
            # so the next render fetches the new PNGs / placeholders.
            # board_materials is colour-only and needs no cache flush.
            piece_textures.clear_cache()
            # Drop our sprite cache too — the cached sprites still
            # reference the old textures, so a fresh frame must rebuild.
            for sp in self._piece_sprites.values():
                try:
                    self._piece_sprite_list.remove(sp)
                except (ValueError, KeyError):
                    pass
            self._piece_sprites.clear()
            self._settings_save()
            return

    def _draw_masters_browser(self):
        """Master games selector."""
        # Park every avatar sprite off-screen first; only the ones we
        # reposition onto rows this frame should be visible.
        self._park_all_avatar_sprites()

        arcade.draw_lbwh_rectangle_filled(0, 0, self.width, self.height, COLOR_MENU_BG)
        cx = self.width // 2

        arcade.draw_text("MASTER GAMES",
                         cx, self.height - 60, COLOR_MENU_TITLE,
                         font_size=30, anchor_x="center", bold=True)
        arcade.draw_text("Select a game to replay it onto the board.",
                         cx, self.height - 92, COLOR_MENU_SUBTITLE,
                         font_size=11, anchor_x="center")
        arcade.draw_text("ESC to return to menu.",
                         cx, self.height - 108, COLOR_TEXT_DIM,
                         font_size=9, anchor_x="center")

        # List of games as clickable cards
        mx, my = self._mouse_xy()
        self._masters_rects = []
        row_h = 62
        top_y = self.height - 140
        bottom_y = 40
        list_w = min(900, self.width - 80)
        list_x = cx - list_w // 2

        # Avatar column widths at each end of the row
        av_size = 44
        av_margin = 10  # horizontal padding inside the row
        left_av_cx = list_x + av_margin + av_size // 2
        right_av_cx = list_x + list_w - av_margin - av_size // 2

        # Inner text bounds shrink so the avatars don't overlap text
        text_left = list_x + av_margin * 2 + av_size
        text_right = list_x + list_w - av_margin * 2 - av_size

        # ── v10: Scrolling support ───────────────────────────────────
        # The list now holds 20+ entries — more than fit on most
        # windows. We compute how many rows fit and clamp
        # _masters_scroll so it stays in the valid range every frame
        # (window resize, list growth, etc. all stay correct).
        viewport_h = top_y - bottom_y
        rows_fit = max(1, viewport_h // row_h)
        max_scroll = max(0, len(MASTER_GAMES) - rows_fit)
        if self._masters_scroll < 0:
            self._masters_scroll = 0
        if self._masters_scroll > max_scroll:
            self._masters_scroll = max_scroll

        for i, game in enumerate(MASTER_GAMES):
            # Apply scroll offset: subtract _masters_scroll rows worth
            # of pixels, so scrolling down lifts later entries into
            # the visible viewport.
            ry = top_y - (i - self._masters_scroll) * row_h
            if ry > top_y + row_h - 6:
                continue  # off the top — scrolled past
            if ry - row_h + 6 < bottom_y:
                break  # off the bottom — clip the rest
            hover = (list_x <= mx <= list_x + list_w
                     and ry - row_h + 6 <= my <= ry)
            bg = COLOR_MENU_BTN_HOVER if hover else (
                (48, 56, 72, 230) if i % 2 == 0 else (40, 48, 62, 230))
            arcade.draw_lbwh_rectangle_filled(list_x, ry - row_h + 6, list_w, row_h - 4, bg)
            arcade.draw_rect_outline(
                XYWH(list_x + list_w / 2, ry - row_h / 2 + 4, list_w, row_h - 4),
                COLOR_ACCENT, 1)

            # Avatars: the FEATURED player (game.player) sits on the
            # left, immediately next to their highlighted name tag.
            # The opponent sits on the right. This avoids the confusing
            # case where the player tag (e.g. "Javokhir Sindarov") sat
            # right next to their *opponent's* avatar (Firouzja, who
            # played White in that game). The small label under each
            # avatar still reflects which colour they played, so the
            # White/Black role information is preserved.
            #
            # Slot-keyed so the same player appearing in two different
            # rows gets two distinct sprites (one position each frame).
            av_cy = ry - row_h // 2 + 4
            # Resolve who is featured vs opponent, and what side each
            # one played, robust to "Study Position" or mismatched
            # player tags.
            if game.player == game.black and game.player != game.white:
                featured_name = game.black
                opponent_name = game.white
                featured_side_label = "Black"
                opponent_side_label = "White"
            else:
                # Default / common case: featured player = White, or
                # the player field doesn't match either side cleanly
                # (e.g. Study Position vs Study Position).
                featured_name = game.white
                opponent_name = game.black
                featured_side_label = "White"
                opponent_side_label = "Black"

            featured_sprite = self._get_avatar_sprite(
                featured_name, "master", av_size,
                slot_key=f"masters_row{i}_featured")
            featured_sprite.position = (left_av_cx, av_cy)
            opponent_sprite = self._get_avatar_sprite(
                opponent_name, "master", av_size,
                slot_key=f"masters_row{i}_opponent")
            opponent_sprite.position = (right_av_cx, av_cy)
            # Side labels under each avatar — reflect the actual
            # colour each one played in this game.
            arcade.draw_text(featured_side_label,
                             left_av_cx - 14, ry - row_h + 10,
                             COLOR_TEXT_DIM, font_size=8)
            arcade.draw_text(opponent_side_label,
                             right_av_cx - 14, ry - row_h + 10,
                             COLOR_TEXT_DIM, font_size=8)

            # Player tag (left, after the white avatar)
            arcade.draw_text(game.player,
                             text_left, ry - 20, COLOR_MENU_TITLE,
                             font_size=12, bold=True)

            # Title
            arcade.draw_text(game.title,
                             text_left, ry - 38, COLOR_TEXT,
                             font_size=11)

            # White vs Black as a sub-label under the player tag
            matchup = f"{game.white}  vs  {game.black}"
            arcade.draw_text(matchup,
                             text_left, ry - 54, COLOR_TEXT_DIM,
                             font_size=9)

            # Date / result / ECO — shift to the middle-right area
            meta = f"{game.date}  {game.result}  [{game.eco}]"
            arcade.draw_text(meta,
                             text_right - 180, ry - 20,
                             COLOR_TEXT_DIM, font_size=9)

            # Truncation warning
            if game.truncated:
                arcade.draw_text("(partial — legal moves only)",
                                 text_right - 180, ry - 54,
                                 (220, 160, 80, 255), font_size=9)

            # Move count + opening
            arcade.draw_text(f"{len(game.moves_san)} moves  •  {game.opening}",
                             text_right - 180, ry - 38,
                             COLOR_TEXT_DIM, font_size=9)

            self._masters_rects.append((i, list_x, ry - row_h + 6, list_w, row_h - 4))

        # ── v10: Scroll indicator + hint ─────────────────────────────
        # Show "page X / Y" + a thin scrollbar on the right edge of
        # the list, plus a hint line so users discover the wheel/keys.
        if max_scroll > 0:
            # Hint line under the title
            arcade.draw_text(
                "Scroll wheel / ↑↓ / PgUp / PgDn / Home / End to scroll",
                cx, self.height - 124, COLOR_TEXT_DIM,
                font_size=9, anchor_x="center")
            # Position counter
            shown_first = self._masters_scroll + 1
            shown_last = min(len(MASTER_GAMES),
                             self._masters_scroll + rows_fit)
            arcade.draw_text(
                f"Showing {shown_first}–{shown_last} of {len(MASTER_GAMES)}",
                list_x + list_w - 6, top_y + 8,
                COLOR_TEXT_DIM, font_size=9, anchor_x="right")
            # Thin scrollbar track + thumb on the right gutter
            sb_x = list_x + list_w + 6
            sb_w = 6
            sb_top = top_y
            sb_bot = bottom_y
            sb_h = sb_top - sb_bot
            arcade.draw_lbwh_rectangle_filled(
                sb_x, sb_bot, sb_w, sb_h, (50, 56, 70, 200))
            thumb_h = max(20, int(sb_h * rows_fit / len(MASTER_GAMES)))
            thumb_travel = sb_h - thumb_h
            thumb_y = (sb_top - thumb_h
                       - int(thumb_travel * self._masters_scroll / max_scroll))
            arcade.draw_lbwh_rectangle_filled(
                sb_x, thumb_y, sb_w, thumb_h, COLOR_ACCENT)

        # Flush the avatar sprites for this frame
        self._avatar_sprite_list.draw()

    def _handle_masters_click(self, x, y):
        for idx, rx, ry, rw, rh in self._masters_rects:
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                self._load_master_game(MASTER_GAMES[idx])
                self.app_state = "game"
                return

    # ── v12: Imbalances tutorial (Silman-inspired) ───────────────────
    def _draw_imbalances_browser(self):
        """Two-pane browser for the imbalances tutorial.

        Left pane: the 9 book parts (Concept of Imbalances, Minor
        Pieces, Rooks, etc.). Click one to make it active.
        Right pane: the lessons that belong to the active part —
        scrollable when more than fit on screen. Click a lesson to
        open its detail page.

        Click rects are stored on self._imbalance_part_rects and
        self._imbalance_lesson_rects, consumed by
        _handle_imbalances_click."""
        arcade.draw_lbwh_rectangle_filled(
            0, 0, self.width, self.height, COLOR_MENU_BG)
        cx = self.width // 2

        # Title block
        arcade.draw_text(
            "REASSESS YOUR CHESS THROUGH IMBALANCES",
            cx, self.height - 50, COLOR_MENU_TITLE,
            font_size=24, anchor_x="center", bold=True)
        arcade.draw_text(
            "A 64-lesson positional tutorial inspired by Jeremy "
            "Silman's 'How to Reassess Your Chess, 4th Edition'.",
            cx, self.height - 80, COLOR_MENU_SUBTITLE,
            font_size=11, anchor_x="center")
        arcade.draw_text(
            "Click a part on the left, then a lesson on the right. "
            "ESC or Backspace to return to the menu.",
            cx, self.height - 98, COLOR_TEXT_DIM,
            font_size=9, anchor_x="center")

        # Layout: left pane = parts list, right pane = lessons list
        top_y = self.height - 130
        bot_y = 40
        margin = 30
        left_w = 320
        right_x = margin + left_w + margin
        right_w = self.width - right_x - margin

        mx, my = self._mouse_xy()

        # ── Left pane: parts list ────────────────────────────────────
        arcade.draw_text("BOOK PARTS",
                         margin, top_y + 8, COLOR_ACCENT,
                         font_size=11, bold=True)
        self._imbalance_part_rects = []
        part_row_h = 56
        # Total parts always fit; no scrolling for the left column.
        for i, part_name in enumerate(IMBALANCE_PARTS):
            ry = top_y - i * (part_row_h + 4) - part_row_h
            if ry < bot_y:
                break  # safety — would only happen on very small windows
            active = (i == self._imbalance_part_i)
            hover = (margin <= mx <= margin + left_w
                     and ry <= my <= ry + part_row_h)
            if active:
                bg = (70, 120, 170, 230)
            elif hover:
                bg = COLOR_MENU_BTN_HOVER
            else:
                bg = (48, 56, 72, 230) if i % 2 == 0 else (40, 48, 62, 230)
            arcade.draw_lbwh_rectangle_filled(
                margin, ry, left_w, part_row_h, bg)
            arcade.draw_rect_outline(
                XYWH(margin + left_w / 2, ry + part_row_h / 2,
                     left_w, part_row_h),
                COLOR_ACCENT if active else (80, 90, 110, 200), 1)

            # Part number + name
            n_lessons = len(imbalance_lessons_for_part(part_name))
            arcade.draw_text(
                f"Part {i + 1}",
                margin + 10, ry + part_row_h - 20,
                COLOR_TEXT_DIM, font_size=9)
            arcade.draw_text(
                part_name,
                margin + 10, ry + part_row_h - 36,
                COLOR_TEXT, font_size=12, bold=True)
            arcade.draw_text(
                f"{n_lessons} lessons",
                margin + 10, ry + 6,
                COLOR_TEXT_DIM, font_size=9)

            self._imbalance_part_rects.append(
                (i, margin, ry, left_w, part_row_h))

        # ── Right pane: lessons for the active part ──────────────────
        active_part = IMBALANCE_PARTS[self._imbalance_part_i]
        arcade.draw_text(active_part.upper(),
                         right_x, top_y + 8, COLOR_ACCENT,
                         font_size=11, bold=True)

        # Part description blurb above the lesson list
        desc = IMBALANCE_PART_DESCRIPTIONS.get(active_part, "")
        desc_y = top_y - 8
        # Word-wrap the description manually to fit the pane width.
        # Approximate chars per line based on font_size 10 ≈ 6.2px per
        # character, with some headroom.
        max_chars = max(20, int(right_w / 6.4))
        for line in self._wrap_text(desc, max_chars)[:3]:
            arcade.draw_text(line, right_x, desc_y, COLOR_TEXT_DIM,
                             font_size=10)
            desc_y -= 14
        # Divider
        arcade.draw_lbwh_rectangle_filled(
            right_x, desc_y - 4, right_w, 1, (80, 90, 110, 200))

        # Lesson list — scrollable. Each row shows lesson title + a
        # tiny FEN-available indicator + a one-line preview of the
        # key idea.
        lesson_list_top = desc_y - 14
        lesson_row_h = 54
        lessons = imbalance_lessons_for_part(active_part)
        viewport_h = lesson_list_top - bot_y
        rows_fit = max(1, viewport_h // lesson_row_h)
        max_scroll = max(0, len(lessons) - rows_fit)
        # Clamp scroll to valid range every frame (window resize,
        # part switch, etc. all stay correct).
        if self._imbalance_scroll < 0:
            self._imbalance_scroll = 0
        if self._imbalance_scroll > max_scroll:
            self._imbalance_scroll = max_scroll

        self._imbalance_lesson_rects = []
        for j, lesson in enumerate(lessons):
            ry = lesson_list_top - (j - self._imbalance_scroll) * lesson_row_h
            if ry > lesson_list_top + 4:
                continue
            if ry - lesson_row_h + 4 < bot_y:
                break
            hover = (right_x <= mx <= right_x + right_w
                     and ry - lesson_row_h + 4 <= my <= ry)
            bg = COLOR_MENU_BTN_HOVER if hover else (
                (48, 56, 72, 230) if j % 2 == 0 else (40, 48, 62, 230))
            arcade.draw_lbwh_rectangle_filled(
                right_x, ry - lesson_row_h + 4,
                right_w, lesson_row_h - 4, bg)
            arcade.draw_rect_outline(
                XYWH(right_x + right_w / 2,
                     ry - lesson_row_h / 2 + 2,
                     right_w, lesson_row_h - 4),
                (80, 90, 110, 200), 1)

            # Lesson number (per part) + title
            arcade.draw_text(
                f"{j + 1}.",
                right_x + 10, ry - 22,
                COLOR_TEXT_DIM, font_size=10, bold=True)
            arcade.draw_text(
                lesson.title,
                right_x + 36, ry - 22,
                COLOR_TEXT, font_size=13, bold=True)

            # Position indicator (small icon at right edge if FEN
            # attached). Helps the user see at a glance which lessons
            # have a playable board preview.
            if lesson.fen:
                arcade.draw_text(
                    "♔ board",
                    right_x + right_w - 12, ry - 22,
                    COLOR_ACCENT, font_size=10, anchor_x="right")

            # Key-idea preview line (truncated)
            preview = lesson.key_idea
            if len(preview) > max_chars * 1.4:
                preview = preview[:int(max_chars * 1.4)].rstrip() + "…"
            arcade.draw_text(
                preview,
                right_x + 36, ry - 42,
                COLOR_TEXT_DIM, font_size=9)

            self._imbalance_lesson_rects.append(
                (lesson.slug, right_x, ry - lesson_row_h + 4,
                 right_w, lesson_row_h - 4))

        # Scrollbar + position counter if needed
        if max_scroll > 0:
            shown_first = self._imbalance_scroll + 1
            shown_last = min(len(lessons),
                             self._imbalance_scroll + rows_fit)
            arcade.draw_text(
                f"{shown_first}–{shown_last} of {len(lessons)}",
                right_x + right_w - 4, lesson_list_top + 6,
                COLOR_TEXT_DIM, font_size=9, anchor_x="right")
            arcade.draw_text(
                "Wheel / ↑↓ / PgUp / PgDn / Home / End",
                right_x, lesson_list_top + 6,
                COLOR_TEXT_DIM, font_size=9)
            # Thin scrollbar on the right gutter of the lessons list
            sb_x = right_x + right_w + 4
            sb_w = 5
            sb_top = lesson_list_top
            sb_bot = bot_y
            sb_h = sb_top - sb_bot
            if sb_h > 0:
                arcade.draw_lbwh_rectangle_filled(
                    sb_x, sb_bot, sb_w, sb_h, (50, 56, 70, 200))
                thumb_h = max(20, int(sb_h * rows_fit / len(lessons)))
                thumb_travel = sb_h - thumb_h
                thumb_y = (sb_top - thumb_h
                           - int(thumb_travel * self._imbalance_scroll
                                 / max_scroll))
                arcade.draw_lbwh_rectangle_filled(
                    sb_x, thumb_y, sb_w, thumb_h, COLOR_ACCENT)

    def _handle_imbalances_click(self, x, y):
        """Dispatch a click in the imbalances browser.

        Two click zones: parts in the left pane (changes the active
        part and resets the right-pane scroll) and lessons in the
        right pane (transitions to the imbalance_lesson detail view).
        """
        # Parts first — left pane sits at lower z, but rects don't
        # overlap so order is purely cosmetic.
        for idx, rx, ry, rw, rh in self._imbalance_part_rects:
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                if idx != self._imbalance_part_i:
                    self._imbalance_part_i = idx
                    self._imbalance_scroll = 0  # fresh view of a new part
                return
        for slug, rx, ry, rw, rh in self._imbalance_lesson_rects:
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                self._imbalance_lesson_slug = slug
                self.app_state = "imbalance_lesson"
                return

    def _draw_imbalance_lesson(self):
        """Detail page for a single imbalance lesson.

        Layout: title at the top; key-idea paragraph; numbered plan
        list; and (if the lesson has a FEN attached) a mini-board on
        the right showing the illustrative position, with an
        'Open on main board' button that loads the FEN into the
        engine for hands-on study.
        """
        arcade.draw_lbwh_rectangle_filled(
            0, 0, self.width, self.height, COLOR_MENU_BG)
        cx = self.width // 2

        lesson = find_imbalance_lesson(self._imbalance_lesson_slug)
        if lesson is None:
            # Shouldn't happen, but bail gracefully if it does.
            arcade.draw_text(
                "(lesson not found — press ESC to return)",
                cx, self.height // 2, COLOR_TEXT,
                font_size=14, anchor_x="center")
            self._imbalance_open_btn_rect = ()
            return

        # Header: which part this lesson belongs to, then the title
        arcade.draw_text(
            f"PART · {lesson.part.upper()}",
            cx, self.height - 50, COLOR_ACCENT,
            font_size=11, anchor_x="center", bold=True)
        arcade.draw_text(
            lesson.title,
            cx, self.height - 82, COLOR_MENU_TITLE,
            font_size=24, anchor_x="center", bold=True)
        arcade.draw_text(
            "ESC or Backspace returns to the lesson list.",
            cx, self.height - 108, COLOR_TEXT_DIM,
            font_size=9, anchor_x="center")

        # Layout: left text column for prose, right column for the
        # mini-board (when present). When no FEN is attached, the
        # text column expands to use the whole width.
        margin = 40
        text_top = self.height - 140
        text_x = margin
        if lesson.fen:
            board_size = min(360, self.height // 2 + 40)
            board_x = self.width - margin - board_size
            board_y = text_top - board_size - 20
            text_w = board_x - margin - 30
        else:
            board_size = 0
            board_x = board_y = 0
            text_w = self.width - 2 * margin

        # Key idea — wrapped paragraph
        arcade.draw_text("KEY IDEA",
                         text_x, text_top, COLOR_ACCENT,
                         font_size=11, bold=True)
        max_chars = max(30, int(text_w / 7.4))  # 13px font ≈ 7.4 px/char
        y = text_top - 22
        for line in self._wrap_text(lesson.key_idea, max_chars):
            arcade.draw_text(line, text_x, y, COLOR_TEXT,
                             font_size=13)
            y -= 18

        # Plan list — numbered steps
        y -= 14
        arcade.draw_text("PLAN",
                         text_x, y, COLOR_ACCENT,
                         font_size=11, bold=True)
        y -= 22
        for n, step in enumerate(lesson.plan, start=1):
            # Number bullet
            arcade.draw_text(
                f"{n}.",
                text_x, y, COLOR_ACCENT,
                font_size=12, bold=True)
            for k, line in enumerate(self._wrap_text(step, max_chars - 5)):
                arcade.draw_text(line, text_x + 24, y, COLOR_TEXT,
                                 font_size=12)
                y -= 18
            y -= 4  # extra gap between plan items

        # Right column: mini-board if we have a FEN
        self._imbalance_open_btn_rect = ()
        if lesson.fen:
            try:
                board = chess.Board(lesson.fen)
            except ValueError:
                board = None
            if board is not None:
                # Label
                arcade.draw_text(
                    "ILLUSTRATIVE POSITION",
                    board_x, board_y + board_size + 28,
                    COLOR_ACCENT, font_size=11, bold=True)
                # Whose turn
                turn_label = ("White to move" if board.turn == chess.WHITE
                              else "Black to move")
                arcade.draw_text(
                    turn_label,
                    board_x, board_y + board_size + 8,
                    COLOR_TEXT, font_size=11)

                # The board itself
                self._draw_mini_board(board, board_x, board_y, board_size)

                # FEN note (caption under the board)
                note_y = board_y - 12
                note_chars = max(20, int(board_size / 6.0))
                for line in self._wrap_text(lesson.fen_note,
                                            note_chars)[:4]:
                    arcade.draw_text(line, board_x, note_y,
                                     COLOR_TEXT_DIM, font_size=10)
                    note_y -= 14

                # "Open on main board" button — loads the FEN into
                # the engine and switches to game state. Same pattern
                # as the FEN text-input box: lets the user study the
                # position hands-on, make moves, get hints, etc.
                btn_w, btn_h = 220, 36
                btn_x = board_x + (board_size - btn_w) // 2
                btn_y = note_y - btn_h - 10
                # Don't draw the button off the bottom edge
                if btn_y > 6:
                    mx, my = self._mouse_xy()
                    hover = (btn_x <= mx <= btn_x + btn_w
                             and btn_y <= my <= btn_y + btn_h)
                    bg = COLOR_MENU_BTN_HOVER if hover else COLOR_MENU_BTN_BG
                    arcade.draw_lbwh_rectangle_filled(
                        btn_x, btn_y, btn_w, btn_h, bg)
                    arcade.draw_rect_outline(
                        XYWH(btn_x + btn_w / 2, btn_y + btn_h / 2,
                             btn_w, btn_h),
                        COLOR_ACCENT, 1)
                    arcade.draw_text(
                        "Open on main board",
                        btn_x + btn_w // 2, btn_y + 10,
                        COLOR_TEXT, font_size=12,
                        anchor_x="center", bold=True)
                    self._imbalance_open_btn_rect = (
                        btn_x, btn_y, btn_w, btn_h)

    def _handle_imbalance_lesson_click(self, x, y):
        """Handle clicks on a lesson detail page.

        Only one clickable region: the optional 'Open on main board'
        button at the bottom of the right column. Clicking it loads
        the lesson's FEN into the engine (reusing _load_from_fen)
        and switches to the game state."""
        if not self._imbalance_open_btn_rect:
            return
        bx, by, bw, bh = self._imbalance_open_btn_rect
        if bx <= x <= bx + bw and by <= y <= by + bh:
            lesson = find_imbalance_lesson(self._imbalance_lesson_slug)
            if lesson is None or not lesson.fen:
                return
            # Reuse the existing FEN loader so behavior matches the
            # paste-FEN flow (eval tracker reset, animator cleared,
            # info panel populated, etc.). The loader transitions
            # nothing on its own, so we set the game state ourselves.
            self._load_from_fen(lesson.fen)
            self.info = [
                f"Loaded position from lesson:",
                f"  {lesson.title}",
                "Play moves or press I for a hint.",
            ]
            self.app_state = "game"

    @staticmethod
    def _wrap_text(text: str, max_chars: int) -> list[str]:
        """Greedy word-wrap helper for in-game prose blocks.

        Arcade's `draw_text` doesn't word-wrap — we'd have to use
        `multiline=True, width=...`, which produces awkward
        breaking for variable-width fonts. Doing it ourselves at
        the word level gives consistent results across screens.
        """
        words = text.split()
        lines = []
        cur = ""
        for w in words:
            if not cur:
                cur = w
            elif len(cur) + 1 + len(w) <= max_chars:
                cur = f"{cur} {w}"
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    # ── Openings Table ───────────────────────────────────────────────
    def _black_columns_for_white(self, white_key: str) -> list[str]:
        """Which Black-defense column keys to render for a given White row."""
        return {
            "1.e4":  OPENINGS_TABLE_BLACK_VS_E4,
            "1.d4":  OPENINGS_TABLE_BLACK_VS_D4,
            "1.c4":  OPENINGS_TABLE_BLACK_VS_C4,
            "1.Nf3": OPENINGS_TABLE_BLACK_VS_NF3,
            "1.f4":  OPENINGS_TABLE_BLACK_VS_F4,
        }.get(white_key, [])

    def _draw_openings_table(self):
        """Matrix view: White openings (rows on the left) x typical Black
        responses (one column per Black defense). Each cell shows the
        named line and ECO range. Click a White row on the left to
        change which defenses appear as columns."""
        arcade.draw_lbwh_rectangle_filled(0, 0, self.width, self.height, COLOR_MENU_BG)
        cx = self.width // 2
        arcade.draw_text("OPENINGS TABLE",
                         cx, self.height - 50, COLOR_MENU_TITLE,
                         font_size=28, anchor_x="center", bold=True)
        arcade.draw_text("Left: click a White first move. Right: "
                         "resulting lines vs typical Black defenses.",
                         cx, self.height - 82, COLOR_MENU_SUBTITLE,
                         font_size=11, anchor_x="center")
        arcade.draw_text("ESC = back to menu",
                         cx, self.height - 100, COLOR_TEXT_DIM,
                         font_size=9, anchor_x="center")

        # Left panel: White first moves as rows
        left_x = 40
        top_y = self.height - 140
        row_h = 40
        row_w = 180
        self._openings_table_row_rects = []
        for i, w in enumerate(OPENINGS_TABLE_WHITE):
            ry = top_y - i * (row_h + 6)
            sel = (i == self.openings_table_white_i)
            bg = COLOR_MENU_BTN_HOVER if sel else COLOR_MENU_BTN_BG
            arcade.draw_lbwh_rectangle_filled(left_x, ry - row_h + 6,
                                              row_w, row_h - 4, bg)
            arcade.draw_rect_outline(
                XYWH(left_x + row_w / 2, ry - row_h / 2 + 4,
                     row_w, row_h - 4),
                COLOR_ACCENT, 2 if sel else 1)
            arcade.draw_text(w, left_x + 16, ry - 24,
                             COLOR_TEXT, font_size=16, bold=True)
            self._openings_table_row_rects.append(
                (i, left_x, ry - row_h + 6, row_w, row_h - 4))

        # Right panel: cells for the selected White row
        white_key = OPENINGS_TABLE_WHITE[self.openings_table_white_i]
        cols = self._black_columns_for_white(white_key)
        right_x = left_x + row_w + 30
        right_w = self.width - right_x - 30
        arcade.draw_text(f"Selected: {white_key}   →   Black defenses:",
                         right_x, self.height - 140, COLOR_MENU_TITLE,
                         font_size=14, bold=True)

        cell_y0 = self.height - 180
        cell_h = 58
        cell_gap = 6
        for i, blk in enumerate(cols):
            cy = cell_y0 - i * (cell_h + cell_gap)
            if cy - cell_h < 30:
                break
            # Cell background alternates
            bg = (48, 56, 72, 230) if i % 2 == 0 else (40, 48, 62, 230)
            arcade.draw_lbwh_rectangle_filled(right_x, cy - cell_h,
                                              right_w, cell_h, bg)
            arcade.draw_rect_outline(
                XYWH(right_x + right_w / 2, cy - cell_h / 2,
                     right_w, cell_h),
                COLOR_ACCENT, 1)

            # Black column label
            arcade.draw_text(blk, right_x + 14, cy - 22,
                             COLOR_MENU_TITLE, font_size=13, bold=True)

            # Named line + ECO
            cell = OPENINGS_TABLE_CELLS.get((white_key, blk))
            if cell:
                name, eco = cell
                arcade.draw_text(name, right_x + 150, cy - 22,
                                 COLOR_TEXT, font_size=12)
                arcade.draw_text(f"[{eco}]", right_x + right_w - 110,
                                 cy - 22, COLOR_TEXT_DIM, font_size=11)
            else:
                arcade.draw_text("(rare / transposes)",
                                 right_x + 150, cy - 22,
                                 COLOR_TEXT_DIM, font_size=11, italic=True)

    def _handle_openings_table_click(self, x, y):
        for idx, rx, ry, rw, rh in self._openings_table_row_rects:
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                self.openings_table_white_i = idx
                return

    def _draw_openings_list(self):
        """Per-side openings list view, driven by openings_catalog.

        Shows one card per catalog entry for the current side
        (self.openings_view_side == 'white' or 'black'). Each card
        displays the opening name, ECO, defining move sequence, and a
        one-line summary. Clicking jumps to the opening-detail view
        (NOT the matrix), where the user picks a famous game to replay."""
        arcade.draw_lbwh_rectangle_filled(0, 0, self.width, self.height, COLOR_MENU_BG)
        cx = self.width // 2

        side = self.openings_view_side
        title = "WHITE OPENINGS" if side == "white" else "BLACK DEFENSES"
        subtitle = (
            "Openings named for White's defining systems."
            if side == "white" else
            "Defenses named for Black's replies to White's opening moves."
        )
        arcade.draw_text(title, cx, self.height - 60, COLOR_MENU_TITLE,
                         font_size=28, anchor_x="center", bold=True)
        arcade.draw_text(subtitle, cx, self.height - 92, COLOR_MENU_SUBTITLE,
                         font_size=11, anchor_x="center")
        arcade.draw_text(
            "ESC to return to menu.  Click an opening to see famous games and replay them.",
            cx, self.height - 110, COLOR_TEXT_DIM,
            font_size=9, anchor_x="center")

        rows = entries_for_side(side)

        # Layout: 2-column card grid. Larger cards than before so we
        # can fit name + ECO + move sequence + summary without crowding.
        self._openings_list_rects = []
        col_w = 440
        row_h = 78
        gap_x = 20
        gap_y = 10
        cols = 2
        total_cols_w = cols * col_w + (cols - 1) * gap_x
        left0 = cx - total_cols_w // 2
        top_y = self.height - 140

        mx, my = self._mouse_xy()
        for i, entry in enumerate(rows):
            col = i % cols
            row = i // cols
            rx = left0 + col * (col_w + gap_x)
            ry = top_y - row * (row_h + gap_y)
            if ry - row_h < 40:
                break
            hover = (rx <= mx <= rx + col_w and ry - row_h <= my <= ry)
            bg = COLOR_MENU_BTN_HOVER if hover else (48, 56, 72, 230)
            arcade.draw_lbwh_rectangle_filled(rx, ry - row_h, col_w, row_h, bg)
            arcade.draw_rect_outline(
                XYWH(rx + col_w / 2, ry - row_h / 2, col_w, row_h),
                COLOR_ACCENT, 1)

            # Row 1: name (bold) + ECO badge on the right
            arcade.draw_text(entry.name, rx + 14, ry - 22,
                             COLOR_MENU_TITLE, font_size=14, bold=True)
            arcade.draw_text(f"ECO {entry.eco}", rx + col_w - 120, ry - 22,
                             COLOR_TEXT_DIM, font_size=10)
            # Row 2: defining SAN move sequence
            arcade.draw_text(entry.moves_san, rx + 14, ry - 42,
                             COLOR_TEXT, font_size=11)
            # Row 3: one-line summary, truncated
            summary = entry.summary
            max_chars = max(30, (col_w - 28) // 6)
            if len(summary) > max_chars:
                summary = summary[:max_chars - 1] + "…"
            arcade.draw_text(summary, rx + 14, ry - 62,
                             COLOR_TEXT_DIM, font_size=9, italic=True)

            # Store (slug, ...) — side is implicit from current view
            self._openings_list_rects.append(
                (entry.slug, rx, ry - row_h, col_w, row_h))

    def _handle_openings_list_click(self, x, y):
        """Click on an opening → jump to the opening-detail view for
        that entry (does NOT jump to the matrix). The user then picks
        a famous game from the detail view to actually replay."""
        for slug, rx, ry, rw, rh in self._openings_list_rects:
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                self.opening_detail_slug = slug
                self.app_state = "opening_detail"
                return

    def _draw_opening_detail(self):
        """Detail view for one selected opening. Shows full name, ECO,
        move sequence, multi-line summary, a list of canonical variations
        (each clickable to replay on the main board), a "View all
        variations" satellite button, and a list of famous games.

        v8 added the variations panel and the satellite button. The
        famous-games panel is unchanged in semantics — just rendered
        below the variations panel rather than taking the whole page.
        """
        arcade.draw_lbwh_rectangle_filled(0, 0, self.width, self.height, COLOR_MENU_BG)
        cx = self.width // 2

        entry = find_entry(self.openings_view_side, self.opening_detail_slug)
        if entry is None:
            arcade.draw_text("(opening not found — ESC to return)",
                             cx, self.height // 2, COLOR_TEXT,
                             font_size=14, anchor_x="center")
            self._opening_detail_game_rects = []
            self._opening_detail_variation_rects = []
            self._opening_detail_satellite_btn_rect = ()
            return

        # Header
        arcade.draw_text(entry.name, cx, self.height - 50, COLOR_MENU_TITLE,
                         font_size=28, anchor_x="center", bold=True)
        side_label = ("White opening" if entry.side == "white"
                      else "Black defense")
        arcade.draw_text(f"{side_label}  •  ECO {entry.eco}",
                         cx, self.height - 78, COLOR_MENU_SUBTITLE,
                         font_size=12, anchor_x="center")
        arcade.draw_text(
            "ESC / Backspace = back to openings list  •  "
            "click a variation to replay it",
            cx, self.height - 96, COLOR_TEXT_DIM,
            font_size=9, anchor_x="center")

        # Idea panel — compact (smaller than v7 since variations now
        # share the page)
        panel_w = min(860, self.width - 80)
        panel_x = cx - panel_w // 2
        idea_top = self.height - 120
        idea_h = 70
        arcade.draw_lbwh_rectangle_filled(panel_x, idea_top - idea_h,
                                          panel_w, idea_h,
                                          (48, 56, 72, 230))
        arcade.draw_rect_outline(
            XYWH(panel_x + panel_w / 2, idea_top - idea_h / 2,
                 panel_w, idea_h),
            COLOR_ACCENT, 1)
        arcade.draw_text("Moves:", panel_x + 16, idea_top - 22,
                         COLOR_ACCENT, font_size=11, bold=True)
        arcade.draw_text(entry.moves_san, panel_x + 90, idea_top - 22,
                         COLOR_TEXT, font_size=12)
        arcade.draw_text("Idea:", panel_x + 16, idea_top - 44,
                         COLOR_ACCENT, font_size=11, bold=True)
        wrap_chars = max(50, (panel_w - 120) // 7)
        for j, line in enumerate(_wrap(entry.summary, wrap_chars)[:2]):
            arcade.draw_text(line, panel_x + 90, idea_top - 44 - j * 14,
                             COLOR_TEXT, font_size=10)

        # ── Variations panel ─────────────────────────────────────────
        var_top = idea_top - idea_h - 20
        # Title row, with the "View all" button on the right
        arcade.draw_text("Variations:",
                         panel_x + 8, var_top,
                         COLOR_MENU_TITLE, font_size=14, bold=True)

        # "View all variations" button — right-aligned with the title
        btn_w, btn_h = 200, 28
        btn_x = panel_x + panel_w - btn_w
        btn_y = var_top - 6
        mx, my = self._mouse_xy()
        valid_variations = [v for v in entry.variations if v.moves_valid]
        btn_active = len(valid_variations) >= 2
        btn_hover = (btn_active
                     and btn_x <= mx <= btn_x + btn_w
                     and btn_y <= my <= btn_y + btn_h)
        btn_bg = (COLOR_MENU_BTN_HOVER if btn_hover
                  else (60, 80, 110, 230) if btn_active
                  else (40, 44, 52, 200))
        arcade.draw_lbwh_rectangle_filled(btn_x, btn_y, btn_w, btn_h, btn_bg)
        arcade.draw_rect_outline(
            XYWH(btn_x + btn_w / 2, btn_y + btn_h / 2, btn_w, btn_h),
            COLOR_ACCENT if btn_active else COLOR_TEXT_DIM, 1)
        btn_label = ("View all variations →" if btn_active
                     else "(no variations to compare)")
        btn_color = (COLOR_TEXT if btn_active else COLOR_TEXT_DIM)
        arcade.draw_text(btn_label, btn_x + btn_w / 2, btn_y + 9,
                         btn_color, font_size=10, anchor_x="center")
        self._opening_detail_satellite_btn_rect = (
            (btn_x, btn_y, btn_w, btn_h) if btn_active else ())

        # Variation cards — two-up if two variations, stacked otherwise
        var_card_top = var_top - 24
        var_card_h = 90
        var_card_gap = 10
        self._opening_detail_variation_rects = []
        if len(valid_variations) == 0:
            arcade.draw_text("(no curated variations for this opening)",
                             panel_x + 8, var_card_top - 14,
                             COLOR_TEXT_DIM, font_size=10, italic=True)
        else:
            n = len(valid_variations)
            cols = 2 if n >= 2 else 1
            col_w = (panel_w - (cols - 1) * var_card_gap) // cols
            for i, v in enumerate(valid_variations):
                col = i % cols
                row = i // cols
                vx = panel_x + col * (col_w + var_card_gap)
                vy = var_card_top - row * (var_card_h + var_card_gap)
                hover = (vx <= mx <= vx + col_w
                         and vy - var_card_h <= my <= vy)
                bg = (COLOR_MENU_BTN_HOVER if hover
                      else (44, 52, 66, 230))
                arcade.draw_lbwh_rectangle_filled(
                    vx, vy - var_card_h, col_w, var_card_h, bg)
                arcade.draw_rect_outline(
                    XYWH(vx + col_w / 2, vy - var_card_h / 2,
                         col_w, var_card_h),
                    COLOR_ACCENT, 1)
                # Name + ECO
                arcade.draw_text(v.name, vx + 12, vy - 20,
                                 COLOR_MENU_TITLE, font_size=13, bold=True)
                arcade.draw_text(f"ECO {v.eco}",
                                 vx + col_w - 90, vy - 20,
                                 COLOR_TEXT_DIM, font_size=10)
                # Moves SAN — truncate if needed
                moves_text = v.moves_san
                max_chars = max(20, (col_w - 24) // 6)
                if len(moves_text) > max_chars:
                    moves_text = moves_text[:max_chars - 1] + "…"
                arcade.draw_text(moves_text, vx + 12, vy - 40,
                                 COLOR_TEXT, font_size=10)
                # 1-line summary
                summary = v.summary
                summ_max = max(30, (col_w - 24) // 6)
                if len(summary) > summ_max:
                    summary = summary[:summ_max - 1] + "…"
                arcade.draw_text(summary, vx + 12, vy - 56,
                                 COLOR_TEXT_DIM, font_size=9, italic=True)
                # Famous-game line: "<player1> vs <player2>, <year> - <result>"
                fg_line = self._variation_famous_game_line(v)
                if fg_line:
                    fg_max = max(30, (col_w - 24) // 6)
                    fg_text = fg_line if len(fg_line) <= fg_max \
                              else fg_line[:fg_max - 1] + "…"
                    arcade.draw_text(fg_text, vx + 12, vy - 72,
                                     (180, 200, 160, 255),
                                     font_size=9, italic=True)
                # Click cue
                arcade.draw_text("Click to replay →",
                                 vx + col_w - 132, vy - 84,
                                 (140, 220, 140, 255), font_size=9,
                                 bold=True)
                self._opening_detail_variation_rects.append(
                    (v, vx, vy - var_card_h, col_w, var_card_h))

        # ── Famous games panel (compacted from v7) ───────────────────
        # Layout the famous-games panel below the variations panel,
        # using whatever vertical space remains.
        rows_used = (
            (len(valid_variations) + 1) // 2
            if valid_variations else 0)
        games_top = var_card_top - rows_used * (var_card_h + var_card_gap) - 20
        arcade.draw_text("Famous games illustrating this opening:",
                         panel_x + 8, games_top,
                         COLOR_MENU_TITLE, font_size=13, bold=True)

        playable = []
        for fg in entry.famous_games:
            if fg.master_game_id is not None:
                mg = resolve_famous_game(fg, MASTER_GAMES)
                if mg is not None:
                    playable.append((fg, mg, None))
            elif fg.pgn is not None and fg.pgn_valid:
                playable.append((fg, None, fg.pgn))

        self._opening_detail_game_rects = []

        if not playable:
            arcade.draw_text(
                "(no top-level games for this opening — "
                "see the per-variation games above)",
                panel_x + 8, games_top - 18,
                COLOR_TEXT_DIM, font_size=10, italic=True)
            return

        card_y0 = games_top - 20
        card_h = 64
        card_gap = 6
        for i, (fg, mg, pgn_text) in enumerate(playable):
            cy = card_y0 - i * (card_h + card_gap)
            if cy - card_h < 30:
                break
            hover = (panel_x <= mx <= panel_x + panel_w
                     and cy - card_h <= my <= cy)
            bg = COLOR_MENU_BTN_HOVER if hover else (40, 48, 62, 230)
            arcade.draw_lbwh_rectangle_filled(
                panel_x, cy - card_h, panel_w, card_h, bg)
            arcade.draw_rect_outline(
                XYWH(panel_x + panel_w / 2, cy - card_h / 2,
                     panel_w, card_h),
                COLOR_ACCENT, 1)
            arcade.draw_text(fg.title, panel_x + 16, cy - 20,
                             COLOR_MENU_TITLE, font_size=12, bold=True)
            if mg is not None:
                meta = f"{mg.date}   {mg.result}   [{mg.eco}]   " \
                       f"{len(mg.moves_san)} moves"
            else:
                meta = "(inline PGN)"
            arcade.draw_text(meta, panel_x + 16, cy - 38,
                             COLOR_TEXT_DIM, font_size=9)
            if fg.note:
                note_max = max(50, (panel_w - 180) // 6)
                note = fg.note
                if len(note) > note_max:
                    note = note[:note_max - 1] + "…"
                arcade.draw_text(note, panel_x + 16, cy - 54,
                                 COLOR_TEXT, font_size=9, italic=True)
            arcade.draw_text("Click to replay →",
                             panel_x + panel_w - 150, cy - 32,
                             (140, 220, 140, 255), font_size=11, bold=True)
            self._opening_detail_game_rects.append(
                (i, panel_x, cy - card_h, panel_w, card_h,
                 mg, pgn_text, fg))

    def _variation_famous_game_line(self, v):
        """One-line description of v's paired famous game, or '' if none.
        Format: 'Famous: <White> vs <Black>, <Year> (<Result>)'.
        Sources are: famous_master_id (master_games) or
        famous_game_slug (variations.pgn bundle)."""
        if v.famous_master_id:
            for mg in MASTER_GAMES:
                if mg.id == v.famous_master_id:
                    year = mg.date.split(".")[0] if mg.date else ""
                    yp = f", {year}" if year and year != "????" else ""
                    return (f"Famous: {mg.white} vs {mg.black}{yp} "
                            f"({mg.result})")
            return ""
        if v.famous_game_slug:
            pg = get_variation_game(v.famous_game_slug)
            if pg is None:
                return ""
            year = pg.date.split(".")[0] if pg.date else ""
            yp = f", {year}" if year and year != "????" else ""
            tag = " (truncated)" if pg.truncated else ""
            return (f"Famous: {pg.white} vs {pg.black}{yp} "
                    f"({pg.result}){tag}")
        return ""

    def _handle_opening_detail_click(self, x, y):
        """Click handler for the opening-detail page. Three regions:
        the 'View all variations' satellite button, the variation cards,
        and the famous-game cards. Variation clicks load the variation's
        UCI sequence into the main game view (Option A from the v8
        plan); famous-game clicks load the existing master/PGN game."""
        # 1. Satellite button
        if self._opening_detail_satellite_btn_rect:
            bx, by, bw, bh = self._opening_detail_satellite_btn_rect
            if bx <= x <= bx + bw and by <= y <= by + bh:
                self._satellite_ply_index = 0
                self._satellite_zoom_level = 0
                self.app_state = "variations_satellite"
                return
        # 2. Variation cards
        for (v, rx, ry, rw, rh) in self._opening_detail_variation_rects:
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                self._load_variation(v)
                return
        # 3. Famous-game cards (legacy v7 path, unchanged)
        for (i, rx, ry, rw, rh, mg, pgn_text, fg) in self._opening_detail_game_rects:
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                if mg is not None:
                    self._load_master_game(mg)
                elif pgn_text:
                    self._load_from_pgn_text(pgn_text)
                    self.info.insert(0,
                        f"Loaded from Openings catalog: {fg.title}")
                if self.loaded_moves:
                    self.ply_index = 0
                    self._rebuild_from_ply_index()
                # v8: when game launched from detail, ESC returns here
                self._game_return_state = ("opening_detail",)
                self.app_state = "game"
                return

    def _load_variation(self, v):
        """Load a Variation's UCI move sequence into the main game view.

        If the variation has a paired famous game (master or bundle),
        load THAT game so the user gets the full canonical example.
        Otherwise synthesize a short 'opening study' game with just
        the variation's defining moves. Either way, ply_index is reset
        to 0 so the user can step forward from move 1."""
        # Prefer the famous-game pairing when present (richer learning).
        if v.famous_master_id:
            for mg in MASTER_GAMES:
                if mg.id == v.famous_master_id:
                    self._load_master_game(mg)
                    if self.loaded_moves:
                        self.ply_index = 0
                        self._rebuild_from_ply_index()
                    self.info.insert(0,
                        f"Variation: {v.name} — replaying paired game.")
                    self._game_return_state = ("opening_detail",)
                    self.app_state = "game"
                    return
        if v.famous_game_slug:
            pg = get_variation_game(v.famous_game_slug)
            if pg is not None:
                self._load_parsed_variation_game(pg, v)
                if self.loaded_moves:
                    self.ply_index = 0
                    self._rebuild_from_ply_index()
                self._game_return_state = ("opening_detail",)
                self.app_state = "game"
                return
        # No paired game — load just the defining moves as a study.
        self._load_uci_sequence(v.moves_uci, label=f"Variation: {v.name}")
        if self.loaded_moves:
            self.ply_index = 0
            self._rebuild_from_ply_index()
        self._game_return_state = ("opening_detail",)
        self.app_state = "game"

    def _load_parsed_variation_game(self, pg, v):
        """Load a ParsedGame (from variations_pgn) via the same path
        used for master games — synthesize a chess.pgn.Game from its
        SAN move list and apply through _apply_pgn_game."""
        headers = {
            "Event": pg.event or v.name,
            "Site": pg.site or "?",
            "Date": pg.date or "????.??.??",
            "White": pg.white or "?",
            "Black": pg.black or "?",
            "Result": pg.result or "*",
        }
        if pg.eco:
            headers["ECO"] = pg.eco
        game = chess.pgn.Game()
        for k, val in headers.items():
            game.headers[k] = val
        node = game
        temp = chess.Board()
        for san in pg.moves_san:
            try:
                mv = temp.parse_san(san)
            except Exception:
                break
            node = node.add_variation(mv)
            temp.push(mv)
        self._apply_pgn_game(game, source_label=f"{v.name}: {pg.title}")
        self.loaded_white_name = pg.white
        self.loaded_black_name = pg.black
        suffix = " (opening phase only)" if pg.truncated else ""
        self.info.insert(0,
            f"Variation '{v.name}' — {pg.title}{suffix}")

    def _load_uci_sequence(self, uci_list, label="Opening study"):
        """Load a bare UCI move list (no famous-game wrapper) as a
        study game. Used when a Variation has no paired famous game.
        Builds a chess.pgn.Game stub and routes through _apply_pgn_game
        like _load_master_game does."""
        game = chess.pgn.Game()
        game.headers["Event"] = label
        game.headers["Site"] = "?"
        game.headers["Date"] = "????.??.??"
        game.headers["White"] = "?"
        game.headers["Black"] = "?"
        game.headers["Result"] = "*"
        node = game
        board = chess.Board()
        for u in uci_list:
            try:
                mv = chess.Move.from_uci(u)
            except Exception:
                break
            if mv not in board.legal_moves:
                break
            node = node.add_variation(mv)
            board.push(mv)
        self._apply_pgn_game(game, source_label=label)
        self.loaded_white_name = "—"
        self.loaded_black_name = "—"
        self.info.insert(0,
            f"{label} — step forward with → or scroll wheel.")

    def _navigate_back_one_level(self):
        """Universal 'back one level' transition. Called from ESC and
        Backspace handlers. Designed so that one press = one level up
        in the menu hierarchy:

            game (loaded from variation) → opening_detail
            variations_satellite        → opening_detail
            opening_detail              → openings_list
            openings_list               → menu
            credits/masters/openings_table → menu
            imbalance_lesson            → imbalances
            imbalances                  → menu

        The game-state branch is handled separately (in on_key_press
        directly) because it needs to consult _game_return_state. This
        helper only fires for non-game states."""
        if self.app_state == "variations_satellite":
            self.app_state = "opening_detail"
            return
        if self.app_state == "opening_detail":
            self.app_state = "openings_list"
            return
        if self.app_state == "imbalance_lesson":
            self.app_state = "imbalances"
            return
        if self.app_state in ("openings_list", "openings_table",
                              "masters", "credits", "settings",
                              "imbalances"):
            self.app_state = "menu"
            return
        # Fallback (shouldn't happen): go to menu.
        self.app_state = "menu"

    # ─── v8: satellite view ──────────────────────────────────────────
    def _draw_variations_satellite(self):
        """Satellite ('zoom-out') view of all variations for the
        current opening. Draws one mini-board per variation, all
        synchronized to a global ply index. The user steps every
        board forward with the right arrow, back with the left arrow,
        and zooms with the scroll wheel.

        Layout: a grid with column count chosen by zoom level. At
        zoom 0 (widest), the grid is at most 4 columns; each zoom
        step reduces column count, growing the boards. Single-board
        case (only one valid variation) shouldn't reach here because
        the satellite button is disabled, but it's handled defensively
        anyway."""
        arcade.draw_lbwh_rectangle_filled(
            0, 0, self.width, self.height, COLOR_MENU_BG)
        cx = self.width // 2

        entry = find_entry(self.openings_view_side, self.opening_detail_slug)
        if entry is None:
            arcade.draw_text("(opening not found — Backspace to return)",
                             cx, self.height // 2, COLOR_TEXT,
                             font_size=14, anchor_x="center")
            self._satellite_board_rects = []
            return
        valid_variations = [v for v in entry.variations if v.moves_valid]

        # Header
        arcade.draw_text(f"All variations: {entry.name}",
                         cx, self.height - 36, COLOR_MENU_TITLE,
                         font_size=22, anchor_x="center", bold=True)
        # Status / instruction line
        max_plies = max((len(v.moves_uci) for v in valid_variations),
                        default=0)
        ply_clamped = min(self._satellite_ply_index, max_plies)
        instr = (
            f"Ply {ply_clamped} / {max_plies}   •   "
            "→ next move   ←  previous   "
            "scroll wheel = zoom   "
            "click a board = open variation   "
            "Backspace = back"
        )
        arcade.draw_text(instr, cx, self.height - 60, COLOR_TEXT_DIM,
                         font_size=10, anchor_x="center")

        if not valid_variations:
            arcade.draw_text("(no curated variations to display)",
                             cx, self.height // 2, COLOR_TEXT_DIM,
                             font_size=12, anchor_x="center")
            self._satellite_board_rects = []
            return

        # Choose column count by zoom level. Zoom 0 = widest.
        n = len(valid_variations)
        # Cap candidate column counts to what we have variations for.
        if self._satellite_zoom_level == 0:
            cols = min(n, 4)
        elif self._satellite_zoom_level == 1:
            cols = min(n, 3)
        elif self._satellite_zoom_level == 2:
            cols = min(n, 2)
        else:
            cols = 1
        rows = (n + cols - 1) // cols

        # Reserve top space for the header, bottom space for footer.
        # Lay out boards filling the rest, with margins.
        top_margin = 80
        bottom_margin = 40
        side_margin = 40
        avail_w = self.width - 2 * side_margin
        avail_h = self.height - top_margin - bottom_margin
        gap = 16
        # Reserve room for a small caption strip below each board
        cap_h = 40
        # Choose square side that fits both width and height
        sq_w = (avail_w - (cols - 1) * gap) // cols
        sq_h = (avail_h - rows * cap_h - (rows - 1) * gap) // rows
        size = max(80, min(sq_w, sq_h))
        # Recompute total grid dimensions for centering
        grid_w = cols * size + (cols - 1) * gap
        grid_h = rows * (size + cap_h) + (rows - 1) * gap
        start_x = (self.width - grid_w) // 2
        start_y = self.height - top_margin - 10  # top edge of first row

        self._satellite_board_rects = []
        mx, my = self._mouse_xy()
        for i, v in enumerate(valid_variations):
            col = i % cols
            row = i // cols
            bx = start_x + col * (size + gap)
            # board top edge:
            top_edge = start_y - row * (size + cap_h + gap)
            # convert to bottom-left for arcade
            by = top_edge - size

            # How many plies this board has played:
            played = min(self._satellite_ply_index, len(v.moves_uci))
            board = chess.Board()
            for u in v.moves_uci[:played]:
                try:
                    board.push(chess.Move.from_uci(u))
                except Exception:
                    break
            # Hover highlight — thicker outline when mouse over the
            # board area (not the caption).
            hover = (bx <= mx <= bx + size and by <= my <= by + size)
            self._draw_mini_board(board, bx, by, size,
                                  highlight=hover)

            # Caption: variation name + current ply / total
            cap_y = by - 6
            arcade.draw_text(v.name, bx + size / 2, cap_y - 12,
                             COLOR_MENU_TITLE, font_size=11,
                             anchor_x="center", bold=True)
            ply_txt = f"{played} / {len(v.moves_uci)} plies"
            arcade.draw_text(ply_txt, bx + size / 2, cap_y - 28,
                             COLOR_TEXT_DIM, font_size=9,
                             anchor_x="center")

            self._satellite_board_rects.append(
                (v, bx, by, size, size))

    def _handle_variations_satellite_click(self, x, y):
        """Click a mini-board → load that variation into the main
        game view (same path as the variation card on the detail
        page). Outside any board: noop."""
        for (v, rx, ry, rw, rh) in self._satellite_board_rects:
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                self._load_variation(v)
                return

    def _draw_mini_board(self, board, x, y, size, highlight=False):
        """Draw a static chess.Board at (x, y) with the given pixel
        side length. Used by the satellite view, but extracted so
        that any future feature wanting to draw a non-engine board
        position can call it.

        Renders: light/dark squares, the last move highlight (when
        the board has a move stack), pieces in Unicode glyphs.
        Does NOT render legal moves, threats, eval bar, drag ghost,
        animations — those belong to the main game view.
        Coordinate convention matches _draw_game: (x, y) is the
        bottom-left of the board area; squares are size/8 each."""
        sq = size / 8
        # Optional outer glow on hover, drawn before squares
        if highlight:
            arcade.draw_lbwh_rectangle_filled(
                x - 4, y - 4, size + 8, size + 8, (200, 220, 240, 60))
        # Border
        arcade.draw_lbwh_rectangle_filled(
            x - 2, y - 2, size + 4, size + 4, COLOR_BOARD_BORDER)
        # Squares — v9: live read from board_materials (matches the
        # main board so a Settings switch updates everywhere at once).
        _mat = board_materials.get_material(self.board_material_key)
        _light = _mat.light_sq
        _dark = _mat.dark_sq
        for r in range(8):
            for f in range(8):
                c = _light if (f + r) % 2 == 1 else _dark
                arcade.draw_lbwh_rectangle_filled(
                    x + f * sq, y + r * sq, sq, sq, c)
        # Last-move highlight (if this board has a move stack)
        if board.move_stack:
            lm = board.peek()
            for s in (lm.from_square, lm.to_square):
                f, r = chess.square_file(s), chess.square_rank(s)
                arcade.draw_lbwh_rectangle_filled(
                    x + f * sq, y + r * sq, sq, sq, COLOR_LAST_MOVE)
        # Pieces (Unicode)
        fs = max(8, int(sq * 0.66))
        for s in chess.SQUARES:
            p = board.piece_at(s)
            if not p:
                continue
            f, r = chess.square_file(s), chess.square_rank(s)
            cx_ = x + f * sq + sq / 2
            cy_ = y + r * sq + sq / 2 - sq * 0.32
            uni = UNICODE_PIECES.get(p.symbol(), "?")
            # Small shadow
            arcade.draw_text(uni, cx_ + 1, cy_ - 1, (0, 0, 0, 120),
                             font_size=fs, anchor_x="center")
            pc = ((255, 255, 255, 255) if p.color == chess.WHITE
                  else (40, 40, 40, 255))
            arcade.draw_text(uni, cx_, cy_, pc, font_size=fs,
                             anchor_x="center")

    def _load_master_game(self, mg):
        """Load a MasterGame into the engine + tracker and synthesize a PGN headers."""
        # Build a python-chess Game object so we reuse _apply_pgn_game
        headers = {
            "Event": mg.event, "Site": mg.site, "Date": mg.date,
            "White": mg.white, "Black": mg.black, "Result": mg.result,
        }
        if mg.eco:
            headers["ECO"] = mg.eco
        if mg.opening:
            headers["Opening"] = mg.opening

        # Construct the Game programmatically by pushing SAN into a board
        game = chess.pgn.Game()
        for k, v in headers.items():
            game.headers[k] = v
        node = game
        temp = chess.Board()
        for san in mg.moves_san:
            try:
                move = temp.parse_san(san)
            except Exception:
                break
            node = node.add_variation(move)
            temp.push(move)

        self._apply_pgn_game(game, source_label=mg.title)
        # Remember the players for the avatar cards
        self.loaded_white_name = mg.white
        self.loaded_black_name = mg.black
        extra = " (partial)" if mg.truncated else ""
        self.info.insert(0, f"Master game loaded{extra}.")
        if mg.notes:
            self.info.append(f"Note: {mg.notes}")

    
    def _save_pgn(self):
        """Save current game to a PGN file. Uses a tkinter 'Save As'
        dialog so the user can choose the filename and directory. If tk
        is unavailable, falls back to the previous timestamped-file
        behavior in ./pgn_losses/."""
        os.makedirs(PGN_DIR, exist_ok=True)

        game = chess.pgn.Game.from_board(self.engine.board)
        game.headers["Event"] = "Chess Game Session"
        game.headers["Date"] = datetime.date.today().isoformat()
        game.headers["White"] = "Human" if self.player_color == chess.WHITE else self.profiled_ai.profile.name
        game.headers["Black"] = "Human" if self.player_color == chess.BLACK else self.profiled_ai.profile.name
        result = self.engine.game_result() or "*"
        game.headers["Result"] = result

        pgn_text = str(game) + "\n\n"

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"game_{ts}.pgn"

        # Try tkinter save dialog
        filepath = None
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            filepath = filedialog.asksaveasfilename(
                parent=root,
                title="Save PGN as…",
                initialdir=PGN_DIR,
                initialfile=default_name,
                defaultextension=".pgn",
                filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")],
            )
            root.destroy()
        except Exception as e:
            print(f"[PGN] Save dialog unavailable ({e}); using default path.")
            filepath = None

        if filepath is None or filepath == "":
            # Dialog cancelled or unavailable — fall back to old behavior
            # only if dialog was truly unavailable. If the user simply
            # cancelled, respect that and return.
            if filepath == "":
                self.info = ["Save cancelled."]
                return
            filepath = os.path.join(PGN_DIR, default_name)

        try:
            with open(filepath, "w") as f:
                f.write(pgn_text)
            # Also append to the rolling all_games.pgn in PGN_DIR so
            # long-running users still accumulate a single history file.
            all_path = os.path.join(PGN_DIR, "all_games.pgn")
            with open(all_path, "a") as f:
                f.write(pgn_text)
            self.info = [
                "Game saved.",
                f"File: {os.path.basename(filepath)}",
                f"Dir: {os.path.dirname(filepath) or '.'}",
            ]
            print(f"[PGN] Saved to {filepath}")
        except OSError as e:
            self.info = ["Save failed:", str(e)[:60]]
            print(f"[PGN] Save error: {e}")

    def _load_pgn(self):
        """Load a PGN file. Uses a tkinter 'Open' dialog so the user can
        pick any file on disk. Falls back to loading the most recent
        file in ./pgn_losses/ if tk is unavailable."""
        # Try tkinter open dialog
        filepath = None
        used_dialog = False
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            initial = PGN_DIR if os.path.isdir(PGN_DIR) else os.getcwd()
            filepath = filedialog.askopenfilename(
                parent=root,
                title="Open PGN file",
                initialdir=initial,
                filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")],
            )
            root.destroy()
            used_dialog = True
        except Exception as e:
            print(f"[PGN] Load dialog unavailable ({e}); using latest in {PGN_DIR}.")
            filepath = None

        # Dialog-unavailable fallback: load the latest in PGN_DIR
        if filepath is None:
            if not os.path.isdir(PGN_DIR):
                self.info = ["No saved games found.", f"Dir: {PGN_DIR}"]
                return
            files = sorted(glob.glob(os.path.join(PGN_DIR, "*.pgn")))
            if not files:
                self.info = ["No saved games found.",
                             f"Dir: {PGN_DIR}",
                             "Use Save PGN first, or paste PGN text."]
                return
            filepath = files[-1]
        elif filepath == "":
            # User cancelled the dialog
            self.info = ["Load cancelled."]
            return

        try:
            with open(filepath) as f:
                game = chess.pgn.read_game(f)
            if game is None:
                self.info = ["Could not parse PGN file."]
                return
            self._apply_pgn_game(game, source_label=os.path.basename(filepath))
            print(f"[PGN] Loaded {filepath}")
        except Exception as e:
            self.info = [f"Error loading PGN: {str(e)[:60]}"]
            print(f"[PGN] Load error: {e}")

    # ── Avatar rendering ──────────────────────────────────────────────
    def _get_avatar_sprite(self, name: str, role: str, size: int,
                           slot_key: str | None = None) -> arcade.Sprite:
        """Get or build a Sprite for a named avatar, registered into the
        persistent sprite list. Arcade 3.x can only draw textures via a
        SpriteList, so we keep one list and reuse sprites across frames.

        v10 hot-fix (mirrors the same fix applied to piece sprites): a
        single Sprite cannot occupy two positions in the same frame, so
        every *visible slot* needs its OWN Sprite instance — even when
        several slots share the same texture. The master-games browser
        is a perfect trigger for this bug: when the same player
        appears in two rows (e.g. Magnus Carlsen as White in two
        consecutive games), sharing one sprite means only ONE of those
        positions survives, leaving the other row's avatar invisible
        (the "White"/"Black" placeholder text shows through).

        The fix: cache by `slot_key` (e.g. "masters_row7_white") so
        every cell gets its own Sprite. Texture lookup is still cached
        upstream in get_avatar — only the Sprite wrappers multiply,
        which is cheap. When `slot_key` is None we fall back to the
        old name-keyed behaviour for callers that draw a unique avatar
        once per frame (e.g. the two in-game cards)."""
        if slot_key is None:
            # Legacy path: one sprite per (name, role, size). Safe when
            # the caller only ever positions this avatar in one place
            # per frame — e.g. the in-game top-band cards.
            cache_key = f"name:{name}|{role}|{size}"
        else:
            # Slot path: one sprite per slot, even if multiple slots
            # share the same texture. Required by the master-games list.
            cache_key = f"slot:{slot_key}|{name}|{role}|{size}"
        sp = self._avatar_sprites.get(cache_key)
        if sp is None:
            tex = get_avatar(name, role, size)
            sp = arcade.Sprite(tex)
            self._avatar_sprites[cache_key] = sp
            self._avatar_sprite_list.append(sp)
        elif slot_key is not None:
            # Slot-keyed entries can be re-targeted at a different
            # player on later frames (e.g. when the list is scrolled
            # and row 7 now shows a different game). Swap the texture
            # in place rather than allocating a new Sprite — keeps the
            # SpriteList stable and avoids unbounded growth.
            tex = get_avatar(name, role, size)
            if sp.texture is not tex:
                sp.texture = tex
        return sp

    def _park_all_avatar_sprites(self):
        """Move every cached avatar sprite far off-screen so stale
        sprites from a previous view (e.g. master-games browser) don't
        render over the current view. Call this once per frame BEFORE
        positioning the sprites you actually want to draw — the ones
        that get a new position in this frame move back on-screen, and
        everything else stays parked."""
        # Any negative coordinate well outside the window works; using
        # -10000 guarantees we're off any reasonable viewport.
        for sp in self._avatar_sprites.values():
            sp.position = (-10000, -10000)

    # ── v9: Piece sprite helpers ─────────────────────────────────────
    def _get_piece_sprite(self, slot_key: str, symbol: str, theme: str,
                          side_hint: str | None,
                          size: int) -> arcade.Sprite:
        """Get or build a Sprite for one piece occurrence.

        v10: `slot_key` identifies a unique on-screen slot (typically a
        chess square index, but "drag" for the drag ghost and any other
        unique label that the caller wants). Two different slots get
        two different Sprite objects, even when they happen to share a
        texture — so eight pawns get eight sprites, all backed by the
        same cached arcade.Texture.

        The slot's stored sprite is updated to the right texture each
        time this is called: this matters because (a) the user can
        change theme mid-game and (b) the piece on a given square
        changes after a capture / promotion.
        """
        # Kings/queens have no flank distinction — collapse to "k".
        sh = side_hint if (side_hint in ("k", "q") and
                           symbol.upper() not in ("K", "Q")) else "k"
        tex = piece_textures.get_piece_texture(
            symbol, theme=theme, side_hint=sh, size=size)
        sp = self._piece_sprites.get(slot_key)
        if sp is None:
            sp = arcade.Sprite(tex)
            self._piece_sprites[slot_key] = sp
            self._piece_sprite_list.append(sp)
        else:
            # Update the texture on the existing sprite in case the
            # piece on this square has changed since last frame
            # (capture, promotion, theme switch, etc.).
            if sp.texture is not tex:
                sp.texture = tex
        return sp

    def _park_all_piece_sprites(self):
        """Park every piece sprite off-screen — same pattern as
        _park_all_avatar_sprites. Called once per frame at the start of
        any board rendering pass that uses piece sprites."""
        for sp in self._piece_sprites.values():
            sp.position = (-10000, -10000)

    # ── v10: Gender overlay glyphs ───────────────────────────────────
    # Tiny ♂ / ♀ glyphs drawn on top of each flanked piece so the user
    # can read kingside vs queenside at a glance, independent of the
    # piece-sprite artwork. Helpful when the user has dropped in their
    # own custom set where the _k / _q distinction is too subtle.
    _GENDER_GLYPH_KS = "\u2642"   # ♂ Male — assigned to kingside
    _GENDER_GLYPH_QS = "\u2640"   # ♀ Female — assigned to queenside
    # Soft semi-transparent colors so the glyph doesn't fight with the
    # piece silhouette underneath. Kingside = warm gold, queenside =
    # cool silver — same convention as the placeholder corner pip in
    # piece_textures.py so the two cues reinforce each other.
    _GENDER_COLOR_KS = (235, 200, 60, 235)
    _GENDER_COLOR_QS = (210, 220, 235, 235)

    def _draw_gender_overlay(self, sq_size: int):
        """Render ♂/♀ glyphs over flanked pieces on the live board.

        Drawn after the piece sprite list so the glyph sits on top.
        Skips kings/queens (unique, no flank), squares currently being
        animated (the slider owns those sprites), and the dragged
        square (handled separately so the marker follows the cursor).
        Position: small badge in the top-right corner of the square
        — close enough to read with the piece, far enough not to
        obscure the piece silhouette.
        """
        anim_sqs = self.animator.animating_squares
        # Glyph size: small enough to act as a corner badge, but
        # large enough to remain legible on tiny boards. Floor it at
        # 9pt so it never disappears completely.
        fs = max(9, int(sq_size * 0.28))
        # Offset of the glyph centre from the square centre, in pixels.
        # 0.30 puts the badge cleanly in the upper-right corner without
        # overlapping the centre of the piece artwork.
        off = int(sq_size * 0.30)
        for sq in chess.SQUARES:
            if sq in anim_sqs:
                continue
            if self.dragging and sq == self.drag_sq:
                continue  # handled via the drag-ghost branch below
            p = self.engine.board.piece_at(sq)
            if not p:
                continue
            piece_letter = p.symbol().upper()
            if piece_letter in ("K", "Q"):
                continue  # no flank distinction for the royal pair
            cx, cy = self._s2p(sq)
            sh = piece_textures.flank_for_square(sq)
            self._draw_one_gender_glyph(cx + off, cy + off, sh, fs)

        # Drag ghost gets its own glyph at the cursor so the user
        # can see the flank marker mid-drag.
        if self.dragging and self.drag_sq is not None:
            p = self.engine.board.piece_at(self.drag_sq)
            if p and p.symbol().upper() not in ("K", "Q"):
                sh = piece_textures.flank_for_square(self.drag_sq)
                # Drag ghost is 1.05x sq_size; offset accordingly.
                doff = int(sq_size * 0.32)
                self._draw_one_gender_glyph(
                    self.dmx + doff, self.dmy + doff, sh, fs)

    def _draw_one_gender_glyph(self, cx, cy, side_hint, font_size):
        """Helper: draw a single ♂ or ♀ glyph centred at (cx, cy).
        A faint dark backdrop is drawn first for legibility on light
        squares; the glyph itself is drawn in the side-hint colour."""
        glyph = (self._GENDER_GLYPH_KS if side_hint == "k"
                 else self._GENDER_GLYPH_QS)
        col = (self._GENDER_COLOR_KS if side_hint == "k"
               else self._GENDER_COLOR_QS)
        # Subtle dark halo for contrast on light squares
        arcade.draw_text(glyph, cx + 1, cy - 1,
                         (0, 0, 0, 180),
                         font_size=font_size,
                         anchor_x="center", anchor_y="center", bold=True)
        arcade.draw_text(glyph, cx, cy, col,
                         font_size=font_size,
                         anchor_x="center", anchor_y="center", bold=True)

    def _draw_avatar_card(self, left, bottom, name: str, role: str,
                          subtitle: str, active: bool,
                          slot_key: str | None = None):
        """Draw a single avatar card: background, avatar disc, name,
        subtitle (e.g. 'White' / 'AI thinking…'), and a green pulse
        ring when it's this player's turn.

        `slot_key` distinguishes the two cards drawn each frame (e.g.
        "ingame_left" vs "ingame_right") so that if both happen to
        show the same player name (e.g. an AI-vs-AI replay where
        White and Black are the same configured player), they still
        get distinct Sprite objects and both positions render."""
        # Card background
        bg = (58, 66, 82, 240) if active else (42, 48, 60, 220)
        border = (120, 200, 120, 255) if active else COLOR_ACCENT
        border_w = 2 if active else 1
        arcade.draw_lbwh_rectangle_filled(
            left, bottom, AV_CARD_W, AV_CARD_H, bg)
        _draw_outline_lbwh(
            left, bottom, AV_CARD_W, AV_CARD_H, border, border_w)

        # Position the avatar sprite inside the card
        av_cx = left + AV_SIZE // 2 + 6
        av_cy = bottom + AV_CARD_H // 2
        sp = self._get_avatar_sprite(name, role, AV_SIZE, slot_key=slot_key)
        sp.position = (av_cx, av_cy)

        # Text beside the avatar
        text_x = left + AV_SIZE + 14
        # Truncate long names so they don't overflow the card
        max_chars = max(12, (AV_CARD_W - AV_SIZE - 20) // 8)
        disp_name = name if len(name) <= max_chars else name[:max_chars - 1] + "…"
        # Name on top, subtitle below
        arcade.draw_text(disp_name, text_x, bottom + AV_CARD_H - 22,
                         COLOR_TEXT, font_size=13, bold=True)
        sub_color = (140, 220, 140, 255) if active else COLOR_TEXT_DIM
        arcade.draw_text(subtitle, text_x, bottom + 8,
                         sub_color, font_size=10)

    def _draw_avatars_in_game(self):
        """Draw the two avatar cards during play. Left card = whoever is
        on the bottom of the board from the viewer's POV (White when
        not flipped); right card = the top side. Active card gets a
        green ring when it's that side's turn.

        When a master game or a pasted PGN is loaded, avatars use the
        real players' names (role='master'). Otherwise they use
        Human/AI labels."""
        # Park all avatar sprites off-screen first — the master-games
        # browser and this view share the same persistent SpriteList, so
        # leftover sprites from the browser would otherwise keep drawing
        # their old positions over the game view. Only the two cards we
        # reposition below will be visible this frame.
        self._park_all_avatar_sprites()

        # Resolve White / Black identity
        if self.loaded_white_name or self.loaded_black_name:
            white_name = self.loaded_white_name or "White"
            white_role = "master" if self.loaded_white_name else "human"
            black_name = self.loaded_black_name or "Black"
            black_role = "master" if self.loaded_black_name else "human"
        else:
            white_is_ai = (self.engine.ai_color == chess.WHITE)
            if white_is_ai:
                white_name = self.profiled_ai.profile.name
                white_role = "ai"
                black_name = "Human"
                black_role = "human"
            else:
                white_name = "Human"
                white_role = "human"
                black_name = self.profiled_ai.profile.name
                black_role = "ai"

        # Bottom-of-board player first (left card), then top (right)
        if not self.board_flipped:
            bottom_name, bottom_role, bottom_sub = white_name, white_role, "White"
            top_name,    top_role,    top_sub    = black_name, black_role, "Black"
        else:
            bottom_name, bottom_role, bottom_sub = black_name, black_role, "Black"
            top_name,    top_role,    top_sub    = white_name, white_role, "White"

        # "to move" indicator matches engine turn, regardless of flip
        turn_is_white = self.engine.is_white_turn()
        white_active = turn_is_white and not self.engine.is_game_over()
        black_active = (not turn_is_white) and not self.engine.is_game_over()

        if not self.board_flipped:
            left_active = white_active
            right_active = black_active
        else:
            left_active = black_active
            right_active = white_active

        # Build subtitles with role + state
        def _sub(role, side_label, active):
            if role == "ai":
                if active and self.thinking:
                    return f"AI ({side_label}) — thinking…"
                if active:
                    return f"AI ({side_label}) — to move"
                return f"AI ({side_label})"
            if role == "master":
                return f"{side_label} — master game"
            # human
            if active:
                return f"You ({side_label}) — your move"
            return f"You ({side_label})"

        # Left card
        self._draw_avatar_card(
            AV_LEFT_CARD_X, AV_BAND_Y,
            bottom_name, bottom_role,
            _sub(bottom_role, bottom_sub, left_active),
            left_active,
            slot_key="ingame_left")
        # Right card
        self._draw_avatar_card(
            AV_RIGHT_CARD_X, AV_BAND_Y,
            top_name, top_role,
            _sub(top_role, top_sub, right_active),
            right_active,
            slot_key="ingame_right")

        # Flush the sprite list — draws all avatars for this frame
        self._avatar_sprite_list.draw()

    # ── Clipboard helpers + toast popup ───────────────────────────────
    def _copy_to_clipboard(self, text: str) -> bool:
        """Try multiple clipboard strategies in order of reliability:
        pyperclip → tkinter → arcade window. Returns True on success.
        Mirrors the paste logic in ui_widgets.TextInputBox but writes."""
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except Exception:
            pass
        try:
            import tkinter as tk
            r = tk.Tk()
            r.withdraw()
            r.clipboard_clear()
            r.clipboard_append(text)
            r.update()
            r.destroy()
            return True
        except Exception:
            pass
        try:
            win = arcade.get_window()
            if win is not None and hasattr(win, "set_clipboard_text"):
                win.set_clipboard_text(text)
                return True
        except Exception:
            pass
        return False

    def _copy_fen(self):
        """Copy the current FEN to the system clipboard and show a toast."""
        fen = self.engine.board.fen()
        ok = self._copy_to_clipboard(fen)
        if ok:
            self._show_toast("FEN saved in clipboard")
            self.info = ["FEN copied to clipboard:",
                         fen[:60] + ("…" if len(fen) > 60 else "")]
            print(f"[Clipboard] Copied FEN: {fen}")
        else:
            self._show_toast("Clipboard copy failed")
            self.info = ["Could not access clipboard.",
                         "Install pyperclip or tkinter for clipboard support."]

    def _copy_pgn(self):
        """Copy the full PGN (with headers) to the system clipboard and
        show a toast. Uses the same Game.from_board pipeline as Save PGN
        so the clipboard content matches the saved file format."""
        game = chess.pgn.Game.from_board(self.engine.board)
        game.headers["Event"] = "Chess Game Session"
        game.headers["Date"] = datetime.date.today().isoformat()
        game.headers["White"] = "Human" if self.player_color == chess.WHITE else self.profiled_ai.profile.name
        game.headers["Black"] = "Human" if self.player_color == chess.BLACK else self.profiled_ai.profile.name
        game.headers["Result"] = self.engine.game_result() or "*"
        pgn_text = str(game)
        ok = self._copy_to_clipboard(pgn_text)
        if ok:
            self._show_toast("PGN saved in clipboard")
            preview = self._display_pgn_short or "(no moves yet)"
            self.info = ["PGN copied to clipboard.",
                         f"Length: {len(pgn_text)} chars",
                         f"Preview: {preview[:60]}{'…' if len(preview) > 60 else ''}"]
            print(f"[Clipboard] Copied PGN ({len(pgn_text)} chars)")
        else:
            self._show_toast("Clipboard copy failed")
            self.info = ["Could not access clipboard.",
                         "Install pyperclip or tkinter for clipboard support."]

    def _show_toast(self, text: str):
        """Queue a transient centered popup. Overwrites any existing one."""
        self._toast = (text, time.time() + self.TOAST_DURATION)

    def _draw_toast(self):
        """Render the toast pill, centered near the top of the board,
        with an alpha fade during the last 0.4 s of its life."""
        if self._toast is None:
            return
        text, expires_at = self._toast
        now = time.time()
        remaining = expires_at - now
        if remaining <= 0:
            self._toast = None
            return
        fade = 0.4
        alpha_mul = min(1.0, remaining / fade)
        pad_x = 18
        text_w = max(160, int(len(text) * 8.5) + pad_x * 2)
        text_h = 34
        cx = self.width // 2
        cy = BY + BOARD_SIZE - 40
        left = cx - text_w // 2
        bottom = cy - text_h // 2
        arcade.draw_lbwh_rectangle_filled(
            left + 3, bottom - 3, text_w, text_h,
            (0, 0, 0, int(120 * alpha_mul)))
        arcade.draw_lbwh_rectangle_filled(
            left, bottom, text_w, text_h,
            (45, 55, 72, int(235 * alpha_mul)))
        _draw_outline_lbwh(
            left, bottom, text_w, text_h,
            (120, 190, 100, int(255 * alpha_mul)), 2)
        arcade.draw_text(text, cx, cy - 7,
                         (240, 250, 230, int(255 * alpha_mul)),
                         font_size=14, anchor_x="center", bold=True)

    def _update_toast(self):
        """Expire the toast if its deadline has passed."""
        if self._toast and time.time() >= self._toast[1]:
            self._toast = None

    # ── FEN / PGN text loaders (used by text input widgets) ─────────
    def _load_from_fen(self, fen: str):
        """Callback: apply a pasted FEN string to the engine board."""
        fen = fen.strip()
        try:
            board = chess.Board(fen)
        except ValueError as e:
            self.info = ["Invalid FEN:", str(e)[:60]]
            self.fen_input.focused = False
            return

        # ── Critical: silence anything that would stomp the board ──
        # If teacher is active, on_update() copies teacher.board into the
        # engine every frame, which would overwrite the FEN immediately.
        if self.teacher.active:
            self.teacher.stop()
        self.show_opening_menu = False
        self.show_help = False

        # Reset any pasted-PGN / master-game replay state — a fresh FEN
        # is a standalone position, not a point in a loaded game.
        self.loaded_moves = []
        self.ply_index = 0
        self.loaded_label = ""
        self.loaded_start_fen = fen

        self.engine.board = board
        self.eval_tracker.reset()
        # Record the current position's eval as the starting point
        self.eval_tracker.history[0] = self.eval_tracker.history[0].__class__(
            ply=0, cp=self.engine.get_eval_cp(), mover=None, delta=0.0)

        self.sel = None
        self.legal = []
        self.arrows = []
        self.dragging = False
        self.drag_sq = None
        self.animator.clear()
        self.fen_input.text = ""
        self.fen_input.focused = False
        self._analyze()
        turn = "White" if board.turn == chess.WHITE else "Black"
        self.info = ["FEN loaded.",
                     f"{turn} to move.",
                     f"cp {self.engine.get_eval_cp()/100:+.2f}"]
        print(f"[FEN] Loaded: {fen}")

    def _load_from_pgn_text(self, text: str):
        """Callback: parse a PGN string (full game or movetext) and load it."""
        text = text.strip()
        if not text:
            return

        # Try full PGN first
        game = None
        try:
            game = chess.pgn.read_game(io.StringIO(text))
        except Exception:
            game = None

        if game is None or not list(game.mainline_moves()):
            # Fall back: treat input as raw SAN movetext like "1. e4 e5 2. Nf3 ..."
            wrapped = '[Event "Pasted"]\n[Result "*"]\n\n' + text
            try:
                game = chess.pgn.read_game(io.StringIO(wrapped))
            except Exception as e:
                self.info = ["Could not parse PGN:", str(e)[:60]]
                self.pgn_input.focused = False
                return

        if game is None:
            self.info = ["Could not parse PGN text."]
            self.pgn_input.focused = False
            return

        self._apply_pgn_game(game, source_label="(pasted)")
        self.pgn_input.text = ""
        self.pgn_input.focused = False

    def _apply_pgn_game(self, game, source_label: str = ""):
        """Replay a python-chess Game object onto the board, rebuilding
        the eval tracker as we go so the graph reflects the loaded game.

        Also stashes the move list so mouse-wheel scroll can step
        backward/forward through the plies (see on_mouse_scroll and
        _rebuild_from_ply_index)."""
        # Stop teacher so on_update won't stomp our loaded position.
        if self.teacher.active:
            self.teacher.stop()
        self.show_opening_menu = False

        # Determine starting FEN (some PGNs start from a non-standard position)
        start_fen = game.headers.get("FEN", chess.STARTING_FEN) if game.headers else chess.STARTING_FEN
        try:
            start_board = chess.Board(start_fen)
        except ValueError:
            start_board = chess.Board()
            start_fen = chess.STARTING_FEN

        self.engine.board = start_board.copy()
        self.eval_tracker.reset()
        self.sel = None
        self.legal = []
        self.arrows = []
        self.dragging = False
        self.drag_sq = None
        self.animator.clear()

        # Collect legal moves from the game into a flat list we can step through
        probe = start_board.copy()
        moves: list[chess.Move] = []
        total_in_pgn = 0
        for move in game.mainline_moves():
            total_in_pgn += 1
            if move in probe.legal_moves:
                moves.append(move)
                probe.push(move)
            else:
                break

        # Stash for scroll
        self.loaded_moves = moves
        self.loaded_start_fen = start_fen
        self.ply_index = len(moves)        # start at end of game
        self.loaded_label = source_label
        # Extract White / Black names from PGN headers for the avatar
        # cards. Missing / placeholder names fall back to empty so the
        # avatars revert to Human/AI display.
        hdrs = game.headers if game.headers else {}
        w_hdr = (hdrs.get("White") or "").strip()
        b_hdr = (hdrs.get("Black") or "").strip()
        self.loaded_white_name = w_hdr if w_hdr and w_hdr != "?" else ""
        self.loaded_black_name = b_hdr if b_hdr and b_hdr != "?" else ""

        # Apply all moves now so the graph is fully populated
        for move in moves:
            mover = self.engine.board.turn
            self.engine.board.push(move)
            self.eval_tracker.record(
                ply=len(self.engine.board.move_stack),
                cp=self.engine.get_eval_cp(),
                mover=mover,
            )

        self._analyze()
        headers = game.headers if game.headers else {}
        self.info = [
            f"Loaded: {source_label}" if source_label else "PGN loaded.",
            f"W: {headers.get('White', '?')}  vs  "
            f"B: {headers.get('Black', '?')}",
            f"Result: {headers.get('Result', '*')}",
            f"Moves applied: {len(moves)}/{total_in_pgn}",
            "Scroll wheel: step through plies",
        ]


def main():
    ChessGame()
    arcade.run()


if __name__ == "__main__":
    main()
