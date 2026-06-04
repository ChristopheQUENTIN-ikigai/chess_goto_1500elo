# Opening Variations PGN Bundle

This folder ships `variations.pgn`, a curated database of famous-game
illustrations for the opening variations declared in
`openings_catalog.py`. The bundle is loaded once at startup by
`variations_pgn.py`, indexed by a non-standard `[VariationSlug "..."]`
header, and surfaced in the UI when the user opens a variation that
has a paired game.

## Why a single bundle file

We considered four options (one PGN per variation; inline strings in
`openings_catalog.py`; promoting these to `master_games.py`; and this
single bundle). The bundle won because:

- It is real PGN format, so any chess GUI (Lichess, ChessBase,
  SCID, Chess.com) can open and verify it.
- One file keeps review focused and avoids filesystem noise from
  many tiny per-variation files.
- The `[VariationSlug "..."]` tag makes the catalog-to-game mapping
  explicit, so the link survives game reordering inside the file.
- Failures are isolated: one bad game prints a console warning and
  is skipped, the rest of the bundle still loads.

## Format

Standard PGN, with three notable conventions:

```pgn
[Event "..."]
[Site "..."]
[Date "YYYY.MM.DD" or "YYYY.??.??"]
[Round "?"]
[White "..."]
[Black "..."]
[Result "1-0" | "0-1" | "1/2-1/2"]
[ECO "..."]
[VariationSlug "italian_evans_gambit"]   ; required: links to catalog
[Truncated "true"]                       ; optional: opening-phase only
[Annotator "v8 catalog"]                 ; optional: provenance hint

1. e4 e5 2. Nf3 Nc6 ... 1-0
```

### Required: `VariationSlug`

The slug **must** match a `Variation.famous_game_slug` value in
`openings_catalog.py`. Mismatches are not errors — the bundle game is
just orphaned and never displayed. Catalog slugs that don't resolve
to a bundle game fall through to the empty-state UI.

Slug conventions: `<opening_slug>_<variation_descriptor>` in
snake_case. Examples already in the bundle:

- `ruy_lopez_berlin`
- `italian_evans_gambit`
- `najdorf_poisoned_pawn`
- `kia_fischer_myagmarsuren`

Slugs are scoped globally across the bundle, not per-opening, so keep
them disambiguating.

### Optional: `Truncated`

Set `[Truncated "true"]` when the move list shows only the opening
phase or first part of the game. The UI labels these explicitly so
users don't expect the full game. The `[Result "..."]` tag should
still reflect the actual game's outcome — the move list just stops
before the final position.

Use truncation honestly:

- **OK**: stopping at move 13 of a 41-move game where the variation's
  thematic structure has clearly emerged. Mark `[Truncated "true"]`.
- **Not OK**: stopping mid-tactic and labeling 1-0, leading the
  reader to believe the position shown is decisive. Either include
  the full game, or stop earlier at a clearly non-decisive position.

### Optional: `Annotator`

Free-form provenance. Useful when the bundle gets contributions from
multiple sources or curators.

## Validation

`variations_pgn._load()` runs at import. For each game it:

1. Parses headers and movetext via python-chess.
2. Walks the mainline, asserting every move is legal.
3. Counts SAN tokens in the raw movetext and compares to parsed
   plies — catches the silent-truncation trap where python-chess
   stops at the first illegal move without raising.
4. Records the `ParsedGame` under its slug. Duplicates print a
   warning; later entries override earlier.

Failures print one line each to the console:

```
[variations_pgn] WARNING: game 'najdorf_english_attack' failed
  validation: illegal move in mainline: e2e5
```

The bundle keeps loading after a failure. Other games remain
available. The UI shows the empty state for the failed slug.

## Adding a game

1. Open `variations.pgn` in any text editor or chess GUI.
2. Append a complete PGN block including a `[VariationSlug "..."]`
   header that matches a `Variation.famous_game_slug` in the catalog.
   (If you're adding a brand-new variation, add the catalog entry
   first.)
3. Save and run `python3 -c "import variations_pgn"` from the
   project root. Console output should report your new game in the
   loaded count and no warnings.
4. If you can verify the move list against a primary source
   (chessgames.com, an authoritative book, or the original
   tournament record), that's strongly preferred over reconstructing
   from memory.

## Removing a game

Delete the PGN block. The catalog reference will surface as
"missing slug" on next startup; remove the `famous_game_slug` line
from the matching `Variation` in `openings_catalog.py` to clean up.

## Why some variations have no game

Of the 54 variations in v8, 33 ship without a paired famous game.
This is intentional. We hold to a hard rule: only ship PGNs whose
exact move sequence we can verify against a primary source. The v7
ship notes record the cost of breaking this rule — an early v7
experiment had 11 truncated PGNs that looked plausible but failed
the strict validator.

The friendly empty state ("no famous game paired yet — see the
moves above") is honest about the gap and points editors at this
file. Users who want to populate one are invited to drop in a
verified PGN.
