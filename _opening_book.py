"""
_opening_book.py — Built-in opening database for fallback when Prolog is unavailable.
Pre-computes UCI move sequences for reliable matching.
"""
import chess

_RAW = [
    ("Italian Game", "C50", ["e4","e5","Nf3","Nc6","Bc4"],
     ["center_control","development"], "Develop quickly, control center, prepare castling."),
    ("Giuoco Piano", "C53", ["e4","e5","Nf3","Nc6","Bc4","Bc5"],
     ["center_control","classical"], "Both develop bishops. White aims for d4."),
    ("Ruy Lopez", "C60", ["e4","e5","Nf3","Nc6","Bb5"],
     ["strategic","pressure"], "Long-term pressure on e5. Prepare d4."),
    ("Scotch Game", "C45", ["e4","e5","Nf3","Nc6","d4"],
     ["open_center","tactical"], "Open center immediately."),
    ("King's Gambit", "C30", ["e4","e5","f4"],
     ["gambit","kingside_attack"], "Pawn sacrifice for center and initiative."),
    ("Petrov's Defense", "C42", ["e4","e5","Nf3","Nf6"],
     ["symmetrical","solid"], "Mirror defense. Solid, equal."),
    ("Sicilian Defense", "B20", ["e4","c5"],
     ["asymmetric","complex"], "Fight for d4 asymmetrically."),
    ("Sicilian Najdorf", "B90", ["e4","c5","Nf3","d6","d4","cxd4","Nxd4","Nf6","Nc3","a6"],
     ["complex","queenside"], "Prepares e5 or b5. Deep theory."),
    ("French Defense", "C00", ["e4","e6"],
     ["solid","pawn_chain"], "Pawn chain. Undermine with d5 and c5."),
    ("Caro-Kann Defense", "B10", ["e4","c6"],
     ["solid","reliable"], "Prepares d5 with active light bishop."),
    ("Queen's Gambit", "D06", ["d4","d5","c4"],
     ["center_control","classical"], "Challenge d5. Classical center control."),
    ("Queen's Gambit Declined", "D30", ["d4","d5","c4","e6"],
     ["solid","strategic"], "Solid defense of d5."),
    ("Slav Defense", "D10", ["d4","d5","c4","c6"],
     ["solid","light_bishop"], "Supports d5 with c6."),
    ("London System", "D00", ["d4","d5","Bf4"],
     ["system","solid"], "Bishop to f4 early. Low-theory."),
    ("King's Indian Defense", "E60", ["d4","Nf6","c4","g6"],
     ["fianchetto","kingside_attack"], "Fianchetto, prepare e5."),
    ("Nimzo-Indian Defense", "E20", ["d4","Nf6","c4","e6","Nc3","Bb4"],
     ["pin","strategic"], "Pin knight on c3. Rich play."),
    ("Grunfeld Defense", "D70", ["d4","Nf6","c4","g6","Nc3","d5"],
     ["counter_attack","dynamic"], "Challenge center with d5. Dynamic."),
    ("English Opening", "A10", ["c4"],
     ["flank","flexible"], "Control d5 from flank."),
    ("Reti Opening", "A04", ["Nf3","d5","c4"],
     ["hypermodern","flank"], "Undermine d5 from flanks."),
    ("Dutch Defense", "A80", ["d4","f5"],
     ["aggressive","kingside"], "Grab kingside space."),
    ("Scandinavian Defense", "B01", ["e4","d5"],
     ["early_queen","simple"], "Challenges e4 immediately."),
]

def _san_to_uci(san_moves):
    board = chess.Board()
    uci = []
    for san in san_moves:
        try:
            m = board.parse_san(san)
            uci.append(m.uci())
            board.push(m)
        except:
            break
    return uci

OPENING_DATABASE = []
for name, eco, san_moves, themes, plan in _RAW:
    uci_moves = _san_to_uci(san_moves)
    if len(uci_moves) == len(san_moves):
        OPENING_DATABASE.append((name, eco, san_moves, uci_moves, themes, plan))
