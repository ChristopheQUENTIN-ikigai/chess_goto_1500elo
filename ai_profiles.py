"""
ai_profiles.py — Multiple AI difficulty levels with distinct personalities.
Each AI profile has its own:
  - Search depth (controls lookahead)
  - Evaluation weights (material, position, mobility, king safety)
  - Behavioral traits (aggression, randomness, opening preference)
  - Piece-square table scaling
  - Quiescence search depth
  - Error injection for lower levels

Profiles range from ELO ~400 (Beginner) to ~1800+ (Master).
"""
import chess
import random
import math
import time
from typing import Optional
from dataclasses import dataclass, field


# ── AI Profile Definition ────────────────────────────────────────────

@dataclass
class AIProfile:
    """Complete AI personality definition."""
    name: str
    elo_estimate: int
    description: str

    # Search parameters
    depth: int = 3                  # Main search depth
    quiescence_depth: int = 0       # Extra depth for captures at leaf
    time_limit: float = 5.0         # Max seconds per move (iterative deepening)
    use_iterative_deepening: bool = False

    # Evaluation weights (multipliers on base evaluation)
    material_weight: float = 1.0    # How much material matters
    position_weight: float = 1.0    # Piece-square table weight
    mobility_weight: float = 1.0    # Legal move count bonus
    king_safety_weight: float = 1.0 # King exposure penalty
    pawn_structure_weight: float = 0.5  # Pawn weakness penalties

    # Behavioral traits
    aggression: float = 0.0         # Bonus for captures/checks (-1 to 1)
    randomness: float = 0.0         # Random noise added to eval (0 to 1)
    blunder_rate: float = 0.0       # Chance of picking a random move (0 to 1)
    contempt: int = 0               # Positive = avoid draws, negative = seek draws

    # Opening behavior
    book_depth: int = 0             # How many book moves to play
    preferred_openings: list = field(default_factory=list)


# ── Pre-defined Profiles ─────────────────────────────────────────────

