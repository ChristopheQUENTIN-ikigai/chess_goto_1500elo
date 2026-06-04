"""
eval_tracker.py — per-move evaluation history.

Records a centipawn evaluation (from White's perspective, as is standard)
after every move pushed on the board, plus the per-move delta, plus a
per-player running sum of losses.

Usage:
    tracker = EvalTracker()
    tracker.record(ply=0, cp=0)                # initial position
    # after White plays:
    tracker.record(ply=1, cp=engine.get_eval_cp(), mover=chess.WHITE)
    # after Black plays:
    tracker.record(ply=2, cp=engine.get_eval_cp(), mover=chess.BLACK)

    tracker.history        -> list[EvalPoint]
    tracker.white_deltas   -> [delta_cp after each white move]
    tracker.black_deltas   -> [delta_cp after each black move]
    tracker.max_abs_cp     -> float (for graph auto-scale)
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class EvalPoint:
    ply: int           # 0 = initial position, 1 = after move 1, etc.
    cp: float          # centipawns, from White's POV
    mover: Optional[bool]  # chess.WHITE / chess.BLACK / None for initial
    delta: float       # change in cp vs. previous point (from mover's POV:
                       #   positive = good for the mover, negative = blunder-ish)


class EvalTracker:
    """Records evaluation after every move and supplies plot-ready data."""

    # Clamp extreme mate-scores so they don't destroy the graph scale.
    # Anything ≥ +CLAMP_CP is treated as "clearly winning" for plotting only.
    CLAMP_CP = 1000.0

    def __init__(self):
        self.history: list[EvalPoint] = []
        self.reset()

    def reset(self):
        """Start fresh — record ply 0 at 0.0 cp."""
        self.history = [EvalPoint(ply=0, cp=0.0, mover=None, delta=0.0)]

    def record(self, ply: int, cp: float, mover: Optional[bool]):
        """Append an eval point. `cp` is raw centipawns from White's POV.
        `mover` is the color that *just* moved (None for ply 0)."""
        cp_c = max(-self.CLAMP_CP, min(self.CLAMP_CP, float(cp)))

        prev_cp = self.history[-1].cp if self.history else 0.0
        raw_delta = cp_c - prev_cp
        # Flip sign for black: a drop in White-POV cp is good for Black.
        if mover is False:   # chess.BLACK == False
            player_delta = -raw_delta
        else:
            player_delta = raw_delta

        self.history.append(EvalPoint(
            ply=ply, cp=cp_c, mover=mover, delta=player_delta))

    def pop(self):
        """Drop the last eval point (for undo)."""
        if len(self.history) > 1:
            self.history.pop()

    # ── Plot-ready views ──────────────────────────────────────────────
    @property
    def cp_series(self) -> list[float]:
        return [p.cp for p in self.history]

    @property
    def white_deltas(self) -> list[float]:
        """Deltas after each White move (in order played)."""
        return [p.delta for p in self.history if p.mover is True]

    @property
    def black_deltas(self) -> list[float]:
        """Deltas after each Black move (in order played)."""
        return [p.delta for p in self.history if p.mover is False]

    @property
    def max_abs_cp(self) -> float:
        """Max |cp| across the history, for auto-scaling. Never below 100."""
        if not self.history:
            return 100.0
        return max(100.0, max(abs(p.cp) for p in self.history))

    # ── Summary stats ─────────────────────────────────────────────────
    def total_loss(self, is_white: bool) -> float:
        """Cumulative cp lost (negative-delta moves only) for a side.
        Useful for post-game 'accuracy' style summaries."""
        src = self.white_deltas if is_white else self.black_deltas
        return sum(-d for d in src if d < 0)

    def biggest_blunder(self, is_white: bool) -> Optional[float]:
        src = self.white_deltas if is_white else self.black_deltas
        negs = [d for d in src if d < 0]
        return min(negs) if negs else None

    def last_delta(self) -> float:
        return self.history[-1].delta if self.history else 0.0
