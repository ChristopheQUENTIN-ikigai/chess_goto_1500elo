"""
chess_engine.py — Board logic and AI move generation.
Uses python-chess for move validation and board state.
AI is implemented via minimax with alpha-beta pruning (no Stockfish).
"""
import chess
import random
import threading
from typing import Optional
from config import PIECE_VALUES, AI_STYLES, AI_OPENINGS


# ── Piece-Square Tables for positional evaluation ──────────────────
# Values are from White's perspective; flip for Black.
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

PST = {
    chess.PAWN: PST_PAWN,
    chess.KNIGHT: PST_KNIGHT,
    chess.BISHOP: PST_BISHOP,
    chess.ROOK: PST_ROOK,
    chess.QUEEN: PST_QUEEN,
    chess.KING: PST_KING_MID,
}


def _pst_value(piece_type: int, square: int, is_white: bool) -> int:
    """Get piece-square table value. Tables are from White's POV (rank 0 = row 0)."""
    if is_white:
        # Flip vertically: square on rank r maps to row (7-r)
        row = 7 - chess.square_rank(square)
        col = chess.square_file(square)
    else:
        row = chess.square_rank(square)
        col = chess.square_file(square)
    return PST.get(piece_type, [0]*64)[row * 8 + col]


def evaluate_board(board: chess.Board) -> int:
    """Evaluate board in centipawns from White's perspective."""
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    material = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
                chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}

    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if p is None:
            continue
        val = material.get(p.piece_type, 0) + _pst_value(p.piece_type, sq, p.color == chess.WHITE)
        if p.color == chess.WHITE:
            score += val
        else:
            score -= val

    # Mobility bonus
    if board.turn == chess.WHITE:
        score += len(list(board.legal_moves)) * 2
    else:
        score -= len(list(board.legal_moves)) * 2

    return score


def _order_moves(board: chess.Board):
    """Order moves for better alpha-beta pruning: captures first, then checks."""
    moves = list(board.legal_moves)
    scored = []
    for m in moves:
        s = 0
        if board.is_capture(m):
            victim = board.piece_at(m.to_square)
            attacker = board.piece_at(m.from_square)
            if victim and attacker:
                s = 10 * (victim.piece_type) - attacker.piece_type
            else:
                s = 5
        if m.promotion:
            s += 900
        board.push(m)
        if board.is_check():
            s += 50
        board.pop()
        scored.append((s, m))
    scored.sort(key=lambda x: -x[0])
    return [m for _, m in scored]


def minimax(board: chess.Board, depth: int, alpha: int, beta: int, maximizing: bool) -> int:
    """Minimax with alpha-beta pruning."""
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    if maximizing:
        max_eval = -999999
        for move in _order_moves(board):
            board.push(move)
            val = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, val)
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = 999999
        for move in _order_moves(board):
            board.push(move)
            val = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, val)
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_eval


