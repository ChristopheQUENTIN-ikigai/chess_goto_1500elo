"""
prolog_reasoner.py — Chess reasoning via Prolog (janus_swi).

CRITICAL FIX: janus.query() returns an iterator that MUST be fully consumed
or explicitly closed. Partially-consumed iterators cause:
    AttributeError: 'query' object has no attribute 'state'
SOLUTION: We ONLY use janus.query_once() here. For multi-result queries
we use Prolog's findall/3 wrapped in query_once(), which is always safe.
"""
import chess
import os
from typing import Optional
from config import PIECE_VALUES, PROLOG_RULES_PATH

try:
    import janus_swi as janus
    PROLOG_AVAILABLE = True
except ImportError:
    PROLOG_AVAILABLE = False
    print("[PrologReasoner] janus_swi not available. Using Python-only analysis.")

PT = {chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop",
      chess.ROOK: "rook", chess.QUEEN: "queen", chess.KING: "king"}
PV = {"pawn": 1, "knight": 3, "bishop": 3, "rook": 5, "queen": 9, "king": 0}
FILE_NAMES = "abcdefgh"


class ThreatWarning:
    def __init__(self, threat_type, severity, square=None, piece_name="",
                 attacker_squares=None, details="", target_squares=None):
        self.threat_type = threat_type
        self.severity = severity
        self.square = square
        self.piece_name = piece_name
        self.attacker_squares = attacker_squares or []
        self.target_squares = target_squares or []
        self.details = details

    def __repr__(self):
        sn = chess.square_name(self.square) if self.square is not None else "?"
        return f"<{self.threat_type}:{self.severity} {self.piece_name}@{sn}>"


class OpeningInfo:
    def __init__(self, name="", eco="", plan="", themes=None):
        self.name = name
        self.eco = eco
        self.plan = plan
        self.themes = themes or []


# ── Safe Prolog wrappers ─────────────────────────────────────────────

def _qonce(goal: str):
    """Safe query_once — returns dict on success, None on failure/error."""
    try:
        r = janus.query_once(goal)
        return r if r not in (False, None) else None
    except Exception:
        return None


def _findall(template: str, goal: str) -> list:
    """Safe multi-result via findall/3 + query_once. No iterator issues."""
    try:
        r = janus.query_once(f"findall({template}, ({goal}), _ResultList)")
        if r and '_ResultList' in r:
            return list(r['_ResultList'])
    except Exception:
        pass
    return []


