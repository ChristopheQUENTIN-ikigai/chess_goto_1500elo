"""
animation.py — True smooth piece sliding for Arcade 3.x.

Arcade 3.x rules:
  - Sprite has NO .draw() method. Must use SpriteList.draw().
  - Texture created from PIL Image: arcade.Texture(pil_image, name=key)
  - Sprite created: arcade.Sprite(texture) then set .position
  - SpriteList created: arcade.SpriteList() then .append(sprite)
  - draw_lbwh_rectangle_filled, draw_circle_filled still exist for effects.

Approach:
  1. Check ./assets/textures/{wK,bK,…}.png — load if present.
  2. Otherwise render each chess glyph to PIL → arcade.Texture, and save
     a PNG to ./assets/textures/ so subsequent runs reuse the file.
  3. Create Sprite from texture, add to SpriteList.
  4. Each frame: update sprite.position via easing interpolation.
  5. Draw entire SpriteList in one GPU-batched call.
"""
import math
import os
import arcade
import chess
from config import UNICODE_PIECES, ASSETS_DIR

# ── Piece texture cache ──────────────────────────────────────────────
_TEX_CACHE: dict[str, arcade.Texture] = {}


def _piece_png_path(symbol: str) -> str:
    """On-disk path for a given piece glyph, inside ASSETS_DIR.

    Filenames use the standard chess-texture naming: color prefix (w/b)
    then uppercase piece letter. Example: 'K' → 'wK.png', 'k' → 'bK.png'.
    Size is not in the filename — we render at whatever sq_size the
    first caller requests and keep it; rescaling is good enough for
    other sizes (Arcade does it on the GPU).
    """
    is_white = symbol.isupper()
    letter = symbol.upper()
    return os.path.join(ASSETS_DIR, f"{'w' if is_white else 'b'}{letter}.png")