class ChessEngine:
    def __init__(self):
        self.board = chess.Board()
        self.ai_color: bool = chess.BLACK
        self.ai_style = "normal"
        self.ai_opening = "any"
        self._lock = threading.Lock()

    # ── Style & Opening ──
    def set_ai_style(self, key: str):
        if key in AI_STYLES:
            self.ai_style = key

    def set_ai_opening(self, key: str):
        if key in AI_OPENINGS:
            self.ai_opening = key

    @property
    def ai_depth(self) -> int:
        """Search depth based on style."""
        depths = {"beginner": 1, "normal": 3, "aggressive": 3, "defensive": 3}
        return depths.get(self.ai_style, 3)

    # ── Moves ──
    def get_legal_moves(self):
        return list(self.board.legal_moves)

    def try_move(self, fr: int, to: int) -> bool:
        move = chess.Move(fr, to)
        p = self.board.piece_at(fr)
        if p and p.piece_type == chess.PAWN:
            tr = chess.square_rank(to)
            if (p.color == chess.WHITE and tr == 7) or (p.color == chess.BLACK and tr == 0):
                move = chess.Move(fr, to, promotion=chess.QUEEN)
        if move in self.board.legal_moves:
            self.board.push(move)
            return True
        return False

    def undo(self):
        if self.board.move_stack:
            self.board.pop()
            return True
        return False

    def reset(self):
        self.board.reset()

    # ── Queries ──
    def get_fen(self): return self.board.fen()
    def move_history_san(self):
        t = chess.Board(); out = []
        for m in self.board.move_stack:
            out.append(t.san(m)); t.push(m)
        return out
    def move_history_uci(self):
        return [m.uci() for m in self.board.move_stack]
    def is_white_turn(self): return self.board.turn == chess.WHITE
    def is_check(self): return self.board.is_check()
    def is_checkmate(self): return self.board.is_checkmate()
    def is_stalemate(self): return self.board.is_stalemate()
    def is_game_over(self): return self.board.is_game_over()
    def game_result(self):
        if self.board.is_checkmate():
            return "0-1" if self.board.turn == chess.WHITE else "1-0"
        if self.board.is_stalemate() or self.board.is_insufficient_material():
            return "1/2-1/2"
        return None
    def get_king_square(self, c): return self.board.king(c)
    def last_move(self):
        return self.board.move_stack[-1] if self.board.move_stack else None

    # ── AI Move ──
    def get_ai_move(self) -> Optional[chess.Move]:
        """Get AI move using book moves then minimax."""
        # Try book move first
        forced = self._forced_book_move()
        if forced and forced in self.board.legal_moves:
            return forced

        # Minimax search
        depth = self.ai_depth
        maximizing = (self.board.turn == chess.WHITE)
        best_move = None
        best_val = -999999 if maximizing else 999999

        with self._lock:
            moves = _order_moves(self.board)
            # Add randomness for beginner
            if self.ai_style == "beginner" and random.random() < 0.3:
                return random.choice(moves) if moves else None

            for move in moves:
                self.board.push(move)
                val = minimax(self.board, depth - 1, -999999, 999999, not maximizing)
                self.board.pop()

                # Style adjustments
                if self.ai_style == "aggressive":
                    if self.board.is_capture(move):
                        val += 15 if maximizing else -15
                elif self.ai_style == "defensive":
                    if self.board.is_capture(move):
                        val -= 10 if maximizing else 10

                if maximizing:
                    if val > best_val:
                        best_val = val
                        best_move = move
                else:
                    if val < best_val:
                        best_val = val
                        best_move = move

        return best_move

    def _forced_book_move(self) -> Optional[chess.Move]:
        if self.ai_opening == "any":
            return None
        book = AI_OPENINGS.get(self.ai_opening)
        if not book or self.board.turn != self.ai_color:
            return None
        moves = book["white"] if self.ai_color == chess.WHITE else book["black"]
        idx = len(self.board.move_stack) // 2 if self.ai_color == chess.WHITE else (len(self.board.move_stack) - 1) // 2
        if idx < 0 or idx >= len(moves):
            return None
        try:
            m = chess.Move.from_uci(moves[idx])
            return m if m in self.board.legal_moves else None
        except:
            return None

    # ── Simple evaluation for display ──
    def get_eval_cp(self) -> int:
        """Get centipawn evaluation of current position."""
        return evaluate_board(self.board)

    def get_best_move_san(self) -> str:
        """Get best move in SAN notation (quick shallow search)."""
        maximizing = (self.board.turn == chess.WHITE)
        best_move = None
        best_val = -999999 if maximizing else 999999
        for move in _order_moves(self.board):
            self.board.push(move)
            val = minimax(self.board, 2, -999999, 999999, not maximizing)
            self.board.pop()
            if maximizing and val > best_val:
                best_val = val; best_move = move
            elif not maximizing and val < best_val:
                best_val = val; best_move = move
        if best_move:
            return self.board.san(best_move)
        return "?"
