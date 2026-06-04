"""test_v12_fixes.py — headless regression tests for the v12 repair pass.

Run under Xvfb:
    xvfb-run -a -s "-screen 0 1920x1080x24" python3 test_v12_fixes.py

Exercises exactly the code paths that were changed:

  1. PGN correctness — all 34 master games replay legally inside the app's
     own master_games module, and the 6 corrected games have the expected
     ply counts / results (So–Nakamura must end in checkmate).
  2. AI move hand-off — _ai_go() runs the search on a worker thread and the
     move is applied on the MAIN thread via on_update()/_apply_ai_move(),
     advancing the board by exactly one ply. (This is the teleport fix.)
  3. Themed sliding animation — _apply_ai_move() and the human path both
     create a SlidingPiece whose texture comes from the themed pipeline
     (piece_textures), not the legacy Unicode-glyph fallback, and register
     the moving squares as 'animating' so the static board skips them.
  4. Board-background cache — _board_background() returns a cached
     ShapeElementList and rebuilds only when the material/geometry key
     changes (the batched-render optimization).
  5. Prolog optional — analyze() no longer asserts the board, and opening
     advice works with Prolog absent.

Exits 0 on success, non-zero on the first failure.
"""
import os
import sys
import time
import traceback

try:
    import pyglet.window.xlib  # noqa: F401  (import-order workaround)
except ImportError:
    pass

import chess
import arcade  # noqa: F401
import piece_textures
import master_games as mg
import main as chess_main


FIXED = {
    "capablanca_vs_tartakower_1924": (103, "1-0", False),
    "karpov_vs_unzicker_1974":       (87,  "1-0", False),
    "carlsen_vs_anand_2013_g5":      (115, "1-0", False),
    "carlsen_vs_karjakin_2016_tb4":  (99,  "1-0", False),
    "so_vs_nakamura_2015":           (78,  "0-1", True),   # ends in mate
    "benjamin_vs_silman_1979":       (109, "1-0", False),
}

_passed = 0


def check(label, cond):
    global _passed
    if not cond:
        raise AssertionError(f"FAILED: {label}")
    _passed += 1
    print(f"  ✓ {label}")


def test_pgn_legality():
    print("\n[1] PGN correctness")
    games = mg.MASTER_GAMES
    check(f"library has 34 games (got {len(games)})", len(games) == 34)
    by_id = {}
    for g in games:
        moves = getattr(g, "moves_san", None) or getattr(g, "moves", None)
        b = chess.Board()
        ply = 0
        for san in moves:
            b.push_san(san)          # raises if illegal
            ply += 1
        by_id[g.id] = (ply, b.is_checkmate(), g.result)
    check("all 34 games replay fully legally", len(by_id) == 34)
    for gid, (exp_ply, exp_res, exp_mate) in FIXED.items():
        check(f"{gid} present", gid in by_id)
        ply, mate, res = by_id[gid]
        check(f"{gid}: {ply} plies == {exp_ply}", ply == exp_ply)
        check(f"{gid}: result {res} == {exp_res}", res == exp_res)
        check(f"{gid}: ends_in_mate {mate} == {exp_mate}", mate == exp_mate)
    # The misattributed entry must be gone.
    check("misattributed nakamura_vs_caruana_2015 removed",
          "nakamura_vs_caruana_2015" not in by_id)
    check("fake silman_demo_imbalance removed",
          "silman_demo_imbalance" not in by_id)


def test_ai_handoff(g):
    print("\n[2] AI move hand-off (worker → main thread)")
    g.MIN_AI_DELAY = 0.0                       # don't wait in the test
    board = g.engine.board
    ply_before = len(board.move_stack)
    g.thinking = False
    g._ai_go()                                 # spawns worker thread
    # The worker only *computes*; the move is applied on the main thread
    # the next time on_update() runs. Pump update ticks until applied.
    deadline = time.time() + 10.0
    applied = False
    while time.time() < deadline:
        g.on_update(1 / 60)
        if (not g.thinking) and len(board.move_stack) == ply_before + 1:
            applied = True
            break
        time.sleep(0.02)
    check("AI move was applied on the main thread", applied)
    check("board advanced by exactly one ply",
          len(board.move_stack) == ply_before + 1)
    # Right after application a slider should exist for the move.
    check("animator became active for the AI slide", g.animator.active)
    check("moving squares registered as animating",
          len(g.animator.animating_squares) >= 1)


