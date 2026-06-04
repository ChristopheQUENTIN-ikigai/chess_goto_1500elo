"""smoke_test.py — exercise the new imbalances tutorial draw paths.

Instantiates the ChessGame window inside Xvfb, walks through:
  menu → imbalances browser → switches part → opens a lesson with FEN
  → opens a lesson without FEN → triggers the FEN loader → back to menu.

Each navigation step is followed by a single on_draw() invocation so
runtime errors (missing attributes, wrong argument names, etc.) surface
as exceptions. The script exits 0 on success, non-zero on the first
exception.
"""
import os
import sys
import traceback

# Pyglet 2.x has an import-order bug where the Linux x11_xinput module
# uses a class-level `@pyglet.window.xlib.XlibEventHandler(0)` that
# triggers before pyglet.window.xlib has been loaded by the regular
# window-platform discovery. Preloading the xlib submodule fixes the
# AttributeError on import. (We still need a real or virtual display
# for arcade's Window class to construct successfully.)
try:
    import pyglet.window.xlib  # noqa: F401
except ImportError:
    pass

import arcade
import main as chess_main
from imbalances_tutorial import LESSONS

def step(label):
    print(f"  ▸ {label}")

try:
    print("Constructing ChessGame window…")
    g = chess_main.ChessGame()
    # arcade 3.x: a single dispatch_events call to initialize state.
    g.dispatch_events()
    print("  ▸ initial state:", g.app_state)
    assert g.app_state == "menu", "should start on menu"

    step("draw menu")
    g.on_draw()
    # Confirm the new menu button rect exists
    actions = [r[0] for r in g._menu_rects]
    print("  ▸ menu actions:", actions)
    assert "imbalances" in actions, "imbalances button missing from menu"

    step("navigate menu → imbalances")
    g._handle_menu_click(*[
        (bx + 5, by + 5)
        for action, bx, by, bw, bh in g._menu_rects
        if action == "imbalances"
    ][0])
    print("  ▸ state after click:", g.app_state)
    assert g.app_state == "imbalances"

    step("draw imbalances browser, part 0")
    g.on_draw()
    print(f"  ▸ part_rects: {len(g._imbalance_part_rects)}, "
          f"lesson_rects: {len(g._imbalance_lesson_rects)}")
    assert len(g._imbalance_part_rects) == 9, "expected 9 part rows"

    step("switch to part 1 (Minor Pieces)")
    g._imbalance_part_i = 1
    g.on_draw()
    assert len(g._imbalance_lesson_rects) > 0

    step("walk through every part to exercise each branch")
    for i in range(9):
        g._imbalance_part_i = i
        g._imbalance_scroll = 0
        g.on_draw()
        if i == 2:
            # also exercise the scrolled view (max_scroll path)
            g._imbalance_scroll = 99
            g.on_draw()
            g._imbalance_scroll = 0

    step("open a lesson WITH a FEN (mp_outpost_knight)")
    g._imbalance_lesson_slug = "mp_outpost_knight"
    g.app_state = "imbalance_lesson"
    g.on_draw()
    print(f"  ▸ open_btn_rect: {g._imbalance_open_btn_rect}")
    assert g._imbalance_open_btn_rect, "expected button rect when FEN present"

    step("simulate clicking 'Open on main board'")
    bx, by, bw, bh = g._imbalance_open_btn_rect
    g._handle_imbalance_lesson_click(bx + 5, by + 5)
    print("  ▸ state:", g.app_state)
    assert g.app_state == "game"

    step("return to menu, then back to imbalances")
    g.app_state = "menu"
    g.on_draw()
    g.app_state = "imbalances"
    g._imbalance_part_i = 0
    g.on_draw()

    step("open a lesson WITHOUT a FEN (imb_what_is)")
    g._imbalance_lesson_slug = "imb_what_is"
    g.app_state = "imbalance_lesson"
    g.on_draw()
    print(f"  ▸ open_btn_rect (no FEN expected empty): "
          f"{g._imbalance_open_btn_rect}")
    assert g._imbalance_open_btn_rect == ()

    step("ESC from lesson → imbalances")
    g._navigate_back_one_level()
    assert g.app_state == "imbalances"

    step("ESC from imbalances → menu")
    g._navigate_back_one_level()
    assert g.app_state == "menu"

    step("draw every FEN-bearing lesson to validate boards render")
    fen_lessons = [L for L in LESSONS if L.fen]
    for L in fen_lessons:
        g._imbalance_lesson_slug = L.slug
        g.app_state = "imbalance_lesson"
        g.on_draw()
    print(f"  ▸ drew {len(fen_lessons)} FEN lessons cleanly")

    print()
    print("SMOKE TEST PASSED")
    sys.exit(0)
except Exception:
    print()
    print("SMOKE TEST FAILED")
    traceback.print_exc()
    sys.exit(1)
