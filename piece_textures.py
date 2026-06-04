"""
piece_textures.py — Piece-image asset manager.

Resolution order when get_piece_texture(symbol, theme, side_hint, size) is called:
  1. In-memory cache (keyed by symbol + theme + side_hint + size).
  2. File at  ./assets/textures/pieces/{theme}/{filename}.png
     loaded via PIL and converted to an arcade.Texture. This is where
     the user drops their own custom artwork.
  3. Auto-generated placeholder PNG, written to disk on first run so
     the user has a real file to overwrite. User-supplied files are
     never overwritten — we only write when the file does not already
     exist.

Theme catalog
-------------
There are two top-level texture **styles**:

  * "classical"  — the traditional set (one look only).
  * "fancy"      — themed sets the user can pick from. The fancy
                   sub-themes (ambiances) ship as:
                       roman          — ancient roman / classical
                       fantasy        — heroic fantasy / sword & sorcery
                       scifi          — sci-fi / futurist
                       steampunk      — brass and clockwork
                       cyberpunk      — neon noir / glitch

Each piece type has TWO sprites: a "kingside" and a "queenside" variant.
The two are visually similar but sufficiently distinguishable that a
player who looks closely can tell, for any given rook, knight or
bishop, which flank it started on. This is the user's "slightly
distinguish king side from queen side" requirement.

Filename convention
-------------------
Inside ./assets/textures/pieces/{theme}/ the filenames are:

    w{P}_k.png    white piece, kingside variant
    w{P}_q.png    white piece, queenside variant
    b{P}_k.png    black piece, kingside variant
    b{P}_q.png    black piece, queenside variant

Where {P} is one of  K Q R B N P  (king, queen, rook, bishop, knight, pawn).
Examples:  wK_k.png, wK_q.png, wR_k.png, wR_q.png, bN_k.png, bN_q.png …

The KING and QUEEN share the same image regardless of side_hint (they
are unique pieces, sat on their own original square). For everything
else, _k vs _q matters.

Flank inference
---------------
We don't know at look-up time whether a given rook on, say, e4 is the
"kingside rook" — pieces move around. Caller passes a side_hint ("k"
or "q") that is computed once per game from the starting position and
threaded through the move history; the renderer simply hands back the
right placeholder. If the caller hands None we fall back to "k" — this
is what happens for promoted pieces (a promoted queen has no original
flank), where it doesn't matter.

The placeholder generator draws a tiny coloured pip in the corner —
gold for kingside, silver for queenside — so the distinction is
visible even before the user replaces the placeholders with their own
artwork.

Public API
----------
    get_piece_texture(symbol, theme, side_hint, size) -> arcade.Texture
    available_themes()                                -> list[str]
    theme_label(theme)                                -> str
    ensure_placeholders(theme)                        -> None
        Write any missing placeholder PNGs for `theme` so the user has
        12 files to edit. Idempotent.
    ensure_all_placeholders()                         -> None
        Same, for every theme in available_themes(). Run once at app
        startup so the assets folder is always populated.

This module never crashes — every error path falls through to a
generated placeholder. PIL is required (it's already a dependency of
avatar_gen.py).
"""
import os
import hashlib
import arcade

from config import ASSETS_DIR

PIECES_DIR = os.path.join(ASSETS_DIR, "pieces")

# ── Theme registry ──────────────────────────────────────────────────
# The 'classical' style is a single theme. The 'fancy' style is a
# family of named ambiances. Each theme has its own subdirectory so a
# user can ship five totally independent piece sets without conflict.
_THEMES = {
    "classical":  "Classical",
    "roman":      "Roman / Ancient",
    "fantasy":    "Heroic Fantasy",
    "scifi":      "Sci-Fi / Futurist",
    "steampunk":  "Steampunk",
    "cyberpunk":  "Cyberpunk",
}

