"""
avatar_gen.py — Player/AI/master-game avatars.

Resolution order when get_avatar(name, size) is called:
  1. In-memory cache (keyed by name+size).
  2. File in ASSETS_DIR/avatars/{sanitized_name}.{png,jpg,jpeg} — loaded
     via PIL and converted to an arcade.Texture. This lets users drop
     real photos (Fischer.jpg, Kasparov.jpg, …) into the folder.
  3. Generated initials disc — a flat color background with the player's
     initials centered in a bold font. Color is hash-deterministic so
     the same name always gets the same palette.

All generated avatars are saved to disk on first render so subsequent
runs can load them from file. User-supplied photos are never
overwritten — we only write when the file does not already exist.
"""
import os
import hashlib
import arcade

from config import ASSETS_DIR

# User-editable name → filename mapping. Kept in a separate module so
# non-developers can extend it without touching this file. If the
# module is missing or malformed, we fall back to filesystem
# heuristics only — the game still runs.
try:
    from avatars_links import get_avatar_filename as _links_lookup
except Exception as _e:
    print(f"[avatar] avatars_links.py unavailable ({_e}); "
          f"using filesystem heuristics only.")
    def _links_lookup(name: str):
        return None

AVATAR_DIR = os.path.join(ASSETS_DIR, "avatars")

_AVATAR_CACHE: dict[str, arcade.Texture] = {}


# ── Palette picker ──────────────────────────────────────────────────
# Stylized, high-contrast backgrounds that work with white text. One
# color per "role hint" so Human / AI / masters don't blend together.
_PALETTE_HUMAN = [
    (52, 120, 190),   # steel blue
    (46, 149, 140),   # teal
    (80, 130, 90),    # forest
]
_PALETTE_AI = [
    (140, 70, 140),   # purple
    (180, 100, 40),   # rust
    (95, 90, 170),    # indigo
]
_PALETTE_MASTER = [
    (156, 102, 68),   # bronze
    (120, 130, 90),   # olive
    (90, 60, 100),    # plum
    (140, 80, 80),    # brick
    (70, 100, 130),   # slate
    (160, 120, 60),   # brass
    (85, 115, 95),    # sage
]


def _role_palette(role: str):
    r = role.lower()
    if r == "human":
        return _PALETTE_HUMAN
    if r == "ai":
        return _PALETTE_AI
    return _PALETTE_MASTER


def _pick_color(name: str, role: str):
    """Deterministic color for a given name within its role palette."""
    pal = _role_palette(role)
    h = int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16)
    return pal[h % len(pal)]


