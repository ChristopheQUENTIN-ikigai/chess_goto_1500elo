"""
ui_widgets.py — Reusable UI widgets for the chess app (Arcade 3.x).

Provides:
  - TextInputBox : focusable single-line text input with clipboard paste
  - EvalGraph    : per-ply centipawn plot with delta bars

Both widgets are lightweight — no external GUI framework. They expose:
  .draw()                    — render
  .contains(x, y)            — hit-test
  .on_mouse_press(x, y)      — focus/unfocus
  .on_key_press(key, mod)    — type / paste / submit (TextInputBox only)
  .on_text(text)             — character input (TextInputBox only)
"""
import arcade
import arcade.key
from arcade import XYWH

from config import (
    COLOR_INPUT_BG, COLOR_INPUT_BG_FOCUS,
    COLOR_INPUT_BORDER, COLOR_INPUT_BORDER_FC,
    COLOR_INPUT_TEXT, COLOR_INPUT_PLACEHOLDER,
    COLOR_GRAPH_BG, COLOR_GRAPH_GRID, COLOR_GRAPH_AXIS,
    COLOR_GRAPH_LINE, COLOR_GRAPH_FILL_W, COLOR_GRAPH_FILL_B,
    COLOR_GRAPH_DELTA_GOOD, COLOR_GRAPH_DELTA_BAD,
    COLOR_GRAPH_ZERO, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_ACCENT,
)


def _draw_rect_outline_lbwh(left, bottom, w, h, color, border=1):
    arcade.draw_rect_outline(
        XYWH(left + w / 2, bottom + h / 2, w, h), color, border)


# ─────────────────────────────────────────────────────────────────────────
# TextInputBox
# ─────────────────────────────────────────────────────────────────────────