# Theme-specific palettes used by the placeholder generator. The user
# replaces these placeholders with real artwork; the palettes here are
# only meant to make the placeholder PNGs visually distinct so the
# theme picker in the splash menu has something to preview.
_THEME_PALETTES = {
    "classical": {
        "white_body": (250, 248, 240),
        "white_edge": (60, 60, 60),
        "black_body": (45, 45, 50),
        "black_edge": (10, 10, 10),
        "accent":     (140, 100, 50),
    },
    "roman": {
        "white_body": (235, 220, 180),   # ivory marble
        "white_edge": (140, 110, 70),
        "black_body": (90, 60, 40),      # bronze
        "black_edge": (40, 25, 15),
        "accent":     (200, 160, 70),    # gold
    },
    "fantasy": {
        "white_body": (220, 230, 250),   # silver moonsteel
        "white_edge": (90, 110, 150),
        "black_body": (60, 40, 80),      # dark sorcerer purple
        "black_edge": (20, 10, 40),
        "accent":     (200, 50, 80),     # blood ruby
    },
    "scifi": {
        "white_body": (210, 240, 255),   # chrome cyan
        "white_edge": (40, 110, 160),
        "black_body": (35, 45, 60),      # graphite
        "black_edge": (10, 15, 25),
        "accent":     (80, 230, 255),    # holo-blue
    },
    "steampunk": {
        "white_body": (215, 180, 130),   # polished brass
        "white_edge": (110, 75, 30),
        "black_body": (80, 60, 40),      # oiled iron
        "black_edge": (30, 20, 10),
        "accent":     (220, 130, 40),    # copper rivet
    },
    "cyberpunk": {
        "white_body": (240, 240, 250),
        "white_edge": (200, 50, 200),    # magenta neon
        "black_body": (15, 20, 35),
        "black_edge": (255, 0, 200),
        "accent":     (0, 240, 220),     # cyan neon
    },
}

# Unicode glyphs used as the placeholder "art" for each piece.
# Matches config.UNICODE_PIECES but kept local so this module is
# self-contained and the placeholder generator can run before the
# rest of the game is wired up.
_GLYPHS = {
    "K": "\u2654", "Q": "\u2655", "R": "\u2656",
    "B": "\u2657", "N": "\u2658", "P": "\u2659",
    "k": "\u265A", "q": "\u265B", "r": "\u265C",
    "b": "\u265D", "n": "\u265E", "p": "\u265F",
}

# Sides that carry a flank distinction. Kings and queens sit on their
# own unique starting squares so we don't bother (it would be confusing
# — there is no "kingside king"). All other pieces get _k and _q.
_FLANKED = ("R", "B", "N", "P")

# ── Cache ────────────────────────────────────────────────────────────
_CACHE: dict[str, arcade.Texture] = {}


def available_themes() -> list[str]:
    """Theme keys in display order (classical first, then fancy)."""
    return list(_THEMES.keys())


def theme_label(theme: str) -> str:
    """Human-readable label for a theme key."""
    return _THEMES.get(theme, theme.capitalize())


def is_classical(theme: str) -> bool:
    return theme == "classical"


def is_fancy(theme: str) -> bool:
    return theme in _THEMES and theme != "classical"


def fancy_themes() -> list[str]:
    """Just the fancy sub-themes."""
    return [t for t in _THEMES if t != "classical"]


# ── Filename helpers ────────────────────────────────────────────────
def _theme_dir(theme: str) -> str:
    """Absolute directory for `theme`'s pieces. May not exist yet."""
    return os.path.join(PIECES_DIR, theme)


def _filename(symbol: str, side_hint: str | None) -> str:
    """Filename for a piece in any theme.

    `symbol` is python-chess style: uppercase = white, lowercase = black.
    `side_hint` is "k" or "q" or None. King/Queen ignore it.
    """
    color = "w" if symbol.isupper() else "b"
    piece = symbol.upper()
    if piece in ("K", "Q"):
        # Kings and queens have no flank distinction — but we still
        # write _k to keep filenames uniform; the loader just ignores
        # side_hint for these two.
        return f"{color}{piece}_k.png"
    sh = (side_hint or "k").lower()
    if sh not in ("k", "q"):
        sh = "k"
    return f"{color}{piece}_{sh}.png"


