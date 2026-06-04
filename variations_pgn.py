"""
variations_pgn.py — Loader for ./assets/openings/variations.pgn.

Parses the bundled PGN file once at import, indexes every game by its
non-standard `[VariationSlug "..."]` header tag, validates that every
move in every game is legal, and exposes a small public API:

    get_variation_game(slug) -> ParsedGame | None
    list_variation_slugs()   -> list[str]

ParsedGame is a flat container holding the metadata most callers need
(title, white, black, date, result, eco, truncated flag) plus the list
of moves in SAN form. The catalog points at a slug; the UI looks up
the game and feeds its SAN list into the same loader path used for
master games.

If the bundle file is missing, the loader logs once and returns an
empty index — the catalog falls through to the empty-state UI.
If individual games fail validation, those games are skipped and a
per-game warning is printed; other games in the file remain available.

This module deliberately mirrors the validation ethos of
openings_catalog._validate(): warn on console, never crash.
"""
from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class ParsedGame:
    slug: str                       # value of [VariationSlug "..."]
    title: str                      # synthesized from White vs Black, Date
    white: str = ""
    black: str = ""
    event: str = ""
    site: str = ""
    date: str = ""
    result: str = ""
    eco: str = ""
    truncated: bool = False         # value of [Truncated "true"] tag
    moves_san: list = field(default_factory=list)


# Module-level state, populated by _load() on import.
VARIATION_GAMES: dict = {}   # slug -> ParsedGame
_LOADED: bool = False


def _bundle_path() -> str:
    """Return absolute path to the bundled variations.pgn next to
    this module, under ./assets/openings/. Independent of CWD."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "assets", "openings", "variations.pgn")


def _load() -> None:
    """Parse and index the bundle. Idempotent — safe to call again."""
    global _LOADED, VARIATION_GAMES
    if _LOADED:
        return
    _LOADED = True
    VARIATION_GAMES = {}

    path = _bundle_path()
    if not os.path.isfile(path):
        # Not an error — feature simply ships without bundled games.
        # The catalog will surface empty-state UI for variation slugs
        # that fail to resolve.
        print(f"[variations_pgn] No bundle found at {path}; "
              "variation games unavailable.")
        return

    try:
        import chess
        import chess.pgn
    except ImportError:
        print("[variations_pgn] python-chess not installed; "
              "variation games unavailable.")
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"[variations_pgn] Failed to read {path}: {e}")
        return

    import io
    import re
    stream = io.StringIO(text)
    count_ok = 0
    count_fail = 0

    # We need the raw movetext per game to detect silent truncation,
    # since python-chess truncates the mainline on the first illegal
    # move without raising. The simplest reliable approach: split the
    # file on blank-line-then-tag-bracket-then-blank-line boundaries
    # and pair each headers-block with its movetext block. Easier:
    # walk the original text and read each game's PGN substring.

    # Split into game blocks by [Event header lines.
    # Each block is "headers\n\nmovetext".
    raw_blocks = []
    current_lines = []
    for line in text.splitlines(keepends=True):
        if line.startswith("[Event ") and current_lines:
            raw_blocks.append("".join(current_lines))
            current_lines = [line]
        elif line.startswith(";") and not current_lines:
            # comment-only preamble before the first [Event
            continue
        else:
            current_lines.append(line)
    if current_lines:
        raw_blocks.append("".join(current_lines))

    for block in raw_blocks:
        if "[Event " not in block:
            continue
        try:
            game = chess.pgn.read_game(io.StringIO(block))
        except Exception as e:
            count_fail += 1
            print(f"[variations_pgn] Parse error in block: {e}")
            continue
        if game is None:
            continue

        slug = game.headers.get("VariationSlug", "").strip()
        if not slug:
            continue

        # Walk the mainline, asserting every move is legal.
        try:
            board = game.board()
            san_list = []
            parsed_plies = 0
            for mv in game.mainline_moves():
                if mv not in board.legal_moves:
                    raise ValueError(f"illegal move in mainline: {mv}")
                san_list.append(board.san(mv))
                board.push(mv)
                parsed_plies += 1

            # Truncation detection: count SAN tokens in the raw
            # movetext and compare to parsed plies. python-chess
            # silently truncates on illegal moves; the v7 catalog
            # validator caught this same trap.
            movetext = block.split("\n\n", 1)[-1] if "\n\n" in block else ""
            movetext = re.sub(r"\{[^}]*\}", " ", movetext)
            movetext = re.sub(r";[^\n]*", " ", movetext)
            tokens = []
            for tok in movetext.split():
                if re.match(r"^\d+\.+$", tok):
                    continue
                if tok in ("1-0", "0-1", "1/2-1/2", "*"):
                    continue
                if re.match(r"^\$\d+$", tok):
                    continue
                tokens.append(tok)
            if parsed_plies < len(tokens):
                raise ValueError(
                    f"truncated: parsed {parsed_plies} of "
                    f"{len(tokens)} declared moves — illegal move "
                    f"somewhere after ply {parsed_plies}")
        except Exception as e:
            count_fail += 1
            print(f"[variations_pgn] WARNING: game {slug!r} failed "
                  f"validation: {e}")
            continue

        if slug in VARIATION_GAMES:
            print(f"[variations_pgn] WARNING: duplicate slug "
                  f"{slug!r}; later entry overrides earlier.")

        white = game.headers.get("White", "?")
        black = game.headers.get("Black", "?")
        date = game.headers.get("Date", "????.??.??")
        # Synthesize a display title: "White vs Black, Year"
        year = date.split(".")[0] if date else ""
        title = f"{white} vs {black}"
        if year and year != "????":
            title += f", {year}"

        truncated = (
            game.headers.get("Truncated", "").strip().lower() == "true")

        VARIATION_GAMES[slug] = ParsedGame(
            slug=slug,
            title=title,
            white=white,
            black=black,
            event=game.headers.get("Event", ""),
            site=game.headers.get("Site", ""),
            date=date,
            result=game.headers.get("Result", "*"),
            eco=game.headers.get("ECO", ""),
            truncated=truncated,
            moves_san=san_list,
        )
        count_ok += 1

    print(f"[variations_pgn] Loaded {count_ok} games, "
          f"{count_fail} failed.")


def get_variation_game(slug: str) -> Optional[ParsedGame]:
    """Return the ParsedGame for a slug, or None if not in the bundle.
    Triggers a lazy load on first call."""
    if not _LOADED:
        _load()
    return VARIATION_GAMES.get(slug)


def list_variation_slugs() -> list:
    """Return all known slugs in the bundle, in load order. Useful for
    debugging / catalog-coverage reports."""
    if not _LOADED:
        _load()
    return list(VARIATION_GAMES.keys())


# Eager load at import — same pattern as openings_catalog._validate().
# Console messages surface immediately; UI never blocks on load.
_load()
