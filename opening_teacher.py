"""
opening_teacher.py — Interactive opening repertoire trainer.
Lets the player select a famous opening and guides them through it
move by move, showing the correct moves, explaining the ideas,
and letting them practice both sides.

Works standalone (no Prolog required) with a built-in opening library.
"""
import chess
from dataclasses import dataclass, field


@dataclass
class OpeningLine:
    """A complete opening line to teach."""
    name: str
    eco: str
    moves_san: list[str]      # Moves in SAN notation
    moves_uci: list[str] = field(default_factory=list)  # Auto-computed
    explanations: list[str] = field(default_factory=list)  # Per-move explanation
    summary: str = ""
    themes: list[str] = field(default_factory=list)
    difficulty: str = "beginner"  # beginner, intermediate, advanced


# ── Opening Library ──────────────────────────────────────────────────

OPENING_LIBRARY: list[OpeningLine] = [
    OpeningLine(
        name="Italian Game",
        eco="C50",
        moves_san=["e4", "e5", "Nf3", "Nc6", "Bc4"],
        explanations=[
            "1.e4 — Control the center and open lines for your bishop and queen.",
            "1...e5 — Black mirrors, claiming central space.",
            "2.Nf3 — Develop the knight toward the center, attacking e5.",
            "2...Nc6 — Defend e5 and develop a piece.",
            "3.Bc4 — The Italian bishop! Targets f7, the weakest square in Black's camp.",
        ],
        summary="The Italian Game develops pieces quickly toward the center and kingside. White's bishop on c4 eyes the vulnerable f7 pawn. Plan: castle kingside, then push d4.",
        themes=["center_control", "development", "f7_pressure"],
        difficulty="beginner",
    ),
    OpeningLine(
        name="Giuoco Piano",
        eco="C53",
        moves_san=["e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5"],
        explanations=[
            "1.e4 — Seize the center.",
            "1...e5 — Black matches the center.",
            "2.Nf3 — Attack e5, develop toward center.",
            "2...Nc6 — Defend and develop.",
            "3.Bc4 — Italian bishop aims at f7.",
            "3...Bc5 — Black mirrors! Both bishops are active. The 'Quiet Game' begins.",
        ],
        summary="Giuoco Piano ('Quiet Game') leads to rich middlegames. Both sides develop classically. White aims for d4; Black should aim for ...d5.",
        themes=["classical", "symmetrical_development"],
        difficulty="beginner",
    ),
    OpeningLine(
        name="Ruy Lopez",
        eco="C60",
        moves_san=["e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4", "Nf6", "O-O"],
        explanations=[
            "1.e4 — Central pawn, opening diagonals.",
            "1...e5 — Classical response.",
            "2.Nf3 — Develops and attacks e5.",
            "2...Nc6 — Defends e5.",
            "3.Bb5 — The Ruy Lopez! Puts pressure on the knight defending e5.",
            "3...a6 — The Morphy Defense. Asks the bishop: stay or retreat?",
            "4.Ba4 — Maintain the pin. The bishop stays active.",
            "4...Nf6 — Counter-attack e4! Develop with tempo.",
            "5.O-O — Castle early for king safety. The most common continuation.",
        ],
        summary="The Ruy Lopez is one of the oldest and most respected openings. White builds long-term pressure on e5 while developing harmoniously. Black aims for ...d5 to equalize.",
        themes=["strategic", "long_term_pressure", "classical"],
        difficulty="intermediate",
    ),
    OpeningLine(
        name="Sicilian Defense",
        eco="B20",
        moves_san=["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4"],
        explanations=[
            "1.e4 — White takes the center.",
            "1...c5 — The Sicilian! Fights for d4 asymmetrically.",
            "2.Nf3 — Prepares d4, develops naturally.",
            "2...d6 — Supports e5 square, prepares ...Nf6.",
            "3.d4 — White opens the center aggressively.",
            "3...cxd4 — Black captures, opening the c-file for counterplay.",
            "4.Nxd4 — White has a central knight. The Open Sicilian begins!",
        ],
        summary="The Sicilian creates asymmetric, fighting positions. White gets central space; Black gets the semi-open c-file and queenside counterplay. The most popular response to 1.e4.",
        themes=["asymmetric", "tactical", "counterplay"],
        difficulty="intermediate",
    ),
    OpeningLine(
        name="Queen's Gambit Declined",
        eco="D30",
        moves_san=["d4", "d5", "c4", "e6", "Nc3", "Nf6", "Bg5", "Be7"],
        explanations=[
            "1.d4 — Central pawn. Opens the diagonal for the bishop.",
            "1...d5 — Symmetrical center.",
            "2.c4 — The Queen's Gambit! Challenges d5 for center control.",
            "2...e6 — Decline the gambit. Solid defense of d5.",
            "3.Nc3 — Develop and add pressure to d5.",
            "3...Nf6 — Defend d5 again, develop the knight.",
            "4.Bg5 — Pin the knight! Classic QGD pressure.",
            "4...Be7 — Break the pin, prepare to castle.",
        ],
        summary="The QGD is the cornerstone of classical chess. Black builds a solid pawn chain (d5-e6) while White applies systematic pressure. Strategic, rich middlegames.",
        themes=["solid", "strategic", "pawn_chain"],
        difficulty="intermediate",
    ),
    OpeningLine(
        name="King's Indian Defense",
        eco="E60",
        moves_san=["d4", "Nf6", "c4", "g6", "Nc3", "Bg7", "e4", "d6", "Nf3", "O-O"],
        explanations=[
            "1.d4 — White claims center space.",
            "1...Nf6 — Flexible knight move. Doesn't commit pawn structure yet.",
            "2.c4 — Expand in the center.",
            "2...g6 — Preparing the fianchetto! The King's Indian signature.",
            "3.Nc3 — Develop and support e4.",
            "3...Bg7 — The fianchettoed bishop! A monster on the long diagonal.",
            "4.e4 — White builds a big center. Looks imposing!",
            "4...d6 — Solid. Prepares ...e5 counter-strike.",
            "5.Nf3 — Complete development.",
            "5...O-O — Castle first, fight later. Black will strike with ...e5.",
        ],
        summary="The King's Indian lets White build a big center, then Black attacks it with ...e5 (or ...c5). The Bg7 is a monster. Leads to rich, double-edged middlegames.",
        themes=["fianchetto", "counter_attack", "kingside_attack"],
        difficulty="intermediate",
    ),
    OpeningLine(
        name="French Defense",
        eco="C00",
        moves_san=["e4", "e6", "d4", "d5", "Nc3", "Nf6"],
        explanations=[
            "1.e4 — Center pawn.",
            "1...e6 — The French! Prepares ...d5 with solid support.",
            "2.d4 — White builds a classical center.",
            "2...d5 — Challenge e4 immediately. The French pawn chain begins.",
            "3.Nc3 — Defend e4, develop.",
            "3...Nf6 — Attack e4 again! Consistent pressure.",
        ],
        summary="The French Defense creates a pawn chain (e6-d5 vs e4-d4). Black's plan: undermine White's center with ...c5. The light-squared bishop can be a problem for Black.",
        themes=["pawn_chain", "solid", "strategic"],
        difficulty="beginner",
    ),
    OpeningLine(
        name="Caro-Kann Defense",
        eco="B10",
        moves_san=["e4", "c6", "d4", "d5", "Nc3", "dxe4", "Nxe4", "Bf5"],
        explanations=[
            "1.e4 — Center pawn.",
            "1...c6 — The Caro-Kann! Prepares ...d5 while keeping the light bishop free.",
            "2.d4 — Classical center.",
            "2...d5 — Challenge the center.",
            "3.Nc3 — Defend e4.",
            "3...dxe4 — Exchange! Open the position.",
            "4.Nxe4 — White has a strong centralized knight.",
            "4...Bf5 — THIS is why Caro-Kann! The bishop is OUTSIDE the pawn chain.",
        ],
        summary="The Caro-Kann is solid and reliable. Unlike the French, Black's light bishop gets out before ...e6. The main trade-off: Black spends two moves (...c6, ...d5) on one pawn.",
        themes=["solid", "reliable", "active_bishop"],
        difficulty="beginner",
    ),
    OpeningLine(
        name="London System",
        eco="D00",
        moves_san=["d4", "d5", "Bf4", "Nf6", "e3", "c5", "c3", "Nc6", "Nd2"],
        explanations=[
            "1.d4 — Claim the center.",
            "1...d5 — Mirror center.",
            "2.Bf4 — The London! Develop the bishop BEFORE playing e3.",
            "2...Nf6 — Natural development.",
            "3.e3 — Solid. The bishop is already out, so e3 doesn't trap it.",
            "3...c5 — Black challenges the d4 pawn.",
            "4.c3 — Support d4. The London triangle (d4-e3-c3) is solid.",
            "4...Nc6 — Develop naturally.",
            "5.Nd2 — Knight goes to d2 (not c3) to support e4 push later.",
        ],
        summary="The London System is a low-theory, solid opening. The Bf4-e3-c3 setup works against almost anything. Plan: Nd2, Ngf3, Bd3, O-O, then Re1 and e4.",
        themes=["system", "solid", "low_theory"],
        difficulty="beginner",
    ),
    OpeningLine(
        name="Sicilian Najdorf",
        eco="B90",
        moves_san=["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "a6"],
        explanations=[
            "1.e4 — Center.",
            "1...c5 — Sicilian.",
            "2.Nf3 — Prepare d4.",
            "2...d6 — The main line. Supports e5 square.",
            "3.d4 — Open it up!",
            "3...cxd4 — Take, opening the c-file.",
            "4.Nxd4 — Centralized knight.",
            "4...Nf6 — Attack e4, develop.",
            "5.Nc3 — Defend e4, develop.",
            "5...a6 — The Najdorf! Bobby Fischer's weapon. Prevents Bb5, prepares ...e5 or ...b5.",
        ],
        summary="The Najdorf is the sharpest Sicilian. 5...a6 is flexible: it prepares ...e5 (controlling center) or ...b5 (queenside expansion). Enormously complex theory. Fischer and Kasparov's favorite.",
        themes=["complex", "sharp", "queenside_expansion"],
        difficulty="advanced",
    ),
    OpeningLine(
        name="Scotch Game",
        eco="C45",
        moves_san=["e4", "e5", "Nf3", "Nc6", "d4", "exd4", "Nxd4"],
        explanations=[
            "1.e4 — Center.",
            "1...e5 — Classical.",
            "2.Nf3 — Develop, attack e5.",
            "2...Nc6 — Defend.",
            "3.d4! — The Scotch! Immediately opens the center.",
            "3...exd4 — Black must capture.",
            "4.Nxd4 — White has a powerful centralized knight and open lines.",
        ],
        summary="The Scotch Game opens the center immediately, leading to active piece play. Less theoretical than the Ruy Lopez but very direct. Kasparov revived it in the 1990s.",
        themes=["open_center", "active_play", "direct"],
        difficulty="beginner",
    ),
    OpeningLine(
        name="Slav Defense",
        eco="D10",
        moves_san=["d4", "d5", "c4", "c6", "Nf3", "Nf6", "Nc3", "dxc4"],
        explanations=[
            "1.d4 — Center.",
            "1...d5 — Solid center.",
            "2.c4 — Queen's Gambit.",
            "2...c6 — The Slav! Supports d5 with c6 instead of e6.",
            "3.Nf3 — Develop.",
            "3...Nf6 — Counter-pressure on e4 square.",
            "4.Nc3 — Develop, pressure d5.",
            "4...dxc4 — Take the pawn! The Semi-Slav capture. Black plans ...b5 to hold it.",
        ],
        summary="The Slav defends d5 with ...c6, keeping the light-squared bishop free (unlike QGD). Very solid. Many world champions have used it.",
        themes=["solid", "light_bishop_free", "reliable"],
        difficulty="intermediate",
    ),
]


def _compute_uci(line: OpeningLine):
    """Pre-compute UCI moves for an opening line."""
    if line.moves_uci:
        return
    board = chess.Board()
    uci = []
    for san in line.moves_san:
        try:
            move = board.parse_san(san)
            uci.append(move.uci())
            board.push(move)
        except:
            break
    line.moves_uci = uci


# Initialize UCI for all openings
for _line in OPENING_LIBRARY:
    _compute_uci(_line)


# ── Opening Teacher State Machine ────────────────────────────────────

class OpeningTeacher:
    """Interactive opening teacher. Guides the player through an opening
    move by move, showing explanations and highlighting correct moves."""

    def __init__(self):
        self.active = False
        self.current_line: Optional[OpeningLine] = None
        self.current_step = 0           # Which move we're on (0-indexed)
        self.player_color = chess.WHITE  # Which color the player is practicing
        self.board = chess.Board()
        self.messages: list[str] = []
        self.hint_square_from: Optional[int] = None
        self.hint_square_to: Optional[int] = None
        self.completed = False

    def start(self, opening_index: int, player_color: bool = chess.WHITE):
        """Start teaching a specific opening."""
        if opening_index < 0 or opening_index >= len(OPENING_LIBRARY):
            return

        self.current_line = OPENING_LIBRARY[opening_index]
        self.player_color = player_color
        self.current_step = 0
        self.board = chess.Board()
        self.active = True
        self.completed = False
        self.hint_square_from = None
        self.hint_square_to = None

        self.messages = [
            f"=== LEARNING: {self.current_line.name} [{self.current_line.eco}] ===",
            self.current_line.summary,
            "",
        ]

        # If player is Black, auto-play White's first move
        if player_color == chess.BLACK and self.current_step < len(self.current_line.moves_san):
            self._auto_play_opponent()
        else:
            self._show_current_step()

    def stop(self):
        """Stop teaching."""
        self.active = False
        self.current_line = None
        self.messages = ["Teaching mode ended."]

    def _show_current_step(self):
        """Show explanation for current step and hint."""
        if not self.current_line or self.current_step >= len(self.current_line.moves_san):
            self._finish()
            return

        # Show explanation
        if self.current_step < len(self.current_line.explanations):
            self.messages.append(self.current_line.explanations[self.current_step])

        # Is it the player's turn to move?
        is_player_turn = self.board.turn == self.player_color
        if is_player_turn:
            expected_san = self.current_line.moves_san[self.current_step]
            self.messages.append(f"YOUR TURN: Play {expected_san}")
            # Show hint squares
            try:
                move = self.board.parse_san(expected_san)
                self.hint_square_from = move.from_square
                self.hint_square_to = move.to_square
            except:
                self.hint_square_from = None
                self.hint_square_to = None
        else:
            self.messages.append("Opponent's move...")
            self._auto_play_opponent()

    def try_player_move(self, from_sq: int, to_sq: int) -> bool:
        """Check if the player's move matches the expected opening move.
        Returns True if move was accepted (correct or we allow it)."""
        if not self.active or not self.current_line:
            return False
        if self.current_step >= len(self.current_line.moves_san):
            return False
        if self.board.turn != self.player_color:
            return False

        # Check if it matches
        expected_san = self.current_line.moves_san[self.current_step]
        try:
            expected_move = self.board.parse_san(expected_san)
        except:
            return False

        attempted = chess.Move(from_sq, to_sq)
        # Handle promotion
        p = self.board.piece_at(from_sq)
        if p and p.piece_type == chess.PAWN:
            tr = chess.square_rank(to_sq)
            if (p.color == chess.WHITE and tr == 7) or (p.color == chess.BLACK and tr == 0):
                attempted = chess.Move(from_sq, to_sq, promotion=chess.QUEEN)

        if attempted == expected_move:
            # Correct!
            san = self.board.san(attempted)
            self.board.push(attempted)
            self.current_step += 1
            self.hint_square_from = None
            self.hint_square_to = None
            self.messages.append(f"Correct! {san}")

            # Show next step or finish
            if self.current_step < len(self.current_line.moves_san):
                self._show_current_step()
            else:
                self._finish()
            return True
        else:
            # Wrong move
            self.messages.append(f"Not quite! The opening move is {expected_san}.")
            self.messages.append("Try again.")
            return False

    def _auto_play_opponent(self):
        """Play the opponent's move automatically."""
        if self.current_step >= len(self.current_line.moves_san):
            self._finish()
            return

        san = self.current_line.moves_san[self.current_step]
        try:
            move = self.board.parse_san(san)
            self.board.push(move)
            self.current_step += 1

            # Show explanation
            if self.current_step - 1 < len(self.current_line.explanations):
                self.messages.append(self.current_line.explanations[self.current_step - 1])

            # Next step
            if self.current_step < len(self.current_line.moves_san):
                self._show_current_step()
            else:
                self._finish()
        except Exception as e:
            self.messages.append(f"Error in opening line: {e}")

    def _finish(self):
        """Opening line completed."""
        self.completed = True
        self.hint_square_from = None
        self.hint_square_to = None
        self.messages.append("")
        self.messages.append("Opening complete! You can now play freely.")
        if self.current_line:
            themes = ", ".join(t.replace("_", " ") for t in self.current_line.themes)
            self.messages.append(f"Key themes: {themes}")

    def get_opening_list(self) -> list[tuple[int, str, str, str]]:
        """Get list of available openings: (index, name, eco, difficulty)."""
        return [(i, o.name, o.eco, o.difficulty)
                for i, o in enumerate(OPENING_LIBRARY)]

    def get_board(self) -> chess.Board:
        """Get the teaching board state."""
        return self.board
