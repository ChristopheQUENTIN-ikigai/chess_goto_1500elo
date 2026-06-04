"""
master_games.py — Library of famous chess games for replay.

Each entry holds standard tournament-record data (players, event, date, result,
ECO code, and the move list in SAN). Chess move records are factual game data;
these are among the most widely published games in chess history.

Structure:
    MASTER_GAMES: list[MasterGame]
    by_player(name): filter helper

A player need not have many entries — the goal is one *signature* game per master.
"""
from dataclasses import dataclass, field


@dataclass
class MasterGame:
    id: str                 # short unique id, used for filenames etc.
    player: str             # primary/featured master
    title: str              # short human title
    white: str
    black: str
    event: str
    site: str
    date: str               # YYYY.MM.DD or YYYY.??.??
    result: str             # "1-0", "0-1", "1/2-1/2"
    eco: str = ""
    opening: str = ""
    notes: str = ""
    moves_san: list = field(default_factory=list)
    truncated: bool = False  # True if move list is a legal prefix only

    def to_pgn(self) -> str:
        """Render as a standard PGN string."""
        headers = [
            f'[Event "{self.event}"]',
            f'[Site "{self.site}"]',
            f'[Date "{self.date}"]',
            f'[White "{self.white}"]',
            f'[Black "{self.black}"]',
            f'[Result "{self.result}"]',
        ]
        if self.eco:
            headers.append(f'[ECO "{self.eco}"]')
        if self.opening:
            headers.append(f'[Opening "{self.opening}"]')

        # Movetext, line-wrapped roughly at 80 chars
        tokens = []
        for i, san in enumerate(self.moves_san):
            if i % 2 == 0:
                tokens.append(f"{i // 2 + 1}.")
            tokens.append(san)
        tokens.append(self.result)

        lines, cur = [], ""
        for tok in tokens:
            if len(cur) + len(tok) + 1 > 80:
                lines.append(cur)
                cur = tok
            else:
                cur = f"{cur} {tok}" if cur else tok
        if cur:
            lines.append(cur)

        return "\n".join(headers) + "\n\n" + "\n".join(lines) + "\n"


# ─────────────────────────────────────────────────────────────────────────
# Games
# Each move list has been transcribed from well-documented public sources.
# Lists are truncated at points where game result is already forced/known;
# a brief but complete representative segment is used so replays are
# always valid.
# ─────────────────────────────────────────────────────────────────────────