class PrologReasoner:
    def __init__(self, prolog_rules_path=PROLOG_RULES_PATH):
        self._last_warnings: list[ThreatWarning] = []
        self._last_opening: Optional[OpeningInfo] = None
        self._prolog_loaded = False

        if PROLOG_AVAILABLE and os.path.exists(prolog_rules_path):
            try:
                janus.consult(prolog_rules_path)
                self._prolog_loaded = True
                print(f"[PrologReasoner] Loaded rules: {prolog_rules_path}")
            except Exception as e:
                print(f"[PrologReasoner] Could not load rules: {e}")

    @property
    def prolog_available(self):
        return PROLOG_AVAILABLE and self._prolog_loaded

    # ── Assert board state ────────────────────────────────────────────
    def _assert_board(self, board: chess.Board):
        if not self.prolog_available:
            return
        try:
            # Retract everything
            for pred in ['piece_at', 'pawn_on', 'in_check', 'has_legal_move',
                         'attacks', 'defends', 'has_piece', 'piece_count',
                         'king_unmoved', 'rook_unmoved',
                         'castling_path_clear', 'castling_path_attacked']:
                for arity in ['(_)', '(_,_)', '(_,_,_)']:
                    _qonce(f"retractall({pred}{arity})")

            total_pieces = 0
            for sq in chess.SQUARES:
                p = board.piece_at(sq)
                if p is None:
                    continue
                total_pieces += 1
                c = "white" if p.color == chess.WHITE else "black"
                pt = PT[p.piece_type]
                sn = chess.square_name(sq)
                _qonce(f"assert(piece_at({sn}, {c}, {pt}))")
                _qonce(f"assert(has_piece({c}, {pt}, {sn}))")
                if p.piece_type == chess.PAWN:
                    fn = FILE_NAMES[chess.square_file(sq)]
                    rk = chess.square_rank(sq) + 1
                    _qonce(f"assert(pawn_on({c}, {fn}, {rk}))")

            _qonce(f"assert(piece_count({total_pieces}))")

            for cb, cs in [(chess.WHITE, "white"), (chess.BLACK, "black")]:
                if board.is_check() and board.turn == cb:
                    _qonce(f"assert(in_check({cs}))")
                tb = board.copy()
                if tb.turn != cb:
                    try:
                        tb.push(chess.Move.null())
                    except:
                        continue
                if list(tb.legal_moves):
                    _qonce(f"assert(has_legal_move({cs}))")

            if board.has_kingside_castling_rights(chess.WHITE):
                _qonce("assert(king_unmoved(white))")
                _qonce("assert(rook_unmoved(white, kingside))")
            if board.has_queenside_castling_rights(chess.WHITE):
                _qonce("assert(king_unmoved(white))")
                _qonce("assert(rook_unmoved(white, queenside))")
            if board.has_kingside_castling_rights(chess.BLACK):
                _qonce("assert(king_unmoved(black))")
                _qonce("assert(rook_unmoved(black, kingside))")
            if board.has_queenside_castling_rights(chess.BLACK):
                _qonce("assert(king_unmoved(black))")
                _qonce("assert(rook_unmoved(black, queenside))")
        except Exception as e:
            print(f"[PrologReasoner] Assert error: {e}")

    # ── Opening advice ────────────────────────────────────────────────
    # Pure-Python knowledge base mirroring the (optional) Prolog rules in
    # data/chess_rules.pl. Kept here so opening advice works identically
    # whether or not SWI-Prolog/janus is installed.
    _OPENING_PRINCIPLES = [
        "Control the center squares (e4, d4, e5, d5) with pawns and pieces.",
        "Develop knights and bishops before moving the queen or rooks.",
        "Castle early to protect the king and connect the rooks.",
    ]

    def get_opening_advice(self, move_number: int, color: str) -> list[str]:
        advice: list[str] = []
        # Phase-specific tip (mirrors opening_advice/3 in chess_rules.pl).
        if move_number <= 3:
            advice.append(
                "Focus on controlling the center with pawns (e4/d4 or e5/d5).")
        elif move_number <= 6:
            advice.append("Develop knights and bishops toward the center.")
        elif move_number <= 10:
            # castling_advice/2 equivalent — reuse the colour-aware helper.
            col = chess.WHITE if str(color).lower().startswith("w") else chess.BLACK
            board = getattr(self, "_last_board", None)
            if isinstance(board, chess.Board):
                advice.append(self.get_castling_advice(board, col))
            else:
                advice.append("Castle early to safeguard your king.")
        else:
            advice.append(
                "Transition to middlegame: connect rooks and find a plan.")
        # General principles (mirrors the first few opening_principle/3 facts).
        advice.extend(self._OPENING_PRINCIPLES)
        return advice

    # ── Pawn structure ────────────────────────────────────────────────
    def get_pawn_structure_advice(self, board: chess.Board, color: bool) -> list[str]:
        self._assert_board(board)
        cs = "white" if color == chess.WHITE else "black"
        advice = []
        if self.prolog_available:
            results = _findall("A", f"pawn_structure_advice({cs}, A)")
            for r in results[:5]:
                advice.append(str(r))
        if not advice:
            advice = self._python_pawn_analysis(board, color)
        return advice

    # ── Castling advice ───────────────────────────────────────────────
    def get_castling_advice(self, board: chess.Board, color: bool) -> str:
        self._assert_board(board)
        cs = "white" if color == chess.WHITE else "black"
        if self.prolog_available:
            r = _qonce(f"castling_advice({cs}, Advice)")
            if r and 'Advice' in r:
                return str(r['Advice'])
        if board.has_kingside_castling_rights(color):
            return "Castle kingside for safety."
        elif board.has_queenside_castling_rights(color):
            return "Castle queenside."
        return "Cannot castle — protect king by other means."

    # ── Opening classification ────────────────────────────────────────
    def classify_opening(self, moves_uci: list[str]) -> Optional[OpeningInfo]:
        if not moves_uci:
            self._last_opening = None
            return None

        # Always use Python-based classification (reliable, fast)
        # Prolog DB is used for advice; Python book for matching
        return self._python_classify_opening(moves_uci)

    # ── Full threat analysis ──────────────────────────────────────────
    def analyze(self, board: chess.Board) -> list[ThreatWarning]:
        # NOTE (v12 perf): we deliberately do NOT call _assert_board() here.
        # Every helper below (_hanging/_forks/_king_safety/_mate_threats/
        # _discovered_checks_against) is pure Python and reads the board
        # object directly — none of them query the asserted Prolog facts.
        # Asserting the board cost ~39 retractalls + up to 64*3 asserts plus
        # board copies and null-move pushes on EVERY move, for results that
        # were never used. Removing it is a free CPU win with zero behaviour
        # change. (Prolog facts are still asserted on demand by the pawn /
        # castling advice methods that actually consult them.)
        w = []
        us = board.turn
        them = not us
        w += self._hanging(board, us)
        w += self._forks(board, them)
        w += self._king_safety(board, us)
        w += self._mate_threats(board, us)
        # Incoming discovered checks: opponent has a piece whose moves
        # (on their turn) could reveal a check against our king from
        # a piece behind it. We list these as warnings so the Threats
        # panel can flag "discovered check coming".
        w += self._discovered_checks_against(board, us)
        self._last_warnings = w
        return w

    @property
    def last_warnings(self):
        return self._last_warnings

    @property
    def last_opening(self):
        return self._last_opening

    def get_threat_squares(self) -> set[int]:
        s = set()
        for w in self._last_warnings:
            if w.square is not None:
                s.add(w.square)
            s.update(w.attacker_squares)
            s.update(w.target_squares)
        return s

    def find_discovered_check_opportunities(self, board: chess.Board,
                                             color: bool) -> list[dict]:
        """Return all discovered-check ideas for `color` from the
        current position. Each entry describes ONE legal move by a
        blocking piece that reveals a check from a piece behind it.

        Returned dict shape:
            {
              "blocker_from": int,   # square the masking piece starts on
              "blocker_to":   int,   # square it moves to
              "revealer":     int,   # square of the piece giving check
                                     # AFTER the move
              "move":         chess.Move,
              "san":          str,
              "gives_direct_check": bool,  # True if the blocker ALSO
                                     # delivers its own check on the
                                     # destination (double check)
            }

        Implementation: for each legal move, we check whether
        (a) the resulting board is in check AND
        (b) the piece on the destination square is NOT itself the
            attacker delivering the check (otherwise it's a normal
            direct check, not a discovered one).
        For double checks we still flag it — that's the most powerful
        form of discovered check and the Hint button should highlight
        these aggressively."""
        if board.is_game_over():
            return []
        out = []
        # Build a probe where it's `color`'s turn. If it isn't, push a
        # null move. Null-move push is illegal if we're in check, so
        # we skip discovered-check *opportunity* detection in that
        # case — the player has more pressing concerns than setting up
        # a long-term trap.
        probe = board.copy()
        if probe.turn != color:
            if probe.is_check():
                return []
            try:
                probe.push(chess.Move.null())
            except Exception:
                return []

        opp_king = probe.king(not color)
        if opp_king is None:
            return []

        for move in probe.legal_moves:
            piece = probe.piece_at(move.from_square)
            if not piece or piece.color != color:
                continue
            # Skip king moves — a king cannot unmask a check (moving it
            # into check would be illegal anyway).
            if piece.piece_type == chess.KING:
                continue

            after = probe.copy()
            after.push(move)
            if not after.is_check():
                continue

            # Who's giving check? Collect every attacker of the
            # opponent king on the `after` board.
            attackers = after.attackers(color, opp_king)
            if not attackers:
                continue

            # Discovered check = at least one attacker is on a square
            # *other* than move.to_square. (If all attackers are on
            # move.to_square, it's a plain direct check by the piece
            # we just moved — not discovered.)
            revealers = [sq for sq in attackers if sq != move.to_square]
            if not revealers:
                continue

            # Record ONE revealer per opportunity for UI clarity;
            # prefer a revealer that is a long-range piece (Q/R/B).
            # This is almost always unique in practice.
            def _rank(sq):
                p = after.piece_at(sq)
                if not p:
                    return 9
                order = {chess.QUEEN: 0, chess.ROOK: 1, chess.BISHOP: 2,
                         chess.KNIGHT: 3, chess.PAWN: 4, chess.KING: 5}
                return order.get(p.piece_type, 9)
            revealer = min(revealers, key=_rank)

            # Double check? (blocker also attacks the king from its
            # new square.) The SAN representation already marks this
            # as "++", but we flag it explicitly so callers don't
            # need to parse SAN.
            double = (move.to_square in attackers)

            try:
                san = probe.san(move)
            except Exception:
                san = move.uci()

            out.append({
                "blocker_from": move.from_square,
                "blocker_to":   move.to_square,
                "revealer":     revealer,
                "move":         move,
                "san":          san,
                "gives_direct_check": double,
            })
        return out

    def _discovered_checks_against(self, board: chess.Board,
                                    us: bool) -> list[ThreatWarning]:
        """Scan the opponent's potential moves for discovered checks
        that would expose our king. Returns ThreatWarning entries with
        threat_type='discovered_check'. One warning per distinct
        (blocker, revealer) pair — we don't enumerate all blocker
        destinations to keep the panel readable."""
        them = not us
        opps = self.find_discovered_check_opportunities(board, them)
        if not opps:
            return []

        # Collapse by (blocker_from, revealer) so we don't repeat
        # "knight at f3 can reveal check from bishop at c4" once per
        # legal knight destination.
        seen = {}
        for opp in opps:
            key = (opp["blocker_from"], opp["revealer"])
            if key in seen:
                continue
            seen[key] = opp

        out = []
        for (blk_from, rev), opp in seen.items():
            blk_piece = board.piece_at(blk_from)
            rev_piece = board.piece_at(rev)
            if not blk_piece or not rev_piece:
                continue
            blk_name = PT[blk_piece.piece_type]
            rev_name = PT[rev_piece.piece_type]
            double_note = " (DOUBLE check!)" if opp["gives_direct_check"] else ""
            out.append(ThreatWarning(
                "discovered_check",
                "critical" if opp["gives_direct_check"] else "high",
                square=blk_from,
                piece_name=blk_name,
                attacker_squares=[rev, blk_from],
                target_squares=[board.king(us)] if board.king(us) is not None else [],
                details=(
                    f"Discovered check coming: opp {blk_name}@{chess.square_name(blk_from)} "
                    f"could move and reveal {rev_name}@{chess.square_name(rev)} "
                    f"attacking your king{double_note}."
                ),
            ))
        return out

    # ── Python fallbacks ──────────────────────────────────────────────
    def _hanging(self, b, color):
        out = []
        opp = not color
        for sq in chess.SQUARES:
            p = b.piece_at(sq)
            if not p or p.color != color or p.piece_type == chess.KING:
                continue
            if b.is_attacked_by(opp, sq) and not b.is_attacked_by(color, sq):
                n = PT[p.piece_type]
                v = PV.get(n, 0)
                out.append(ThreatWarning(
                    "hanging", "high" if v >= 3 else "medium", sq, n,
                    list(b.attackers(opp, sq)),
                    f"Your {n} on {chess.square_name(sq)} is undefended!"))
        return out

    def _forks(self, b, atk_color):
        out = []
        def_color = not atk_color
        for sq in chess.SQUARES:
            p = b.piece_at(sq)
            if not p or p.color != atk_color:
                continue
            targets = []
            for tsq in chess.SQUARES:
                tp = b.piece_at(tsq)
                if not tp or tp.color != def_color or tp.piece_type == chess.PAWN:
                    continue
                if sq in b.attackers(atk_color, tsq):
                    targets.append(tsq)
            if len(targets) >= 2:
                names = [f"{PT[b.piece_at(t).piece_type]}@{chess.square_name(t)}"
                         for t in targets if b.piece_at(t)]
                out.append(ThreatWarning(
                    "fork", "high", sq, PT[p.piece_type],
                    target_squares=targets,
                    details=f"Opp {PT[p.piece_type]}@{chess.square_name(sq)} forks {', '.join(names)}"))
        return out

    def _king_safety(self, b, color):
        out = []
        kingsq = b.king(color)
        if kingsq is None:
            return out
        mn = len(b.move_stack) // 2
        kf, kr = chess.square_file(kingsq), chess.square_rank(kingsq)
        if mn >= 8:
            if (color == chess.WHITE and kr == 0 and 2 <= kf <= 5) or \
               (color == chess.BLACK and kr == 7 and 2 <= kf <= 5):
                out.append(ThreatWarning(
                    "uncastled", "medium", kingsq, "king",
                    details="King still in center! Castle soon."))
        return out

    def _mate_threats(self, b, color):
        out = []
        t = b.copy()
        if t.turn != (not color):
            try:
                t.push(chess.Move.null())
            except:
                return out
        for m in t.legal_moves:
            t2 = t.copy()
            t2.push(m)
            if t2.is_checkmate():
                out.append(ThreatWarning(
                    "mate_threat", "critical", m.to_square, "",
                    details=f"Opponent threatens mate with {t.san(m)}!"))
                break
        return out

    def _python_pawn_analysis(self, board, color):
        advice = []
        files_with_pawns = {}
        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if p and p.piece_type == chess.PAWN and p.color == color:
                f = chess.square_file(sq)
                files_with_pawns.setdefault(f, []).append(sq)
        for f, sqs in files_with_pawns.items():
            if len(sqs) > 1:
                advice.append(f"Doubled pawns on {FILE_NAMES[f]}-file.")
        for f in files_with_pawns:
            has_neighbor = (f > 0 and (f-1) in files_with_pawns) or \
                           (f < 7 and (f+1) in files_with_pawns)
            if not has_neighbor:
                advice.append(f"Isolated pawn on {FILE_NAMES[f]}-file.")
        if not advice:
            advice.append("Solid pawn structure.")
        return advice

    def _python_classify_opening(self, moves_uci) -> Optional[OpeningInfo]:
        from _opening_book import OPENING_DATABASE
        best = None
        best_depth = 0
        for name, eco, san_moves, uci_moves, themes, plan in OPENING_DATABASE:
            book_len = len(uci_moves)
            if len(moves_uci) >= book_len:
                if moves_uci[:book_len] == uci_moves and book_len > best_depth:
                    best_depth = book_len
                    best = OpeningInfo(name, eco, plan, themes)
            else:
                if uci_moves[:len(moves_uci)] == moves_uci:
                    partial = len(moves_uci)
                    if partial > best_depth:
                        best_depth = partial
                        best = OpeningInfo(f"{name} (developing...)", eco, plan, themes)
        self._last_opening = best
        return best