class TextInputBox:
    """Single-line focusable text input with Ctrl+V paste support.

    on_submit(text) is called when Enter is pressed with a non-empty value.
    """

    def __init__(self, left, bottom, width, height,
                 placeholder="", label="", max_chars=256, on_submit=None,
                 font_size=11):
        self.left = left
        self.bottom = bottom
        self.width = width
        self.height = height
        self.label = label
        self.placeholder = placeholder
        self.max_chars = max_chars
        self.on_submit = on_submit or (lambda _: None)
        self.font_size = font_size

        self.text = ""
        self.focused = False
        self._scroll_off = 0   # horizontal scroll in chars

    # ── Hit-testing ───────────────────────────────────────────────────
    def contains(self, x, y) -> bool:
        return (self.left <= x <= self.left + self.width
                and self.bottom <= y <= self.bottom + self.height)

    def on_mouse_press(self, x, y) -> bool:
        """Handle a click. Returns True if the widget absorbed the event."""
        if self.contains(x, y):
            self.focused = True
            return True
        self.focused = False
        return False

    # ── Keyboard ──────────────────────────────────────────────────────
    def on_text(self, text: str):
        """Arcade 3.x: called with each typed character."""
        if not self.focused:
            return
        if len(self.text) + len(text) > self.max_chars:
            return
        # Filter out control chars
        filtered = "".join(ch for ch in text if ord(ch) >= 32)
        self.text += filtered

    def on_key_press(self, key, mod) -> bool:
        """Return True if the widget absorbed the key."""
        if not self.focused:
            return False

        if key == arcade.key.BACKSPACE:
            self.text = self.text[:-1]
            return True
        if key == arcade.key.ENTER or key == arcade.key.NUM_ENTER:
            val = self.text.strip()
            if val:
                self.on_submit(val)
            return True
        if key == arcade.key.ESCAPE:
            self.focused = False
            return True
        # Ctrl+V — paste
        if key == arcade.key.V and (mod & arcade.key.MOD_CTRL or mod & arcade.key.MOD_COMMAND):
            self._paste_from_clipboard()
            return True
        # Ctrl+A style select-all — we'll implement as clear for simplicity
        if key == arcade.key.A and (mod & arcade.key.MOD_CTRL or mod & arcade.key.MOD_COMMAND):
            self.text = ""
            return True
        return False

    def _paste_from_clipboard(self):
        """Try multiple clipboard strategies (pyperclip → Tk → Arcade window)."""
        clip = ""
        # pyperclip if installed
        try:
            import pyperclip
            clip = pyperclip.paste() or ""
        except Exception:
            pass
        # Tk fallback
        if not clip:
            try:
                import tkinter
                r = tkinter.Tk()
                r.withdraw()
                clip = r.clipboard_get()
                r.destroy()
            except Exception:
                pass
        # Arcade window fallback
        if not clip:
            try:
                win = arcade.get_window()
                if win is not None and hasattr(win, "get_clipboard_text"):
                    clip = win.get_clipboard_text() or ""
            except Exception:
                pass
        if clip:
            remaining = self.max_chars - len(self.text)
            if remaining > 0:
                self.text += clip[:remaining]

    # ── Drawing ───────────────────────────────────────────────────────
    def draw(self):
        # Label above the box — sit it a few pixels higher so the label
        # of the *next* input doesn't visually crowd this one's content.
        if self.label:
            arcade.draw_text(self.label, self.left, self.bottom + self.height + 4,
                             COLOR_TEXT_DIM, font_size=10)

        bg = COLOR_INPUT_BG_FOCUS if self.focused else COLOR_INPUT_BG
        arcade.draw_lbwh_rectangle_filled(
            self.left, self.bottom, self.width, self.height, bg)

        border_col = COLOR_INPUT_BORDER_FC if self.focused else COLOR_INPUT_BORDER
        _draw_rect_outline_lbwh(
            self.left, self.bottom, self.width, self.height, border_col, 1)

        # Center the text vertically inside the taller box
        text_y = self.bottom + (self.height - self.font_size) / 2 - 1

        if self.text:
            # Show only the tail of the text that fits inside the box.
            # Approx 6.5 px per char at size 11 — slightly generous so
            # long FEN/PGN strings don't overflow the right border.
            char_w = 6.5
            max_chars_visible = max(4, int((self.width - 16) / char_w))
            disp = self.text[-max_chars_visible:]
            arcade.draw_text(
                disp, self.left + 6, text_y,
                COLOR_INPUT_TEXT, font_size=self.font_size)
            # Blinking caret — keep it simple: always-on underscore at
            # the visible tail. Pin it just left of the right edge so
            # it stays inside the box for any text length.
            if self.focused:
                caret_x = self.left + 6 + min(len(disp), max_chars_visible) * char_w
                caret_x = min(caret_x, self.left + self.width - 10)
                arcade.draw_text(
                    "_", caret_x, text_y - 1,
                    COLOR_INPUT_TEXT, font_size=self.font_size)
        else:
            # Placeholder in italic — truncate if it's longer than the
            # visible width so it doesn't spill over.
            char_w = 6.5
            max_chars_visible = max(8, int((self.width - 16) / char_w))
            ph = self.placeholder
            if len(ph) > max_chars_visible:
                ph = ph[:max_chars_visible - 1] + "…"
            arcade.draw_text(
                ph, self.left + 6, text_y,
                COLOR_INPUT_PLACEHOLDER, font_size=self.font_size, italic=True)


# ─────────────────────────────────────────────────────────────────────────
# EvalGraph
# ─────────────────────────────────────────────────────────────────────────