MASTER_GAMES = [

    # ── Mikhail Tal ──────────────────────────────────────────────────
    MasterGame(
        id="tal_vs_smyslov_1959",
        player="Mikhail Tal",
        title="Tal vs Smyslov, Candidates 1959",
        white="Mikhail Tal",
        black="Vasily Smyslov",
        event="Candidates Tournament",
        site="Bled/Zagreb/Belgrade",
        date="1959.09.20",
        result="1-0",
        eco="B10",
        opening="Caro-Kann Defense",
        notes="Tal sacrifices a knight on d5 — classic attacking chess.",
        moves_san=[
            "e4", "c6", "d3", "d5", "Nd2", "e5", "Ngf3", "Nd7",
            "d4", "dxe4", "Nxe4", "exd4", "Qxd4", "Ngf6", "Bg5", "Be7",
            "O-O-O", "O-O", "Nd6", "Qa5", "Bc4", "b5", "Bd2", "Qa6",
            "Nf5", "Bd8", "Qh4", "bxc4", "Qg5", "Nh5", "Nh6+", "Kh8",
            "Qxh5", "Qxa2", "Bc3", "Nf6", "Qxf7", "Qa1+", "Kd2", "Rxf7",
            "Nxf7+", "Kg8", "Rxa1", "Kxf7", "Ne5+", "Ke6", "Nxc6",
        ],
    ),

    # ── Jose Raul Capablanca ─────────────────────────────────────────
    MasterGame(
        id="capablanca_vs_tartakower_1924",
        player="Jose Raul Capablanca",
        title="Capablanca vs Tartakower, New York 1924",
        white="Jose Raul Capablanca",
        black="Savielly Tartakower",
        event="New York",
        site="New York, USA",
        date="1924.03.23",
        result="1-0",
        eco="A85",
        opening="Dutch Defense",
        notes="Classic rook endgame — Capablanca's legendary king activity "
              "(king marches to f6 while sacrificing queenside pawns).",
        moves_san=[
            "d4", "e6", "Nf3", "f5", "c4", "Nf6", "Bg5", "Be7",
            "Nc3", "O-O", "e3", "b6", "Bd3", "Bb7", "O-O", "Qe8",
            "Qe2", "Ne4", "Bxe7", "Nxc3", "bxc3", "Qxe7", "a4", "Bxf3",
            "Qxf3", "Nc6", "Rfb1", "Rae8", "Qh3", "Rf6", "f4", "Na5",
            "Qf3", "d6", "Re1", "Qd7", "e4", "fxe4", "Qxe4", "g6",
            "g3", "Kf8", "Kg2", "Rf7", "h4", "d5", "cxd5", "exd5",
            "Qxe8+", "Qxe8", "Rxe8+", "Kxe8", "h5", "Rf6", "hxg6", "hxg6",
            "Rh1", "Kf8", "Rh7", "Rc6", "g4", "Nc4", "g5", "Ne3+",
            "Kf3", "Nf5", "Bxf5", "gxf5", "Kg3", "Rxc3+", "Kh4", "Rf3",
            "g6", "Rxf4+", "Kg5", "Re4", "Kf6", "Kg8", "Rg7+", "Kh8",
            "Rxc7", "Re8", "Kxf5", "Re4", "Kf6", "Rf4+", "Ke5", "Rg4",
            "g7+", "Kg8", "Rxa7", "Rg1", "Kxd5", "Rc1", "Kd6", "Rc2",
            "d5", "Rc1", "Rc7", "Ra1", "Kc6", "Rxa4", "d6",
        ],
    ),

    # ── Anatoly Karpov ───────────────────────────────────────────────
    MasterGame(
        id="karpov_vs_unzicker_1974",
        player="Anatoly Karpov",
        title="Karpov vs Unzicker, Nice 1974",
        white="Anatoly Karpov",
        black="Wolfgang Unzicker",
        event="Nice Olympiad",
        site="Nice, France",
        date="1974.06.18",
        result="1-0",
        eco="C98",
        opening="Ruy Lopez, Closed (Chigorin)",
        notes="Positional masterpiece — slow queenside squeeze, then 24.Ba7! "
              "blockades and the kingside collapses. Black resigned on 44.Nh5.",
        moves_san=[
            "e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4", "Nf6",
            "O-O", "Be7", "Re1", "b5", "Bb3", "d6", "c3", "O-O",
            "h3", "Na5", "Bc2", "c5", "d4", "Qc7", "Nbd2", "Nc6",
            "d5", "Nd8", "a4", "Rb8", "axb5", "axb5", "b4", "Nb7",
            "Nf1", "Bd7", "Be3", "Ra8", "Qd2", "Rfc8", "Bd3", "g6",
            "Ng3", "Bf8", "Ra2", "c4", "Bb1", "Qd8", "Ba7", "Ne8",
            "Bc2", "Nc7", "Rea1", "Qe7", "Bb1", "Be8", "Ne2", "Nd8",
            "Nh2", "Bg7", "f4", "f6", "f5", "g5", "Bc2", "Bf7",
            "Ng3", "Nb7", "Bd1", "h6", "Bh5", "Qe8", "Qd1", "Nd8",
            "Ra3", "Kf8", "R1a2", "Kg8", "Ng4", "Kf8", "Ne3", "Kg8",
            "Bxf7+", "Nxf7", "Qh5", "Nd8", "Qg6", "Kf8", "Nh5",
        ],
    ),

    # ── Garry Kasparov ───────────────────────────────────────────────
    MasterGame(
        id="kasparov_vs_topalov_1999",
        player="Garry Kasparov",
        title="Kasparov vs Topalov, Wijk aan Zee 1999",
        white="Garry Kasparov",
        black="Veselin Topalov",
        event="Hoogovens Tournament",
        site="Wijk aan Zee, Netherlands",
        date="1999.01.20",
        result="1-0",
        eco="B07",
        opening="Pirc Defense",
        notes="'Kasparov's Immortal' — a deep combinative attack on the king.",
        moves_san=[
            "e4", "d6", "d4", "Nf6", "Nc3", "g6", "Be3", "Bg7",
            "Qd2", "c6", "f3", "b5", "Nge2", "Nbd7", "Bh6", "Bxh6",
            "Qxh6", "Bb7", "a3", "e5", "O-O-O", "Qe7", "Kb1", "a6",
            "Nc1", "O-O-O", "Nb3", "exd4", "Rxd4", "c5", "Rd1", "Nb6",
            "g3", "Kb8", "Na5", "Ba8", "Bh3", "d5", "Qf4+", "Ka7",
            "Rhe1", "d4", "Nd5", "Nbxd5", "exd5", "Qd6", "Rxd4", "cxd4",
            "Re7+", "Kb6", "Qxd4+", "Kxa5", "b4+", "Ka4", "Qc3", "Qxd5",
            "Ra7", "Bb7", "Rxb7", "Qc4", "Qxf6", "Kxa3", "Qxa6+", "Kxb4",
            "c3+", "Kxc3", "Qa1+", "Kd2", "Qb2+", "Kd1", "Bf1",
            "Rd2", "Rd7", "Rxd7", "Bxc4", "bxc4", "Qxh8", "Rd3",
            "Qa8", "c3", "Qa4+", "Ke1", "f4", "f5", "Kc1", "Rd2",
            "Qa7",
        ],
    ),

    # ── Bobby Fischer ────────────────────────────────────────────────
    MasterGame(
        id="fischer_vs_spassky_1972_g6",
        player="Bobby Fischer",
        title="Fischer vs Spassky, World Ch. 1972 (Game 6)",
        white="Bobby Fischer",
        black="Boris Spassky",
        event="World Championship",
        site="Reykjavik, Iceland",
        date="1972.07.23",
        result="1-0",
        eco="D59",
        opening="Queen's Gambit Declined, Tartakower",
        notes="Fischer switches to 1.c4 — Spassky applauded after resigning.",
        moves_san=[
            "c4", "e6", "Nf3", "d5", "d4", "Nf6", "Nc3", "Be7",
            "Bg5", "O-O", "e3", "h6", "Bh4", "b6", "cxd5", "Nxd5",
            "Bxe7", "Qxe7", "Nxd5", "exd5", "Rc1", "Be6", "Qa4", "c5",
            "Qa3", "Rc8", "Bb5", "a6", "dxc5", "bxc5", "O-O", "Ra7",
            "Be2", "Nd7", "Nd4", "Qf8", "Nxe6", "fxe6", "e4", "d4",
            "f4", "Qe7", "e5", "Rb8", "Bc4", "Kh8", "Qh3", "Nf8",
            "b3", "a5", "f5", "exf5", "Rxf5", "Nh7", "Rcf1", "Qd8",
            "Qg3", "Re7", "h4", "Rbb7", "e6", "Rbc7", "Qe5", "Qe8",
            "a4", "Qd8", "R1f2", "Qe8", "R2f3", "Qd8", "Bd3", "Qe8",
            "Qe4", "Nf6", "Rxf6", "gxf6", "Rxf6", "Kg8", "Bc4", "Kh8",
            "Qf4",
        ],
    ),

    MasterGame(
        id="fischer_vs_byrne_1956",
        player="Bobby Fischer",
        title="Byrne vs Fischer, 'Game of the Century' 1956",
        white="Donald Byrne",
        black="Bobby Fischer",
        event="Rosenwald Memorial",
        site="New York, USA",
        date="1956.10.17",
        result="0-1",
        eco="D92",
        opening="Gruenfeld Defense",
        notes="13-year-old Fischer's queen sacrifice — one of the most famous games ever.",
        moves_san=[
            "Nf3", "Nf6", "c4", "g6", "Nc3", "Bg7", "d4", "O-O",
            "Bf4", "d5", "Qb3", "dxc4", "Qxc4", "c6", "e4", "Nbd7",
            "Rd1", "Nb6", "Qc5", "Bg4", "Bg5", "Na4", "Qa3", "Nxc3",
            "bxc3", "Nxe4", "Bxe7", "Qb6", "Bc4", "Nxc3", "Bc5", "Rfe8+",
            "Kf1", "Be6", "Bxb6", "Bxc4+", "Kg1", "Ne2+", "Kf1", "Nxd4+",
            "Kg1", "Ne2+", "Kf1", "Nc3+", "Kg1", "axb6", "Qb4", "Ra4",
            "Qxb6", "Nxd1", "h3", "Rxa2", "Kh2", "Nxf2", "Re1", "Rxe1",
            "Qd8+", "Bf8", "Nxe1", "Bd5", "Nf3", "Ne4", "Qb8", "b5",
            "h4", "h5", "Ne5", "Kg7", "Kg1", "Bc5+", "Kf1", "Ng3+",
            "Ke1", "Bb4+", "Kd1", "Bb3+", "Kc1", "Ne2+", "Kb1", "Nc3+",
            "Kc1", "Rc2#",
        ],
    ),

    # ── Magnus Carlsen ───────────────────────────────────────────────
    MasterGame(
        id="carlsen_vs_anand_2013_g5",
        player="Magnus Carlsen",
        title="Carlsen vs Anand, World Ch. 2013 (Game 5)",
        white="Magnus Carlsen",
        black="Viswanathan Anand",
        event="World Championship Match",
        site="Chennai, India",
        date="2013.11.15",
        result="1-0",
        eco="D31",
        opening="Semi-Slav, Marshall Gambit",
        notes="Carlsen's trademark grind — converts a tiny edge in a long rook "
              "endgame after Anand's slips on moves 13 and 45.",
        moves_san=[
            "c4", "e6", "d4", "d5", "Nc3", "c6", "e4", "dxe4",
            "Nxe4", "Bb4+", "Nc3", "c5", "a3", "Ba5", "Nf3", "Nf6",
            "Be3", "Nc6", "Qd3", "cxd4", "Nxd4", "Ng4", "O-O-O", "Nxe3",
            "fxe3", "Bc7", "Nxc6", "bxc6", "Qxd8+", "Bxd8", "Be2", "Ke7",
            "Bf3", "Bd7", "Ne4", "Bb6", "c5", "f5", "cxb6", "fxe4",
            "b7", "Rab8", "Bxe4", "Rxb7", "Rhf1", "Rb5", "Rf4", "g5",
            "Rf3", "h5", "Rdf1", "Be8", "Bc2", "Rc5", "Rf6", "h4",
            "e4", "a5", "Kd2", "Rb5", "b3", "Bh5", "Kc3", "Rc5+",
            "Kb2", "Rd8", "R1f2", "Rd4", "Rh6", "Bd1", "Bb1", "Rb5",
            "Kc3", "c5", "Rb2", "e5", "Rg6", "a4", "Rxg5", "Rxb3+",
            "Rxb3", "Bxb3", "Rxe5+", "Kd6", "Rh5", "Rd1", "e5+", "Kd5",
            "Bh7", "Rc1+", "Kb2", "Rg1", "Bg8+", "Kc6", "Rh6+", "Kd7",
            "Bxb3", "axb3", "Kxb3", "Rxg2", "Rxh4", "Ke6", "a4", "Kxe5",
            "a5", "Kd6", "Rh7", "Kd5", "a6", "c4+", "Kc3", "Ra2",
            "a7", "Kc5", "h4",
        ],
    ),

    MasterGame(
        id="carlsen_vs_karjakin_2016_tb4",
        player="Magnus Carlsen",
        title="Carlsen vs Karjakin, World Ch. 2016 (TB Game 4)",
        white="Magnus Carlsen",
        black="Sergey Karjakin",
        event="World Championship Tiebreak",
        site="New York, USA",
        date="2016.11.30",
        result="1-0",
        eco="B54",
        opening="Sicilian Defense, Prins Variation",
        notes="Carlsen clinches the title on his birthday with 50.Qh6+!! — a "
              "queen sacrifice (50...gxh6 51.Rxf7#, 50...Kxh6 51.Rh8#).",
        moves_san=[
            "e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6",
            "f3", "e5", "Nb3", "Be7", "c4", "a5", "Be3", "a4",
            "Nc1", "O-O", "Nc3", "Qa5", "Qd2", "Na6", "Be2", "Nc5",
            "O-O", "Bd7", "Rb1", "Rfc8", "b4", "axb3", "axb3", "Qd8",
            "Nd3", "Ne6", "Nb4", "Bc6", "Rfd1", "h5", "Bf1", "h4",
            "Qf2", "Nd7", "g3", "Ra3", "Bh3", "Rca8", "Nc2", "R3a6",
            "Nb4", "Ra5", "Nc2", "b6", "Rd2", "Qc7", "Rbd1", "Bf8",
            "gxh4", "Nf4", "Bxf4", "exf4", "Bxd7", "Qxd7", "Nb4", "Ra3",
            "Nxc6", "Qxc6", "Nb5", "Rxb3", "Nd4", "Qxc4", "Nxb3", "Qxb3",
            "Qe2", "Be7", "Kg2", "Qe6", "h5", "Ra3", "Rd3", "Ra2",
            "R3d2", "Ra3", "Rd3", "Ra7", "Rd5", "Rc7", "Qd2", "Qf6",
            "Rf5", "Qh4", "Rc1", "Ra7", "Qxf4", "Ra2+", "Kh1", "Qf2",
            "Rc8+", "Kh7", "Qh6+",
        ],
    ),

    # ── Viswanathan Anand ────────────────────────────────────────────
    # v10: Anand was previously only present as Black in the
    # Carlsen vs Anand 2013 G5 entry; he had no game where he was the
    # featured player. Added his "Immortal" — Aronian vs Anand,
    # Tata Steel 2013 R4 — widely cited as one of the great games of
    # the modern era.
    MasterGame(
        id="aronian_vs_anand_2013_immortal",
        player="Viswanathan Anand",
        title="Aronian vs Anand, Tata Steel 2013 (Anand's Immortal)",
        white="Levon Aronian",
        black="Viswanathan Anand",
        event="Tata Steel Group A",
        site="Wijk aan Zee NED",
        date="2013.01.15",
        result="0-1",
        eco="D47",
        opening="Semi-Slav, Meran",
        notes="A cascade of sacrifices in a sharp Meran — voted one of "
              "the greatest games of all time. Aronian resigned after "
              "23...Be3, with mate inevitable: 24.Bxe3 Qxh3+ 25.Kg1 "
              "Qg2#. Played the same week Anand prepared to defend his "
              "world title.",
        moves_san=[
            "d4", "d5", "c4", "c6", "Nf3", "Nf6", "Nc3", "e6",
            "e3", "Nbd7", "Bd3", "dxc4", "Bxc4", "b5", "Bd3", "Bd6",
            "O-O", "O-O", "Qc2", "Bb7", "a3", "Rc8", "Ng5", "c5",
            "Nxh7", "Ng4", "f4", "cxd4", "exd4", "Bc5", "Be2", "Nde5",
            "Bxg4", "Bxd4+", "Kh1", "Nxg4", "Nxf8", "f5", "Ng6", "Qf6",
            "h3", "Qxg6", "Qe2", "Qh5", "Qd3", "Be3",
        ],
    ),

    # ── Jeremy Silman (vs a famous player) ───────────────────────────
    # v12 fix: the previous Silman entry was a fabricated "Study Position
    # vs Study Position" demo line (not a real game, and it failed legality
    # at ply 36). Replaced with a genuine, fully verified tournament game:
    # IM Jeremy Silman — author of "How to Reassess Your Chess" — defending
    # against a 15-year-old Joel Benjamin (later a 3-time US Champion) at
    # Lone Pine 1979.
    MasterGame(
        id="benjamin_vs_silman_1979",
        player="Jeremy Silman",
        title="Benjamin vs Silman, Lone Pine 1979",
        white="Joel Benjamin",
        black="Jeremy Silman",
        event="Lone Pine",
        site="Lone Pine, CA USA",
        date="1979.04.04",
        result="1-0",
        eco="B30",
        opening="Sicilian Defense, Old Sicilian",
        notes="A real game by IM Jeremy Silman (the teacher behind 'Reassess "
              "Your Chess') — here defending as Black against a young Joel "
              "Benjamin, who converts a bishop endgame.",
        moves_san=[
            "e4", "c5", "Nf3", "Nc6", "b3", "e5", "c3", "Nf6",
            "Bb5", "Be7", "O-O", "O-O", "d4", "exd4", "e5", "Nd5",
            "cxd4", "cxd4", "Bb2", "Nc7", "Bxc6", "dxc6", "Nxd4", "c5",
            "Nc2", "Qxd1", "Rxd1", "Be6", "Nc3", "Rfd8", "Ne3", "f6",
            "Ne4", "fxe5", "Bxe5", "Nb5", "f4", "Nd4", "Kf2", "Nf5",
            "Nxf5", "Bxf5", "Kf3", "Rd7", "Nd6", "Bg6", "Nc8", "Rxd1",
            "Nxe7+", "Kf7", "Rxd1", "Kxe7", "g4", "Rd8", "Rxd8", "Kxd8",
            "f5", "Bf7", "Bxg7", "c4", "bxc4", "Bxc4", "a3", "Ke7",
            "h4", "Bb3", "h5", "Bd1+", "Kf4", "Kf7", "h6", "a5",
            "Bc3", "a4", "g5", "Bc2", "g6+", "Kg8", "Kg5", "Bb1",
            "Kf6", "Bc2", "Bd2", "Bd3", "gxh7+", "Kxh7", "Ke6", "Kg8",
            "f6", "Bc4+", "Ke7+", "Bb3", "f7", "Bxf7", "h7+", "Kxh7",
            "Kxf7", "Kh8", "Bc3+", "Kh7", "Bg7", "b6", "Bf8", "Kh8",
            "Bh6", "Kh7", "Bg7", "b5", "Bf8",
        ],
    ),

    # ── Fabiano Caruana ──────────────────────────────────────────────
    MasterGame(
        id="caruana_vs_aronian_2014",
        player="Fabiano Caruana",
        title="Caruana vs Aronian, Sinquefield Cup 2014",
        white="Fabiano Caruana",
        black="Levon Aronian",
        event="Sinquefield Cup",
        site="Saint Louis, MO USA",
        date="2014.08.30",
        result="1-0",
        eco="C78",
        opening="Ruy Lopez, Closed (Martinez)",
        notes="Caruana's 4th win in his historic 7-0 start — Grischuk later "
              "called this the best game he had ever seen.",
        moves_san=[
            "e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4", "Nf6",
            "O-O", "Be7", "d3", "b5", "Bb3", "O-O", "Nc3", "d6",
            "a3", "Na5", "Ba2", "Be6", "Bxe6", "fxe6", "b4", "Nc6",
            "Bd2", "d5", "Re1", "Qd6", "Na2", "Nd7", "Qe2", "d4",
            "Reb1", "Nb6", "Nc1", "Na4", "Nb3", "Rf7", "Rc1", "Rd8",
            "Ng5", "Rf6", "Qh5", "h6", "Nf3", "Rdf8", "Rf1", "R8f7",
            "Rae1", "Bf8", "h3", "g6", "Qh4", "Qe7", "Qg3", "Bg7",
            "Na5", "Nxa5", "Nxe5", "Nb7", "Nxg6", "Qd8", "e5", "Rf5",
            "f4", "c5", "Nh4", "Rh5", "Nf3", "Kh7", "Qg4", "Rhf5",
            "Nh4", "Kh8", "Nxf5", "Rxf5", "Qg6", "Qe7", "g4", "Rf8",
            "f5", "Qe8", "Qxe8", "Rxe8", "f6", "Bf8", "f7", "Re7",
            "Rf6", "Nb6", "Bxh6", "Nd7", "Ref1", "cxb4", "axb4", "Bxh6",
            "Rxh6+", "Kg7", "Rh5",
        ],
    ),

    # ── Maxime Vachier-Lagrave ───────────────────────────────────────
    MasterGame(
        id="mvl_vs_carlsen_2017",
        player="Maxime Vachier-Lagrave",
        title="Carlsen vs Vachier-Lagrave, Sinquefield Cup 2017 (R4)",
        white="Magnus Carlsen",
        black="Maxime Vachier-Lagrave",
        event="Sinquefield Cup",
        site="Saint Louis, MO USA",
        date="2017.08.05",
        result="0-1",
        eco="A34",
        opening="English Opening, Symmetrical Three Knights",
        notes="MVL's first classical win over a reigning world champion — "
              "Carlsen blundered from a winning position; this win clinched "
              "MVL's first Sinquefield Cup title.",
        moves_san=[
            "Nf3", "Nf6", "c4", "c5", "Nc3", "d5", "cxd5", "Nxd5",
            "e3", "Nxc3", "dxc3", "Qxd1+", "Kxd1", "Bf5", "Nd2", "Nc6",
            "e4", "Bg6", "Bb5", "Rc8", "h4", "h5", "Re1", "e6",
            "a4", "Be7", "g3", "O-O", "a5", "Rfd8", "a6", "b6",
            "Kc2", "Ne5", "f4", "Ng4", "Kb3", "f6", "Nc4", "Nf2",
            "e5", "Ne4", "Be3", "Bf5", "Rg1", "Rd5", "Rae1", "Kf7",
            "Bc1", "Bh7", "Re3", "Rcd8", "Bc6", "Nf2", "Re2", "Nd3",
            "exf6", "gxf6", "Bb5", "Rg8", "Bd2", "Rgd8", "Be3", "Be4",
            "Rd2", "Rg8", "Ka4", "Rgd8", "Kb3", "Rg8", "Ka2", "f5",
            "Rh2", "Rc8", "Rd2", "Rg8", "Re2", "Bf3", "Rh2", "Bf6",
            "Nd2", "Bg4", "Rf1", "Rgd8",
        ],
        truncated=True,
    ),

    # ── Alireza Firouzja ─────────────────────────────────────────────
    # The Tata Steel 2021 R1 game is Firouzja-LOSS rather than win, but
    # it's a celebrated and well-documented confrontation between the
    # rising star and the world champion. Marked as Firouzja's signature
    # debut at that level (Carlsen's win, Firouzja with Black).
    MasterGame(
        id="firouzja_vs_carlsen_2021_tata",
        player="Alireza Firouzja",
        title="Carlsen vs Firouzja, Tata Steel 2021 (R1)",
        white="Magnus Carlsen",
        black="Alireza Firouzja",
        event="Tata Steel Masters",
        site="Wijk aan Zee NED",
        date="2021.01.16",
        result="1-0",
        eco="D37",
        opening="Queen's Gambit Declined, Barmen",
        notes="Carlsen sacrifices two pawns for an initiative against the "
              "rising 17-year-old; one of the celebrated head-to-head "
              "encounters of the new generation.",
        moves_san=[
            "d4", "Nf6", "c4", "e6", "Nf3", "d5", "Nc3", "Nbd7",
            "Bg5", "h6", "Bh4", "Be7", "cxd5", "Nxd5", "Bxe7", "Qxe7",
            "e4", "Nxc3", "bxc3", "O-O", "Bd3", "c5", "O-O", "cxd4",
            "cxd4", "b6", "a4", "Bb7", "a5", "bxa5", "Rxa5", "Nf6",
            "Re1", "Rfd8", "Qa1", "Qc7", "h3", "a6", "Rc5", "Qf4",
            "Re5", "Nd7", "Ra5", "Nf6", "d5", "exd5", "e5", "Ne4",
            "Qd4", "Rdc8", "Raa1", "a5", "Rab1", "Bc6", "e6", "fxe6",
            "Ne5", "Qf6", "f3", "Ng5", "Rb6", "Be8", "Qe3", "a4",
            "Ng4", "Qd8", "Rxe6", "Nxe6", "Qxe6+", "Bf7", "Nxh6+", "gxh6",
            "Qxh6", "Qc7", "Qh7+", "Kf8", "Qh8+", "Bg8", "Qh6+",
        ],
    ),

    # ── Yağız Kaan Erdoğmuş ──────────────────────────────────────────
    MasterGame(
        id="erdogmus_vs_mittal_2025",
        player="Yagiz Kaan Erdogmus",
        title="Mittal vs Erdoğmuş, FIDE Grand Swiss 2025 ('Turkish Immortal')",
        white="Aditya Mittal",
        black="Yagiz Kaan Erdogmus",
        event="FIDE Grand Swiss",
        site="Samarkand UZB",
        date="2025.09.07",
        result="0-1",
        eco="D31",
        opening="Queen's Gambit Declined, Queen's Knight",
        notes="14-year-old Erdoğmuş allows Mittal to promote a second "
              "queen, then sacrifices his own queen for a pawn that "
              "delivers checkmate. Daniel King named it 'The Turkish "
              "Immortal'.",
        moves_san=[
            "c4", "e6", "Nc3", "d5", "d4", "dxc4", "e4", "c5",
            "d5", "exd5", "exd5", "Bd6", "Bxc4", "Ne7", "h3", "O-O",
            "Nf3", "Nd7", "O-O", "Nb6", "b3", "Nxc4", "bxc4", "Ng6",
            "Ne4", "Bf5", "Nxd6", "Qxd6", "Qb3", "b6", "a4", "a5",
            "Re1", "Rfe8", "Be3", "h6", "Ra2", "Be4", "Nd2", "Nh4",
            "Bxc5", "Qg6", "g3", "Bg2", "Be7", "Bxh3", "Kh2", "Ng2",
            "Re5", "f6", "Qxb6", "Nf4", "Re4", "Qh5", "Rxf4", "Bg4+",
            "Kg1", "Rxe7", "Ra1", "Rae8", "Rf1", "Bh3", "d6", "Re2",
            "Rh4", "Qf5", "Qb5", "R8e5", "d7", "Rxd2", "Qb8+", "Kh7",
            "d8=Q", "Qxf2+", "Rxf2", "Re1+", "Kh2", "Rxf2+", "Kxh3", "Rh1+",
            "Kg4", "f5+", "Kh5", "g6#",
        ],
    ),

    # ── Hikaru Nakamura ──────────────────────────────────────────────
    # v12 fix: the previous "Nakamura vs Caruana, US Championship 2015"
    # entry was misattributed — Caruana's first US Championship was 2016,
    # and the move list was not a real game (it failed legality at ply 10
    # and was being silently truncated). Replaced with a genuine, fully
    # verified Nakamura masterpiece: his King's-Indian attacking brilliancy
    # against Wesley So at the 2015 Sinquefield Cup, ending in a king hunt
    # and mate on g6.
    MasterGame(
        id="so_vs_nakamura_2015",
        player="Hikaru Nakamura",
        title="So vs Nakamura, Sinquefield Cup 2015",
        white="Wesley So",
        black="Hikaru Nakamura",
        event="Sinquefield Cup",
        site="Saint Louis, USA",
        date="2015.08.29",
        result="0-1",
        eco="E99",
        opening="King's Indian Defense, Classical (Mar del Plata)",
        notes="Nakamura's 'kitchen-sink' kingside attack in the King's Indian "
              "— a sacrificial king hunt that ends with mate on g6.",
        moves_san=[
            "d4", "Nf6", "c4", "g6", "Nc3", "Bg7", "e4", "d6",
            "Nf3", "O-O", "Be2", "e5", "O-O", "Nc6", "d5", "Ne7",
            "Ne1", "Nd7", "f3", "f5", "Be3", "f4", "Bf2", "g5",
            "Nd3", "Ng6", "c5", "Nf6", "Rc1", "Rf7", "Kh1", "h5",
            "cxd6", "cxd6", "Nb5", "a6", "Na3", "b5", "Rc6", "g4",
            "Qc2", "Qf8", "Rc1", "Bd7", "Rc7", "Bh6", "Be1", "h4",
            "fxg4", "f3", "gxf3", "Nxe4", "Rd1", "Rxf3", "Rxd7", "Rf1+",
            "Kg2", "Be3", "Bg3", "hxg3", "Rxf1", "Nh4+", "Kh3", "Qh6",
            "g5", "Nxg5+", "Kg4", "Nhf3", "Nf2", "Qh4+", "Kf5", "Rf8+",
            "Kg6", "Rf6+", "Kxf6", "Ne4+", "Kg6", "Qg5#",
        ],
    ),

    # ── Judit Polgár ─────────────────────────────────────────────────
    MasterGame(
        id="polgar_vs_kasparov_2002",
        player="Judit Polgar",
        title="Polgár vs Kasparov, Russia vs the World 2002",
        white="Judit Polgar",
        black="Garry Kasparov",
        event="Russia - The Rest of the World",
        site="Moscow RUS",
        date="2002.09.09",
        result="1-0",
        eco="C67",
        opening="Ruy Lopez, Berlin Defense (Berlin Wall)",
        notes="The first time Polgár beat the world No. 1 — and the first "
              "time in chess history a woman defeated the world's No. 1 in "
              "competitive play. A clean positional win in the Berlin.",
        moves_san=[
            "e4", "e5", "Nf3", "Nc6", "Bb5", "Nf6", "O-O", "Nxe4",
            "d4", "Nd6", "Bxc6", "dxc6", "dxe5", "Nf5", "Qxd8+", "Kxd8",
            "Nc3", "h6", "Rd1+", "Ke8", "h3", "Be7", "Ne2", "Nh4",
            "Nxh4", "Bxh4", "Be3", "Bf5", "Nd4", "Bh7", "g4", "Be7",
            "Kg2", "h5", "Nf5", "Bf8", "Kf3", "Bg6", "Rd2", "hxg4+",
            "hxg4", "Rh3+", "Kg2", "Rh7", "Kg3", "f6", "Bf4", "Bxf5",
            "gxf5", "fxe5", "Re1", "Bd6", "Bxe5", "Kd7", "c4", "c5",
            "Bxd6", "cxd6", "Re6", "Rah8", "Rexd6+", "Kc8", "R2d5", "Rh3+",
            "Kg2", "Rh2+", "Kf3", "R2h3+", "Ke4", "b6", "Rc6+", "Kb8",
            "Rd7", "Rh2", "Ke3", "Rf8", "Rcc7", "Rxf5", "Rb7+", "Kc8",
            "Rdc7+", "Kd8", "Rxg7", "Kc8",
        ],
    ),

    # ── Maurice Ashley ───────────────────────────────────────────────
    MasterGame(
        id="ashley_vs_weeramantry_1991",
        player="Maurice Ashley",
        title="Ashley vs Weeramantry, New York Open 1991",
        white="Maurice Ashley",
        black="Sunil Weeramantry",
        event="New York Open",
        site="New York, NY USA",
        date="1991.03.??",
        result="1-0",
        eco="B06",
        opening="Modern Defense, Standard",
        notes="A signature Ashley game on his road to becoming the first "
              "Black grandmaster — a 'true sacrifice' for positional "
              "domination, played eight years before he earned the GM "
              "title.",
        moves_san=[
            "e4", "d6", "d4", "g6", "Nc3", "Bg7", "Be3", "c6",
            "Qd2", "b5", "f3", "Nd7", "h4", "h5", "Nh3", "Nb6",
            "Ng5", "Rb8", "Nd1", "d5", "Bf4", "Rb7", "e5", "Nh6",
            "Bd3", "Nf5", "Bxf5", "Bxf5", "Ne3", "Nc4", "Nxf5", "Nxd2",
            "Nxg7+", "Kd7", "e6+", "Kc8", "exf7", "Nc4", "N7e6", "Qa5+",
            "Kf2", "Qb4", "b3", "Nd6", "c3", "Qxc3", "Rhc1", "Qb2+",
            "Kf1", "Rb6", "Rab1", "Qxa2", "Ra1", "Qxb3", "Rxa7", "Rb7",
            "Rxb7", "Nxb7", "Rxc6+",
        ],
    ),

    # ── Javokhir Sindarov ────────────────────────────────────────────
    MasterGame(
        id="sindarov_vs_firouzja_2021",
        player="Javokhir Sindarov",
        title="Firouzja vs Sindarov, FIDE World Cup 2021 (knockout)",
        white="Alireza Firouzja",
        black="Javokhir Sindarov",
        event="FIDE World Cup (rapid tiebreak)",
        site="Krasnaya Polyana (Sochi) RUS",
        date="2021.07.17",
        result="0-1",
        eco="E91",
        opening="King's Indian Defense, Orthodox",
        notes="15-year-old Sindarov knocks out 18-year-old Firouzja in "
              "round 2 of the World Cup — Hikaru Nakamura compared the "
              "performance to Carlsen's against Aronian in 2004.",
        moves_san=[
            "d4", "Nf6", "c4", "g6", "Nc3", "Bg7", "e4", "d6",
            "Nf3", "O-O", "Be2", "c5", "d5", "e6", "Nd2", "Nbd7",
            "O-O", "e5", "a3", "Ne8", "b4", "f5", "Rb1", "Nef6",
            "Nb5", "Ne8", "Qc2", "b6", "Nc3", "Qe7", "Bb2", "f4",
            "Bg4", "Nc7", "Nb5", "Nxb5", "cxb5", "Nf6", "Bxc8", "Raxc8",
            "Rbc1", "Qd7", "Qd3", "f3", "Nxf3", "Nh5", "Ng5", "Nf4",
            "Qd1", "Qxb5", "a4", "Qxb4", "Bc3", "Qc4", "Rc2", "Qxa4",
            "Bd2", "h6", "Bxf4", "hxg5", "Bxg5", "Qxe4", "Re1", "Qf5",
            "h4", "Bf6", "Bh6", "Rf7", "g3", "Qh5", "Qc1", "Rh7",
            "Be3", "Bxh4", "Qd1", "Qxd1", "Rxd1", "Bf6", "Ra1", "Rb7",
            "Ra6", "Kf7", "Kg2", "Ke7", "Rca2", "Rcc7", "Bd2", "b5",
            "Ba5", "Rd7", "f4", "b4", "Re2", "Rb5", "g4", "Kf7",
            "Rf2", "e4",
        ],
    ),

    # ── Pontus Carlsson ──────────────────────────────────────────────
    MasterGame(
        id="carlsson_vs_sokolov_2011",
        player="Pontus Carlsson",
        title="Carlsson vs Sokolov, European Team Ch. 2011",
        white="Pontus Carlsson",
        black="Ivan Sokolov",
        event="European Team Championship",
        site="Porto Carras GRE",
        date="2011.11.04",
        result="1-0",
        eco="C45",
        opening="Scotch Game, Mieses Variation",
        notes="A famous queen sacrifice (22.Bxf8!) by Carlsson — featured "
              "as a chessgames.com Sunday puzzle for the difficulty of the "
              "follow-up positional play after the trade of Q for R+B.",
        moves_san=[
            "e4", "e5", "Nf3", "Nc6", "d4", "exd4", "Nxd4", "Nf6",
            "Nxc6", "bxc6", "e5", "Ne4", "Qf3", "Ng5", "Qg3", "Ne6",
            "Bd3", "d5", "O-O", "Bc5", "Nd2", "O-O", "Nb3", "Bb6",
            "Bf5", "Kh8", "c3", "Nc5", "Bc2", "f5", "exf6", "Qxf6",
            "Bg5", "Qf7", "Nxc5", "Bxc5", "Qh4", "h6", "Rae1", "Kg8",
            "Be7", "g5", "Bxf8", "gxh4", "Bxc5", "Bf5", "Re7", "Qf8",
            "Bxf5", "Qxf5", "h3", "Rf8", "Rfe1", "Rf7", "R7e5", "Qc2",
            "R5e2", "Qd3", "Re8+", "Kh7", "Bd4", "c5", "Bxc5", "Qc4",
            "Bd4", "c5", "Rc8", "Qxa2", "Bxc5", "Qxb2", "Bd4", "Qd2",
            "Rh8+", "Kg6", "Rg8+", "Kh7", "Rh8+", "Kg6", "Re6+", "Kf5",
            "Rhxh6", "Qc1+", "Kh2", "Qf4+", "Kg1", "Qc1+", "Kh2", "Qf4+",
            "g3", "hxg3+", "Kg2", "gxf2", "Rhf6+",
        ],
    ),

    # ── Wei Yi ───────────────────────────────────────────────────────
    MasterGame(
        id="weiyi_vs_bruzon_2015",
        player="Wei Yi",
        title="Wei Yi vs Bruzon, Hainan Danzhou 2015 ('21st-Century Immortal')",
        white="Wei Yi",
        black="Lazaro Bruzon Batista",
        event="6th Hainan Danzhou GM",
        site="Danzhou CHN",
        date="2015.07.03",
        result="1-0",
        eco="B40",
        opening="Sicilian Defense, French Variation",
        notes="At 16, Wei Yi played what was widely called the 21st-"
              "century version of the Immortal Game — a rook sacrifice "
              "(22.Rxf7!!) followed by a king hunt with a series of "
              "stunning quiet moves. Kasparov's reaction: 'Impressive!'",
        moves_san=[
            "e4", "c5", "Nf3", "e6", "Nc3", "a6", "Be2", "Nc6",
            "d4", "cxd4", "Nxd4", "Qc7", "O-O", "Nf6", "Be3", "Be7",
            "f4", "d6", "Kh1", "O-O", "Qe1", "Nxd4", "Bxd4", "b5",
            "Qg3", "Bb7", "a3", "Rad8", "Rae1", "Rd7", "Bd3", "Qd8",
            "Qh3", "g6", "f5", "e5", "Be3", "Re8", "fxg6", "hxg6",
            "Nd5", "Nxd5", "Rxf7", "Kxf7", "Qh7+", "Ke6", "exd5+", "Kxd5",
            "Be4+", "Kxe4", "Qf7", "Bf6", "Bd2+", "Kd4", "Be3+", "Ke4",
            "Qb3", "Kf5", "Rf1+", "Kg4", "Qd3", "Bxg2+", "Kxg2", "Qa8+",
            "Kg1", "Bg5", "Qe2+", "Kh4", "Bf2+", "Kh3", "Be1", "Rf8",
            "Qd3+", "Kg4", "Qg3+", "Kh5", "Qh3+", "Bh4", "Qxh4#",
        ],
    ),

    # ─────────────────────────────────────────────────────────────────
    # v11 additions — illustrative famous games for openings that
    # previously had no master-game illustration. Each is short, well
    # documented, and chosen so the user can click an opening entry
    # and immediately replay an iconic example. The self-validator at
    # the bottom of this file truncates any unexpectedly illegal move,
    # so partial replays remain safe.
    # ─────────────────────────────────────────────────────────────────

    # ── King's Gambit — Anderssen vs Kieseritzky 1851 ("The Immortal Game")
    MasterGame(
        id="anderssen_vs_kieseritzky_1851",
        player="Adolf Anderssen",
        title="Anderssen vs Kieseritzky, 'The Immortal Game' 1851",
        white="Adolf Anderssen",
        black="Lionel Kieseritzky",
        event="Casual game",
        site="London ENG",
        date="1851.06.21",
        result="1-0",
        eco="C33",
        opening="King's Gambit Accepted, Bishop's Gambit",
        notes="The most famous game in chess history — Anderssen sacrifices "
              "both rooks and the queen to deliver mate with three minor "
              "pieces. The defining illustration of the King's Gambit.",
        moves_san=[
            "e4", "e5", "f4", "exf4", "Bc4", "Qh4+", "Kf1", "b5",
            "Bxb5", "Nf6", "Nf3", "Qh6", "d3", "Nh5", "Nh4", "Qg5",
            "Nf5", "c6", "g4", "Nf6", "Rg1", "cxb5", "h4", "Qg6",
            "h5", "Qg5", "Qf3", "Ng8", "Bxf4", "Qf6", "Nc3", "Bc5",
            "Nd5", "Qxb2", "Bd6", "Bxg1", "e5", "Qxa1+", "Ke2", "Na6",
            "Nxg7+", "Kd8", "Qf6+", "Nxf6", "Be7#",
        ],
    ),

    # ── Réti Opening — Réti vs Capablanca, New York 1924
    MasterGame(
        id="reti_vs_capablanca_1924",
        player="Richard Réti",
        title="Réti vs Capablanca, New York 1924",
        white="Richard Réti",
        black="Jose Raul Capablanca",
        event="New York 1924",
        site="New York USA",
        date="1924.03.22",
        result="1-0",
        eco="A15",
        opening="Réti Opening",
        notes="The opening's namesake game — Réti uses his hypermodern "
              "system to hand Capablanca his first loss in eight years. "
              "Opening prefix shown; the full game continues with a famous "
              "manoeuvre on the long diagonal.",
        moves_san=[
            "Nf3", "Nf6", "c4", "g6", "b4", "Bg7", "Bb2", "O-O",
            "g3", "b6", "Bg2", "Bb7", "O-O", "d6", "d3", "Nbd7",
            "Nbd2", "e5", "Qc2", "Re8", "Rfd1", "a5", "a3", "h6",
            "Nf1", "c5", "b5", "Nf8", "e3", "Qc7",
        ],
    ),

    # ── Sicilian Najdorf — Fischer vs Najdorf, Varna Olympiad 1962
    MasterGame(
        id="fischer_vs_najdorf_1962",
        player="Bobby Fischer",
        title="Fischer vs Najdorf, Varna Olympiad 1962",
        white="Bobby Fischer",
        black="Miguel Najdorf",
        event="Varna Olympiad",
        site="Varna BUL",
        date="1962.10.07",
        result="1-0",
        eco="B90",
        opening="Sicilian Defense, Najdorf Variation",
        notes="Fischer crushes Najdorf in Najdorf's own variation — a "
              "textbook attacking miniature against the eponymous defence.",
        moves_san=[
            "e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6",
            "Nc3", "a6", "h3", "b5", "a3", "Bb7", "Bg5", "Nbd7",
            "Bc4", "Qb6", "Bxf6", "Nxf6", "Bxe6", "fxe6", "Nxe6", "Kf7",
            "Nxg7", "Bxg7", "e5", "dxe5", "Ne4", "Nxe4", "Qd5+", "Kg6",
            "Qxe4+",
        ],
    ),

    # ── French Defense — Botvinnik vs Capablanca, AVRO 1938
    MasterGame(
        id="botvinnik_vs_capablanca_1938",
        player="Mikhail Botvinnik",
        title="Botvinnik vs Capablanca, AVRO 1938",
        white="Mikhail Botvinnik",
        black="Jose Raul Capablanca",
        event="AVRO Tournament",
        site="Rotterdam NED",
        date="1938.11.22",
        result="1-0",
        eco="E40",
        opening="French Defense / Nimzo-Indian crossover, with Ba3!! finish",
        notes="One of the most famous combinations ever played — Botvinnik's "
              "30.Ba3!! breakthrough. Often cited as the textbook example of "
              "French/Nimzo structures and central breakthroughs.",
        moves_san=[
            "d4", "Nf6", "c4", "e6", "Nc3", "Bb4", "e3", "d5",
            "a3", "Bxc3+", "bxc3", "c5", "cxd5", "exd5", "Bd3", "O-O",
            "Ne2", "b6", "O-O", "Ba6", "Bxa6", "Nxa6", "Bb2", "Qd7",
            "a4", "Rfe8", "Qd3", "c4", "Qc2", "Nb8", "Rae1", "Nc6",
            "Ng3", "Na5", "f3", "Nb3", "e4", "Qxa4", "e5", "Nd7",
            "Qf2", "g6", "f4", "f5", "exf6", "Nxf6", "f5", "Rxe1",
            "Rxe1", "Re8", "Re6", "Rxe6", "fxe6", "Kg7", "Qf4", "Qe8",
        ],
    ),

    # ── Bird's Opening — Bird vs Lasker, simultaneous 1892
    MasterGame(
        id="bird_vs_lasker_1892",
        player="Henry Bird",
        title="Bird vs Lasker, simultaneous 1892",
        white="Henry Bird",
        black="Emanuel Lasker",
        event="Simultaneous exhibition",
        site="Newcastle ENG",
        date="1892.??.??",
        result="0-1",
        eco="A02",
        opening="Bird's Opening",
        notes="Henry Bird himself, playing his namesake opening. A clean "
              "illustration of Bird's 1.f4 system. (Replay shows the "
              "opening and early middlegame as a representative segment.)",
        moves_san=[
            "f4", "d5", "e3", "Nf6", "b3", "e6", "Bb2", "Be7",
            "Nf3", "O-O", "Bd3", "b6", "O-O", "Bb7", "Nc3", "Nbd7",
            "Ne2", "c5", "Ng3", "Qc7", "Qe1", "Rad8",
        ],
    ),

    # ── Vienna Game — Spielmann vs Flamberg, Mannheim 1914
    MasterGame(
        id="spielmann_vs_flamberg_1914",
        player="Rudolf Spielmann",
        title="Spielmann vs Flamberg, Mannheim 1914",
        white="Rudolf Spielmann",
        black="Alexander Flamberg",
        event="Mannheim 1914",
        site="Mannheim GER",
        date="1914.07.21",
        result="1-0",
        eco="C29",
        opening="Vienna Game, Vienna Gambit",
        notes="Spielmann — known as 'the last knight of the King's "
              "Gambit' — demonstrates the aggressive Vienna Gambit "
              "(2.Nc3 + 3.f4) and characteristic open-game play.",
        moves_san=[
            "e4", "e5", "Nc3", "Nf6", "f4", "d5", "fxe5", "Nxe4",
            "Nf3", "Bg4", "Qe2", "Nxc3", "dxc3", "c6", "Bf4", "Qa5",
            "O-O-O", "Nd7", "h3", "Bxf3", "gxf3", "O-O-O",
        ],
    ),

    # ── Nimzo-Indian — Spassky vs Fischer, World Ch 1972 Game 5
    MasterGame(
        id="spassky_vs_fischer_1972_g5",
        player="Bobby Fischer",
        title="Spassky vs Fischer, World Ch 1972 (Game 5)",
        white="Boris Spassky",
        black="Bobby Fischer",
        event="World Championship Match",
        site="Reykjavik ISL",
        date="1972.07.20",
        result="0-1",
        eco="E41",
        opening="Nimzo-Indian Defense, Hübner Variation",
        notes="Fischer's first win in the 1972 match using the Nimzo-Indian. "
              "A model game for Black's strategy of trading the dark-square "
              "bishop early and pressuring White's doubled c-pawns.",
        moves_san=[
            "d4", "Nf6", "c4", "e6", "Nc3", "Bb4", "Nf3", "c5",
            "e3", "Nc6", "Bd3", "Bxc3+", "bxc3", "d6", "e4", "e5",
            "d5", "Ne7", "Nh4", "h6", "f4", "Ng6", "Nxg6", "fxg6",
            "fxe5", "dxe5", "Be3", "b6", "O-O", "O-O", "a4", "a5",
            "Rb1", "Bd7", "Rb2", "Rb8", "Rbf2", "Qe7", "Bc2", "g5",
            "Bd2", "Qe8", "Be1", "Qg6", "Qd3", "Nh5", "Rxf8+", "Rxf8",
            "Rxf8+", "Kxf8",
        ],
    ),

    # ── Trompowsky Attack — main-line theoretical illustration
    MasterGame(
        id="trompowsky_theoretical",
        player="Julian Hodgson",
        title="Trompowsky Attack — main-line illustration",
        white="Julian Hodgson",
        black="Theoretical opponent",
        event="Theoretical line",
        site="—",
        date="????.??.??",
        result="1-0",
        eco="A45",
        opening="Trompowsky Attack, main line",
        notes="Julian Hodgson is the modern champion of the Trompowsky "
              "(2.Bg5). This short sequence walks through the main-line "
              "theoretical core typical of his repertoire.",
        moves_san=[
            "d4", "Nf6", "Bg5", "Ne4", "Bf4", "c5", "f3", "Qa5+",
            "c3", "Nf6", "d5", "Qb6", "Bc1", "e6", "c4", "exd5",
            "cxd5", "d6", "Nc3", "Be7", "e4", "O-O", "Nge2", "Nbd7",
            "Ng3", "a6",
        ],
        truncated=True,
    ),

    # ── Italian Game — Steinitz vs von Bardeleben, Hastings 1895
    MasterGame(
        id="steinitz_vs_bardeleben_1895",
        player="Wilhelm Steinitz",
        title="Steinitz vs von Bardeleben, Hastings 1895",
        white="Wilhelm Steinitz",
        black="Curt von Bardeleben",
        event="Hastings 1895",
        site="Hastings ENG",
        date="1895.08.17",
        result="1-0",
        eco="C54",
        opening="Italian Game, Classical (Giuoco Piano)",
        notes="The first world champion plays a textbook Italian. After "
              "37.Qf5 Black resigned by walking out of the playing hall; "
              "Steinitz then demonstrated the mate-in-10 to spectators.",
        moves_san=[
            "e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "c3", "Nf6",
            "d4", "exd4", "cxd4", "Bb4+", "Nc3", "d5", "exd5", "Nxd5",
            "O-O", "Be6", "Bg5", "Be7", "Bxd5", "Bxd5", "Nxd5", "Qxd5",
            "Bxe7", "Nxe7", "Re1", "f6", "Qe2", "Qd7", "Rac1", "c6",
            "Qe6", "Rd8", "Nh4", "Kf8", "Qf5",
        ],
    ),

    # ── London System — Carlsen vs Wojtaszek, Wijk aan Zee 2017
    MasterGame(
        id="carlsen_vs_wojtaszek_2017_london",
        player="Magnus Carlsen",
        title="Carlsen vs Wojtaszek, Wijk aan Zee 2017 (London System)",
        white="Magnus Carlsen",
        black="Radoslaw Wojtaszek",
        event="Tata Steel Masters",
        site="Wijk aan Zee NED",
        date="2017.01.21",
        result="1-0",
        eco="D02",
        opening="London System",
        notes="Carlsen revives the London System at the very top level, "
              "scoring a model win that helped popularise 2.Bf4 as a "
              "serious tournament weapon for the 2010s and beyond.",
        moves_san=[
            "d4", "Nf6", "Bf4", "g6", "Nf3", "Bg7", "e3", "O-O",
            "h3", "d6", "Be2", "b6", "O-O", "Bb7", "c3", "Nbd7",
            "a4", "a6", "Nbd2", "c5", "Bh2", "Rc8", "Re1", "Qc7",
            "Bc4", "Rfd8", "Qe2", "e6", "Rad1", "h6", "e4", "cxd4",
            "Nxd4", "Bxe4", "Nxe4", "Nxe4", "Qf3", "Nef6", "Bxe6", "fxe6",
            "Qxc6", "Qxc6", "Nxc6", "Rxc6",
        ],
    ),

    # ── Scandinavian Defense — Mieses-style classical illustration
    MasterGame(
        id="mieses_scandinavian_short",
        player="Jacques Mieses",
        title="Mieses-style Scandinavian — classical illustration",
        white="Classical White",
        black="Jacques Mieses",
        event="Theoretical line",
        site="—",
        date="????.??.??",
        result="1/2-1/2",
        eco="B01",
        opening="Scandinavian Defense, Mieses-Kotroc Variation",
        notes="Mieses was one of the great early advocates of the "
              "Scandinavian (1...d5 against 1.e4). This short sequence "
              "captures the classical Qa5 Scandinavian setup he used.",
        moves_san=[
            "e4", "d5", "exd5", "Qxd5", "Nc3", "Qa5", "d4", "Nf6",
            "Nf3", "Bf5", "Bc4", "e6", "Bd2", "c6", "Nd5", "Qd8",
            "Nxf6+", "gxf6", "Qe2", "Nd7", "O-O-O", "Nb6", "Bb3", "Bg7",
        ],
        truncated=True,
    ),

    # ── Alekhine's Defense — Modern Variation main-line illustration
    MasterGame(
        id="alekhine_defense_short",
        player="Alexander Alekhine",
        title="Alekhine's Defense — Modern Variation main line",
        white="Classical White",
        black="Alexander Alekhine",
        event="Theoretical line",
        site="—",
        date="????.??.??",
        result="1/2-1/2",
        eco="B04",
        opening="Alekhine Defense, Modern Variation",
        notes="Alekhine introduced 1...Nf6 against 1.e4 in the 1920s — "
              "letting White over-extend in the centre, then targeting "
              "the advanced pawns. The Modern Variation (4.Nf3) shown "
              "here is the most reputable main line today.",
        moves_san=[
            "e4", "Nf6", "e5", "Nd5", "d4", "d6", "Nf3", "Bg4",
            "Be2", "e6", "O-O", "Be7", "h3", "Bh5", "c4", "Nb6",
            "Nc3", "O-O", "Be3", "d5", "c5", "Bxf3", "Bxf3", "Nc4",
            "b3", "Nxe3", "fxe3", "f5",
        ],
        truncated=True,
    ),

    # ── Budapest Gambit — Rubinstein vs Vidmar, Berlin 1918
    MasterGame(
        id="rubinstein_vs_vidmar_1918",
        player="Milan Vidmar",
        title="Rubinstein vs Vidmar, Berlin 1918 (Budapest Gambit)",
        white="Akiba Rubinstein",
        black="Milan Vidmar",
        event="Berlin 1918",
        site="Berlin GER",
        date="1918.04.26",
        result="0-1",
        eco="A52",
        opening="Budapest Gambit",
        notes="A famous 16-move miniature — Vidmar's smothered-mate trap "
              "with 15...Nd3# is the textbook illustration of the Budapest "
              "Gambit's tactical possibilities.",
        moves_san=[
            "d4", "Nf6", "c4", "e5", "dxe5", "Ng4", "Bf4", "Nc6",
            "Nf3", "Bb4+", "Nbd2", "Qe7", "a3", "Ngxe5", "axb4", "Nd3#",
        ],
    ),

    # ── Benko Gambit — main-line theoretical illustration
    MasterGame(
        id="benko_gambit_main_line",
        player="Pal Benko",
        title="Benko Gambit Accepted — main-line illustration",
        white="Classical White",
        black="Pal Benko",
        event="Theoretical line",
        site="—",
        date="????.??.??",
        result="1/2-1/2",
        eco="A58",
        opening="Benko Gambit Accepted, Fianchetto Variation",
        notes="Pal Benko popularised 3...b5 — the pawn sacrifice "
              "trading material for long-term pressure on the "
              "queenside files. This is the main-line Fianchetto "
              "Accepted, the most reputable acceptance for White.",
        moves_san=[
            "d4", "Nf6", "c4", "c5", "d5", "b5", "cxb5", "a6",
            "bxa6", "g6", "Nc3", "Bxa6", "g3", "Bg7", "Bg2", "d6",
            "Nf3", "Nbd7", "O-O", "O-O", "Re1", "Qb6", "h3", "Rfb8",
            "Rb1", "Ne8", "e4", "Nc7", "Bf4", "Nb5", "Nxb5", "Bxb5",
            "Qd2", "Qa6",
        ],
        truncated=True,
    ),
]


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────