PROFILES = {
    "beginner": AIProfile(
        name="Beginner Bot",
        elo_estimate=400,
        description="Just learning the rules. Makes frequent mistakes.",
        depth=1,
        quiescence_depth=0,
        time_limit=1.0,
        material_weight=1.0,
        position_weight=0.2,    # Barely understands positioning
        mobility_weight=0.0,    # Ignores mobility
        king_safety_weight=0.1,
        pawn_structure_weight=0.0,
        aggression=0.0,
        randomness=0.4,         # Very random
        blunder_rate=0.25,      # Blunders 25% of the time
        book_depth=0,
    ),

    "casual": AIProfile(
        name="Casual Player",
        elo_estimate=800,
        description="Knows basics, sometimes misses tactics.",
        depth=2,
        quiescence_depth=1,
        time_limit=2.0,
        material_weight=1.0,
        position_weight=0.5,
        mobility_weight=0.3,
        king_safety_weight=0.4,
        pawn_structure_weight=0.1,
        aggression=0.1,
        randomness=0.15,
        blunder_rate=0.08,
        book_depth=3,
    ),

    "intermediate": AIProfile(
        name="Club Player",
        elo_estimate=1200,
        description="Solid fundamentals, decent tactical vision.",
        depth=3,
        quiescence_depth=2,
        time_limit=3.0,
        material_weight=1.0,
        position_weight=0.8,
        mobility_weight=0.6,
        king_safety_weight=0.7,
        pawn_structure_weight=0.3,
        aggression=0.0,
        randomness=0.05,
        blunder_rate=0.02,
        book_depth=6,
    ),

    "advanced": AIProfile(
        name="Tournament Player",
        elo_estimate=1500,
        description="Strong positional play, sharp tactics.",
        depth=4,
        quiescence_depth=3,
        time_limit=5.0,
        use_iterative_deepening=True,
        material_weight=1.0,
        position_weight=1.0,
        mobility_weight=0.8,
        king_safety_weight=1.0,
        pawn_structure_weight=0.5,
        aggression=0.0,
        randomness=0.02,
        blunder_rate=0.0,
        book_depth=8,
    ),

    "master": AIProfile(
        name="Master",
        elo_estimate=1800,
        description="Deep calculation, excellent positional judgment.",
        depth=5,
        quiescence_depth=4,
        time_limit=8.0,
        use_iterative_deepening=True,
        material_weight=1.0,
        position_weight=1.0,
        mobility_weight=1.0,
        king_safety_weight=1.2,
        pawn_structure_weight=0.7,
        aggression=0.0,
        randomness=0.0,
        blunder_rate=0.0,
        book_depth=10,
    ),

    # ── Personality variants ──
    "attacker": AIProfile(
        name="The Attacker",
        elo_estimate=1300,
        description="Aggressive, sacrificial, seeks king attacks.",
        depth=3,
        quiescence_depth=3,
        time_limit=4.0,
        material_weight=0.85,   # Willing to sacrifice material
        position_weight=0.9,
        mobility_weight=1.0,
        king_safety_weight=1.5, # Heavily weights opponent king exposure
        pawn_structure_weight=0.2,
        aggression=0.5,         # Strong capture/check bonus
        randomness=0.05,
        book_depth=5,
        preferred_openings=["italian", "kings_gambit", "sicilian"],
    ),

    "fortress": AIProfile(
        name="The Fortress",
        elo_estimate=1300,
        description="Ultra-defensive, builds walls, grinds you down.",
        depth=3,
        quiescence_depth=2,
        time_limit=4.0,
        material_weight=1.1,    # Values material highly
        position_weight=1.0,
        mobility_weight=0.5,
        king_safety_weight=0.8,
        pawn_structure_weight=1.0,  # Loves solid pawns
        aggression=-0.3,        # Avoids exchanges
        randomness=0.03,
        contempt=-20,           # OK with draws
        book_depth=6,
        preferred_openings=["london", "caro_kann", "french"],
    ),

    "gambiteer": AIProfile(
        name="The Gambiteer",
        elo_estimate=1100,
        description="Loves sacrifices and gambit play. Unpredictable.",
        depth=3,
        quiescence_depth=2,
        time_limit=3.0,
        material_weight=0.7,    # Material? What material?
        position_weight=1.1,
        mobility_weight=1.2,    # Initiative is everything
        king_safety_weight=1.3,
        pawn_structure_weight=0.1,
        aggression=0.7,         # Maximum aggression
        randomness=0.1,
        book_depth=4,
        preferred_openings=["kings_gambit", "sicilian"],
    ),
}


# ── Piece-Square Tables ──────────────────────────────────────────────
# (Reused from chess_engine but applied with profile weights)

PST_PAWN = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]
PST_KNIGHT = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]
PST_BISHOP = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]
PST_ROOK = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
]
PST_QUEEN = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]
PST_KING_MID = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
]
PST_KING_END = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50,
]

_PST = {
    chess.PAWN: PST_PAWN, chess.KNIGHT: PST_KNIGHT,
    chess.BISHOP: PST_BISHOP, chess.ROOK: PST_ROOK,
    chess.QUEEN: PST_QUEEN, chess.KING: PST_KING_MID,
}
MATERIAL = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
            chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}


def _pst_val(piece_type, square, is_white, is_endgame=False):
    if piece_type == chess.KING and is_endgame:
        table = PST_KING_END
    else:
        table = _PST.get(piece_type, [0] * 64)
    row = (7 - chess.square_rank(square)) if is_white else chess.square_rank(square)
    col = chess.square_file(square)
    return table[row * 8 + col]


def _is_endgame(board: chess.Board) -> bool:
    """Simple endgame detection: no queens or queens + minor only."""
    queens = 0
    minors = 0
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if p is None:
            continue
        if p.piece_type == chess.QUEEN:
            queens += 1
        elif p.piece_type in (chess.KNIGHT, chess.BISHOP):
            minors += 1
    return queens == 0 or (queens <= 2 and minors <= 2)