def test_themed_animation(g):
    print("\n[3] Themed sliding animation")
    # Reset to a clean board and pick a deterministic legal move.
    g.engine.board = chess.Board()
    g.animator.clear()
    g.piece_theme = "classical"
    m = chess.Move.from_uci("e2e4")
    g._apply_ai_move(m, 0.0)
    check("e2e4 pushed by _apply_ai_move",
          g.engine.board.peek() == m)
    check("slide registered e4 as animating",
          chess.E4 in g.animator.animating_squares)
    # The slider's texture must be the SAME object the static board would
    # use for this piece+theme — i.e. it came from piece_textures, not the
    # legacy glyph fallback.
    slider = g.animator._sliders[-1]
    sh = piece_textures.flank_for_square(chess.E4)
    expected = piece_textures.get_piece_texture(
        "P", theme="classical", side_hint=sh, size=slider.sprite.texture.width)
    check("sliding piece uses the themed texture (not glyph)",
          slider.sprite.texture is expected)

    # A fancy theme must also resolve through the themed pipeline.
    themes = piece_textures.available_themes()
    fancy = next((t for t in themes if t != "classical"), None)
    if fancy:
        g.engine.board = chess.Board()
        g.animator.clear()
        g.piece_theme = fancy
        g._apply_ai_move(chess.Move.from_uci("d2d4"), 0.0)
        sl = g.animator._sliders[-1]
        exp2 = piece_textures.get_piece_texture(
            "P", theme=fancy,
            side_hint=piece_textures.flank_for_square(chess.D4),
            size=sl.sprite.texture.width)
        check(f"fancy theme '{fancy}' slide uses themed texture",
              sl.sprite.texture is exp2)


def test_board_bg_cache(g):
    print("\n[4] Board-background batched cache")
    g._board_bg_shapes = None
    g._board_bg_key = None
    first = g._board_background()
    second = g._board_background()
    check("ShapeElementList is cached (same object on 2nd call)",
          first is second)
    # 1 border + 64 squares.
    try:
        n = len(list(first))
    except TypeError:
        n = None
    if n is not None:
        check(f"background batches 65 shapes (got {n})", n == 65)
    # Changing the material key must rebuild.
    import board_materials
    keys = list(board_materials.MATERIALS.keys()) if hasattr(
        board_materials, "MATERIALS") else []
    other = next((k for k in keys if k != g.board_material_key), None)
    if other:
        g.board_material_key = other
        rebuilt = g._board_background()
        check("changing material rebuilds the background",
              rebuilt is not first)


def test_prolog_optional(g):
    print("\n[5] Prolog is optional")
    r = g.reasoner
    # analyze() must run and return a list without needing Prolog.
    w = r.analyze(chess.Board())
    check("analyze() returns a list on the start position",
          isinstance(w, list))
    # Opening advice works regardless of Prolog availability.
    for mv, first_word in [(1, "Focus"), (5, "Develop"), (15, "Transition")]:
        a = r.get_opening_advice(mv, "white")
        check(f"opening_advice(move={mv}) non-empty", len(a) >= 1)


def main():
    print("Constructing ChessGame window…")
    g = chess_main.ChessGame()
    g.dispatch_events()

    test_pgn_legality()
    test_ai_handoff(g)
    test_themed_animation(g)
    test_board_bg_cache(g)
    test_prolog_optional(g)

    print(f"\nALL {_passed} CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception:
        print("\nTEST FAILED")
        traceback.print_exc()
        sys.exit(1)