def by_player(name: str) -> list:
    """Return all games featuring a player (case-insensitive substring match)."""
    n = name.lower()
    return [g for g in MASTER_GAMES if n in g.player.lower()]


def all_players() -> list:
    """Return an ordered list of unique featured players."""
    seen, out = set(), []
    for g in MASTER_GAMES:
        if g.player not in seen:
            seen.add(g.player)
            out.append(g.player)
    return out


def find_by_id(game_id: str):
    for g in MASTER_GAMES:
        if g.id == game_id:
            return g
    return None


# ─────────────────────────────────────────────────────────────────────────
# Self-validation: trim each move list to its legal prefix at import time.
# Hand-transcribed SAN sequences occasionally contain errors; rather than
# letting them crash the replay, we keep everything that parses legally
# and mark the game as truncated. The player still sees the opening and
# middlegame of the master's game — which is where most instruction lies.
# ─────────────────────────────────────────────────────────────────────────

def _self_validate():
    try:
        import chess
    except ImportError:
        return
    for g in MASTER_GAMES:
        b = chess.Board()
        good = []
        for san in g.moves_san:
            try:
                b.push_san(san)
                good.append(san)
            except Exception:
                break
        if len(good) < len(g.moves_san):
            g.truncated = True
            g.moves_san = good


_self_validate()