def _get_piece_texture(symbol: str, size: int = 80) -> arcade.Texture:
    """Get or build a texture for a chess piece glyph.

    Resolution order:
      1. In-memory cache (keyed by symbol+size).
      2. PNG file in ./assets/textures/ (loaded via PIL then converted to
         arcade.Texture). Supports user-supplied custom piece art.
      3. Unicode glyph rendered onto a PIL canvas — saved to disk on
         first generation so subsequent runs can reuse it.
    """
    key = f"piece_{symbol}_{size}"
    if key in _TEX_CACHE:
        return _TEX_CACHE[key]

    from PIL import Image, ImageDraw, ImageFont

    png_path = _piece_png_path(symbol)

    # Ensure folder exists for any writes below
    try:
        os.makedirs(ASSETS_DIR, exist_ok=True)
    except OSError:
        pass

    # 2. Disk load if file already present
    if os.path.isfile(png_path):
        try:
            img = Image.open(png_path).convert("RGBA")
            if img.size != (size, size):
                img = img.resize((size, size), Image.LANCZOS)
            tex = arcade.Texture(img, name=key)
            _TEX_CACHE[key] = tex
            return tex
        except Exception as e:
            print(f"[textures] Could not load {png_path}: {e} — regenerating.")

    # 3. Generate Unicode-glyph texture
    is_white = symbol.isupper()
    fg = (255, 255, 255, 255) if is_white else (40, 40, 40, 255)
    shadow_color = (0, 0, 0, 140)
    uni = UNICODE_PIECES.get(symbol, "?")
    fs = int(size * 0.75)

    # Try system fonts with chess glyph support
    font = None
    for path in [
        "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]:
        try:
            font = ImageFont.truetype(path, fs)
            break
        except:
            continue
    if font is None:
        font = ImageFont.load_default()

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Center the glyph
    bbox = draw.textbbox((0, 0), uni, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1]

    # Shadow then foreground
    draw.text((tx + 1, ty + 1), uni, fill=shadow_color, font=font)
    draw.text((tx, ty), uni, fill=fg, font=font)

    # Save to disk so the next run loads from file
    try:
        img.save(png_path, "PNG")
    except OSError as e:
        print(f"[textures] Could not save {png_path}: {e}")

    tex = arcade.Texture(img, name=key)
    _TEX_CACHE[key] = tex
    return tex


# ── Easing ───────────────────────────────────────────────────────────

def _texture_for(symbol: str, size: int,
                 theme: str | None = None,
                 side_hint: str | None = None) -> arcade.Texture:
    """Texture for a sliding piece.

    When a ``theme`` is supplied we use the SAME themed pipeline as the
    static board (``piece_textures.get_piece_texture``) so a sliding piece
    is pixel-identical to its static counterpart — there is no visual
    'pop' the instant the slide ends and the static board takes over.
    ``side_hint`` is collapsed for kings/queens exactly the way the static
    board's ``_get_piece_sprite`` does it, so the cache keys line up.

    Falls back to the legacy Unicode-glyph texture when no theme is given
    (keeps old call sites working).
    """
    if theme is not None:
        try:
            import piece_textures
            sh = side_hint if (side_hint in ("k", "q")
                               and symbol.upper() not in ("K", "Q")) else "k"
            return piece_textures.get_piece_texture(
                symbol, theme=theme, side_hint=sh, size=size)
        except Exception as e:  # pragma: no cover - defensive
            print(f"[animation] themed texture failed ({e}); using glyph.")
    return _get_piece_texture(symbol, size)


def ease_out_cubic(t):
    return 1.0 - (1.0 - t) ** 3

def ease_in_out_quad(t):
    return 2.0 * t * t if t < 0.5 else 1.0 - (-2.0 * t + 2.0) ** 2 / 2.0

def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2


# ── Sliding piece ────────────────────────────────────────────────────

def _sq_px(sq, bx, by, sz, flipped=False):
    """Chess square → pixel center, respecting the board-flipped flag.
    When flipped=True, file a renders on the right and rank 1 on top
    (i.e. Black's POV). Defaults to False for backwards compatibility."""
    f = chess.square_file(sq)
    r = chess.square_rank(sq)
    if flipped:
        f = 7 - f
        r = 7 - r
    return (bx + f * sz + sz // 2,
            by + r * sz + sz // 2)


def _flank_for(sq: int) -> str:
    """'k' for kingside squares (files e..h), else 'q'. Mirrors
    piece_textures.flank_for_square so themed slide art lines up with the
    static board without importing that module on the hot path."""
    return "k" if chess.square_file(sq) >= 4 else "q"


class SlidingPiece:
    """A Sprite that slides between two board positions."""

    def __init__(self, from_sq, to_sq, symbol, bx, by, sz,
                 duration=0.4, easing=ease_out_cubic, flipped=False,
                 theme=None, side_hint=None):
        self.from_sq = from_sq
        self.to_sq = to_sq
        self.duration = duration
        self.easing = easing
        self.elapsed = 0.0
        self.done = False

        self.fx, self.fy = _sq_px(from_sq, bx, by, sz, flipped)
        self.tx, self.ty = _sq_px(to_sq, bx, by, sz, flipped)

        tex = _texture_for(symbol, sz, theme=theme, side_hint=side_hint)
        self.sprite = arcade.Sprite(tex)
        self.sprite.position = (self.fx, self.fy)

    def update(self, dt):
        if self.done:
            return
        self.elapsed += dt
        t = min(self.elapsed / self.duration, 1.0)
        e = self.easing(t)
        x = self.fx + (self.tx - self.fx) * e
        y = self.fy + (self.ty - self.fy) * e
        self.sprite.position = (x, y)
        if t >= 1.0:
            self.done = True


class MoveAnimator:
    """Manages sprite-based sliding animations.

    Arcade 3.x: Sprites cannot draw themselves — we keep them in a
    SpriteList which is drawn in one GPU-batched call.
    """

    def __init__(self):
        self._sliders: list[SlidingPiece] = []
        self._sprite_list = arcade.SpriteList()
        self._effects: list[dict] = []  # Check pulse effects
        self._animating_squares: set[int] = set()

    @property
    def active(self):
        return bool(self._sliders) or bool(self._effects)

    @property
    def animating_squares(self):
        return self._animating_squares

    def start_move(self, from_sq, to_sq, piece_symbol, is_white,
                   board_left, board_bottom, sq_size,
                   is_capture=False, captured_symbol="",
                   captured_is_white=False, duration=0.4, flipped=False,
                   theme=None):
        easing = ease_out_back if is_capture else ease_out_cubic
        dur = duration * 0.85 if is_capture else duration

        # Flank hint matches how the piece will be drawn statically once
        # it lands on `to_sq`, so the themed art is identical end-to-end.
        sh = _flank_for(to_sq)
        slider = SlidingPiece(from_sq, to_sq, piece_symbol,
                              board_left, board_bottom, sq_size, dur, easing,
                              flipped=flipped, theme=theme, side_hint=sh)
        self._sliders.append(slider)
        self._sprite_list.append(slider.sprite)
        self._animating_squares.add(from_sq)
        self._animating_squares.add(to_sq)

    def start_castle(self, king_from, king_to, rook_from, rook_to,
                     is_white, board_left, board_bottom, sq_size,
                     duration=0.45, flipped=False, theme=None):
        ks = "K" if is_white else "k"
        rs = "R" if is_white else "r"
        for fr, to, sym in [(king_from, king_to, ks), (rook_from, rook_to, rs)]:
            slider = SlidingPiece(fr, to, sym, board_left, board_bottom,
                                  sq_size, duration, ease_in_out_quad,
                                  flipped=flipped, theme=theme,
                                  side_hint=_flank_for(to))
            self._sliders.append(slider)
            self._sprite_list.append(slider.sprite)
            self._animating_squares.add(fr)
            self._animating_squares.add(to)

    def start_check_pulse(self, king_sq, board_left, board_bottom, sq_size,
                          flipped=False):
        cx, cy = _sq_px(king_sq, board_left, board_bottom, sq_size, flipped)
        self._effects.append({
            "cx": cx, "cy": cy, "sz": sq_size,
            "elapsed": 0.0, "duration": 0.6, "done": False,
        })

    def update(self, dt):
        # Update sliders
        for s in self._sliders:
            s.update(dt)

        # Update effects
        for e in self._effects:
            e["elapsed"] += dt
            if e["elapsed"] >= e["duration"]:
                e["done"] = True

        # Remove finished sliders — also remove their sprites from the list
        finished = [s for s in self._sliders if s.done]
        for s in finished:
            if s.sprite in self._sprite_list:
                self._sprite_list.remove(s.sprite)
        self._sliders = [s for s in self._sliders if not s.done]
        self._effects = [e for e in self._effects if not e["done"]]

        # Rebuild animating squares
        self._animating_squares = set()
        for s in self._sliders:
            self._animating_squares.add(s.from_sq)
            self._animating_squares.add(s.to_sq)

    def draw(self, sq_size):
        # Draw check pulse effects (plain drawing calls, not sprites)
        for e in self._effects:
            if e["done"]:
                continue
            t = e["elapsed"] / e["duration"]
            pulse = 0.35 + 0.15 * math.sin(t * math.pi * 3)
            alpha = int(200 * (1.0 - t * 0.5))
            arcade.draw_circle_filled(
                e["cx"], e["cy"], sq_size * pulse, (255, 0, 0, alpha))

        # Draw all sliding sprites in one batched GPU call
        if self._sprite_list:
            self._sprite_list.draw()

    def clear(self):
        self._sliders.clear()
        self._sprite_list.clear()
        self._effects.clear()
        self._animating_squares.clear()