class EvalGraph:
    """Per-ply centipawn plot with delta-bar overlay.

    Layout:
        Top 65%  : line plot of cp across plies (y=0 is the middle)
        Bottom 35%: bar plot of last-move deltas (red=loss, green=gain)

    Hit-testing:
        contains(x, y)        — mouse over the whole graph rectangle
        ply_at(x, y)          — which ply index (0..n-1 in tracker.history)
                                the click maps to, or None if outside the
                                plot area. Used by main.py to jump the
                                replay cursor to the clicked ply.
    """

    def __init__(self, left, bottom, width, height, title="Eval Plot"):
        self.left = left
        self.bottom = bottom
        self.width = width
        self.height = height
        self.title = title
        # Filled in every draw() so ply_at() knows where the line plot
        # ended up (split_frac and padding aren't stable across layout
        # changes, so we stash the resolved rects). Keys: 'line' and
        # 'bar', each a (x0, y_bot, x1, y_top) tuple. 'n_pts' is the
        # number of points currently plotted.
        self._plot_rects = {}
        self._n_pts = 0

    # ── Hit-testing ──────────────────────────────────────────────────
    def contains(self, x, y) -> bool:
        return (self.left <= x <= self.left + self.width
                and self.bottom <= y <= self.bottom + self.height)

    def ply_at(self, x, y):
        """Map a click inside the graph to a ply index (0..n-1) in the
        tracker's history, or None if the click is outside the plot
        area or there's nothing to plot yet. The line plot and bar
        plot share the same x-axis, so a click anywhere vertically
        inside either one maps to the same ply."""
        if self._n_pts < 1:
            return None
        # Accept clicks in either the line-plot band or the bar band.
        in_any = False
        for rect in self._plot_rects.values():
            x0, y_bot, x1, y_top = rect
            if x0 <= x <= x1 and y_bot <= y <= y_top:
                in_any = True
                break
        if not in_any:
            return None
        # Use the line-plot x-range for the mapping — both bands share
        # the same horizontal extent, so either would work.
        x0, _, x1, _ = self._plot_rects.get("line", (None, None, None, None))
        if x0 is None or x1 <= x0:
            return None
        frac = (x - x0) / (x1 - x0)
        frac = max(0.0, min(1.0, frac))
        n = self._n_pts
        # Same x-mapping as xy() in _draw_line_plot:
        # px = x0 + (i / max(1, n - 1)) * w, so i = frac * (n-1)
        i = round(frac * max(1, n - 1))
        return max(0, min(n - 1, i))

    def draw(self, tracker):
        # ── Background + frame ────────────────────────────────────────
        arcade.draw_lbwh_rectangle_filled(
            self.left, self.bottom, self.width, self.height, COLOR_GRAPH_BG)
        _draw_rect_outline_lbwh(
            self.left, self.bottom, self.width, self.height, COLOR_ACCENT, 1)

        # ── Title ─────────────────────────────────────────────────────
        title_y = self.bottom + self.height - 14
        arcade.draw_text(self.title, self.left + 6, title_y,
                         COLOR_ACCENT, font_size=10, bold=True)
        # Hint that the graph is clickable
        arcade.draw_text("(click to jump to ply)",
                         self.left + self.width - 140, title_y,
                         COLOR_TEXT_DIM, font_size=8, italic=True)

        # ── Split: top = line, bottom = bars ──────────────────────────
        # Slightly larger pad_bottom so the x-axis labels have room
        # beneath the bar plot without clipping into the frame.
        pad_top = 18
        pad_bottom = 22
        split_frac = 0.60     # line plot takes 60% of inner height

        inner_top = self.bottom + self.height - pad_top
        inner_bot = self.bottom + pad_bottom
        inner_h = inner_top - inner_bot
        line_h = inner_h * split_frac
        bar_h = inner_h * (1 - split_frac) - 10  # wider gap for axis

        line_top = inner_top
        line_bot = inner_top - line_h
        bar_top = line_bot - 10
        bar_bot = inner_bot

        # Store n_pts before drawing so ply_at() can use it
        self._n_pts = len(tracker.history)

        self._draw_line_plot(tracker, line_bot, line_top)
        self._draw_bars(tracker, bar_bot, bar_top)

        # ── Footer: last delta + cumulative loss summary ──────────────
        cp = tracker.history[-1].cp if tracker.history else 0.0
        last_d = tracker.last_delta()
        arcade.draw_text(f"cp {cp/100:+.2f}",
                         self.left + 6, self.bottom + 3,
                         COLOR_TEXT, font_size=9)
        dcol = (COLOR_GRAPH_DELTA_GOOD if last_d >= 0
                else COLOR_GRAPH_DELTA_BAD)
        arcade.draw_text(f"Δ {last_d/100:+.2f}",
                         self.left + self.width - 68, self.bottom + 3,
                         dcol, font_size=9)

    # ── Internals ─────────────────────────────────────────────────────
    def _draw_line_plot(self, tracker, y_bot, y_top):
        h = y_top - y_bot
        w = self.width - 12
        x0 = self.left + 6
        mid_y = (y_top + y_bot) / 2

        # Remember the plot rect for ply_at()
        self._plot_rects["line"] = (x0, y_bot, x0 + w, y_top)

        # Grid: horizontal center line (eval = 0)
        arcade.draw_line(x0, mid_y, x0 + w, mid_y,
                         COLOR_GRAPH_ZERO, 1)
        # Faint quarter lines
        q = h / 4
        arcade.draw_line(x0, mid_y + q, x0 + w, mid_y + q,
                         COLOR_GRAPH_GRID, 1)
        arcade.draw_line(x0, mid_y - q, x0 + w, mid_y - q,
                         COLOR_GRAPH_GRID, 1)

        pts = tracker.history
        if len(pts) < 2:
            arcade.draw_text("(plot builds as the game progresses)",
                             x0, mid_y - 6, COLOR_TEXT_DIM, font_size=8)
            # Still label the Y-axis edges so the "+N / -N" convention is
            # clear to the user even before the first move lands.
            arcade.draw_text("+ = White better", x0 + 1, y_top - 10,
                             COLOR_GRAPH_AXIS, font_size=8)
            arcade.draw_text("- = Black better", x0 + 1, y_bot + 1,
                             COLOR_GRAPH_AXIS, font_size=8)
            return

        scale = tracker.max_abs_cp
        n = len(pts)
        # x positions evenly spaced across width; y = cp scaled to half-height
        half = h / 2 - 2

        def xy(i, cp):
            px = x0 + (i / max(1, n - 1)) * w
            py = mid_y + max(-half, min(half, (cp / scale) * half))
            return px, py

        # Build white/black advantage fill (polygons from curve to mid-line)
        for i in range(n - 1):
            p1x, p1y = xy(i, pts[i].cp)
            p2x, p2y = xy(i + 1, pts[i + 1].cp)
            avg_y = (p1y + p2y) / 2
            col = COLOR_GRAPH_FILL_W if avg_y >= mid_y else COLOR_GRAPH_FILL_B
            if abs(avg_y - mid_y) > 0.5:
                y1 = min(avg_y, mid_y)
                y2 = max(avg_y, mid_y)
                arcade.draw_line((p1x + p2x) / 2, y1,
                                 (p1x + p2x) / 2, y2, col, 2)

        # Curve itself
        for i in range(n - 1):
            p1x, p1y = xy(i, pts[i].cp)
            p2x, p2y = xy(i + 1, pts[i + 1].cp)
            arcade.draw_line(p1x, p1y, p2x, p2y, COLOR_GRAPH_LINE, 2)

        # Dots per ply with W/B color distinction — this is the
        # clearest way to tell which side moved at each point without
        # crowding the x-axis with letters.
        # Ply 0 (starting position) has mover=None and we render it as
        # a neutral grey circle. Subsequent plies use white/black dots.
        COLOR_WHITE_DOT = (240, 240, 245, 255)
        COLOR_BLACK_DOT = (40, 40, 50, 255)
        COLOR_NEUTRAL_DOT = (150, 155, 165, 255)
        for i, p in enumerate(pts):
            px, py = xy(i, p.cp)
            if p.mover is True:
                col_dot = COLOR_WHITE_DOT
            elif p.mover is False:
                col_dot = COLOR_BLACK_DOT
            else:
                col_dot = COLOR_NEUTRAL_DOT
            # Slightly larger circle at the current (last) ply so it
            # stands out as the cursor position.
            rad = 4 if i == n - 1 else 2.5
            arcade.draw_circle_filled(px, py, rad, col_dot)
            # Thin accent outline on every dot so white dots stay
            # visible against the light fill and black dots stay
            # visible against the dark fill.
            arcade.draw_circle_outline(px, py, rad, COLOR_ACCENT, 1)

        # ── X-axis labels: ply index with W/B tag ─────────────────────
        # Each history entry after ply 0 has a .mover (True=White,
        # False=Black). We show short tick labels at regular intervals
        # so the axis stays readable as the game grows.
        # Pick a stride so we render at most ~8 ticks — dense labels
        # overlap on smaller games, sparse labels keep the axis legible.
        tick_stride = max(1, (n - 1) // 8)
        axis_y = y_bot - 2
        # Also draw a thin tick mark at each sample column
        for i in range(1, n):
            p = pts[i]
            if p.mover is None:
                continue
            px_tick = x0 + (i / max(1, n - 1)) * w
            # Thin vertical tick
            arcade.draw_line(px_tick, y_bot, px_tick, y_bot - 3,
                             COLOR_GRAPH_AXIS, 1)
            if (i - 1) % tick_stride == 0 or i == n - 1:
                move_num = (p.ply + 1) // 2
                tag = "W" if p.mover is True else "B"
                arcade.draw_text(f"{move_num}{tag}",
                                 px_tick - 6, axis_y - 8,
                                 COLOR_GRAPH_AXIS, font_size=7)

        # Axis caption (tiny, below the labels). Moved down one line so
        # it doesn't crowd the tick numbers.
        arcade.draw_text("ply  ●=White move  ●=Black move",
                         x0, y_bot - 18, COLOR_TEXT_DIM, font_size=7)

        # Y-axis labels: clearly mark +scale at top = White advantage
        # and -scale at bottom = Black advantage. The sign convention
        # is the most common confusion so we spell it out.
        arcade.draw_text(f"+{scale/100:.1f} (White)",
                         x0 + 1, y_top - 10,
                         COLOR_GRAPH_AXIS, font_size=7)
        arcade.draw_text(f"-{scale/100:.1f} (Black)",
                         x0 + 1, y_bot + 1,
                         COLOR_GRAPH_AXIS, font_size=7)

    def _draw_bars(self, tracker, y_bot, y_top):
        h = y_top - y_bot
        w = self.width - 12
        x0 = self.left + 6
        mid_y = (y_top + y_bot) / 2

        # Remember the plot rect for ply_at()
        self._plot_rects["bar"] = (x0, y_bot, x0 + w, y_top)

        arcade.draw_line(x0, mid_y, x0 + w, mid_y,
                         COLOR_GRAPH_ZERO, 1)

        # Combined delta stream in ply order, but we only plot moves,
        # not the ply-0 entry.
        deltas = [(p.ply, p.mover, p.delta)
                  for p in tracker.history if p.mover is not None]
        if not deltas:
            arcade.draw_text("Δ per ply — green = gain, red = loss",
                             x0, y_bot + 1, COLOR_TEXT_DIM, font_size=7)
            return

        n = len(deltas)
        # Scale: deltas are typically smaller than absolute cp; use a dedicated scale
        max_abs_d = max(50.0, max(abs(d) for _, _, d in deltas))
        half = h / 2 - 2

        bar_w = max(1.5, (w / n) * 0.72)
        gap = (w / n) - bar_w

        # Stride for labelling so tiny bars don't get label-spam
        label_stride = max(1, n // 10)

        for i, (_ply, mover, delta) in enumerate(deltas):
            cx = x0 + (i + 0.5) * (bar_w + gap)
            # delta is from mover's POV already: +=good, -=bad
            bh = (abs(delta) / max_abs_d) * half
            if delta >= 0:
                col = COLOR_GRAPH_DELTA_GOOD
                arcade.draw_lbwh_rectangle_filled(
                    cx - bar_w / 2, mid_y, bar_w, bh, col)
            else:
                col = COLOR_GRAPH_DELTA_BAD
                arcade.draw_lbwh_rectangle_filled(
                    cx - bar_w / 2, mid_y - bh, bar_w, bh, col)

            # Small mover indicator at the bar base: a 2-px tick above
            # for White, below for Black. Cleaner than letter spam.
            if mover is True:
                arcade.draw_line(cx - bar_w / 2, mid_y + 1,
                                 cx + bar_w / 2, mid_y + 1,
                                 (240, 240, 245, 200), 1)
            elif mover is False:
                arcade.draw_line(cx - bar_w / 2, mid_y - 1,
                                 cx + bar_w / 2, mid_y - 1,
                                 (40, 40, 50, 220), 1)

            # W/B tag above the bar at stride intervals (and always the last one)
            if i % label_stride == 0 or i == n - 1:
                tag = "W" if mover is True else "B"
                tag_col = ((240, 240, 245, 220) if mover is True
                           else (160, 160, 170, 220))
                arcade.draw_text(tag, cx - 3, y_top - 8,
                                 tag_col, font_size=7)

        # Legend moved up to bar title level (was overlapping footer)
        arcade.draw_text("Δ per ply — green = gain, red = loss",
                         x0, y_top + 2, COLOR_TEXT_DIM, font_size=7)