# ── Profile-Aware Evaluation ─────────────────────────────────────────

def evaluate_with_profile(board: chess.Board, profile: AIProfile) -> int:
    """Evaluate position using a specific AI profile's weights."""
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return profile.contempt  # Profiles can prefer/avoid draws

    endgame = _is_endgame(board)
    score = 0

    # Material
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if p is None:
            continue
        mat = MATERIAL.get(p.piece_type, 0) * profile.material_weight
        pos = _pst_val(p.piece_type, sq, p.color == chess.WHITE, endgame) * profile.position_weight
        val = mat + pos
        if p.color == chess.WHITE:
            score += val
        else:
            score -= val

    # Mobility
    mob = len(list(board.legal_moves)) * 3 * profile.mobility_weight
    if board.turn == chess.WHITE:
        score += mob
    else:
        score -= mob

    # King safety (simple: count attacks near king)
    if profile.king_safety_weight > 0:
        for color in [chess.WHITE, chess.BLACK]:
            ksq = board.king(color)
            if ksq is None:
                continue
            opp = not color
            danger = 0
            kf, kr = chess.square_file(ksq), chess.square_rank(ksq)
            for df in range(-1, 2):
                for dr in range(-1, 2):
                    nf, nr = kf + df, kr + dr
                    if 0 <= nf <= 7 and 0 <= nr <= 7:
                        nsq = chess.square(nf, nr)
                        if board.is_attacked_by(opp, nsq):
                            danger += 1
            penalty = danger * 15 * profile.king_safety_weight
            if color == chess.WHITE:
                score -= penalty
            else:
                score += penalty

    # Pawn structure
    if profile.pawn_structure_weight > 0:
        for color in [chess.WHITE, chess.BLACK]:
            pawn_files = {}
            for sq in chess.SQUARES:
                p = board.piece_at(sq)
                if p and p.piece_type == chess.PAWN and p.color == color:
                    f = chess.square_file(sq)
                    pawn_files.setdefault(f, []).append(sq)

            penalty = 0
            for f, sqs in pawn_files.items():
                if len(sqs) > 1:
                    penalty += 20  # Doubled
                has_neighbor = (f > 0 and (f - 1) in pawn_files) or \
                               (f < 7 and (f + 1) in pawn_files)
                if not has_neighbor:
                    penalty += 15  # Isolated

            penalty = int(penalty * profile.pawn_structure_weight)
            if color == chess.WHITE:
                score -= penalty
            else:
                score += penalty

    # Randomness injection
    if profile.randomness > 0:
        noise = random.gauss(0, profile.randomness * 50)
        score += int(noise)

    return int(score)


# ── Move Ordering ────────────────────────────────────────────────────

def order_moves_profiled(board: chess.Board, profile: AIProfile):
    """Order moves with profile-aware scoring."""
    moves = list(board.legal_moves)
    scored = []
    for m in moves:
        s = 0
        if board.is_capture(m):
            victim = board.piece_at(m.to_square)
            attacker = board.piece_at(m.from_square)
            if victim and attacker:
                s = 10 * victim.piece_type - attacker.piece_type
            s += int(profile.aggression * 30)
        if m.promotion:
            s += 900
        # Check bonus
        board.push(m)
        if board.is_check():
            s += 50 + int(profile.aggression * 20)
        board.pop()
        scored.append((s, m))
    scored.sort(key=lambda x: -x[0])
    return [m for _, m in scored]


# ── Profiled Minimax Search ──────────────────────────────────────────

def _quiescence(board: chess.Board, alpha: int, beta: int,
                profile: AIProfile, depth: int = 0) -> int:
    """Quiescence search: extend search through capture sequences."""
    stand_pat = evaluate_with_profile(board, profile)

    if board.turn == chess.WHITE:
        if stand_pat >= beta:
            return beta
        alpha = max(alpha, stand_pat)
    else:
        if stand_pat <= alpha:
            return alpha
        beta = min(beta, stand_pat)

    if depth >= profile.quiescence_depth:
        return stand_pat

    # Only search captures
    for move in board.legal_moves:
        if not board.is_capture(move):
            continue
        board.push(move)
        val = _quiescence(board, alpha, beta, profile, depth + 1)
        board.pop()

        if board.turn == chess.WHITE:
            if val > alpha:
                alpha = val
            if alpha >= beta:
                return beta
        else:
            if val < beta:
                beta = val
            if alpha >= beta:
                return alpha

    return alpha if board.turn == chess.WHITE else beta


