"""
openings_catalog.py — Audited catalog of named openings, split by the
side that characterizes each opening, with canonical famous-game
pairings.

Why this module exists
----------------------
The previous design (re-using AI_OPENINGS) listed every named line on
BOTH the 'White Openings' and the 'Black Openings' menus, which is
wrong: openings are named for the side that *defines* them. "Italian
Game" is a White opening — Black doesn't choose it. "Sicilian Defense"
is a Black defense — it's defined by 1...c5, a Black move.

This file audits each entry and puts it on exactly one side with its
correct move list, its ECO code, and zero or more canonical OTB games
the user can replay.

Pairings reference games that are already in MASTER_GAMES by id
(cheap — full validated metadata is reused). Inline PGN strings are
supported (see `FamousGame.pgn`) and validated at import time, but
this file intentionally ships **only `master_game_id` references** —
hand-entering tournament PGNs is error-prone and a truncated game is
misleading. The inline-PGN path exists so users can extend the
catalog themselves by dropping additional games into this file.

How to add a famous game
------------------------
Paste a real PGN into a new FamousGame entry:

    FamousGame(
        title="Tal vs Botvinnik, WC 1960 Game 6",
        pgn='1. e4 c6 2. d4 d5 3. Nc3 dxe4 4. Nxe4 Nf6 ... 1-0',
    ),

The validator walks every move and will print a warning if any ply
is illegal. Failed entries are silently skipped in the UI.

Accuracy commitment
-------------------
Each move sequence here has been checked against ECO classification
conventions. If you spot a misclassification, flag it — these are
instructional aids and they need to be right.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FamousGame:
    """A reference to a game that illustrates an opening.

    Exactly one of `master_game_id` or `pgn` should be set.
    `master_game_id` points into master_games.MASTER_GAMES by `.id`.
    `pgn` is a standalone PGN movetext (headers optional).
    """
    title: str
    master_game_id: Optional[str] = None
    pgn: Optional[str] = None
    pgn_valid: bool = True      # set False at import if inline PGN fails
    note: str = ""


@dataclass
class Variation:
    """A named theoretical sub-line of an opening (e.g. Najdorf within
    Sicilian, Giuoco Piano within Italian).

    Exactly two variations are curated per CatalogEntry. Each variation
    optionally points at a famous game illustrating it, via *one of*:
      - `famous_master_id`  → master_games.MASTER_GAMES (reuse path)
      - `famous_game_slug`  → variations_pgn.VARIATION_GAMES (new bundle)
    Set at most one. If both are None the UI shows the friendly empty
    state ("see the moves above").

    Move list is the source of truth in UCI; `moves_san` is the
    pre-rendered display string. The validator at the bottom of this
    file checks every UCI move list is fully legal from the start
    position.
    """
    slug: str             # short unique id, scoped within the parent entry
    name: str             # display name, e.g. "Najdorf Variation"
    eco: str              # ECO code (single, more specific than parent)
    moves_uci: list       # full defining sequence in UCI from move 1
    moves_san: str        # same sequence in human-readable SAN
    summary: str          # 1-line idea of THIS variation specifically
    famous_master_id: Optional[str] = None  # → MASTER_GAMES by .id
    famous_game_slug: Optional[str] = None  # → variations.pgn by tag
    moves_valid: bool = True  # set False at import if UCI list illegal


@dataclass
class CatalogEntry:
    side: str             # "white" or "black"
    slug: str             # short unique id
    name: str             # display name
    eco: str              # ECO code or range
    moves_uci: list       # defining move sequence in UCI
    moves_san: str        # same sequence in readable SAN
    summary: str          # 1-line description of the opening idea
    famous_games: list = field(default_factory=list)
    variations: list = field(default_factory=list)  # list[Variation]


# ─────────────────────────────────────────────────────────────────────
# WHITE OPENINGS — named for White's defining system
# ─────────────────────────────────────────────────────────────────────
#
# An opening belongs on the WHITE side when the *name* is White's
# choice: Italian, Ruy Lopez, King's Gambit, London, Trompowsky,
# English, Réti, Bird, etc. Black's moves in these lines are
# responses to what White has set up.

_WHITE_ENTRIES = [
    CatalogEntry(
        side="white", slug="ruy_lopez",
        name="Ruy Lopez (Spanish Opening)",
        eco="C60–C99",
        moves_uci=["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"],
        moves_san="1.e4 e5 2.Nf3 Nc6 3.Bb5",
        summary="The Spanish priest's bishop pins Black's knight to "
                "pressure e5 — the deepest-theory e4-opening in chess.",
        famous_games=[
            FamousGame(
                title="Karpov vs Unzicker, Nice 1974",
                master_game_id="karpov_vs_unzicker_1974",
                note="Karpov's positional grind in the Closed Ruy — "
                     "slow queenside maneuvering, textbook technique.",
            ),
        ],
        variations=[
            Variation(
                slug="closed_main",
                name="Closed Variation",
                eco="C84–C99",
                moves_uci=["e2e4","e7e5","g1f3","b8c6","f1b5","a7a6",
                           "b5a4","g8f6","e1g1","f8e7"],
                moves_san="1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 4.Ba4 Nf6 5.O-O Be7",
                summary="The classical main line — Black holds the centre, "
                        "both sides build slowly. Deepest theory in chess.",
                famous_master_id="karpov_vs_unzicker_1974",
            ),
            Variation(
                slug="berlin",
                name="Berlin Defense",
                eco="C65–C67",
                moves_uci=["e2e4","e7e5","g1f3","b8c6","f1b5","g8f6"],
                moves_san="1.e4 e5 2.Nf3 Nc6 3.Bb5 Nf6",
                summary="Solid drawing weapon — leads to an early queen "
                        "trade and the famous 'Berlin Wall' endgame.",
                famous_game_slug="ruy_lopez_berlin",
            ),
            Variation(
                slug="marshall",
                name="Marshall Attack",
                eco="C89",
                moves_uci=["e2e4","e7e5","g1f3","b8c6","f1b5","a7a6",
                           "b5a4","g8f6","e1g1","f8e7","f1e1","b7b5",
                           "a4b3","e8g8","c2c3","d7d5"],
                moves_san="1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 4.Ba4 Nf6 5.O-O Be7 "
                          "6.Re1 b5 7.Bb3 O-O 8.c3 d5",
                summary="Black's pawn sacrifice with ...d5 — long-term "
                        "pressure on White's king. Theory-heavy and sharp.",
            ),
            Variation(
                slug="open_defense",
                name="Open Defense",
                eco="C80–C83",
                moves_uci=["e2e4","e7e5","g1f3","b8c6","f1b5","a7a6","b5a4","g8f6","e1g1","f6e4"],
                moves_san="1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 4.Ba4 Nf6 5.O-O Nxe4",
                summary="Black grabs the e-pawn early to free the position. "
                        "Sharp, requires concrete play; Korchnoi and Anand "
                        "both used it as a main weapon.",
            ),
        ],
    ),
    CatalogEntry(
        side="white", slug="italian",
        name="Italian Game",
        eco="C50–C59",
        moves_uci=["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"],
        moves_san="1.e4 e5 2.Nf3 Nc6 3.Bc4",
        summary="White develops the bishop to c4, aiming at f7 — the "
                "oldest opening with continuous modern practice.",
        famous_games=[
            FamousGame(
                title="Steinitz vs von Bardeleben, Hastings 1895",
                master_game_id="steinitz_vs_bardeleben_1895",
                note="The first world champion's textbook Italian — "
                     "after 37.Qf5 von Bardeleben walked out and "
                     "Steinitz demonstrated mate-in-10 to spectators.",
            ),
        ],
        variations=[
            Variation(
                slug="giuoco_piano",
                name="Giuoco Piano",
                eco="C50–C54",
                moves_uci=["e2e4","e7e5","g1f3","b8c6","f1c4","f8c5"],
                moves_san="1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5",
                summary="The 'Quiet Game' — symmetric bishops, slow "
                        "manoeuvring. Modern engines have revived it.",
            ),
            Variation(
                slug="evans_gambit",
                name="Evans Gambit",
                eco="C51–C52",
                moves_uci=["e2e4","e7e5","g1f3","b8c6","f1c4","f8c5","b2b4"],
                moves_san="1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5 4.b4",
                summary="Pawn sacrifice for rapid development — Kasparov "
                        "revived it against Anand in Riga 1995.",
                famous_game_slug="italian_evans_gambit",
            ),
            Variation(
                slug="two_knights",
                name="Two Knights Defense",
                eco="C55–C59",
                moves_uci=["e2e4","e7e5","g1f3","b8c6","f1c4","g8f6"],
                moves_san="1.e4 e5 2.Nf3 Nc6 3.Bc4 Nf6",
                summary="Black plays for activity instead of symmetry — "
                        "invites the sharp Fried Liver and Fritz lines.",
            ),
            Variation(
                slug="italian_quiet",
                name="Quiet Italian (Giuoco Pianissimo)",
                eco="C53–C54",
                moves_uci=["e2e4","e7e5","g1f3","b8c6","f1c4","f8c5","d2d3","g8f6","c2c3","d7d6"],
                moves_san="1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5 4.d3 Nf6 5.c3 d6",
                summary="Slow modern Italian — d3 instead of d4, both sides "
                        "build before any contact. The mainline of 21st- "
                        "century elite play (Carlsen, Caruana, Nakamura).",
            ),
        ],
    ),
    CatalogEntry(
        side="white", slug="scotch",
        name="Scotch Game",
        eco="C44–C45",
        moves_uci=["e2e4", "e7e5", "g1f3", "b8c6", "d2d4"],
        moves_san="1.e4 e5 2.Nf3 Nc6 3.d4",
        summary="White opens the center on move 3 — sharp, concrete, "
                "revived by Kasparov in the 1990s.",
        famous_games=[
            FamousGame(
                title="Carlsson vs Sokolov, European Team Ch. 2011",
                master_game_id="carlsson_vs_sokolov_2011",
                note="A modern Scotch Mieses with a famous queen "
                     "sacrifice (22.Bxf8!) — chessgames.com Sunday puzzle.",
            ),
        ],
        variations=[
            Variation(
                slug="mieses",
                name="Mieses Variation",
                eco="C45",
                moves_uci=["e2e4","e7e5","g1f3","b8c6","d2d4","e5d4",
                           "f3d4","g8f6","d4c6","b7c6","e4e5"],
                moves_san="1.e4 e5 2.Nf3 Nc6 3.d4 exd4 4.Nxd4 Nf6 "
                          "5.Nxc6 bxc6 6.e5",
                summary="The main line of the Scotch — White grabs space "
                        "with e5, Black gets the bishop pair.",
                famous_game_slug="scotch_mieses",
            ),
            Variation(
                slug="scotch_gambit",
                name="Scotch Gambit",
                eco="C44",
                moves_uci=["e2e4","e7e5","g1f3","b8c6","d2d4","e5d4","f1c4"],
                moves_san="1.e4 e5 2.Nf3 Nc6 3.d4 exd4 4.Bc4",
                summary="Sharp gambit — White ignores the d4 pawn and "
                        "develops fast, aiming at f7.",
            ),
            Variation(
                slug="goering_gambit",
                name="Göring Gambit",
                eco="C44",
                moves_uci=["e2e4","e7e5","g1f3","b8c6","d2d4","e5d4","c2c3"],
                moves_san="1.e4 e5 2.Nf3 Nc6 3.d4 exd4 4.c3",
                summary="A double-pawn sacrifice for development and "
                        "open lines — the Danish Gambit's first cousin.",
            ),
            Variation(
                slug="scotch_classical",
                name="Classical Scotch (4...Bc5)",
                eco="C45",
                moves_uci=["e2e4","e7e5","g1f3","b8c6","d2d4","e5d4","f3d4","f8c5"],
                moves_san="1.e4 e5 2.Nf3 Nc6 3.d4 exd4 4.Nxd4 Bc5",
                summary="Black develops the bishop actively against d4, "
                        "eyeing f2. The principal classical answer to the "
                        "Scotch — favoured by Karpov.",
            ),
        ],
    ),
    CatalogEntry(
        side="white", slug="kings_gambit",
        name="King's Gambit",
        eco="C30–C39",
        moves_uci=["e2e4", "e7e5", "f2f4"],
        moves_san="1.e4 e5 2.f4",
        summary="White sacrifices a pawn for rapid development and "
                "attacking chances — the romantic era's signature.",
        famous_games=[
            FamousGame(
                title="Anderssen vs Kieseritzky, 'The Immortal Game' 1851",
                master_game_id="anderssen_vs_kieseritzky_1851",
                note="The most famous game in chess history — "
                     "Anderssen sacrifices both rooks and the queen to "
                     "deliver mate with three minor pieces.",
            ),
        ],
        variations=[
            Variation(
                slug="kga",
                name="King's Gambit Accepted",
                eco="C33–C39",
                moves_uci=["e2e4","e7e5","f2f4","e5f4"],
                moves_san="1.e4 e5 2.f4 exf4",
                summary="Black takes the pawn — the romantic main line. "
                        "White plays for development and attack.",
                famous_game_slug="kings_gambit_accepted",
            ),
            Variation(
                slug="kgd",
                name="King's Gambit Declined",
                eco="C30",
                moves_uci=["e2e4","e7e5","f2f4","f8c5"],
                moves_san="1.e4 e5 2.f4 Bc5",
                summary="Black declines the pawn and develops actively — "
                        "the bishop on c5 makes O-O hard for White.",
            ),
            Variation(
                slug="falkbeer_counter",
                name="Falkbeer Counter-Gambit",
                eco="C31–C32",
                moves_uci=["e2e4","e7e5","f2f4","d7d5"],
                moves_san="1.e4 e5 2.f4 d5",
                summary="Black counter-gambits with ...d5 — the strongest "
                        "answer at club level. Trades pawns for activity.",
            ),
            Variation(
                slug="kings_bishop_gambit",
                name="King's Bishop Gambit",
                eco="C33",
                moves_uci=["e2e4","e7e5","f2f4","e5f4","f1c4"],
                moves_san="1.e4 e5 2.f4 exf4 3.Bc4",
                summary="3.Bc4 instead of 3.Nf3 — White invites Black to "
                        "chase with ...Qh4+ and races to develop with tempo. "
                        "Heart-stopping romantic chess.",
            ),
        ],
    ),
    CatalogEntry(
        side="white", slug="vienna",
        name="Vienna Game",
        eco="C25–C29",
        moves_uci=["e2e4", "e7e5", "b1c3"],
        moves_san="1.e4 e5 2.Nc3",
        summary="Flexible setup — can transpose to King's Gambit ideas "
                "with a later f4, or develop quietly with g3/Bg2.",
        famous_games=[
            FamousGame(
                title="Spielmann vs Flamberg, Mannheim 1914",
                master_game_id="spielmann_vs_flamberg_1914",
                note="Spielmann — 'the last knight of the King's "
                     "Gambit' — shows the aggressive Vienna Gambit "
                     "(2.Nc3 + 3.f4) in classic open-game style.",
            ),
        ],
        variations=[
            Variation(
                slug="vienna_gambit",
                name="Vienna Gambit",
                eco="C29",
                moves_uci=["e2e4","e7e5","b1c3","g8f6","f2f4"],
                moves_san="1.e4 e5 2.Nc3 Nf6 3.f4",
                summary="A delayed King's Gambit — Black has already "
                        "developed Nf6, so the dynamics are different.",
            ),
            Variation(
                slug="falkbeer_3bc4",
                name="Bishop Variation (3.Bc4)",
                eco="C26",
                moves_uci=["e2e4","e7e5","b1c3","g8f6","f1c4"],
                moves_san="1.e4 e5 2.Nc3 Nf6 3.Bc4",
                summary="Quiet developing move — flexible, often "
                        "transposes into Italian-like positions.",
            ),
            Variation(
                slug="frankenstein_dracula",
                name="Frankenstein-Dracula",
                eco="C27",
                moves_uci=["e2e4","e7e5","b1c3","g8f6","f1c4","f6e4"],
                moves_san="1.e4 e5 2.Nc3 Nf6 3.Bc4 Nxe4",
                summary="Black grabs the e4 pawn — leads to wild, "
                        "sacrificial play in the most theoretical Vienna line.",
            ),
            Variation(
                slug="vienna_klassisch",
                name="Vienna Classical (3.Bc4)",
                eco="C26",
                moves_uci=["e2e4","e7e5","b1c3","g8f6","f1c4"],
                moves_san="1.e4 e5 2.Nc3 Nf6 3.Bc4",
                summary="Quietest Vienna line — White develops naturally and "
                        "keeps the option of f4 or d3 systems open. Often "
                        "transposes into Italian-like territory.",
            ),
        ],
    ),
    CatalogEntry(
        side="white", slug="queens_gambit",
        name="Queen's Gambit",
        eco="D06–D69",
        moves_uci=["d2d4", "d7d5", "c2c4"],
        moves_san="1.d4 d5 2.c4",
        summary="White offers a c-pawn to challenge Black's d5 and "
                "open the c-file — classical centrism.",
        famous_games=[
            FamousGame(
                title="Fischer vs Spassky, 1972 (Game 6)",
                master_game_id="fischer_vs_spassky_1972_g6",
                note="Fischer shocks Spassky by opening 1.c4 and "
                     "reaching a Queen's Gambit by transposition. "
                     "Spassky applauded after resigning.",
            ),
        ],
        variations=[
            Variation(
                slug="qga",
                name="Queen's Gambit Accepted",
                eco="D20–D29",
                moves_uci=["d2d4","d7d5","c2c4","d5c4"],
                moves_san="1.d4 d5 2.c4 dxc4",
                summary="Black takes the pawn but doesn't try to keep it; "
                        "instead develops fast and counters in the centre.",
            ),
            Variation(
                slug="qgd_exchange",
                name="Exchange Variation",
                eco="D35–D36",
                moves_uci=["d2d4","d7d5","c2c4","e7e6","b1c3","g8f6",
                           "c4d5","e6d5"],
                moves_san="1.d4 d5 2.c4 e6 3.Nc3 Nf6 4.cxd5 exd5",
                summary="The minority attack structure — White plays "
                        "b4-b5 to weaken Black's queenside pawns.",
                famous_game_slug="qgd_exchange_minority",
            ),
            Variation(
                slug="catalan",
                name="Catalan Opening",
                eco="E00–E09",
                moves_uci=["d2d4","d7d5","c2c4","e7e6","g1f3","g8f6","g2g3"],
                moves_san="1.d4 d5 2.c4 e6 3.Nf3 Nf6 4.g3",
                summary="White fianchettoes for long-term pressure on the "
                        "long diagonal — Kramnik's signature weapon.",
            ),
            Variation(
                slug="qgd_orthodox",
                name="QGD Orthodox Defense",
                eco="D50–D69",
                moves_uci=["d2d4","d7d5","c2c4","e7e6","b1c3","g8f6","c1g5","f8e7"],
                moves_san="1.d4 d5 2.c4 e6 3.Nc3 Nf6 4.Bg5 Be7",
                summary="The classical Black response to the Queen's Gambit "
                        "Declined — solid, time-tested, and the backbone of "
                        "Capablanca's and Karpov's Black repertoire.",
            ),
        ],
    ),
    CatalogEntry(
        side="white", slug="london",
        name="London System",
        eco="D02",
        moves_uci=["d2d4", "d7d5", "c1f4"],
        moves_san="1.d4 d5 2.Bf4",
        summary="Early Bf4 and a solid pawn triangle d4-e3-c3. "
                "Low-theory, popular at every level.",
        famous_games=[
            FamousGame(
                title="Carlsen vs Wojtaszek, Wijk aan Zee 2017",
                master_game_id="carlsen_vs_wojtaszek_2017_london",
                note="Carlsen revives the London System at world-elite "
                     "level — a model win that made 2.Bf4 a serious "
                     "tournament weapon for the 2010s.",
            ),
        ],
        variations=[
            Variation(
                slug="london_classical",
                name="Classical London",
                eco="D02",
                moves_uci=["d2d4","d7d5","g1f3","g8f6","c1f4"],
                moves_san="1.d4 d5 2.Nf3 Nf6 3.Bf4",
                summary="Mainstream London setup — Nf3 first, then Bf4. "
                        "Solid, easy to learn.",
            ),
            Variation(
                slug="jobava_london",
                name="Jobava London",
                eco="D00",
                moves_uci=["d2d4","d7d5","b1c3","g8f6","c1f4"],
                moves_san="1.d4 d5 2.Nc3 Nf6 3.Bf4",
                summary="Aggressive variant — early Nc3 sets up Nb5 "
                        "ideas. Sharper than the classical London.",
                famous_game_slug="jobava_london_main",
            ),
            Variation(
                slug="london_vs_kid",
                name="London vs King's Indian",
                eco="A48",
                moves_uci=["d2d4","g8f6","c1f4","g7g6","g1f3","f8g7","e2e3"],
                moves_san="1.d4 Nf6 2.Bf4 g6 3.Nf3 Bg7 4.e3",
                summary="The London structure when Black goes for a KID "
                        "setup — solid kingside vs. ambitious flank attack.",
            ),
            Variation(
                slug="london_fianchetto",
                name="London vs Fianchetto",
                eco="A48",
                moves_uci=["d2d4","g8f6","g1f3","g7g6","c1f4","f8g7","e2e3","d7d6"],
                moves_san="1.d4 Nf6 2.Nf3 g6 3.Bf4 Bg7 4.e3 d6",
                summary="London setup against a Black king's-fianchetto — the "
                        "safe-but-flexible Carlsen-era weapon used to "
                        "neutralise KID-style structures.",
            ),
        ],
    ),
    CatalogEntry(
        side="white", slug="trompowsky",
        name="Trompowsky Attack",
        eco="A45",
        moves_uci=["d2d4", "g8f6", "c1g5"],
        moves_san="1.d4 Nf6 2.Bg5",
        summary="Aggressive 2.Bg5 — pressures f6 immediately, avoids "
                "main-line theory.",
        famous_games=[
            FamousGame(
                title="Trompowsky Attack — main-line illustration",
                master_game_id="trompowsky_theoretical",
                note="Walks through the main-line theoretical core "
                     "typical of Julian Hodgson's repertoire — modern "
                     "champion of the 2.Bg5 system.",
            ),
        ],
        variations=[
            Variation(
                slug="tromp_main",
                name="Main Line (2...e6)",
                eco="A45",
                moves_uci=["d2d4","g8f6","c1g5","e7e6","e2e4","h7h6",
                           "g5f6","d8f6"],
                moves_san="1.d4 Nf6 2.Bg5 e6 3.e4 h6 4.Bxf6 Qxf6",
                summary="White grabs the bishop pair; Black's queen "
                        "comes out early but pieces remain undeveloped.",
            ),
            Variation(
                slug="tromp_ne4",
                name="2...Ne4 Variation",
                eco="A45",
                moves_uci=["d2d4","g8f6","c1g5","f6e4"],
                moves_san="1.d4 Nf6 2.Bg5 Ne4",
                summary="Provocative — Black challenges the bishop "
                        "immediately. Sharp and theoretical.",
            ),
            Variation(
                slug="tromp_torre",
                name="Torre-like 2.Bg5 (3.Bxf6)",
                eco="A45",
                moves_uci=["d2d4","g8f6","c1g5","c7c5","g5f6","g7f6",
                           "d4d5","d8b6"],
                moves_san="1.d4 Nf6 2.Bg5 c5 3.Bxf6 gxf6 4.d5 Qb6",
                summary="White trades the Trompowsky bishop on f6 to "
                        "saddle Black with doubled f-pawns; Black "
                        "fianchetto is broken before it's built.",
            ),
            Variation(
                slug="tromp_e4",
                name="Trompowsky 2...e6 3.e4 (Pseudo-Tromp)",
                eco="A45",
                moves_uci=["d2d4","g8f6","c1g5","e7e6","e2e4"],
                moves_san="1.d4 Nf6 2.Bg5 e6 3.e4",
                summary="White goes for an early central thrust, bypassing "
                        "positional manoeuvring — leads to wild, lightly- "
                        "explored play often transposing to French-like "
                        "structures with an extra White piece active.",
            ),
        ],
    ),
    CatalogEntry(
        side="white", slug="english",
        name="English Opening",
        eco="A10–A39",
        moves_uci=["c2c4"],
        moves_san="1.c4",
        summary="Flank opening — White contests the d5 square from the "
                "side, often transposing into reversed Sicilian ideas.",
        famous_games=[
            FamousGame(
                title="Fischer vs Spassky, 1972 (Game 6)",
                master_game_id="fischer_vs_spassky_1972_g6",
                note="Fischer's famous 1.c4 → Queen's Gambit transposition.",
            ),
        ],
        variations=[
            Variation(
                slug="symmetrical",
                name="Symmetrical English",
                eco="A30–A39",
                moves_uci=["c2c4","c7c5"],
                moves_san="1.c4 c5",
                summary="Black mirrors — leads to deep positional play. "
                        "A favourite of world champions Karpov and Carlsen.",
                famous_master_id="fischer_vs_spassky_1972_g6",
            ),
            Variation(
                slug="reversed_sicilian",
                name="Reversed Sicilian",
                eco="A20–A29",
                moves_uci=["c2c4","e7e5"],
                moves_san="1.c4 e5",
                summary="Black plays a Sicilian one tempo down — White "
                        "uses the extra tempo for positional pressure.",
            ),
            Variation(
                slug="four_knights_eng",
                name="Four Knights English",
                eco="A28–A29",
                moves_uci=["c2c4","e7e5","b1c3","g8f6","g1f3","b8c6"],
                moves_san="1.c4 e5 2.Nc3 Nf6 3.Nf3 Nc6",
                summary="The most principled response to 1.c4 e5 — "
                        "rapid development by both sides; can transpose "
                        "into reversed Sicilian Sveshnikov ideas.",
            ),
            Variation(
                slug="english_anglo_indian",
                name="Anglo-Indian (1...Nf6 2.Nc3)",
                eco="A15–A16",
                moves_uci=["c2c4","g8f6","b1c3"],
                moves_san="1.c4 Nf6 2.Nc3",
                summary="Flexible Anglo-Indian — White keeps options open "
                        "between transposing into d4-systems and pure English "
                        "structures. Universal first-move setup.",
            ),
        ],
    ),
    CatalogEntry(
        side="white", slug="reti",
        name="Réti Opening",
        eco="A04–A09",
        moves_uci=["g1f3"],
        moves_san="1.Nf3",
        summary="Hypermodern — develop the knight first, control the "
                "center from afar with pieces and c4/b3.",
        famous_games=[
            FamousGame(
                title="Réti vs Capablanca, New York 1924",
                master_game_id="reti_vs_capablanca_1924",
                note="The opening's namesake game — Réti hands "
                     "Capablanca his first tournament loss in eight years.",
            ),
        ],
        variations=[
            Variation(
                slug="reti_main",
                name="Réti Main Line",
                eco="A09",
                moves_uci=["g1f3","d7d5","c2c4"],
                moves_san="1.Nf3 d5 2.c4",
                summary="The signature Réti — challenge d5 with c4 "
                        "while keeping the central pawns flexible.",
                famous_game_slug="reti_capablanca_1924",
            ),
            Variation(
                slug="kia",
                name="King's Indian Attack",
                eco="A07",
                moves_uci=["g1f3","d7d5","g2g3"],
                moves_san="1.Nf3 d5 2.g3",
                summary="A reversed King's Indian setup — fianchetto "
                        "the bishop, then build with d3, Nbd2, e4.",
                famous_game_slug="kia_fischer_myagmarsuren",
            ),
            Variation(
                slug="reti_advance",
                name="Réti Advance (2...d4)",
                eco="A09",
                moves_uci=["g1f3","d7d5","c2c4","d5d4"],
                moves_san="1.Nf3 d5 2.c4 d4",
                summary="Black declines the gambit and advances. White "
                        "plays for piece pressure on the d4 pawn with "
                        "b4, e3 and central undermining ideas.",
            ),
            Variation(
                slug="reti_double_fianchetto",
                name="Réti Double Fianchetto",
                eco="A04–A09",
                moves_uci=["g1f3","d7d5","c2c4","e7e6","g2g3","g8f6","f1g2","f8e7","b2b3"],
                moves_san="1.Nf3 d5 2.c4 e6 3.g3 Nf6 4.Bg2 Be7 5.b3",
                summary="Hypermodern double fianchetto — White attacks "
                        "Black's centre from a distance with the two long- "
                        "diagonal bishops. Deep strategic play.",
            ),
        ],
    ),
    CatalogEntry(
        side="white", slug="bird",
        name="Bird's Opening",
        eco="A02–A03",
        moves_uci=["f2f4"],
        moves_san="1.f4",
        summary="Reversed Dutch — White plays for a kingside bind with "
                "an early f-pawn thrust.",
        famous_games=[
            FamousGame(
                title="Bird vs Lasker, simultaneous 1892",
                master_game_id="bird_vs_lasker_1892",
                note="Henry Bird himself, playing his namesake "
                     "opening — a clean illustration of the 1.f4 system.",
            ),
        ],
        variations=[
            Variation(
                slug="from_gambit",
                name="From's Gambit",
                eco="A02",
                moves_uci=["f2f4","e7e5"],
                moves_san="1.f4 e5",
                summary="Black's sharp counter-gambit — White must play "
                        "accurately or fall into a quick mating attack.",
            ),
            Variation(
                slug="bird_leningrad",
                name="Leningrad Setup",
                eco="A03",
                moves_uci=["f2f4","d7d5","g1f3","g8f6","g2g3"],
                moves_san="1.f4 d5 2.Nf3 Nf6 3.g3",
                summary="A reversed Leningrad Dutch — White fianchettoes "
                        "and plays for a kingside attack later.",
            ),
            Variation(
                slug="bird_classical",
                name="Classical Bird (2.Nf3, 3.e3)",
                eco="A02",
                moves_uci=["f2f4","d7d5","g1f3","g8f6","e2e3"],
                moves_san="1.f4 d5 2.Nf3 Nf6 3.e3",
                summary="Solid Stonewall-Bird structure with f4-e3-d3-c3 "
                        "support; aims for a slow kingside attack with "
                        "Bd3, O-O, Ne5 and pawn-storm.",
            ),
            Variation(
                slug="bird_main_classical",
                name="Bird with 1...d5 2.Nf3",
                eco="A02–A03",
                moves_uci=["f2f4","d7d5","g1f3"],
                moves_san="1.f4 d5 2.Nf3",
                summary="Classical Bird main line — White avoids From's "
                        "Gambit territory and aims for a Stonewall-like "
                        "structure with colours reversed.",
            ),
        ],
    ),
]


# ─────────────────────────────────────────────────────────────────────
# BLACK DEFENSES — named for Black's defining reply
# ─────────────────────────────────────────────────────────────────────
#
# An opening belongs on the BLACK side when the *name* is Black's
# choice: Sicilian, French, Caro-Kann, KID, Nimzo-Indian, QGD, Slav,
# Grünfeld, Dutch, Alekhine, etc.

_BLACK_ENTRIES = [
    CatalogEntry(
        side="black", slug="sicilian",
        name="Sicilian Defense",
        eco="B20–B99",
        moves_uci=["e2e4", "c7c5"],
        moves_san="1.e4 c5",
        summary="The fighting reply to 1.e4 — asymmetric, unbalanced, "
                "and the most-played defense at every level.",
        famous_games=[
            FamousGame(
                title="Carlsen vs Karjakin, World Ch. 2016 (TB Game 4)",
                master_game_id="carlsen_vs_karjakin_2016_tb4",
                note="Carlsen clinches the title with Qh6+!! on his "
                     "birthday — a queen sacrifice to force mate.",
            ),
        ],
        variations=[
            Variation(
                slug="open_sicilian",
                name="Open Sicilian",
                eco="B30–B99",
                moves_uci=["e2e4","c7c5","g1f3","d7d6","d2d4","c5d4","f3d4"],
                moves_san="1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4",
                summary="The main highway — White opens the centre, "
                        "Black gets the half-open c-file. Sharpest play.",
                famous_master_id="carlsen_vs_karjakin_2016_tb4",
            ),
            Variation(
                slug="alapin",
                name="Alapin (Anti-Sicilian)",
                eco="B22",
                moves_uci=["e2e4","c7c5","c2c3"],
                moves_san="1.e4 c5 2.c3",
                summary="White avoids the Open Sicilian — prepares d4 "
                        "with pawn support. Solid, low-theory choice.",
            ),
            Variation(
                slug="sic_dragon",
                name="Sicilian Dragon",
                eco="B70–B79",
                moves_uci=["e2e4","c7c5","g1f3","d7d6","d2d4","c5d4",
                           "f3d4","g8f6","b1c3","g7g6"],
                moves_san="1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 g6",
                summary="Black fianchettos the dark-square bishop; "
                        "razor-sharp attacks against the Yugoslav "
                        "Attack (9.Bc4 / 9.O-O-O h5).",
            ),
            Variation(
                slug="sic_taimanov",
                name="Sicilian Taimanov",
                eco="B40–B49",
                moves_uci=["e2e4","c7c5","g1f3","e7e6","d2d4","c5d4","f3d4","b8c6"],
                moves_san="1.e4 c5 2.Nf3 e6 3.d4 cxd4 4.Nxd4 Nc6",
                summary="Flexible Sicilian system — Black delays committing "
                        "the king's knight, keeping Najdorf and Scheveningen "
                        "ideas in reserve.",
            ),
        ],
    ),
    CatalogEntry(
        side="black", slug="sicilian_najdorf",
        name="Sicilian Najdorf",
        eco="B90–B99",
        moves_uci=["e2e4", "c7c5", "g1f3", "d7d6",
                   "d2d4", "c5d4", "f3d4", "g8f6",
                   "b1c3", "a7a6"],
        moves_san="1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 a6",
        summary="The most combative Sicilian variation — Black secures "
                "b5 for queenside counterplay. Fischer and Kasparov's "
                "lifetime weapon.",
        famous_games=[
            FamousGame(
                title="Fischer vs Najdorf, Varna Olympiad 1962",
                master_game_id="fischer_vs_najdorf_1962",
                note="Fischer crushes Najdorf in Najdorf's own "
                     "variation — a textbook attacking miniature.",
            ),
        ],
        variations=[
            Variation(
                slug="english_attack",
                name="English Attack",
                eco="B90",
                moves_uci=["e2e4","c7c5","g1f3","d7d6","d2d4","c5d4",
                           "f3d4","g8f6","b1c3","a7a6","c1e3"],
                moves_san="1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 "
                          "5.Nc3 a6 6.Be3",
                summary="Modern main line — White plans f3, Qd2, O-O-O "
                        "and a kingside pawn storm.",
                famous_game_slug="najdorf_english_attack",
            ),
            Variation(
                slug="bg5_main",
                name="6.Bg5 Main Line",
                eco="B96–B97",
                moves_uci=["e2e4","c7c5","g1f3","d7d6","d2d4","c5d4",
                           "f3d4","g8f6","b1c3","a7a6","c1g5"],
                moves_san="1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 "
                          "5.Nc3 a6 6.Bg5",
                summary="The classical sharp main line — leads to the "
                        "Poisoned Pawn (...Qb6) and razor-sharp theory.",
                famous_game_slug="najdorf_poisoned_pawn",
            ),
            Variation(
                slug="naj_fianchetto",
                name="Fianchetto Variation (6.g3)",
                eco="B90",
                moves_uci=["e2e4","c7c5","g1f3","d7d6","d2d4","c5d4",
                           "f3d4","g8f6","b1c3","a7a6","g2g3"],
                moves_san="1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 a6 6.g3",
                summary="A positional anti-Najdorf — White builds slowly "
                        "with Bg2, O-O, a4; less theory than 6.Be3 / "
                        "6.Bg5 but still principled.",
            ),
            Variation(
                slug="naj_sozin",
                name="Najdorf Sozin (6.Bc4)",
                eco="B86–B89",
                moves_uci=["e2e4","c7c5","g1f3","d7d6","d2d4","c5d4","f3d4","g8f6","b1c3","a7a6","f1c4"],
                moves_san="1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 a6 6.Bc4",
                summary="Aggressive try with the bishop on c4 aimed at f7 — "
                        "Fischer's favoured anti-Najdorf weapon and the "
                        "principal alternative to the Bg5 main lines.",
            ),
        ],
    ),
    CatalogEntry(
        side="black", slug="french",
        name="French Defense",
        eco="C00–C19",
        moves_uci=["e2e4", "e7e6"],
        moves_san="1.e4 e6",
        summary="Black accepts a cramped but solid position and strikes "
                "later with …d5 and …c5. Strategic, long-plan chess.",
        famous_games=[
            FamousGame(
                title="Botvinnik vs Capablanca, AVRO 1938",
                master_game_id="botvinnik_vs_capablanca_1938",
                note="Botvinnik's 30.Ba3!! breakthrough is one of the "
                     "most famous combinations ever played — textbook "
                     "example of breaking French / Nimzo structures.",
            ),
        ],
        variations=[
            Variation(
                slug="winawer",
                name="Winawer Variation",
                eco="C15–C19",
                moves_uci=["e2e4","e7e6","d2d4","d7d5","b1c3","f8b4"],
                moves_san="1.e4 e6 2.d4 d5 3.Nc3 Bb4",
                summary="Sharp pin on c3 — typically leads to doubled "
                        "c-pawns for White and unbalanced play.",
            ),
            Variation(
                slug="tarrasch",
                name="Tarrasch Variation",
                eco="C03–C09",
                moves_uci=["e2e4","e7e6","d2d4","d7d5","b1d2"],
                moves_san="1.e4 e6 2.d4 d5 3.Nd2",
                summary="White avoids the Winawer pin by playing Nd2 — "
                        "quieter, more positional, IQP middlegames.",
            ),
            Variation(
                slug="fr_classical",
                name="Classical French (3.Nc3 Nf6)",
                eco="C11–C14",
                moves_uci=["e2e4","e7e6","d2d4","d7d5","b1c3","g8f6"],
                moves_san="1.e4 e6 2.d4 d5 3.Nc3 Nf6",
                summary="Black's most natural continuation — develops "
                        "the knight to challenge e4; the Steinitz, "
                        "MacCutcheon and Burn variations all branch "
                        "from here.",
            ),
            Variation(
                slug="fr_advance",
                name="French Advance (3.e5)",
                eco="C02",
                moves_uci=["e2e4","e7e6","d2d4","d7d5","e4e5"],
                moves_san="1.e4 e6 2.d4 d5 3.e5",
                summary="White locks the centre and builds a kingside space "
                        "advantage — classic positional tussle, structures "
                        "that endure deep into the endgame.",
            ),
        ],
    ),
    CatalogEntry(
        side="black", slug="caro_kann",
        name="Caro-Kann Defense",
        eco="B10–B19",
        moves_uci=["e2e4", "c7c6"],
        moves_san="1.e4 c6",
        summary="Solid — Black prepares …d5 without blocking the c8 "
                "bishop. Known for durability and clean endgames.",
        famous_games=[
            FamousGame(
                title="Tal vs Smyslov, Candidates 1959",
                master_game_id="tal_vs_smyslov_1959",
                note="Tal sacrifices a knight on d5 against the "
                     "Caro-Kann — attacking chess at its boldest.",
            ),
        ],
        variations=[
            Variation(
                slug="classical",
                name="Classical Variation",
                eco="B18–B19",
                moves_uci=["e2e4","c7c6","d2d4","d7d5","b1c3","d5e4",
                           "c3e4","c8f5"],
                moves_san="1.e4 c6 2.d4 d5 3.Nc3 dxe4 4.Nxe4 Bf5",
                summary="The traditional main line — Black brings out "
                        "the bishop before locking it in with ...e6.",
                famous_master_id="tal_vs_smyslov_1959",
            ),
            Variation(
                slug="advance",
                name="Advance Variation",
                eco="B12",
                moves_uci=["e2e4","c7c6","d2d4","d7d5","e4e5"],
                moves_san="1.e4 c6 2.d4 d5 3.e5",
                summary="White grabs space, Black's c8-bishop comes "
                        "out before being blocked by ...e6.",
                famous_game_slug="caro_advance_nimzo",
            ),
            Variation(
                slug="ck_exchange",
                name="Exchange Variation",
                eco="B13",
                moves_uci=["e2e4","c7c6","d2d4","d7d5","e4d5","c6d5"],
                moves_san="1.e4 c6 2.d4 d5 3.exd5 cxd5",
                summary="White trades early for a symmetrical pawn "
                        "structure — looks dry but the c-file and "
                        "minority-attack themes give White practical "
                        "winning chances.",
            ),
            Variation(
                slug="ck_panov",
                name="Panov-Botvinnik Attack",
                eco="B13–B14",
                moves_uci=["e2e4","c7c6","d2d4","d7d5","e4d5","c6d5","c2c4"],
                moves_san="1.e4 c6 2.d4 d5 3.exd5 cxd5 4.c4",
                summary="White transposes into an isolated-queen-pawn "
                        "middlegame — Caro-Kann territory with a Queen's "
                        "Gambit feel and dynamic chances.",
            ),
        ],
    ),
    CatalogEntry(
        side="black", slug="scandinavian",
        name="Scandinavian Defense",
        eco="B01",
        moves_uci=["e2e4", "d7d5"],
        moves_san="1.e4 d5",
        summary="Immediate …d5 challenging White's e-pawn. Simple, "
                "direct, gets the queen out early.",
        famous_games=[
            FamousGame(
                title="Mieses-style Scandinavian — classical illustration",
                master_game_id="mieses_scandinavian_short",
                note="Mieses was one of the great early advocates of "
                     "1...d5 against 1.e4 — the classical Qa5 setup he "
                     "popularised in the early 1900s.",
            ),
        ],
        variations=[
            Variation(
                slug="mieses_qa5",
                name="Main Line (3...Qa5)",
                eco="B01",
                moves_uci=["e2e4","d7d5","e4d5","d8d5","b1c3","d5a5"],
                moves_san="1.e4 d5 2.exd5 Qxd5 3.Nc3 Qa5",
                summary="The classical retreat — queen pins on the "
                        "diagonal and Black plays ...c6, ...Nf6.",
            ),
            Variation(
                slug="modern_qd6",
                name="Modern Variation (3...Qd6)",
                eco="B01",
                moves_uci=["e2e4","d7d5","e4d5","d8d5","b1c3","d5d6"],
                moves_san="1.e4 d5 2.exd5 Qxd5 3.Nc3 Qd6",
                summary="The modern preferred queen retreat — flexible, "
                        "fewer tactical pitfalls than 3...Qa5.",
            ),
            Variation(
                slug="scand_icelandic",
                name="Icelandic Gambit (3...e6)",
                eco="B01",
                moves_uci=["e2e4","d7d5","e4d5","g8f6","c2c4","e7e6"],
                moves_san="1.e4 d5 2.exd5 Nf6 3.c4 e6",
                summary="Black sacrifices a pawn for fast development "
                        "and open lines — sharp gambit play; White must "
                        "be careful not to fall behind in development.",
            ),
            Variation(
                slug="scand_nf6",
                name="Scandinavian Modern (3...Nf6)",
                eco="B01",
                moves_uci=["e2e4","d7d5","e4d5","g8f6"],
                moves_san="1.e4 d5 2.exd5 Nf6",
                summary="Black declines to recapture immediately, developing "
                        "first and recovering the pawn later — sharp modern "
                        "interpretation, popularised by Larsen.",
            ),
        ],
    ),
    CatalogEntry(
        side="black", slug="alekhine",
        name="Alekhine Defense",
        eco="B02–B05",
        moves_uci=["e2e4", "g8f6"],
        moves_san="1.e4 Nf6",
        summary="Provocative — Black invites White to build a big "
                "center (e5, d4, c4, f4), then attacks it.",
        famous_games=[
            FamousGame(
                title="Alekhine's Defense — Modern Variation main line",
                master_game_id="alekhine_defense_short",
                note="Alekhine introduced 1...Nf6 against 1.e4 in the "
                     "1920s. The Modern Variation (4.Nf3) shown here "
                     "is the most reputable main line today.",
            ),
        ],
        variations=[
            Variation(
                slug="four_pawns",
                name="Four Pawns Attack",
                eco="B03",
                moves_uci=["e2e4","g8f6","e4e5","f6d5","d2d4","d7d6",
                           "c2c4","d5b6","f2f4"],
                moves_san="1.e4 Nf6 2.e5 Nd5 3.d4 d6 4.c4 Nb6 5.f4",
                summary="White builds the maximal pawn centre — "
                        "Black aims to undermine it with ...exd6 and ...Bf5.",
            ),
            Variation(
                slug="modern_nf3",
                name="Modern Variation",
                eco="B04–B05",
                moves_uci=["e2e4","g8f6","e4e5","f6d5","d2d4","d7d6","g1f3"],
                moves_san="1.e4 Nf6 2.e5 Nd5 3.d4 d6 4.Nf3",
                summary="The modern positional approach — White declines "
                        "to overextend and develops solidly instead.",
            ),
            Variation(
                slug="alekhine_exchange",
                name="Exchange Variation",
                eco="B03",
                moves_uci=["e2e4","g8f6","e4e5","f6d5","d2d4","d7d6",
                           "c2c4","d5b6","e5d6","c7d6"],
                moves_san="1.e4 Nf6 2.e5 Nd5 3.d4 d6 4.c4 Nb6 5.exd6 cxd6",
                summary="White exchanges the e5 pawn for a long-term "
                        "structural plus — simple and solid; Black has "
                        "the half-open c-file in compensation.",
            ),
            Variation(
                slug="alekhine_chase",
                name="Chase Variation",
                eco="B02",
                moves_uci=["e2e4","g8f6","e4e5","f6d5","c2c4","d5b6","c4c5"],
                moves_san="1.e4 Nf6 2.e5 Nd5 3.c4 Nb6 4.c5",
                summary="White chases the knight to the rim — gains huge "
                        "space at the cost of structural commitments. Sharp, "
                        "double-edged, theory-heavy.",
            ),
        ],
    ),
    CatalogEntry(
        side="black", slug="pirc",
        name="Pirc Defense",
        eco="B07–B09",
        moves_uci=["e2e4", "d7d6", "d2d4", "g8f6", "b1c3", "g7g6"],
        moves_san="1.e4 d6 2.d4 Nf6 3.Nc3 g6",
        summary="Hypermodern — Black fianchettoes and waits for White "
                "to overextend.",
        famous_games=[
            FamousGame(
                title="Kasparov vs Topalov, Wijk aan Zee 1999",
                master_game_id="kasparov_vs_topalov_1999",
                note="Kasparov's Immortal — a deep king-hunt combination "
                     "that chased Topalov's king from b8 to d2.",
            ),
        ],
        variations=[
            Variation(
                slug="austrian",
                name="Austrian Attack",
                eco="B09",
                moves_uci=["e2e4","d7d6","d2d4","g8f6","b1c3","g7g6","f2f4"],
                moves_san="1.e4 d6 2.d4 Nf6 3.Nc3 g6 4.f4",
                summary="The most ambitious White setup — pawns roll "
                        "forward with f4-e5 to crush the kingside.",
                famous_master_id="kasparov_vs_topalov_1999",
            ),
            Variation(
                slug="classical_be3",
                name="150 Attack (Classical)",
                eco="B07",
                moves_uci=["e2e4","d7d6","d2d4","g8f6","b1c3","g7g6","c1e3"],
                moves_san="1.e4 d6 2.d4 Nf6 3.Nc3 g6 4.Be3",
                summary="The 150-Attack setup — Be3, Qd2, O-O-O, then "
                        "h4-h5 to attack the fianchettoed king.",
            ),
            Variation(
                slug="pirc_classical",
                name="Classical Variation (Two Knights)",
                eco="B07–B08",
                moves_uci=["e2e4","d7d6","d2d4","g8f6","b1c3","g7g6",
                           "g1f3","f8g7","f1e2","e8g8"],
                moves_san="1.e4 d6 2.d4 Nf6 3.Nc3 g6 4.Nf3 Bg7 5.Be2 O-O",
                summary="The most principled anti-Pirc — quiet "
                        "development with O-O, Re1, h3; aims for a "
                        "small but durable space advantage.",
            ),
            Variation(
                slug="pirc_byrne",
                name="Byrne Variation (4.Bg5)",
                eco="B07",
                moves_uci=["e2e4","d7d6","d2d4","g8f6","b1c3","g7g6","c1g5"],
                moves_san="1.e4 d6 2.d4 Nf6 3.Nc3 g6 4.Bg5",
                summary="Quick development, eyeing f6 and f7 — White avoids "
                        "the slower main lines for direct attacking chances.",
            ),
        ],
    ),
    CatalogEntry(
        side="black", slug="modern",
        name="Modern Defense",
        eco="B06",
        moves_uci=["e2e4", "g7g6"],
        moves_san="1.e4 g6",
        summary="Black fianchettoes immediately and holds the centre "
                "back. Flexible, transposes to Pirc / KID structures.",
        famous_games=[
            FamousGame(
                title="Ashley vs Weeramantry, New York Open 1991",
                master_game_id="ashley_vs_weeramantry_1991",
                note="A classic Modern Defense game by Maurice Ashley — "
                     "Black uses the fianchetto setup before counter-"
                     "punching against White's central pawn chain.",
            ),
        ],
        variations=[
            Variation(
                slug="standard",
                name="Standard Modern",
                eco="B06",
                moves_uci=["e2e4","g7g6","d2d4","f8g7","b1c3","d7d6"],
                moves_san="1.e4 g6 2.d4 Bg7 3.Nc3 d6",
                summary="The mainstream setup — flexible, often "
                        "transposes into Pirc structures.",
            ),
            Variation(
                slug="averbakh",
                name="Averbakh System",
                eco="B06",
                moves_uci=["e2e4","g7g6","d2d4","f8g7","c2c4","d7d6","b1c3"],
                moves_san="1.e4 g6 2.d4 Bg7 3.c4 d6 4.Nc3",
                summary="White grabs maximum space with c4 — "
                        "transposes into King's Indian-like positions.",
            ),
            Variation(
                slug="modern_three_pawns",
                name="Three Pawns Attack (Pseudo-Austrian)",
                eco="B06",
                moves_uci=["e2e4","g7g6","d2d4","f8g7","f2f4","d7d6",
                           "g1f3"],
                moves_san="1.e4 g6 2.d4 Bg7 3.f4 d6 4.Nf3",
                summary="White grabs maximum central space with e4-d4-f4; "
                        "Black plays a hyper-modern strategy of "
                        "undermining with c5, Nc6 and ...e5.",
            ),
            Variation(
                slug="modern_pterodactyl",
                name="Pterodactyl Variation",
                eco="B06",
                moves_uci=["e2e4","g7g6","d2d4","f8g7","b1c3","c7c5"],
                moves_san="1.e4 g6 2.d4 Bg7 3.Nc3 c5",
                summary="Modern with an early ...c5 — Black challenges "
                        "White's centre directly, transposing into Sicilian- "
                        "like structures with a fianchettoed king.",
            ),
        ],
    ),
    CatalogEntry(
        side="black", slug="qgd",
        name="Queen's Gambit Declined",
        eco="D30–D69",
        moves_uci=["d2d4", "d7d5", "c2c4", "e7e6"],
        moves_san="1.d4 d5 2.c4 e6",
        summary="Classical — Black supports d5 with …e6 at the cost of "
                "the c8 bishop. Deep strategic battles.",
        famous_games=[
            FamousGame(
                title="Fischer vs Spassky, 1972 (Game 6)",
                master_game_id="fischer_vs_spassky_1972_g6",
                note="Tartakower variation of the QGD. "
                     "Spassky applauded after resigning.",
            ),
        ],
        variations=[
            Variation(
                slug="orthodox",
                name="Orthodox Defense",
                eco="D60–D69",
                moves_uci=["d2d4","d7d5","c2c4","e7e6","b1c3","g8f6",
                           "c1g5","f8e7"],
                moves_san="1.d4 d5 2.c4 e6 3.Nc3 Nf6 4.Bg5 Be7",
                summary="The classical Orthodox — Black plays solidly "
                        "with ...Nbd7 and ...c6. Old-school strategy.",
                famous_game_slug="qgd_orthodox",
            ),
            Variation(
                slug="tartakower",
                name="Tartakower Defense",
                eco="D58–D59",
                moves_uci=["d2d4","d7d5","c2c4","e7e6","b1c3","g8f6",
                           "c1g5","f8e7","e2e3","e8g8","g1f3","h7h6",
                           "g5h4","b7b6"],
                moves_san="1.d4 d5 2.c4 e6 3.Nc3 Nf6 4.Bg5 Be7 5.e3 O-O "
                          "6.Nf3 h6 7.Bh4 b6",
                summary="Black fianchettoes the c8-bishop with ...b6 — "
                        "solves the QGD's classical bishop problem.",
                famous_master_id="fischer_vs_spassky_1972_g6",
            ),
            Variation(
                slug="qgd_lasker",
                name="Lasker Defense",
                eco="D56",
                moves_uci=["d2d4","d7d5","c2c4","e7e6","b1c3","g8f6",
                           "c1g5","f8e7","e2e3","e8g8","g1f3","h7h6",
                           "g5h4","f6e4"],
                moves_san="1.d4 d5 2.c4 e6 3.Nc3 Nf6 4.Bg5 Be7 5.e3 O-O "
                          "6.Nf3 h6 7.Bh4 Ne4",
                summary="Black plays ...Ne4 to trade pieces and ease "
                        "the position — Lasker's classical equalizing "
                        "method; aims for a quiet positional game.",
            ),
            Variation(
                slug="qgd_cambridge_springs",
                name="Cambridge Springs",
                eco="D52",
                moves_uci=["d2d4","d7d5","c2c4","e7e6","b1c3","g8f6","c1g5","b8d7","g1f3","c7c6","e2e3","d8a5"],
                moves_san="1.d4 d5 2.c4 e6 3.Nc3 Nf6 4.Bg5 Nbd7 5.Nf3 c6 6.e3 Qa5",
                summary="Black builds a counterattack on the queenside with "
                        "...Qa5, exploiting the pin on g5. Classic surprise "
                        "weapon at all levels.",
            ),
        ],
    ),
    CatalogEntry(
        side="black", slug="slav",
        name="Slav Defense",
        eco="D10–D19",
        moves_uci=["d2d4", "d7d5", "c2c4", "c7c6"],
        moves_san="1.d4 d5 2.c4 c6",
        summary="Defends d5 with the c-pawn, keeping the c8 bishop "
                "active. Solid and popular at every level.",
        famous_games=[
            FamousGame(
                title="Carlsen vs Anand, World Ch. 2013 (Game 5)",
                master_game_id="carlsen_vs_anand_2013_g5",
                note="Semi-Slav structure → Carlsen's technical grind "
                     "turns an equal endgame into a win.",
            ),
        ],
        variations=[
            Variation(
                slug="semi_slav_meran",
                name="Semi-Slav Meran",
                eco="D43–D49",
                moves_uci=["d2d4","d7d5","c2c4","c7c6","g1f3","g8f6",
                           "b1c3","e7e6","e2e3","b8d7","f1d3","d5c4",
                           "d3c4","b7b5"],
                moves_san="1.d4 d5 2.c4 c6 3.Nf3 Nf6 4.Nc3 e6 5.e3 Nbd7 "
                          "6.Bd3 dxc4 7.Bxc4 b5",
                summary="Black plays both ...c6 and ...e6, then breaks "
                        "with ...b5 — extremely sharp, deep theory.",
                famous_master_id="carlsen_vs_anand_2013_g5",
            ),
            Variation(
                slug="slav_main_dxc4",
                name="Main Line (4...dxc4)",
                eco="D11–D19",
                moves_uci=["d2d4","d7d5","c2c4","c7c6","g1f3","g8f6",
                           "b1c3","d5c4"],
                moves_san="1.d4 d5 2.c4 c6 3.Nf3 Nf6 4.Nc3 dxc4",
                summary="Black takes on c4 and often plays ...Bf5 — "
                        "the pure Slav, bishop active outside the chain.",
            ),
            Variation(
                slug="slav_exchange",
                name="Exchange Slav",
                eco="D10–D11",
                moves_uci=["d2d4","d7d5","c2c4","c7c6","c4d5","c6d5"],
                moves_san="1.d4 d5 2.c4 c6 3.cxd5 cxd5",
                summary="Symmetrical pawn structure — looks drawish but "
                        "White's small space edge and minority-attack "
                        "ideas often produce decisive games.",
            ),
            Variation(
                slug="slav_chebanenko",
                name="Chebanenko Slav (4...a6)",
                eco="D15",
                moves_uci=["d2d4","d7d5","c2c4","c7c6","g1f3","g8f6","b1c3","a7a6"],
                moves_san="1.d4 d5 2.c4 c6 3.Nf3 Nf6 4.Nc3 a6",
                summary="Modern Slav — Black plays ...a6 to prepare ...b5 and "
                        "free the queenside without committing the c8-bishop "
                        "early. A favourite of Bareev and Morozevich.",
            ),
        ],
    ),
    CatalogEntry(
        side="black", slug="kings_indian",
        name="King's Indian Defense",
        eco="E60–E99",
        moves_uci=["d2d4", "g8f6", "c2c4", "g7g6"],
        moves_san="1.d4 Nf6 2.c4 g6",
        summary="Black fianchettoes and lets White build the center, "
                "then counter-attacks with …e5 / …f5. Sharp, thematic.",
        famous_games=[
            FamousGame(
                title="Firouzja vs Sindarov, FIDE World Cup 2021",
                master_game_id="sindarov_vs_firouzja_2021",
                note="A modern King's Indian Orthodox knockout-stage "
                     "battle — Black executes the thematic …e5 + …f5 "
                     "counter-attack against the d5 White centre.",
            ),
        ],
        variations=[
            Variation(
                slug="mar_del_plata",
                name="Mar del Plata",
                eco="E97–E99",
                moves_uci=["d2d4","g8f6","c2c4","g7g6","b1c3","f8g7",
                           "e2e4","d7d6","g1f3","e8g8","f1e2","e7e5",
                           "e1g1","b8c6","d4d5","c6e7"],
                moves_san="1.d4 Nf6 2.c4 g6 3.Nc3 Bg7 4.e4 d6 5.Nf3 O-O "
                          "6.Be2 e5 7.O-O Nc6 8.d5 Ne7",
                summary="The fighting main line — closed centre, both "
                        "sides race their pawns on opposite wings.",
            ),
            Variation(
                slug="saemisch",
                name="Sämisch Variation",
                eco="E80–E89",
                moves_uci=["d2d4","g8f6","c2c4","g7g6","b1c3","f8g7",
                           "e2e4","d7d6","f2f3"],
                moves_san="1.d4 Nf6 2.c4 g6 3.Nc3 Bg7 4.e4 d6 5.f3",
                summary="Solid f3 setup — White prepares Be3, Qd2, O-O-O "
                        "and a kingside pawn storm.",
            ),
            Variation(
                slug="kid_classical",
                name="Classical Variation",
                eco="E92–E99",
                moves_uci=["d2d4","g8f6","c2c4","g7g6","b1c3","f8g7",
                           "e2e4","d7d6","g1f3","e8g8","f1e2","e7e5"],
                moves_san="1.d4 Nf6 2.c4 g6 3.Nc3 Bg7 4.e4 d6 5.Nf3 O-O 6.Be2 e5",
                summary="The classical main line — opposite-side pawn "
                        "advances, Black storms the kingside, White "
                        "the queenside; race-to-mate themes.",
            ),
            Variation(
                slug="kid_fianchetto",
                name="Fianchetto KID (g3)",
                eco="E60–E69",
                moves_uci=["d2d4","g8f6","c2c4","g7g6","g2g3","f8g7","f1g2","e8g8","b1c3","d7d6","g1f3"],
                moves_san="1.d4 Nf6 2.c4 g6 3.g3 Bg7 4.Bg2 O-O 5.Nc3 d6 6.Nf3",
                summary="Quiet KID — White builds a long-diagonal bishop and "
                        "avoids the violent Mar del Plata structures. Slow "
                        "manoeuvring war.",
            ),
        ],
    ),
    CatalogEntry(
        side="black", slug="nimzo_indian",
        name="Nimzo-Indian Defense",
        eco="E20–E59",
        moves_uci=["d2d4", "g8f6", "c2c4", "e7e6", "b1c3", "f8b4"],
        moves_san="1.d4 Nf6 2.c4 e6 3.Nc3 Bb4",
        summary="Black pins White's knight and aims for doubled c-pawns. "
                "One of the soundest defenses to 1.d4.",
        famous_games=[
            FamousGame(
                title="Spassky vs Fischer, World Ch 1972 (Game 5)",
                master_game_id="spassky_vs_fischer_1972_g5",
                note="Fischer's first win in the 1972 match — a model "
                     "Nimzo where Black trades the dark-square bishop "
                     "early and pressures White's doubled c-pawns.",
            ),
        ],
        variations=[
            Variation(
                slug="rubinstein",
                name="Rubinstein Variation (4.e3)",
                eco="E40–E59",
                moves_uci=["d2d4","g8f6","c2c4","e7e6","b1c3","f8b4","e2e3"],
                moves_san="1.d4 Nf6 2.c4 e6 3.Nc3 Bb4 4.e3",
                summary="The most popular system — White develops "
                        "calmly, accepts doubled pawns for the bishop pair.",
                famous_game_slug="nimzo_rubinstein",
            ),
            Variation(
                slug="classical_qc2",
                name="Classical (4.Qc2)",
                eco="E32–E39",
                moves_uci=["d2d4","g8f6","c2c4","e7e6","b1c3","f8b4","d1c2"],
                moves_san="1.d4 Nf6 2.c4 e6 3.Nc3 Bb4 4.Qc2",
                summary="White avoids doubled pawns by preparing to "
                        "recapture on c3 with the queen.",
            ),
            Variation(
                slug="nimzo_saemisch",
                name="Sämisch Variation (4.a3)",
                eco="E25–E29",
                moves_uci=["d2d4","g8f6","c2c4","e7e6","b1c3","f8b4",
                           "a2a3","b4c3","b2c3"],
                moves_san="1.d4 Nf6 2.c4 e6 3.Nc3 Bb4 4.a3 Bxc3+ 5.bxc3",
                summary="White accepts doubled c-pawns for the bishop "
                        "pair and central control — sharp and "
                        "double-edged; Black plays against the c-pawns "
                        "with ...c5 and ...Nc6.",
            ),
            Variation(
                slug="nimzo_kasparov",
                name="Nimzo Kasparov Variation (4.Nf3)",
                eco="E20",
                moves_uci=["d2d4","g8f6","c2c4","e7e6","b1c3","f8b4","g1f3"],
                moves_san="1.d4 Nf6 2.c4 e6 3.Nc3 Bb4 4.Nf3",
                summary="Flexible try — White develops the king's knight "
                        "before committing pawns. Often transposes into Bogo- "
                        "Indian or Queen's Indian structures.",
            ),
        ],
    ),
    CatalogEntry(
        side="black", slug="grunfeld",
        name="Grünfeld Defense",
        eco="D70–D99",
        moves_uci=["d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "d7d5"],
        moves_san="1.d4 Nf6 2.c4 g6 3.Nc3 d5",
        summary="Hypermodern — Black trades center pawns for piece "
                "activity. Sharp, theoretical, aggressive defense.",
        famous_games=[
            FamousGame(
                title="Byrne vs Fischer, 'Game of the Century' 1956",
                master_game_id="fischer_vs_byrne_1956",
                note="13-year-old Fischer's queen sacrifice — one of "
                     "the most famous games ever played.",
            ),
        ],
        variations=[
            Variation(
                slug="exchange",
                name="Exchange Variation",
                eco="D85–D89",
                moves_uci=["d2d4","g8f6","c2c4","g7g6","b1c3","d7d5",
                           "c4d5","f6d5","e2e4","d5c3","b2c3","f8g7"],
                moves_san="1.d4 Nf6 2.c4 g6 3.Nc3 d5 4.cxd5 Nxd5 5.e4 "
                          "Nxc3 6.bxc3 Bg7",
                summary="The main battlefield — White builds a big "
                        "centre, Black undermines with ...c5.",
            ),
            Variation(
                slug="russian",
                name="Russian Variation",
                eco="D97",
                moves_uci=["d2d4","g8f6","c2c4","g7g6","b1c3","d7d5",
                           "g1f3","f8g7","d1b3"],
                moves_san="1.d4 Nf6 2.c4 g6 3.Nc3 d5 4.Nf3 Bg7 5.Qb3",
                summary="White grabs the c-pawn with Qb3 — Black plays "
                        "...dxc4 ...c6 ...b5 for queenside counterplay.",
            ),
            Variation(
                slug="grunfeld_fianchetto",
                name="Fianchetto Variation",
                eco="D78–D79",
                moves_uci=["d2d4","g8f6","c2c4","g7g6","g1f3","f8g7",
                           "g2g3","d7d5","f1g2","e8g8","e1g1"],
                moves_san="1.d4 Nf6 2.c4 g6 3.Nf3 Bg7 4.g3 d5 5.Bg2 O-O 6.O-O",
                summary="Quiet positional anti-Grünfeld — both bishops "
                        "fianchettoed, slow maneuvering; less theory "
                        "than the Exchange but harder to break through.",
            ),
            Variation(
                slug="grunfeld_classical_be3",
                name="Classical Grünfeld (7.Be3)",
                eco="D85",
                moves_uci=["d2d4","g8f6","c2c4","g7g6","b1c3","d7d5","c4d5","f6d5","e2e4","d5c3","b2c3","f8g7","c1e3"],
                moves_san="1.d4 Nf6 2.c4 g6 3.Nc3 d5 4.cxd5 Nxd5 5.e4 Nxc3 6.bxc3 Bg7 7.Be3",
                summary="Classical Grünfeld with the bishop on e3 — White "
                        "fortifies the centre while preparing Qd2 and long "
                        "castling. The modern main line.",
            ),
        ],
    ),
    CatalogEntry(
        side="black", slug="dutch",
        name="Dutch Defense",
        eco="A80–A99",
        moves_uci=["d2d4", "f7f5"],
        moves_san="1.d4 f5",
        summary="Black plays for a kingside pawn bind with …f5 and "
                "often …g6 + …Bg7. Sharp, double-edged.",
        famous_games=[
            FamousGame(
                title="Capablanca vs Tartakower, New York 1924",
                master_game_id="capablanca_vs_tartakower_1924",
                note="Famous rook endgame from a Dutch Stonewall — "
                     "Capablanca's textbook king activity.",
            ),
        ],
        variations=[
            Variation(
                slug="stonewall",
                name="Stonewall Variation",
                eco="A90–A95",
                moves_uci=["d2d4","f7f5","g2g3","g8f6","f1g2","e7e6",
                           "g1f3","d7d5","e1g1","f8d6","c2c4","c7c6"],
                moves_san="1.d4 f5 2.g3 Nf6 3.Bg2 e6 4.Nf3 d5 5.O-O Bd6 "
                          "6.c4 c6",
                summary="Black builds a pawn wall on dark squares "
                        "(d5,e6,f5,c6) — strategic, rigid, aggressive.",
                famous_master_id="capablanca_vs_tartakower_1924",
            ),
            Variation(
                slug="leningrad",
                name="Leningrad Variation",
                eco="A87–A89",
                moves_uci=["d2d4","f7f5","g2g3","g8f6","f1g2","g7g6"],
                moves_san="1.d4 f5 2.g3 Nf6 3.Bg2 g6",
                summary="Black plays a King's Indian-like setup with f5 "
                        "instead of d6. Aggressive kingside intentions.",
            ),
            Variation(
                slug="dutch_classical",
                name="Classical Dutch",
                eco="A88",
                moves_uci=["d2d4","f7f5","g2g3","g8f6","f1g2","e7e6",
                           "g1f3","f8e7","e1g1","e8g8"],
                moves_san="1.d4 f5 2.g3 Nf6 3.Bg2 e6 4.Nf3 Be7 5.O-O O-O",
                summary="The flexible Classical setup with ...e6 and "
                        "...Be7 — Black keeps options between Stonewall "
                        "and Leningrad-style pawn structures.",
            ),
            Variation(
                slug="dutch_staunton",
                name="Staunton Gambit",
                eco="A82–A83",
                moves_uci=["d2d4","f7f5","e2e4"],
                moves_san="1.d4 f5 2.e4",
                summary="White sacrifices a pawn to open lines against the "
                        "weakened Black kingside — sharp, theory-light, and "
                        "statistically dangerous for Black.",
            ),
        ],
    ),
    CatalogEntry(
        side="black", slug="budapest",
        name="Budapest Gambit",
        eco="A51–A52",
        moves_uci=["d2d4", "g8f6", "c2c4", "e7e5"],
        moves_san="1.d4 Nf6 2.c4 e5",
        summary="Black offers a pawn to open lines on the kingside. "
                "Sharp and surprising, good club-player weapon.",
        famous_games=[
            FamousGame(
                title="Rubinstein vs Vidmar, Berlin 1918",
                master_game_id="rubinstein_vs_vidmar_1918",
                note="A famous 16-move miniature — Vidmar's smothered-"
                     "mate trap with 15...Nd3# is the textbook "
                     "illustration of the Budapest Gambit's tactics.",
            ),
        ],
        variations=[
            Variation(
                slug="adler",
                name="Main Line (3...Ng4)",
                eco="A52",
                moves_uci=["d2d4","g8f6","c2c4","e7e5","d4e5","f6g4"],
                moves_san="1.d4 Nf6 2.c4 e5 3.dxe5 Ng4",
                summary="Black aims to recover the pawn with ...Nxe5 "
                        "or pressure on f2 / e5. The principal line.",
            ),
            Variation(
                slug="fajarowicz",
                name="Fajarowicz Variation",
                eco="A51",
                moves_uci=["d2d4","g8f6","c2c4","e7e5","d4e5","f6e4"],
                moves_san="1.d4 Nf6 2.c4 e5 3.dxe5 Ne4",
                summary="Provocative knight jump — Black gambits and "
                        "plays for piece activity rather than pawn recovery.",
            ),
            Variation(
                slug="budapest_alekhine",
                name="Alekhine Variation (4.e4)",
                eco="A52",
                moves_uci=["d2d4","g8f6","c2c4","e7e5","d4e5","f6g4",
                           "e2e4"],
                moves_san="1.d4 Nf6 2.c4 e5 3.dxe5 Ng4 4.e4",
                summary="White grabs maximum central space — sharp and "
                        "principled; Black must work hard to recover "
                        "the e5 pawn while White builds with Nf3, Be2.",
            ),
            Variation(
                slug="budapest_rubinstein",
                name="Rubinstein Variation (4.Bf4)",
                eco="A52",
                moves_uci=["d2d4","g8f6","c2c4","e7e5","d4e5","f6g4","c1f4"],
                moves_san="1.d4 Nf6 2.c4 e5 3.dxe5 Ng4 4.Bf4",
                summary="The most popular Budapest reply — White holds the "
                        "e5-pawn under simple development pressure rather "
                        "than Alekhine's ambitious 4.e4.",
            ),
        ],
    ),
    CatalogEntry(
        side="black", slug="benko",
        name="Benko Gambit",
        eco="A57–A59",
        moves_uci=["d2d4", "g8f6", "c2c4", "c7c5", "d4d5", "b7b5"],
        moves_san="1.d4 Nf6 2.c4 c5 3.d5 b5",
        summary="Black sacrifices the b-pawn for long-term pressure on "
                "the queenside. Positional gambit, highly respected.",
        famous_games=[
            FamousGame(
                title="Benko Gambit Accepted — main-line illustration",
                master_game_id="benko_gambit_main_line",
                note="Pal Benko popularised 3...b5 — the pawn sacrifice "
                     "trading material for long-term pressure on the "
                     "queenside files. This is the main-line Fianchetto "
                     "Accepted, the most reputable acceptance for White.",
            ),
        ],
        variations=[
            Variation(
                slug="accepted_fianchetto",
                name="Accepted (5.bxa6)",
                eco="A58–A59",
                moves_uci=["d2d4","g8f6","c2c4","c7c5","d4d5","b7b5",
                           "c4b5","a7a6","b5a6"],
                moves_san="1.d4 Nf6 2.c4 c5 3.d5 b5 4.cxb5 a6 5.bxa6",
                summary="The principled acceptance — White grabs the "
                        "pawn, Black gets long-term queenside pressure.",
            ),
            Variation(
                slug="declined_b6",
                name="Declined (6.b6)",
                eco="A57",
                moves_uci=["d2d4","g8f6","c2c4","c7c5","d4d5","b7b5",
                           "g1f3","g7g6","c4b5","a7a6","b5b6"],
                moves_san="1.d4 Nf6 2.c4 c5 3.d5 b5 4.Nf3 g6 5.cxb5 a6 "
                          "6.b6",
                summary="White refuses the second pawn — keeps the "
                        "Benko player off the open a- and b-files.",
            ),
            Variation(
                slug="benko_modern_decline",
                name="Modern Decline (4.Nf3)",
                eco="A57",
                moves_uci=["d2d4","g8f6","c2c4","c7c5","d4d5","b7b5",
                           "g1f3"],
                moves_san="1.d4 Nf6 2.c4 c5 3.d5 b5 4.Nf3",
                summary="A modern way to sidestep the Benko's main "
                        "lines — White develops naturally and aims to "
                        "consolidate with e3 and Be2 rather than "
                        "accept the gambit pawn.",
            ),
            Variation(
                slug="benko_zaitsev",
                name="Benko Accepted, Main Line (6.e4)",
                eco="A57–A58",
                moves_uci=["d2d4","g8f6","c2c4","c7c5","d4d5","b7b5","c4b5","a7a6","b1c3","a6b5","e2e4"],
                moves_san="1.d4 Nf6 2.c4 c5 3.d5 b5 4.cxb5 a6 5.Nc3 axb5 6.e4",
                summary="Sharp accepted Benko — White takes the pawn but "
                        "allows Black blistering queenside pressure on the a- "
                        "and b-files. Theory-rich main line.",
            ),
        ],
    ),
]


# ─────────────────────────────────────────────────────────────────────
# Public assembly
# ─────────────────────────────────────────────────────────────────────

OPENING_CATALOG: dict = {}
for entry in _WHITE_ENTRIES + _BLACK_ENTRIES:
    OPENING_CATALOG[(entry.side, entry.slug)] = entry


def entries_for_side(side: str) -> list:
    """Return the CatalogEntry list for 'white' or 'black', in the
    order they are declared above (curated, not alphabetical)."""
    if side == "white":
        return list(_WHITE_ENTRIES)
    if side == "black":
        return list(_BLACK_ENTRIES)
    return []


def find_entry(side: str, slug: str):
    return OPENING_CATALOG.get((side, slug))


def resolve_famous_game(fg: FamousGame, master_games_list):
    """Look up a FamousGame by its master_game_id against the master
    games list. Returns the MasterGame or None. Used by the UI when
    the user clicks 'replay' on an entry."""
    if fg.master_game_id is None:
        return None
    for mg in master_games_list:
        if mg.id == fg.master_game_id:
            return mg
    return None


# ─────────────────────────────────────────────────────────────────────
# Self-validation: parse every inline PGN so we know at startup
# whether hand-entered move lists are legal. Games that fail are
# marked pgn_valid=False and the UI will silently skip them; the
# console prints a warning so developers can fix them.
#
# python-chess silently truncates the mainline on an illegal move, so
# we compare parsed-ply count to declared-token count in the source
# to catch partial parses.
# ─────────────────────────────────────────────────────────────────────

def _validate():
    try:
        import chess
        import chess.pgn
        import io
        import re
    except ImportError:
        return

    for entry in _WHITE_ENTRIES + _BLACK_ENTRIES:
        for fg in entry.famous_games:
            if fg.pgn is None:
                continue
            try:
                pgn_text = fg.pgn
                if not pgn_text.lstrip().startswith("["):
                    pgn_text = (
                        f'[Event "{fg.title}"]\n'
                        f'[Site "?"]\n'
                        f'[Date "????.??.??"]\n'
                        f'[White "?"]\n'
                        f'[Black "?"]\n'
                        f'[Result "*"]\n\n' + pgn_text
                    )
                game = chess.pgn.read_game(io.StringIO(pgn_text))
                if game is None:
                    raise ValueError("read_game returned None")

                board = game.board()
                parsed_plies = 0
                for mv in game.mainline_moves():
                    if mv not in board.legal_moves:
                        raise ValueError(f"illegal move in mainline: {mv}")
                    board.push(mv)
                    parsed_plies += 1

                # Count SAN tokens in the raw text and compare.
                movetext = pgn_text.split("]", 1)[-1]
                movetext = re.sub(r"\{[^}]*\}", " ", movetext)
                tokens = []
                for tok in movetext.split():
                    if re.match(r"^\d+\.+$", tok):
                        continue
                    if tok in ("1-0", "0-1", "1/2-1/2", "*"):
                        continue
                    if re.match(r"^\$\d+$", tok):
                        continue
                    tokens.append(tok)
                if parsed_plies < len(tokens):
                    raise ValueError(
                        f"truncated: parsed {parsed_plies} of "
                        f"{len(tokens)} declared moves — illegal move "
                        f"somewhere after ply {parsed_plies}"
                    )
            except Exception as e:
                fg.pgn_valid = False
                print(f"[openings_catalog] WARNING: PGN for "
                      f"{entry.side}/{entry.slug} "
                      f"({fg.title!r}) failed validation: {e}")

    # Variation UCI validation — push every UCI move onto a fresh
    # board, ensure all are legal. Variations with illegal moves get
    # moves_valid=False; the UI silently skips them. This catches the
    # same class of bug the PGN validator catches, but for the much
    # shorter UCI lists used by variations.
    for entry in _WHITE_ENTRIES + _BLACK_ENTRIES:
        for v in entry.variations:
            try:
                board = chess.Board()
                for i, u in enumerate(v.moves_uci):
                    mv = chess.Move.from_uci(u)
                    if mv not in board.legal_moves:
                        raise ValueError(
                            f"illegal move {u} at ply {i+1}")
                    board.push(mv)
            except Exception as e:
                v.moves_valid = False
                print(f"[openings_catalog] WARNING: variation "
                      f"{entry.side}/{entry.slug}/{v.slug} "
                      f"failed UCI validation: {e}")


_validate()
