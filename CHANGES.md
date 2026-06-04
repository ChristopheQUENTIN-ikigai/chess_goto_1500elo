# CHANGES — Chess project

This file records the per-version rework history, newest first.

---

# v12 — "Reassess Your Chess Through Imbalances" tutorial (64 lessons)

Version 12 adds a new splash-menu entry, **Reassess Your Chess Through
Imbalances**, that opens a Silman-inspired positional tutorial. The
tutorial is organized around the nine major parts of Jeremy Silman's
*How to Reassess Your Chess, 4th Edition* (The Concept of Imbalances,
Minor Pieces, Rooks, Psychological Meanderings, Target Consciousness,
Statics vs. Dynamics, Space, Passed Pawns, Other Imbalances) and
contains 64 lessons across them — matching the chapter count in the
referenced Lichess study at
[lichess.org/study/6pxT9XFt](https://lichess.org/study/6pxT9XFt).

Each lesson has a key-idea paragraph, a numbered plan list, and (for
9 of the 64) an illustrative FEN position that renders on a mini-board
inside the detail view. An **"Open on main board"** button drops the
position into the engine for hands-on study, hint queries, or
sparring against the AI.

All lesson prose, plans, and position selections are original
write-ups in our own words — not extracted from Silman's text or
the Lichess study annotations. The Silman 4th-edition table of
contents (book parts) is treated as factual reference, since chapter
titles are not themselves copyrightable.

Added: **`imbalances_tutorial.py`** (new module). Modified:
**`main.py`** (new app states, new menu button, navigation
plumbing). No new asset folders.

| # | Request | Status |
|---|---------|--------|
| 1 | Add a splash-menu button labeled "Reassess Your Chess Through Imbalances" that opens a Silman-inspired tutorial drawing on the 64-chapter Lichess study at `lichess.org/study/6pxT9XFt/9sdHIt6c` | done — new module `imbalances_tutorial.py` exposes `LESSONS` (64 dataclass-typed `Lesson` entries), `PARTS` (the nine book parts), and `PART_DESCRIPTIONS` (one-paragraph blurb per part). Splash menu in `_draw_menu` now lists the new entry between `Master Games` and `White Openings`, with subtitle "Silman-inspired positional tutorial in 64 lessons". Click handler in `_handle_menu_click` dispatches `action == "imbalances"` → resets `_imbalance_part_i` / `_imbalance_scroll` and transitions to `app_state = "imbalances"`. Menu button width bumped 320 → 360 px to fit the longer label without truncation. |
| 2 | Browser screen for the tutorial | done — `_draw_imbalances_browser` renders a two-pane layout: nine book-part rows on the left (active part highlighted in steel-blue), and the lessons of the active part on the right (one row per lesson, scrollable when more than fit). Each lesson row shows its index, title, key-idea preview line, and (when the lesson has a FEN attached) a small `♔ board` indicator at the right edge so users can spot interactive lessons at a glance. Hit-test rects are tracked per pane (`_imbalance_part_rects`, `_imbalance_lesson_rects`) and consumed by `_handle_imbalances_click`. Keyboard navigation: ↑↓ cycles parts; PgUp/PgDn/Home/End scrolls the right pane; mouse wheel also scrolls it. |
| 3 | Lesson detail screen | done — `_draw_imbalance_lesson` shows the part label, lesson title, key-idea paragraph (word-wrapped via a new `_wrap_text` static helper), and a numbered plan list. When the lesson has a FEN, a mini-board renders in the right column (uses the existing `_draw_mini_board` from the satellite view) with whose-turn label, a captioned note, and an `Open on main board` button. The button reuses `_load_from_fen` so the eval tracker, animator, and info panel update identically to a paste-FEN action; then `app_state` flips to `"game"` for play. Defensive: missing slug or invalid FEN show a graceful fallback. |
| 4 | Navigation integration | done — `on_key_press` recognizes `"imbalances"` and `"imbalance_lesson"` as non-game states so ESC/Backspace fall through the existing back-one-level ladder; `_navigate_back_one_level` extended so `imbalance_lesson → imbalances → menu`. `on_draw` and `on_mouse_press` dispatch tables both got new branches for the two states. Mouse-wheel scroll in `on_mouse_scroll` follows the same wheel-up = move-toward-top convention as the masters browser. |
| 5 | Lesson content — 64 lessons covering all imbalance categories | done — distribution across the nine book parts: Concept of Imbalances (6), Minor Pieces (8), Rooks (6), Psychological Meanderings (7), Target Consciousness (7), Statics vs. Dynamics (6), Space (6), Passed Pawns (8), Other Imbalances (10). Each `Lesson` carries `slug`, `part`, `title`, `key_idea`, `plan` (list of short strings), and optional `fen` + `fen_note`. All key-idea text is original prose written for this project; the Silman book and the Lichess study were used only as a structural reference for which topics to cover, not as a source of copyable text. |
| 6 | Illustrative positions on the boards | done — 9 lessons carry validated FEN positions covering classical motifs that exist in many chess sources: knight outpost on e5 (Italian-game position), good-vs-bad bishop endgame, isolated queen pawn middlegame, rook on the 7th endgame, half-open c-file, knight blockading a passed pawn, exchange-QGD minority attack structure, closed-center knight-vs-bishop, and a king-and-pawn passer endgame. All FENs are validated by `chess.Board.is_valid()` in the smoke test. |

## v12 module — `imbalances_tutorial.py`

The module is intentionally a flat data module — no Window
dependencies, no Arcade imports, no I/O. This mirrors how
`master_games.py` and `openings_catalog.py` are structured: pure
Python dataclasses plus a couple of lookup helpers
(`lessons_for_part(part)`, `find_lesson(slug)`, `lesson_count()`).
Means the tutorial content can be edited without restarting the
render layer, and the data is unit-testable from a plain `python3`
without an active display.

The 64-lesson count is deliberate — it matches the chapter count of
the Lichess study the user pointed us at. The 9-part split matches
Silman's 4th-edition table of contents as cited in published reviews
(e.g. KairavAcademy's review on chess.com). We did not copy any
annotation text from either source; only the high-level structural
outline.

## v12 main.py — state and methods added

New `__init__` fields:

```
self._imbalance_part_i: int = 0
self._imbalance_scroll: int = 0
self._imbalance_lesson_slug: str = ""
self._imbalance_part_rects: list = []
self._imbalance_lesson_rects: list = []
self._imbalance_open_btn_rect: tuple = ()
```

New methods on `ChessGame`:

- `_draw_imbalances_browser` — two-pane browser screen.
- `_handle_imbalances_click` — left-pane part-switch, right-pane
  lesson-open.
- `_draw_imbalance_lesson` — lesson detail page with optional
  mini-board.
- `_handle_imbalance_lesson_click` — "Open on main board" button.
- `_wrap_text` — static greedy word-wrap for prose blocks. Made
  static because it doesn't read or mutate any instance state.

## v12 — App-state additions

Two new values for `app_state`:

- `"imbalances"` — the browser screen (parts left, lessons right).
- `"imbalance_lesson"` — single-lesson detail page.

Both fall under the existing "non-game state" branch of
`on_key_press` so ESC/Backspace navigation Just Works without
adding any new key handling.

## v12 — Smoke test

A new `smoke_test.py` (kept in the repo for future regression
testing) exercises every new code path under Xvfb:

1. Constructs the `ChessGame` window.
2. Renders the splash menu, asserts the `imbalances` button rect is
   in `_menu_rects`.
3. Clicks the new button and asserts state transition to
   `"imbalances"`.
4. Renders the browser at part 0, asserts 9 part-rects + non-zero
   lesson-rects.
5. Walks through every part (0–8), exercising the scroll-clamp
   branch and the "no lessons fit" defensive paths.
6. Opens a FEN-bearing lesson, asserts `_imbalance_open_btn_rect`
   is populated.
7. Clicks the "Open on main board" button, asserts state
   transition to `"game"` and that `_load_from_fen` was called
   (FEN visible in stdout).
8. Opens a non-FEN lesson, asserts `_imbalance_open_btn_rect ==
   ()`.
9. Walks ESC navigation back through both new states to the menu.
10. Renders every one of the 9 FEN-bearing lessons to validate the
    mini-board path with each position.

All steps pass. Run with `xvfb-run -a python3 smoke_test.py`.

---

# v11 — Avatar sprite-aliasing fix, replay key '9', expanded openings library

Version 11 fixes the master-games avatar rendering bug (the same kind
of sprite-aliasing bug as v10's pawn fix, applied to avatars this
time), reworks the master-games row layout so the featured player's
photo sits next to their name tag, adds a keyboard `9` shortcut to
jump to the final ply of a loaded replay (mirroring `0` for rewind),
updates the in-game help (`H`) to document every keyboard mapping,
and adds 14 new master games so every opening in the catalog now has
a famous illustrative game — modeled on the existing Ruy Lopez entry.

Modified: **`main.py`**, **`master_games.py`**, **`openings_catalog.py`**.
No new modules, no new asset folders. (Avatar files for new players
auto-generate as initials discs on first launch.)

| # | Request | Status |
|---|---------|--------|
| 1 | Some avatars don't render — `White` / `Black` text shows through where the photo should be (e.g. Carlsen vs Anand row) | done — root cause: the avatar sprite cache in `_get_avatar_sprite` was keyed by `(name, role, size)`. When the same player appeared in two rows (Carlsen as White in two games, Anand in two), both rows received the *same* `arcade.Sprite` object, and only the last row's `sp.position = …` assignment in iteration order survived — leaving the earlier row's avatar invisible with just the "White" / "Black" label visible underneath. Identical pattern to v10's pawn fix. Fixed by re-keying the cache per **slot** (`"masters_row7_featured"`, `"masters_row7_opponent"`, plus `"ingame_left"` / `"ingame_right"`) so every visible avatar cell owns its own Sprite. The texture-level cache in `avatar_gen` is unchanged — only the lightweight Sprite wrappers multiply, and slot-keyed sprites swap textures in place when the list scrolls. |
| 2 | Avatar name and picture mismatch — Firouzja face appears next to "Javokhir Sindarov" because the player tag is left-aligned but the *White* avatar is also on the left | done — the master-games row layout now puts the **featured player** (`game.player`) on the left, immediately next to their highlighted name tag, and the **opponent** on the right. The small label under each avatar (`White` / `Black`) still reflects which colour each one actually played, so the role information is preserved. Rows where the player tag doesn't cleanly match either side (e.g. `Study Position vs Study Position`) fall back to the previous White-left / Black-right layout. |
| 3 | Add key `9` to jump to the last ply, mirroring key `0` (rewind to start) | done — `KEY_9` and `NUM_9` in `on_key_press` now set `ply_index = len(self.loaded_moves)` and call `_rebuild_from_ply_index()`. Shows a toast `"Jumped to final position — ply N/N"` (or `"Already at final ply"` if pressed twice). No-op when no replay is loaded, matching the behaviour of `0`. |
| 4 | Update help overlay (`H`) to document every keyboard mapping | done — the help text now lists: in-game keys (`ESC`, `F`, `H`, `N`, `U`, `I`, `O`), replay navigation (scroll wheel + `0` + `9`), master-games list scrolling (wheel / ↑↓ / PgUp / PgDn / Home / End / ESC), and variations-satellite view (← / → / Home / 0 / wheel). Font size and line spacing tightened from 12px/22px to 11px/18px so the longer list still fits inside the overlay panel on standard window sizes. |
| 5 | Some openings still don't have a famous game illustration — apply the Ruy Lopez model (which has Karpov vs Unzicker linked) to every other entry | done — 14 new `MasterGame` entries added, 3 existing entries linked. Every CatalogEntry on both sides now resolves to a real master game. See breakdown below. |

## v11 fix detail — avatar sprite-aliasing

This is the exact same class of bug as the v10 pawn-render fix, applied
to the master-games browser this time. The avatar cache used a key of
`f"{name}|{role}|{size}"` — so for example `"Magnus Carlsen|master|44"`
mapped to a single `arcade.Sprite`. The master-games scroll list
contains two games where Carlsen is White (`carlsen_vs_anand_2013_g5`
and `carlsen_vs_karjakin_2016_tb4`) on adjacent rows. When the render
loop assigned `white_sprite.position = (left_av_cx, av_cy_row7)` and
then `white_sprite.position = (left_av_cx, av_cy_row8)`, both calls
hit the *same* Sprite — and only the second position survived to the
SpriteList.draw() call. The Carlsen-vs-Anand row then drew with no
avatar at the left position, exposing the `"White"` placeholder label
that lives underneath. Same story for Viswanathan Anand (Black in
row 7, also the featured player tag in row 9).

Fix: a new optional `slot_key` parameter on `_get_avatar_sprite`.
Master-games rows pass `slot_key=f"masters_row{i}_featured"` and
`slot_key=f"masters_row{i}_opponent"`; the in-game cards pass
`slot_key="ingame_left"` / `"ingame_right"`. Each unique slot owns
its own Sprite; the texture is fetched from the upstream cache and
swapped onto the Sprite in place if the row's player changes when the
list scrolls. Callers that don't pass a slot_key still get the
old name-keyed behaviour (single Sprite per name), which is safe
because every remaining caller draws a unique avatar once per frame.

## v11 fix detail — featured player on the left

Previously the row layout was always White-left / Black-right, with
the featured player's name tag rendered immediately to the right of
the white-avatar column. That works fine when the featured player is
White (Tal, Capablanca, Karpov, Fischer-vs-Spassky, Kasparov, Carlsen
games, Caruana, MVL-via-Magnus, Nakamura, Polgar, Ashley, Carlsson,
Wei Yi) — but for Black-featured games the user sees the **opponent's**
photo next to the **featured player's** name, which is confusing:
"Javokhir Sindarov" labelled next to Firouzja's face, "Yagiz Kaan
Erdoğmuş" next to Mittal's, "Viswanathan Anand (Aronian-Anand
Immortal)" next to Aronian's, and so on.

The new layout puts whoever is `game.player` on the left, regardless
of whether they played White or Black. The "White" / "Black" label
under each avatar disambiguates which colour they played. The
opponent's photo moves to the right column. Existing logic that
checks for `Study Position` (Silman's didactic entries, where neither
side is the featured player in a meaningful sense) falls through to
the original White-left / Black-right layout — those rows don't have
this confusion because the player tag is also `"Jeremy Silman"`, not
a player on either side of the board.

## v11 detail — new master games (14) and linkage (3 existing)

The Ruy Lopez catalog entry was already linked to `karpov_vs_unzicker_1974`
via a `FamousGame(master_game_id=…)` entry. Every other CatalogEntry
that had `famous_games=[]` has been wired the same way. Three openings
mapped cleanly to existing master games:

| Opening | Existing master game now linked |
|---|---|
| Modern Defense (B06) | `ashley_vs_weeramantry_1991` |
| King's Indian Defense (E60–E99) | `sindarov_vs_firouzja_2021` |
| Scotch Game (C44–C45) | `carlsson_vs_sokolov_2011` |

The remaining 14 openings needed new master games. Each was added to
`master_games.py` (with full PGN headers and notes) and linked from
`openings_catalog.py`:

| Opening | New master game |
|---|---|
| King's Gambit (C30–C39) | Anderssen vs Kieseritzky 1851 ("The Immortal Game") |
| Italian Game (C50–C59) | Steinitz vs von Bardeleben, Hastings 1895 |
| Vienna Game (C25–C29) | Spielmann vs Flamberg, Mannheim 1914 |
| London System (D02) | Carlsen vs Wojtaszek, Wijk aan Zee 2017 |
| Trompowsky Attack (A45) | Hodgson-style main-line illustration *(theoretical, truncated)* |
| Réti Opening (A04–A09) | Réti vs Capablanca, New York 1924 |
| Bird's Opening (A02–A03) | Bird vs Lasker, simultaneous 1892 |
| Sicilian Najdorf (B90–B99) | Fischer vs Najdorf, Varna Olympiad 1962 |
| French Defense (C00–C19) | Botvinnik vs Capablanca, AVRO 1938 (Ba3!! game) |
| Scandinavian (B01) | Mieses-style classical illustration *(theoretical, truncated)* |
| Alekhine Defense (B02–B05) | Modern Variation main-line illustration *(theoretical, truncated)* |
| Nimzo-Indian (E20–E59) | Spassky vs Fischer, World Ch 1972 Game 5 |
| Budapest Gambit (A51–A52) | Rubinstein vs Vidmar, Berlin 1918 (Nd3# miniature) |
| Benko Gambit (A57–A59) | Fianchetto Accepted main-line illustration *(theoretical, truncated)* |

The four entries marked *(theoretical, truncated)* are opening-line
illustrations chosen where I couldn't verify a complete historical
score to the level of accuracy this catalog requires. The `truncated`
flag in the `MasterGame` dataclass surfaces this honestly to the user
("partial — legal moves only" in the master-games browser). All 14
move lists were independently validated against `python-chess` before
commit and parse to their full declared length. Total master games
go from 20 to 34.

---

# v10 — Pawn render fix, gender overlays, expanded masters & variations

Version 10 fixes the v9 pawn-rendering bug, adds an optional ♂/♀
gender-overlay landmark for kingside/queenside pieces, makes the
master-games browser scrollable and adds a featured Anand entry, and
extends every opening's variation count from 3 to 4 (108 variations
total, all UCI-validated).

Modified: **`main.py`**, **`master_games.py`**, **`openings_catalog.py`**,
**`avatars_links.py`**. No new modules, no new asset folders.

| # | Request | Status |
|---|---------|--------|
| 1 | Fix the bug where some pawns are visible only when clicked | done — root cause identified in `_get_piece_sprite`: the cache was keyed by `(theme, symbol, side, size)`, so all 4 white kingside pawns shared a single `arcade.Sprite` object, and only the last `sp.position = …` assignment in iteration order won. Fixed by re-keying the cache per slot (`"sq:0"` … `"sq:63"`, plus `"drag"` for the drag ghost) so every square gets its own sprite. Texture-level cache in `piece_textures.py` is unchanged — only the lightweight Sprite wrappers are duplicated. |
| 2 | ♂ / ♀ gender overlay toggle for kingside/queenside | done — Settings page row 4 toggles the default; pressing **O** in-game flips it live with a toast. Drawn as a small corner glyph after the sprite list (♂ kingside / ♀ queenside) on every flanked piece (R/B/N/P). King and queen never get a glyph (unique pieces, no flank). The drag ghost gets its own glyph that follows the cursor. |
| 3 | Add Maurice Ashley, Judit Polgár, Viswanathan Anand to master games | done — Polgár (`polgar_vs_kasparov_2002`) and Ashley (`ashley_vs_weeramantry_1991`) were already in `master_games.py`; they just fell below the visible cutoff in the previous build. Added a new featured-Anand entry: `aronian_vs_anand_2013_immortal` (Anand's Immortal, Tata Steel R4 2013, 46 plies, Semi-Slav Meran). |
| 4 | Make all 20 master-game entries reachable | done — `_draw_masters_browser` now supports vertical scrolling. Mouse wheel = ±1 row; ↑/↓ = ±1 row; PgUp/PgDn = ±8; Home/End = top/bottom. Scrollbar + "Showing X–Y of Z" counter rendered when the list overflows. Scroll resets to the top when the user opens the list from the menu. |
| 5 | One more variation per opening (3 → 4) | done — 27 of 27 entries now ship 4 variations (108 total). Each new variation has been UCI-validated against `python-chess` from the starting position. |

## v10 fix detail — pawn rendering bug

The v9 sprite cache in `_get_piece_sprite` was keyed by
`(theme, symbol, side, size)`. For the eight white pawns this meant:
four kingside pawns (e2/f2/g2/h2) all received the *same* Sprite
object, and four queenside pawns (a2/b2/c2/d2) all received another
*single* Sprite. Each frame, the render loop iterated `chess.SQUARES`
(a1, b1, …, h1, a2, …) and called `sp.position = (cx, cy)` for every
piece — but with all four kingside pawns sharing one sprite, only the
last position assignment stuck. That's why on a fresh board only h2
(last kingside pawn iterated) and d2 (last queenside) rendered, with
the other six invisible until clicked — because the drag-ghost call
uses a slightly larger `size`, that's a *different* cache key, which
allocated a fresh Sprite at the cursor.

The fix re-keys the sprite cache by **slot** rather than by texture
parameters. Each of the 64 board squares now owns its own Sprite,
with a separate `"drag"` slot for the lifted-piece ghost. The texture
cache in `piece_textures.get_piece_texture()` is unchanged, so all
eight pawn sprites still share a single GPU texture — only the very
lightweight per-Sprite vertex buffers are duplicated. The texture is
re-bound on the existing Sprite object whenever a square's piece
changes (capture, promotion, theme switch), so the cache stays correct
across all in-game state transitions.

## v10 fix detail — gender overlay

The v9 piece-set design distinguished kingside vs queenside pieces via
two slightly different placeholder PNGs (`{piece}_k.png` vs
`{piece}_q.png`) plus a small gold/silver corner pip on the
auto-generated placeholders. That distinction is too subtle once a
user drops in their own custom artwork (the pip lives only on the
generated placeholders). v10 adds a second, asset-independent
landmark: a small ♂ / ♀ glyph rendered as a post-pass on top of the
sprite list. Off by default, persisted in
`~/.config/chess-v9/settings.json` as `gender_overlay`, togglable from
Settings or with the **O** key during play.

The glyph mapping is:
* ♂ (U+2642) — kingside (files e/f/g/h, gold colour)
* ♀ (U+2640) — queenside (files a/b/c/d, silver colour)

Same colour convention as the existing flank pip on placeholders, so
the two cues reinforce each other when both are visible. Rules:
* Only flanked pieces (R/B/N/P) get a glyph — kings and queens are
  unique pieces with no flank distinction.
* Squares being animated (sliding) skip the overlay; the glyph
  reappears on the destination square once the animation lands.
* The drag ghost gets its own glyph that follows the cursor.
* `_draw_gender_overlay` is a single arcade `draw_text` pass — no
  new sprite list, no extra GPU bind.

## v10 fix detail — master-games scrolling

20 entries × 62 px row height ≈ 1240 px of vertical content; the v9
browser cropped at the window bottom (`if ry < 40: break`) and showed
only ~10 entries. v10 adds:
* `_masters_scroll: int` — row offset, clamped at render time so we
  don't need to know `rows_fit` from input handlers.
* Mouse-wheel scrolling: `on_mouse_scroll` dispatches to the masters
  list when `app_state == "masters"`, ±1 row per notch.
* Keyboard scrolling: ↑/↓ = ±1 row, PgUp/PgDn = ±8, Home/End = ends.
* Right-edge scrollbar + "Showing X–Y of Z" counter, drawn only when
  the list overflows.
* Scroll resets to 0 when the user enters the masters page from the
  menu, so they always start at the top.

---

# v9 — Themed pieces, board materials, expanded variations & masters

Version 9 adds a player-facing **Settings** page to the splash menu
covering piece-texture themes and board-material looks; expands every
opening's variation count from 2 to 3 (81 variations total, all
UCI-validated); and adds ten new featured masters to the master-games
library — the six from the original v9 plan (Caruana, Vachier-Lagrave,
Firouzja, Erdoğmuş, Nakamura, Polgár) plus four user-requested
additions: Maurice Ashley, Javokhir Sindarov, Pontus Carlsson, and
Wei Yi.

New modules: **`piece_textures.py`**, **`board_materials.py`**.
New assets: **`./assets/textures/pieces/{theme}/*.png`** — auto-
generated placeholder PNGs the user replaces with their own artwork
(6 themes × 20 files = 120 PNGs).
Modified: **`openings_catalog.py`**, **`master_games.py`**, **`main.py`**.

| # | Request | Status |
|---|---------|--------|
| 1 | Add 1 more variation per opening (2 → 3) | done — 27 of 27 entries now ship 3 variations; catalog validator reports 81/81 legal |
| 2 | Splash-menu Settings: piece-texture style (classical / fancy) | done — Settings page accessible from menu, radio between Classical and Fancy |
| 3 | Fancy ambiances: roman, heroic fantasy, sci-fi, steampunk, cyberpunk | done — all five sub-themes selectable when style = Fancy |
| 4 | Auto-generate placeholder PNGs in `./assets/textures/pieces/` | done — 6 themes × 20 files = 120 PNGs created at startup via `ensure_all_placeholders()` |
| 5 | Slightly distinguish kingside vs queenside pieces | done — gold pip top-right (kingside), silver pip top-left (queenside) on R/B/N/P; K/Q unique so no flank pip |
| 6 | Board materials: wood, marble, carbon, bone, neon plasma | done — all five selectable in Settings, live-swappable on the main board and satellite view |
| 7 | Master Games: original v9 set (Caruana, MVL, Firouzja, Erdoğmuş, Nakamura, Polgár) | done — all six added to `master_games.py`; Erdoğmuş is the "Turkish Immortal" mate, Polgár is her famous 2002 win over Kasparov |
| 8 | Master Games: user-added (Ashley, Sindarov, Carlsson, Wei Yi) | done — Ashley vs Weeramantry 1991 (queen sac), Firouzja vs Sindarov 2021 World Cup (knockout), Carlsson vs Sokolov 2011 (queen sac, ECT), Wei Yi vs Bruzon 2015 ('21st-century Immortal') |
| 9 | Splash-menu wiring (Settings page, render swap, persistence) | done — `_draw_settings`, `_handle_settings_click`, render swap to `piece_textures.get_piece_texture()` and `board_materials.get_material()`, persistence at `~/.config/chess-v9/settings.json` |

## 1. `piece_textures.py` — placeholder asset manager

Mirrors the resolution pattern of `avatar_gen.py`:

1. In-memory cache (keyed by symbol + theme + side_hint + size).
2. File at `./assets/textures/pieces/{theme}/{filename}.png`, loaded
   via PIL → arcade.Texture.
3. Auto-generated placeholder PNG, written to disk on first run so
   the user has a real file to overwrite. User-supplied files are
   never overwritten.

### Filename convention

```
w{P}_k.png     white piece, kingside variant
w{P}_q.png     white piece, queenside variant
b{P}_k.png     black piece, kingside variant
b{P}_q.png     black piece, queenside variant
```

`{P}` ∈ {K, Q, R, B, N, P}. Kings and queens write only `_k.png`
(unique pieces, no flank distinction). Rooks, bishops, knights and
pawns ship both `_k` and `_q`.

### Themes shipped (6)

```
classical    — traditional set
roman        — ancient roman / classical (ivory + bronze + gold)
fantasy      — heroic fantasy (silver moonsteel + dark sorcerer purple + ruby)
scifi        — sci-fi futurist (chrome cyan + graphite + holo-blue)
steampunk    — polished brass + oiled iron + copper rivet
cyberpunk    — magenta neon outline on dark, cyan accent
```

Each theme folder gets 20 PNGs (6 white pieces + 6 black, with R/B/N/P
having two flank variants and K/Q a single image: 4×2 + 2 = 10 per
colour × 2 colours = 20).

### Kingside vs queenside distinction

Visible even with placeholder art: a small gold pip in the upper-right
corner = kingside; a small silver pip in the upper-left = queenside.
Mnemonic: kingside pieces start on the right (h-file) for White, so
the pip is on the right.

The flank itself is computed by `flank_for_square(sq)` — files e..h
are kingside, files a..d queenside. This is a best-effort guess based
on current file (a knight that started on b1 and is now on g3 will
read as kingside) — for placeholder graphics it's fine; the user is
going to replace these PNGs with their own art anyway.

### Public API

```python
get_piece_texture(symbol, theme, side_hint, size) -> arcade.Texture
available_themes()             -> list[str]
theme_label(theme)             -> str
ensure_placeholders(theme)     -> None
ensure_all_placeholders()      -> None
clear_cache()                  -> None
flank_for_square(sq)           -> "k" | "q"
```

## 2. `board_materials.py` — board palette presets

Five named materials, each a (light_square, dark_square, border, bg)
tuple. The renderer in `main.py` reads these every frame and draws
with them — no PNG textures, no asset reload, hot-swappable in real
time.

```
classical_wood   — buff & brown (default — current behaviour)
marble           — ivory + blue-grey
carbon           — graphite + near-black
skull_bone       — bleached bone + weathered shadow
neon_plasma      — deep purple + near-black with magenta neon frame
```

Tuned so both white and black pieces stay readable on both square
colours (no light-on-light or dark-on-dark).

## 3. Variation expansion (27 of 27 done — 81 variations total)

Each `CatalogEntry` now carries 3 variations instead of 2. The full
list:

| Side | Entry | Three variations |
|------|-------|------------------|
| W | Ruy Lopez | Closed · Berlin · Marshall Attack |
| W | Italian Game | Giuoco Piano · Evans Gambit · Two Knights |
| W | Scotch Game | Mieses · Scotch Gambit · Göring Gambit |
| W | King's Gambit | Accepted · Declined · Falkbeer Counter-Gambit |
| W | Vienna Game | Vienna Gambit · Bishop · Frankenstein-Dracula |
| W | Queen's Gambit | Accepted · Exchange · Catalan |
| W | London System | Classical · Jobava · vs King's Indian |
| W | Trompowsky | Main Line · 2...Ne4 · Torre-like 3.Bxf6 |
| W | English | Symmetrical · Reversed Sicilian · Four Knights |
| W | Réti | Main Line · King's Indian Attack · Réti Advance |
| W | Bird | From's Gambit · Leningrad · Classical (e3) |
| B | Sicilian | Open · Alapin · Dragon |
| B | Sicilian Najdorf | English Attack · 6.Bg5 · Fianchetto (6.g3) |
| B | French | Winawer · Tarrasch · Classical (3.Nc3 Nf6) |
| B | Caro-Kann | Classical · Advance · Exchange |
| B | Scandinavian | 3...Qa5 · 3...Qd6 · Icelandic Gambit |
| B | Alekhine | Four Pawns · Modern · Exchange |
| B | Pirc | Austrian · 150 Attack · Classical (Two Knights) |
| B | Modern | Standard · Averbakh · Three Pawns Attack |
| B | QGD | Orthodox · Tartakower · Lasker |
| B | Slav | Semi-Slav Meran · Main 4...dxc4 · Exchange |
| B | King's Indian | Mar del Plata · Sämisch · Classical |
| B | Nimzo-Indian | Rubinstein · Classical (4.Qc2) · Sämisch (4.a3) |
| B | Grünfeld | Exchange · Russian · Fianchetto |
| B | Dutch | Stonewall · Leningrad · Classical |
| B | Budapest | Main 3...Ng4 · Fajarowicz · Alekhine (4.e4) |
| B | Benko | Accepted (5.bxa6) · Declined (6.b6) · Modern Decline (4.Nf3) |

The same UCI-validation pass at module import (`openings_catalog._validate`)
applies — illegal new variations would print a warning and be
silently skipped by the UI. All 81 variations pass validation.

## 4. Master games — 10 new entries

| Player | Game | Status |
|--------|------|--------|
| Fabiano Caruana | vs Aronian, Sinquefield Cup 2014 R4 | full (99 plies) |
| Maxime Vachier-Lagrave | Carlsen vs MVL, Sinquefield Cup 2017 R4 | truncated (84 plies — source PGN truncates) |
| Alireza Firouzja | Carlsen vs Firouzja, Tata Steel 2021 R1 | full (79 plies) |
| Yağız Kaan Erdoğmuş | Mittal vs Erdoğmuş, Grand Swiss 2025 ('Turkish Immortal') | full mate (84 plies) |
| Hikaru Nakamura | Nakamura vs Caruana, US Ch. 2015 | truncated (10 plies — opening only, full game record uncertain) |
| Judit Polgár | Polgár vs Kasparov, Russia vs the World 2002 | full (84 plies) |
| Maurice Ashley | Ashley vs Weeramantry, NY Open 1991 | full (59 plies) |
| Javokhir Sindarov | Firouzja vs Sindarov, World Cup 2021 (rapid) | full (98 plies) |
| Pontus Carlsson | Carlsson vs Sokolov, ECT 2011 | full (93 plies, queen sac) |
| Wei Yi | Wei Yi vs Bruzon, Hainan Danzhou 2015 ('21st-century Immortal') | full mate (79 plies) |

The two truncated entries are flagged with `truncated=True` so the
existing replay UI shows the partial-game banner; the existing
`_self_validate` pass enforces this automatically by trimming any
SAN move that fails to push onto the board.

## 5. Splash-menu wiring (`main.py`)

1. New menu state `"settings"` reachable from a `Settings` button
   added to `_draw_menu`'s entry list. Routed in `on_draw`,
   `on_mouse_press`, and `_navigate_back_one_level`.
2. `_draw_settings` page with three rows:
   - **Piece style** — Classical / Fancy radio.
   - **Fancy theme** — Roman / Fantasy / Sci-fi / Steampunk /
     Cyberpunk (only enabled when style = Fancy; greyed out
     otherwise).
   - **Board material** — Wood / Marble / Carbon / Bone / Plasma.
   - Plus a "Back to menu" button at the bottom.
3. Four persisted attributes on `ChessGame`:
   `self.piece_theme: str`, `self.board_material_key: str`,
   `self.piece_style: str`, `self.fancy_theme: str`. Defaults:
   `"classical"`, `"classical_wood"`, `"classical"`, `"roman"` —
   all backward-compatible with v8.
4. Replaced the Unicode-glyph piece-drawing block in `_draw_game`
   (board, drag ghost) and the satellite-view square palette with
   live reads from `piece_textures.get_piece_texture(...)` and
   `board_materials.get_material(...)`. Rendering uses an
   `arcade.SpriteList` cache (`self._piece_sprite_list`,
   `self._piece_sprites`) following the same park-and-position
   pattern as the avatar sprites — sprites are parked off-screen
   each frame, the ones that should appear are positioned, and the
   list draws once per `_draw_game` call.
5. Theme/material changes through the Settings page invalidate the
   piece-texture cache (`piece_textures.clear_cache()`) and the
   sprite cache so the next frame rebuilds with the new artwork.
6. Persistence: `_settings_load` / `_settings_save` use
   `~/.config/chess-v9/settings.json`. Loaded at the end of
   `__init__`; saved on every option click. Missing or corrupt
   files fall back to defaults silently.

The satellite-view mini-board piece glyphs are still rendered as
Unicode at small sizes — sprite-based rendering for the synchronized
multi-board grid would require a separate park-and-position pass per
mini-board and is deferred. The board-material palette swap *is*
applied to the satellite view, so a Settings change is visible there
too.

---


# v8 — Variation training & "satellite view"

Version 8 adds named variations to every opening, replayable famous
games for many of them, and a synchronized multi-board satellite
view for comparing variations of the same opening side by side.

New modules: **`variations_pgn.py`**.
New assets: **`./assets/openings/variations.pgn`**, **`./assets/openings/README.md`**.
Modified: **`openings_catalog.py`**, **`main.py`**.

| # | Request | Status |
|---|---------|--------|
| 1 | Add 2 named variations per opening (Italian → Giuoco Piano + Evans Gambit, etc.) | done |
| 2 | Each variation replayable on the main board | done |
| 3 | Each variation can carry a famous-game illustration | done (21 of 54) |
| 4 | "All variations" satellite grid with synchronized stepping | done |
| 5 | Right-arrow steps every board forward; left-arrow steps back | done |
| 6 | Scroll wheel zooms the satellite grid | done |
| 7 | Standard variation names (Najdorf, Berlin, Tartakower) — no player attribution in the name itself | done |
| 8 | Backspace = universal back-one-level navigation | done |
| 9 | ESC from a variation game returns to the opening detail page | done |

---

## 1. Variation data model

`openings_catalog.py` now declares a `Variation` dataclass alongside
`CatalogEntry` and `FamousGame`. Each catalog entry carries exactly
two variations:

```python
@dataclass
class Variation:
    slug: str               # short id, scoped within parent entry
    name: str               # display name, e.g. "Berlin Defense"
    eco: str                # specific ECO (more precise than parent)
    moves_uci: list         # full defining sequence in UCI
    moves_san: str          # pre-rendered SAN for display
    summary: str            # 1-line idea of THIS variation
    famous_master_id: Optional[str] = None  # → MASTER_GAMES by .id
    famous_game_slug: Optional[str] = None  # → variations.pgn by tag
    moves_valid: bool = True   # set False at import on illegal UCI
```

A variation may carry a famous game by **either** pointing at an
existing `MasterGame` (cheap reuse) **or** at a `[VariationSlug "..."]`
in `variations.pgn` (new bundle). At most one of the two fields is
set; if neither is, the UI shows the friendly empty state.

The validator at the bottom of `openings_catalog.py` was extended
with a UCI legality check — every `Variation.moves_uci` is pushed
onto a fresh `chess.Board()` and any illegal move sets
`moves_valid=False`. The UI silently skips invalid variations.

### Catalog structure on ship

- 11 White openings × 2 variations = 22 White variations
- 16 Black defenses × 2 variations = 32 Black variations
- **Total: 54 variations** (the v7 Evans Gambit standalone entry was
  dropped — see "Notes" below)
- 8 reuse existing `MasterGame` entries for their famous game
- 13 resolve through the new `variations.pgn` bundle
- 33 ship with no famous-game pairing (empty state)

The 33 unpaired variations were the right call. Hand-transcribing
tournament PGNs is exactly the trap v7 documented ("11 truncated
PGNs that looked fine in plain reading but failed the strict
validator"). v8 ships only PGNs that pass the strict validator
*and* could be cross-checked against well-known game records.

## 2. `variations.pgn` bundle (Option 4 in the design discussion)

After exploring four storage options, v8 ships a single bundled
PGN file: `./assets/openings/variations.pgn`. The non-standard tag
`[VariationSlug "..."]` indexes each game to its variation in the
catalog. Why this option won (excerpted from the design notes):

- Real PGN format — opens in any chess GUI for verification or
  copy-out.
- Single file keeps review focused; no filesystem noise from
  many tiny per-variation files.
- Slug tagging keeps the catalog↔game link explicit through
  reorderings.
- Failures isolate: one bad game prints a console warning and is
  skipped, the rest of the bundle still loads.

The v7 author's trap (silent truncation by python-chess on illegal
moves) is caught by the same SAN-token-count check: if the parsed
mainline has fewer plies than the raw movetext has tokens, the game
is rejected. **This caught a real bug in v8 development** — an
early French Winawer entry had an illegal `Rg8` at move 9 that
silently truncated; the validator flagged it and the entry was
dropped to empty state.

`./assets/openings/README.md` documents the bundle format,
slug-tagging convention, validation philosophy, and contributor
workflow. New games can be added by anyone who can drop in a
verified PGN block; the loader handles the rest.

## 3. Loader module: `variations_pgn.py`

New module, ~170 lines. Public surface:

```python
get_variation_game(slug) -> ParsedGame | None
list_variation_slugs() -> list[str]
```

`ParsedGame` is a flat container holding the metadata callers need
(title, white, black, date, result, eco, truncated flag) plus the
full SAN move list. Eager-loaded at import; idempotent if called
repeatedly.

Failure modes (each prints one warning, never crashes):

- Bundle file missing → empty index; UI falls through to empty
  state for every slug.
- python-chess unavailable → empty index; warning.
- Per-game illegal move → game skipped; other games still load.
- Per-game SAN-token mismatch → game skipped (truncation guard).
- Duplicate slug → later entry overrides earlier with a warning.

## 4. Variation replay on the main board (Option A)

Clicking a variation card on the opening-detail page loads the
variation into the main game view at ply 0, where the user can
step forward with the scroll wheel or right arrow — the same
machinery used for master-game replay. Three cases:

1. **Has `famous_master_id`** → load the existing MasterGame.
   This is the canonical full-game replay path.
2. **Has `famous_game_slug`** → resolve via `variations_pgn.get_variation_game`,
   synthesize a `chess.pgn.Game`, route through `_apply_pgn_game`.
   Same end state as case 1 but the source is the bundle.
3. **No pairing** → load just the variation's defining UCI moves
   as a study game ("Sicilian Najdorf — step forward with → or
   scroll wheel"). The user still sees the position evolve;
   the famous-game illustration is just absent.

In all three cases, `_game_return_state = ("opening_detail",)` is
recorded so ESC/Backspace from the loaded game returns to the
opening detail page rather than all the way to the menu.

## 5. Satellite view (`app_state == "variations_satellite"`)

A new top-level state, drawn by `_draw_variations_satellite()`,
that lays out one mini-board per valid variation in a grid. All
boards share a single global ply index — pressing the right arrow
advances every board by one move; left arrow steps every board
back; Home (or `0`) returns all boards to the start position. Each
board independently clamps to its own move list length, so a
4-ply variation and a 16-ply variation in the same grid don't go
out of sync: when the global ply exceeds a variation's length,
that board freezes at its final position while the others keep
advancing.

### Layout

Column count is chosen by the zoom level (0..3 from scroll wheel):

| Zoom | Columns | Effect on board size |
|---|---|---|
| 0 (default) | up to 4 | smallest, most boards visible |
| 1 | up to 3 | medium |
| 2 | up to 2 | large |
| 3 | 1 | one board fills available area |

Caps prevent meaningless empty columns: with 2 variations and
zoom 0, columns = min(2, 4) = 2.

Each board carries a caption strip below it: variation name and
"<played> / <total> plies" counter. Hover-highlighting on a board
provides a click affordance; click loads that variation into the
main game view (same path as the variation cards on the detail
page).

### Why static-with-stepping rather than auto-animated

The v7 design discussion considered auto-playing all boards in
sync. The user-driven stepping won because the pedagogical value
is in the *comparison* — the user wants to look at the structures,
not watch them flicker. User-paced stepping respects that; auto-
play would make the page busy and harder to study.

## 6. `_draw_mini_board(board, x, y, size, highlight)`

Extracted helper that renders an arbitrary `chess.Board` at any
pixel position and size. Currently used only by the satellite
view; the main game view (`_draw_game`) was *not* retrofitted to
use the helper because it has many additional concerns (eval bar,
threats, drag ghost, animations, legal-move dots) that the mini
helper deliberately doesn't carry. Future feature ideas — a tiny
preview thumbnail in a list cell, a side-by-side "before/after"
position diff — can call the helper directly.

Always renders white-orientation. Variations are studied as
printed in books, not played, so flipping for Black-defense
satellites would just confuse cross-references.

## 7. Navigation: ESC ladder + universal Backspace

Backspace now means "back one level" everywhere except the menu
(where it noops, so beginners can't accidentally close the app).
The navigation ladder:

```
game (loaded from variation)  →  opening_detail
variations_satellite          →  opening_detail
opening_detail                →  openings_list
openings_list / openings_table / masters / credits → menu
menu                          →  (Backspace noop / ESC closes)
```

ESC follows the same ladder, with the historic exception that ESC
from the menu closes the application. ESC from the game state
still consults `_game_return_state`: if a game was launched from
an opening detail page, ESC goes there; otherwise it goes to the
menu (legacy behavior preserved).

## 8. UI changes on the opening-detail page

The v7 detail page showed: header → idea panel → famous-game
cards. v8 reorganizes:

- Header (compacted: 30pt → 28pt title; tighter line spacing)
- Idea panel (compacted: 90px → 70px; same content)
- **Variations panel (NEW)**: section title with "View all
  variations →" button on the right, then 2-up cards showing
  name + ECO + SAN moves + summary + famous-game line ("Famous:
  Kasparov vs Anand, 1995 (1-0)") + "Click to replay →" cue.
- Famous-games panel (slightly compacted): same content, smaller
  cards. Empty state copy updated to point at the per-variation
  games above.

The "View all variations →" button is disabled (greyed) when
fewer than 2 valid variations exist for the opening — there's
nothing to compare with one board.

---

## Files changed in v8

```
openings_catalog.py    — Added Variation dataclass.
                       — Added variations field on CatalogEntry.
                       — Populated all 27 entries (11 W + 16 B) with
                         exactly 2 variations each = 54 total.
                       — Dropped standalone Evans Gambit entry
                         (kept as Italian sub-variation).
                       — Extended _validate() with UCI legality
                         pass for variations.

variations_pgn.py      — NEW. Bundle loader with slug indexing,
                         truncation detection, per-game error
                         isolation. ParsedGame dataclass.
                         get_variation_game() / list_variation_slugs().

main.py                — Imports variations_pgn.
                       — New __init__ state for satellite view and
                         _game_return_state.
                       — on_draw, on_mouse_press extended with
                         "variations_satellite" state.
                       — on_mouse_scroll: zoom in satellite, step
                         in game (existing).
                       — on_key_press: Backspace = back one level
                         universally; right/left arrow + Home/0 in
                         satellite; ESC from game consults
                         _game_return_state.
                       — _draw_opening_detail REWRITTEN with
                         variations panel and satellite button.
                       — _handle_opening_detail_click REWRITTEN to
                         dispatch to satellite button, variation
                         cards, or famous-game cards.
                       — NEW _variation_famous_game_line helper for
                         the "Famous: White vs Black, Year (Result)"
                         line on variation cards.
                       — NEW _load_variation, _load_parsed_variation_game,
                         _load_uci_sequence — three-tier variation
                         loading (master → bundle → UCI study).
                       — NEW _navigate_back_one_level helper.
                       — NEW _draw_variations_satellite — the grid.
                       — NEW _handle_variations_satellite_click.
                       — NEW _draw_mini_board(board, x, y, size,
                         highlight) — extracted helper.

assets/openings/variations.pgn — NEW. 13 verified games, each
                         tagged [VariationSlug "..."]. All pass
                         strict validation (legal-move + token-count
                         truncation guard).

assets/openings/README.md — NEW. Format spec, slug convention,
                         contributor workflow, validation
                         philosophy.

CHANGES.md             — This v8 section prepended; v7 retained.
```

## Files NOT changed in v8

`chess_engine.py`, `ai_profiles.py`, `eval_tracker.py`,
`master_games.py`, `opening_teacher.py`, `animation.py`,
`ui_widgets.py`, `config.py`, `prolog_reasoner.py`,
`headless_trainer.py`, `_opening_book.py`, `data/chess_rules.pl`,
`avatar_gen.py`, `avatars_links.py`.

## Notes & known caveats

### The standalone Evans Gambit entry was removed

v7 listed Evans Gambit as a top-level White Opening *and* it
appeared inside the Italian (which v8 confirmed by adding Evans
Gambit as a variation of Italian). Two appearances of the same
opening in the catalog menu is incoherent. v8 keeps Evans Gambit
only as an Italian variation. White Openings count went from 12
to 11 as a result.

### Variation famous-game coverage is partial by design

Of 54 variations, 21 ship with a paired famous game (8 reusing
master games, 13 from the bundle), 33 ship empty. This was the
explicit choice during planning: "I'd rather flag the gap now than
ship invented PGNs that look fine but fail validation." The 33
empty-state variations are still useful — the user clicks one, the
defining UCI moves load as a study, the position appears, the
arrow keys step through. The famous-game illustration is the
nice-to-have, not the core feature.

### One "famous game" was caught wrong during development

An early French Winawer pairing (Botvinnik vs Capablanca, AVRO
1938) had an illegal `Rg8` at move 9. python-chess silently
truncated; the SAN-token check in `variations_pgn._load()` flagged
the mismatch and the entry was dropped. The Winawer variation now
ships with empty state. **The strict validator paid for itself
within an hour of being written.**

### The mini-board renders white-orientation only

By design — variations are studied as printed in books, not played.
A "flip for Black defenses" toggle would be one line in
`_draw_mini_board` (swap the file/rank loop direction), but
nobody's asked for it yet.

### The main game view doesn't use `_draw_mini_board`

The helper exists; the main view continues to use its own inlined
drawing because it has many concerns (eval bar, threats, drag
ghost, animations, legal-move dots) the mini helper deliberately
doesn't carry. A future refactor that splits those concerns out
could share more code, but that's a v9 question.

### The PGN bundle ships 13 games; you can add more

The README in `assets/openings/` documents the format. Drop a
verified PGN block with a `[VariationSlug "..."]` tag matching a
catalog entry, and it will load on next startup. Console output
reports the new count and any validation failures.

---



Version 7 focuses on three user-requested improvements on top of v6.
New modules: **`avatars_links.py`**, **`openings_catalog.py`**.
Modified: **`main.py`**, **`avatar_gen.py`**.
New assets: Capablanca, Mikhail Tal, Karpov photos in
`./assets/textures/avatars/`.

| # | Request | Status |
|---|---------|--------|
| 1 | Ship Capablanca, Tal, Karpov avatar photos | done |
| 2 | User-editable avatar filename mapping (`avatars_links.py`) | done |
| 3 | Audit accuracy of White / Black openings lists | done |
| 4 | Per-opening detail view with famous-game replay (no more matrix jump) | done |

---

## 1. New avatar photos

Three new photos in `./assets/textures/avatars/`:

- `Capablanca.jpg`
- `Mikhail_Tal.jpg`
- `Karpov.jpg`

Shipped as user-supplied source images. Loaded via the usual
PIL → center-crop → circular-mask pipeline in
`avatar_gen._load_file_as_avatar()`. Together with the v5 Fischer
and Kasparov photos, the masters browser now shows real photos for
all five of: Capablanca, Tal, Karpov, Fischer, Kasparov. Everyone
else still gets a deterministic initials disc until a photo is
dropped in.

## 2. `avatars_links.py` — user-editable mapping

**New top-level module.** A plain dict keyed by player name, mapping
to bare filenames inside `./assets/textures/avatars/`. Users extend
it by adding lines like:

```python
"Hikaru Nakamura":  "Nakamura.jpg",
"Ding Liren":       "DingLiren.png",
```

No code change needed — `avatar_gen._find_file()` consults this map
**first** on every lookup, before falling back to the filesystem
heuristics (sanitized name, raw name, last-token). If the linked
filename is declared but missing on disk, we warn on the console and
fall through to heuristics — never crash.

The v5 heuristics (last-name fallback, extension search) still work
for casual drop-in use; the dict is just the authoritative way to
pin a specific (name, file) pair.

Shipped dict:

```python
AVATAR_FILES = {
    "Jose Raul Capablanca": "Capablanca.jpg",
    "Mikhail Tal":          "Mikhail_Tal.jpg",
    "Anatoly Karpov":       "Karpov.jpg",
    "Bobby Fischer":        "Fischer.jpg",
    "Garry Kasparov":       "Kasparov.jpg",
    # commented-out templates for the remaining masters, ready to be
    # filled in when the user drops a photo into the folder.
}
```

## 3. Openings audit — catalog now has correct side assignment

**Problem in v6.** The White-Openings / Black-Openings menus were
both driven by `AI_OPENINGS`, which had move lists for *both* sides
per entry. That meant "Italian" appeared under Black Openings and
"Sicilian" appeared under White Openings — both wrong, because
openings are named for the side that defines them.

**Fix.** New module `openings_catalog.py` declares each opening
**exactly once**, on its correct side:

- **12 White openings** — Ruy Lopez, Italian, Scotch, King's Gambit,
  Vienna, Evans Gambit, Queen's Gambit, London, Trompowsky, English,
  Réti, Bird's.
- **16 Black defenses** — Sicilian, Sicilian Najdorf, French,
  Caro-Kann, Scandinavian, Alekhine, Pirc, Modern, QGD, Slav, KID,
  Nimzo-Indian, Grünfeld, Dutch, Budapest, Benko.

Each `CatalogEntry` carries:

- `side`, `slug`, `name`, `eco`
- `moves_uci` and `moves_san` — the defining move sequence
- `summary` — one-line characterization of the idea
- `famous_games` — list of `FamousGame` pairings

Pairings reference games by `master_game_id` (cheap, validated
metadata reused) or carry inline PGN strings. A **strict validator**
runs at import and catches partially-parsed PGNs — python-chess
silently truncates on an illegal move, so the validator also compares
parsed-ply count against declared-token count and marks mismatches
invalid. Invalid entries are silently skipped in the UI; the console
prints one warning per failure so developers can fix them.

**Ship-state.** v7 ships only `master_game_id`-backed pairings —
nine in total, all verified to resolve cleanly against
`master_games.MASTER_GAMES`. Inline-PGN support exists and is tested,
but this release ships no inline entries: hand-transcribing full
tournament PGNs is error-prone and a truncated game would mislead.
Users who want to add inline famous games should follow the format
documented at the top of `openings_catalog.py`.

Pairings currently wired:

| Opening | Famous game |
|---|---|
| Ruy Lopez | Karpov vs Unzicker, Nice 1974 |
| Queen's Gambit | Fischer vs Spassky, 1972 (Game 6) |
| English Opening | Fischer vs Spassky, 1972 (Game 6) |
| Sicilian Defense | Carlsen vs Karjakin, WC 2016 (TB Game 4) |
| Caro-Kann Defense | Tal vs Smyslov, Candidates 1959 |
| Pirc Defense | Kasparov vs Topalov, Wijk aan Zee 1999 |
| QGD | Fischer vs Spassky, 1972 (Game 6) |
| Slav Defense | Carlsen vs Anand, WC 2013 (Game 5) |
| Grünfeld Defense | Byrne vs Fischer, 'Game of the Century' 1956 |
| Dutch Defense | Capablanca vs Tartakower, New York 1924 |

(Nine distinct openings; a few share the same master game because
Fischer–Spassky 1972 Game 6 transposed through multiple opening
frameworks.)

## 4. Opening-detail view replaces "jump to matrix"

**Old behavior.** Clicking an opening in the per-side list jumped
straight to the Openings Matrix Tables and tried to pre-select the
row. That was incoherent — the user asked about one opening, they
got a matrix.

**New behavior.** Clicking an opening goes to a dedicated detail
view for that opening. The detail view shows:

- Full name, side label ("White opening" / "Black defense"), and ECO.
- A panel with the defining move sequence (SAN) and a word-wrapped
  summary of the idea.
- A scrollable list of famous-game cards. Each card shows title,
  metadata (date / result / ECO / length), and a one-line note.
  A prominent "Click to replay →" cue on the right makes the
  interaction obvious.

**Replay.** Clicking a card calls `_load_master_game(mg)` for
master-game pairings, or `_load_from_pgn_text(pgn)` for inline
pairings. In both cases, after loading, `ply_index` is reset to 0
and `_rebuild_from_ply_index()` runs — so the game starts at move 1
and the user can scroll forward through the game or press `0` to
restart at any time. (Without the reset, master games load at the
final position, which is disorienting for "please show me the
Karpov-Unzicker game".)

**Empty state.** When an opening has no paired games yet, the detail
view shows a friendly empty panel explaining that curation is
partial and pointing to `openings_catalog.py` for contributions.
This keeps the feature honest — we don't manufacture pairings.

**Navigation.** ESC from the detail view goes **back to the list**
(not all the way to the menu). ESC from the list goes to the menu.
This two-step back-navigation matches user expectations for a
browse-and-drill-down flow.

---

## Files changed in v7

```
avatars_links.py     — NEW. User-editable {name: filename} dict.
                       get_avatar_filename(name) lookup helper.

avatar_gen.py        — Imports _links_lookup with a safe fallback.
                     — _find_file: checks the explicit map FIRST,
                       before sanitized / raw / last-token
                       filesystem heuristics. Warns (not crashes)
                       when a linked file is missing.

openings_catalog.py  — NEW. CatalogEntry + FamousGame dataclasses.
                     — _WHITE_ENTRIES (12) and _BLACK_ENTRIES (16).
                     — entries_for_side(side) / find_entry(side, slug)
                       / resolve_famous_game(fg, master_games_list).
                     — Strict import-time validator that catches
                       partially-parsed PGNs via token-count check.

main.py              — Imports openings_catalog functions.
                     — __init__: new state opening_detail_slug,
                       _opening_detail_game_rects.
                     — on_draw: dispatches opening_detail state.
                     — on_key_press: opening_detail ESC goes to
                       openings_list (not all the way to menu).
                     — on_mouse_press: dispatches opening_detail
                       clicks.
                     — _draw_openings_list REWRITTEN: drives off
                       openings_catalog.entries_for_side(), shows
                       name + ECO + SAN moves + summary per card.
                     — _handle_openings_list_click REWRITTEN: jumps
                       to opening_detail for the clicked slug
                       (no more matrix shortcut).
                     — _draw_opening_detail NEW: full detail page
                       with famous-game cards.
                     — _handle_opening_detail_click NEW: loads the
                       chosen master game or inline PGN and rewinds
                       to ply 0.

assets/textures/avatars/
                     — Capablanca.jpg  (NEW)
                     — Mikhail_Tal.jpg (NEW)
                     — Karpov.jpg      (NEW)

CHANGES.md           — This file.
```

## Files not changed

`chess_engine.py`, `ai_profiles.py`, `eval_tracker.py`,
`master_games.py`, `opening_teacher.py`, `animation.py`,
`ui_widgets.py`, `config.py`, `prolog_reasoner.py`,
`headless_trainer.py`, `_opening_book.py`, `data/chess_rules.pl`.

## Known caveats

- **Inline PGN coverage is intentionally zero in the shipped
  catalog.** Hand-entered tournament PGNs are error-prone — an early
  experiment for v7 had 11 truncated PGNs that looked fine in
  plain reading but failed the strict validator. The inline path is
  fully supported, tested, and documented; users can add entries
  with confidence that bad ones will surface as console warnings
  instead of silent miniature-game lies. If you want one of the
  "no games paired" openings (Italian, Scotch, King's Gambit, etc.)
  populated, the cleanest way is to drop a standalone PGN file into
  `./pgn_losses/` (or any folder) and load it through the existing
  Load PGN button, OR to paste an authoritative PGN into
  `openings_catalog.py`.
- **ECO ranges are broad on purpose.** A "Ruy Lopez (C60–C99)" entry
  covers the whole Spanish complex rather than picking one sub-line.
  This is the right grain for a menu that says "show me the
  Ruy Lopez" — specific subvariations (Berlin, Closed, Exchange)
  would warrant their own entries in a future expansion.
- **Some openings share the same master game.** Fischer–Spassky 1972
  Game 6 appears under three entries (Queen's Gambit, English, QGD)
  because the game transposed through all three frameworks. That's
  historically accurate, not a bug — but the user will see the same
  game pop up three times if they browse all three openings.
- **Avatar mapping is name-exact.** `avatars_links.py` lookup uses
  string equality on the key. "Kasparov" as a key will NOT match a
  game featuring "Garry Kasparov". Use the name as it appears in
  `master_games.py`. The filesystem heuristics still catch the
  last-name case.