def minimax_profiled(board: chess.Board, depth: int, alpha: int, beta: int,
                     maximizing: bool, profile: AIProfile) -> int:
    """Minimax with profile-aware evaluation and quiescence."""
    if board.is_game_over():
        return evaluate_with_profile(board, profile)
    if depth == 0:
        if profile.quiescence_depth > 0:
            return _quiescence(board, alpha, beta, profile)
        return evaluate_with_profile(board, profile)

    if maximizing:
        max_eval = -999999
        for move in order_moves_profiled(board, profile):
            board.push(move)
            val = minimax_profiled(board, depth - 1, alpha, beta, False, profile)
            board.pop()
            max_eval = max(max_eval, val)
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = 999999
        for move in order_moves_profiled(board, profile):
            board.push(move)
            val = minimax_profiled(board, depth - 1, alpha, beta, True, profile)
            board.pop()
            min_eval = min(min_eval, val)
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_eval


# ── Profile-Aware AI Player ─────────────────────────────────────────

class ProfiledAI:
    """AI player with a specific profile. Used for both GUI and headless play."""

    def __init__(self, profile_name: str = "intermediate"):
        if profile_name not in PROFILES:
            profile_name = "intermediate"
        self.profile = PROFILES[profile_name]
        self.profile_name = profile_name
        self.nodes_searched = 0

    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Get best move for current position using this profile."""
        moves = list(board.legal_moves)
        if not moves:
            return None

        # Blunder check — occasionally pick random move
        if self.profile.blunder_rate > 0 and random.random() < self.profile.blunder_rate:
            return random.choice(moves)

        maximizing = (board.turn == chess.WHITE)

        if self.profile.use_iterative_deepening:
            return self._iterative_deepening(board, maximizing)

        return self._fixed_depth_search(board, maximizing)

    def _fixed_depth_search(self, board: chess.Board,
                            maximizing: bool) -> Optional[chess.Move]:
        """Standard fixed-depth search."""
        best_move = None
        best_val = -999999 if maximizing else 999999
        self.nodes_searched = 0

        for move in order_moves_profiled(board, self.profile):
            board.push(move)
            self.nodes_searched += 1
            val = minimax_profiled(board, self.profile.depth - 1,
                                   -999999, 999999, not maximizing, self.profile)
            board.pop()

            if maximizing and val > best_val:
                best_val = val
                best_move = move
            elif not maximizing and val < best_val:
                best_val = val
                best_move = move

        return best_move

    def _iterative_deepening(self, board: chess.Board,
                             maximizing: bool) -> Optional[chess.Move]:
        """Iterative deepening with time limit."""
        start = time.time()
        best_move = None

        for depth in range(1, self.profile.depth + 1):
            if time.time() - start > self.profile.time_limit:
                break

            current_best = None
            current_val = -999999 if maximizing else 999999
            self.nodes_searched = 0

            for move in order_moves_profiled(board, self.profile):
                if time.time() - start > self.profile.time_limit:
                    break

                board.push(move)
                self.nodes_searched += 1
                val = minimax_profiled(board, depth - 1,
                                       -999999, 999999, not maximizing,
                                       self.profile)
                board.pop()

                if maximizing and val > current_val:
                    current_val = val
                    current_best = move
                elif not maximizing and val < current_val:
                    current_val = val
                    current_best = move

            if current_best:
                best_move = current_best

        return best_move

    def evaluate_position(self, board: chess.Board) -> int:
        """Get this profile's evaluation of the position."""
        return evaluate_with_profile(board, self.profile)