def _initials(name: str) -> str:
    """Compute 1-2 letter initials from a name. 'Bobby Fischer' → 'BF',
    'AI' → 'AI', 'Human' → 'H', 'Jose Raul Capablanca' → 'JC' (first
    and last tokens), 'Tal' → 'T'."""
    parts = [p for p in name.replace(".", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        p = parts[0]
        # Acronyms (all-uppercase like 'AI') keep their letters.
        if p.isupper() and len(p) <= 3:
            return p
        # Otherwise use just the first letter.
        return p[0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _sanitize(name: str) -> str:
    """Filename-safe version of a player name."""
    return "".join(ch if (ch.isalnum() or ch in "-_") else "_"
                   for ch in name).strip("_") or "unknown"


def _find_file(name: str) -> str | None:
    """Look for a user-supplied avatar in AVATAR_DIR.

    Priority:
      1. Explicit mapping in avatars_links.py — this is the authoritative
         source; if the user listed a filename there, we use it even
         when a same-named file sits in the folder. The linked filename
         is just a bare name relative to AVATAR_DIR.
      2. sanitized-name.{png,jpg,jpeg}   — e.g. 'Bobby_Fischer.png'
      3. raw-name.{png,jpg,jpeg}          — e.g. 'Bobby Fischer.png'
      4. last-token.{png,jpg,jpeg}        — e.g. 'Fischer.jpg' from
         'Bobby Fischer'. Handy for casual drop-in use.

    Returns the full filesystem path or None.
    """
    if not os.path.isdir(AVATAR_DIR):
        return None

    # ── 1. Explicit mapping wins ──────────────────────────────────
    linked = _links_lookup(name)
    if linked:
        p = os.path.join(AVATAR_DIR, linked)
        if os.path.isfile(p):
            return p
        # Linked file declared but missing on disk — warn and fall
        # through to heuristics so the user still gets *something*
        # rather than a crash.
        print(f"[avatar] avatars_links.py maps {name!r} to "
              f"{linked!r} but that file is not in {AVATAR_DIR}. "
              f"Falling back to filename heuristics.")

    base = _sanitize(name)
    candidates = [base, name]
    tokens = [p for p in name.split() if p]
    if len(tokens) >= 2:
        candidates.append(tokens[-1])
    for base_try in candidates:
        for ext in (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"):
            p = os.path.join(AVATAR_DIR, base_try + ext)
            if os.path.isfile(p):
                return p
    return None


# ── Rendering ───────────────────────────────────────────────────────

def _render_initials_disc(name: str, role: str, size: int):
    """Build a PIL RGBA image: colored disc + initials in white."""
    from PIL import Image, ImageDraw, ImageFont

    bg = _pick_color(name, role)
    # Darker ring for a small border
    ring = tuple(max(0, c - 40) for c in bg)
    initials = _initials(name)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer soft disc
    draw.ellipse((2, 2, size - 2, size - 2), fill=bg + (255,), outline=ring + (255,), width=2)

    # Initials — pick a font size that fits
    fs = int(size * (0.48 if len(initials) >= 2 else 0.58))
    font = None
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        try:
            font = ImageFont.truetype(path, fs)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initials, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1]
    # Drop shadow
    draw.text((tx + 1, ty + 1), initials, fill=(0, 0, 0, 160), font=font)
    draw.text((tx, ty), initials, fill=(255, 255, 255, 255), font=font)

    return img


def _load_file_as_avatar(path: str, size: int):
    """Load a user-supplied image (any format PIL reads), crop to square
    (center crop), resize to `size`, and softly round the corners so it
    looks like an avatar rather than a raw thumbnail."""
    from PIL import Image, ImageDraw

    img = Image.open(path).convert("RGBA")
    # Center-crop to square
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((size, size), Image.LANCZOS)

    # Apply circular mask for a disc shape (matches the generated avatars)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask=mask)
    # Thin ring
    ImageDraw.Draw(out).ellipse(
        (1, 1, size - 1, size - 1),
        outline=(40, 45, 55, 255), width=2)
    return out


def get_avatar(name: str, role: str = "master", size: int = 64) -> arcade.Texture:
    """Return an arcade.Texture for a named player.

    `role` is one of "human", "ai", or "master" — it only affects the
    fallback color palette when no image file is found.
    """
    key = f"avatar_{name}_{size}"
    if key in _AVATAR_CACHE:
        return _AVATAR_CACHE[key]

    try:
        os.makedirs(AVATAR_DIR, exist_ok=True)
    except OSError:
        pass

    path = _find_file(name)
    img = None
    if path is not None:
        try:
            img = _load_file_as_avatar(path, size)
        except Exception as e:
            print(f"[avatar] Could not load {path}: {e} — falling back.")
            img = None

    if img is None:
        img = _render_initials_disc(name, role, size)
        # Save the generated disc to disk so it doesn't have to be
        # regenerated next run. Only write if the file is not already
        # there (don't overwrite user photos).
        save_path = os.path.join(AVATAR_DIR, f"{_sanitize(name)}.png")
        if not os.path.isfile(save_path):
            try:
                img.save(save_path, "PNG")
            except OSError as e:
                print(f"[avatar] Could not save {save_path}: {e}")

    tex = arcade.Texture(img, name=key)
    _AVATAR_CACHE[key] = tex
    return tex