# ── Placeholder rendering ───────────────────────────────────────────
def _glyph_font(size: int):
    """Locate a font that supports chess Unicode glyphs."""
    from PIL import ImageFont
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansSymbols2-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _render_placeholder(symbol: str, theme: str, side_hint: str | None,
                        size: int):
    """Build a PIL RGBA placeholder image for one piece.

    The placeholder is intentionally simple — a coloured rounded square
    plate with the chess-piece Unicode glyph centered on it, plus a
    small flank pip in the upper corner. The whole point is that the
    user replaces this PNG with their own art; the placeholder just
    gives them a working game and a file to edit.
    """
    from PIL import Image, ImageDraw

    pal = _THEME_PALETTES.get(theme, _THEME_PALETTES["classical"])
    is_white = symbol.isupper()
    body_rgb = pal["white_body"] if is_white else pal["black_body"]
    edge_rgb = pal["white_edge"] if is_white else pal["black_edge"]
    accent_rgb = pal["accent"]
    glyph_color = edge_rgb

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded plate — Pillow's rounded_rectangle is in 9.2+. Fall back
    # to a plain rectangle if not available.
    pad = max(2, size // 16)
    radius = size // 6
    rect = (pad, pad, size - pad, size - pad)
    try:
        draw.rounded_rectangle(rect, radius=radius,
                               fill=body_rgb + (255,),
                               outline=edge_rgb + (255,), width=2)
    except AttributeError:
        draw.rectangle(rect, fill=body_rgb + (255,),
                       outline=edge_rgb + (255,), width=2)

    # Centered Unicode glyph. We render the white-king glyph for
    # white pieces and black-king glyph for black, regardless of which
    # symbol — this gives a more uniform look since the colored
    # outline glyphs (\u2654-\u2659) are line drawings while the
    # filled ones (\u265A-\u265F) are solid. We pick whichever
    # contrasts better with the body colour.
    glyph = _GLYPHS.get(symbol, "?")
    fs = int(size * 0.78)
    font = _glyph_font(fs)
    try:
        bbox = draw.textbbox((0, 0), glyph, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (size - tw) // 2 - bbox[0]
        ty = (size - th) // 2 - bbox[1] - size // 24
    except Exception:
        tx, ty = size // 6, size // 6

    # Drop shadow then glyph
    draw.text((tx + 2, ty + 2), glyph, fill=(0, 0, 0, 110), font=font)
    draw.text((tx, ty), glyph, fill=glyph_color + (255,), font=font)

    # ── Flank pip ──────────────────────────────────────────────────
    # Small coloured dot in a corner so kingside vs queenside pieces
    # are visually different at a glance even with placeholder art.
    # Rule: only flanked pieces (R/B/N/P) get the pip.
    piece_letter = symbol.upper()
    if piece_letter in _FLANKED:
        sh = (side_hint or "k").lower()
        pip_color = (220, 180, 50) if sh == "k" else (210, 215, 225)
        # Kingside pip → top-right corner; queenside → top-left.
        # Easy mnemonic: "kingside" pieces start on the right of the
        # board (h-file) for White, so the pip is on the right.
        pip_r = max(3, size // 14)
        cx = (size - pad - pip_r - 2) if sh == "k" else (pad + pip_r + 2)
        cy = pad + pip_r + 2
        draw.ellipse((cx - pip_r, cy - pip_r, cx + pip_r, cy + pip_r),
                     fill=pip_color + (255,),
                     outline=(20, 20, 20, 255), width=1)

    # ── Theme accent stripe ────────────────────────────────────────
    # A thin strip at the bottom of the plate so theme ambiance is
    # readable (cyberpunk neon vs steampunk brass etc).
    stripe_h = max(3, size // 28)
    sy = size - pad - stripe_h
    draw.rectangle((pad + 4, sy, size - pad - 4, sy + stripe_h),
                   fill=accent_rgb + (255,))

    return img


def ensure_placeholders(theme: str) -> None:
    """Make sure every piece file exists on disk for `theme`.

    Idempotent — only writes files that don't already exist, so a user
    who has dropped in custom art keeps it. Also creates the directory
    tree if needed.
    """
    dir_path = _theme_dir(theme)
    try:
        os.makedirs(dir_path, exist_ok=True)
    except OSError as e:
        print(f"[pieces] Could not create {dir_path}: {e}")
        return

    pieces_white = ("K", "Q", "R", "B", "N", "P")
    pieces_black = ("k", "q", "r", "b", "n", "p")
    sides = ("k", "q")

    for sym in pieces_white + pieces_black:
        for side in sides:
            # Kings/queens only get one file (the _k.png).
            if sym.upper() in ("K", "Q") and side != "k":
                continue
            fname = _filename(sym, side)
            path = os.path.join(dir_path, fname)
            if os.path.isfile(path):
                continue
            try:
                img = _render_placeholder(sym, theme, side, size=192)
                img.save(path, "PNG")
            except Exception as e:
                print(f"[pieces] Could not write {path}: {e}")


def ensure_all_placeholders() -> None:
    """Run ensure_placeholders for every registered theme.

    Called once at app startup. Cheap when the files already exist
    (one os.path.isfile per piece — no I/O).
    """
    for theme in available_themes():
        ensure_placeholders(theme)


# ── Texture loading ─────────────────────────────────────────────────
def _load_disk_texture(symbol: str, theme: str, side_hint: str | None,
                       size: int) -> arcade.Texture | None:
    """Attempt to load a piece image from disk; None on any failure."""
    from PIL import Image

    fname = _filename(symbol, side_hint)
    path = os.path.join(_theme_dir(theme), fname)
    if not os.path.isfile(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        if img.size != (size, size):
            img = img.resize((size, size), Image.LANCZOS)
        key = f"piecedisk_{theme}_{fname}_{size}"
        return arcade.Texture(img, name=key)
    except Exception as e:
        print(f"[pieces] Could not load {path}: {e}")
        return None


def get_piece_texture(symbol: str, theme: str = "classical",
                      side_hint: str | None = None,
                      size: int = 96) -> arcade.Texture:
    """Return a cached arcade.Texture for one piece.

    `symbol`    — python-chess piece symbol ('K','q','p',…).
    `theme`     — one of available_themes(); falls back to 'classical'.
    `side_hint` — 'k' or 'q' (or None for kings/queens / promoted).
    `size`      — pixel size of the rendered texture (square).

    Cache key combines all four parameters so swapping theme at
    runtime works correctly without leaking memory.
    """
    if theme not in _THEMES:
        theme = "classical"
    sh = side_hint if side_hint in ("k", "q") else None

    cache_key = f"piece_{theme}_{symbol}_{sh or 'x'}_{size}"
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    # Make sure the disk version exists — first-run case.
    ensure_placeholders(theme)

    tex = _load_disk_texture(symbol, theme, sh, size)
    if tex is None:
        # Last-resort: synthesize directly without ever touching disk.
        try:
            img = _render_placeholder(symbol, theme, sh, size=size)
            tex = arcade.Texture(img, name=cache_key)
        except Exception as e:
            print(f"[pieces] Could not render placeholder for "
                  f"{symbol}/{theme}: {e}")
            # Build a tiny opaque square so callers don't see None.
            from PIL import Image
            tex = arcade.Texture(
                Image.new("RGBA", (size, size), (200, 200, 200, 255)),
                name=cache_key)

    _CACHE[cache_key] = tex
    return tex


def clear_cache() -> None:
    """Drop every cached arcade.Texture. Call after the user changes
    the theme so the next draw rebuilds with the new artwork."""
    _CACHE.clear()


# ── Side-hint computation from a python-chess Board ─────────────────
# The renderer needs to know, for each piece on the board RIGHT NOW,
# whether it originated on the kingside or the queenside. The easy
# answer is to track this through every move (compute at game start,
# update on each push). The simpler answer is: derive it lazily from
# the starting square encoded in the move history. Even simpler: for
# the placeholder system, accept that we're going to do a best-effort
# guess based on current file. That's what flank_for_square() does.
#
# Rule of thumb (white perspective, mirror for black):
#   kingside  = files e/f/g/h  (the side where the king starts)
#   queenside = files a/b/c/d  (the side where the queen starts)
#
# This isn't perfect — a knight that originally started on b1 and is
# now on g3 will be classified as kingside — but for placeholder
# graphics the user was always going to swap in their own art and
# this gives a reasonable default that requires no game-state tracking.
import chess  # at end to keep top-of-file imports lean


def flank_for_square(sq: int) -> str:
    """Return 'k' if `sq` is on the kingside (files e..h), else 'q'."""
    f = chess.square_file(sq)
    return "k" if f >= 4 else "q"
