"""
imbalances_tutorial.py — Tutorial inspired by Jeremy Silman's
"How to Reassess Your Chess, 4th Edition: Chess Mastery Through
Imbalances" (Siles Press, 2010).

The book teaches positional chess through the concept of *imbalances*:
any significant difference in the two camps. A player's job is to
recognize the imbalances, then formulate a plan that favors their own
imbalances while neutralizing the opponent's.

This module organizes the material into the book's nine major parts
(matching the published table of contents) and exposes a flat
chapter list of 64 lessons that the UI can browse. Each `Lesson`
holds a short key-idea explanation written in our own words — NOT a
verbatim copy of Silman's prose — plus optional illustrative
positions in FEN. The illustrative positions are classic textbook
motifs (a knight on an outpost vs. a bad bishop, a minority attack
pawn formation, etc.) that exist in many sources, not Silman's
specific game diagrams.

The Lichess study at https://lichess.org/study/6pxT9XFt (64
chapters) was used as a structural reference for chapter counts per
part, but no annotation text was copied from it.
"""
from dataclasses import dataclass, field


# ─────────────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────────────

@dataclass
class Lesson:
    """A single tutorial lesson.

    Attributes
    ----------
    slug : str
        Short unique identifier (used as dict key / sprite slot key).
    part : str
        Which of the nine book parts this lesson belongs to (e.g.
        "Minor Pieces"). Used to group lessons under category headers.
    title : str
        Short human-readable title shown in the list.
    key_idea : str
        One-paragraph explanation of the lesson's core concept.
        Written in our own words.
    plan : list[str]
        Step-by-step practical advice — what to *do* when you spot
        this imbalance. Each entry is one short line.
    fen : str
        Optional FEN of an illustrative position. Empty string when
        no representative position is provided (the lesson is then
        purely textual).
    fen_note : str
        Short caption shown under the position, e.g. who's to move
        and what they should be looking at.
    """
    slug: str
    part: str
    title: str
    key_idea: str
    plan: list = field(default_factory=list)
    fen: str = ""
    fen_note: str = ""


# ─────────────────────────────────────────────────────────────────────
# Nine parts (book table of contents)
# Order matches the printed 4th edition.
# ─────────────────────────────────────────────────────────────────────

PARTS = [
    "The Concept of Imbalances",
    "Minor Pieces",
    "Rooks",
    "Psychological Meanderings",
    "Target Consciousness",
    "Statics vs. Dynamics",
    "Space",
    "Passed Pawns",
    "Other Imbalances",
]


# Short blurb for each part — shown when the user clicks the part
# header in the left pane. Again, our own words.
PART_DESCRIPTIONS = {
    "The Concept of Imbalances": (
        "An imbalance is any meaningful difference between the two "
        "sides — better minor piece, weaker king, more space, an open "
        "file, lead in development, and so on. Plans grow out of "
        "imbalances. If you can name what's unbalanced about a "
        "position, you can name the plan."
    ),
    "Minor Pieces": (
        "Bishops and knights have very different temperaments. "
        "Bishops love open diagonals and long-range play; knights "
        "love closed positions and outposts. 'Good bishop vs bad "
        "bishop' and 'knight vs bishop' are two of the most common "
        "and decisive imbalances at club level."
    ),
    "Rooks": (
        "Rooks are file-and-rank pieces — they want open files, the "
        "seventh rank, and connected support. A rook with no file is "
        "a sad rook. Look at where the open and half-open files are, "
        "and at which side can occupy or contest them."
    ),
    "Psychological Meanderings": (
        "Chess is also a mental game. Fear of complications, refusing "
        "to admit a plan failed, copying your opponent's style, "
        "playing too fast when winning — these are imbalances of "
        "*attitude* and they cost rating points. Silman's section on "
        "this is one of the most quietly useful parts of the book."
    ),
    "Target Consciousness": (
        "Every plan needs a target. A weak pawn, a weak square, an "
        "exposed king, an undefended piece — without a target you "
        "are just shuffling. The trained eye spots the target first "
        "and then asks 'how do I get my pieces to it?'."
    ),
    "Statics vs. Dynamics": (
        "Static factors don't change easily: pawn structure, weak "
        "squares, material. Dynamic factors are fleeting: initiative, "
        "tempo, threats. Sometimes you sacrifice a static advantage "
        "for a dynamic one (a gambit), sometimes you neutralize "
        "dynamics to cash in static plus."
    ),
    "Space": (
        "More space = more squares for your pieces. The side with "
        "less space typically has a cramped position and should try "
        "to trade pieces; the side with more space should avoid "
        "trades and look for a breakthrough."
    ),
    "Passed Pawns": (
        "A passed pawn — no enemy pawn ahead of it on its file or "
        "the adjacent files — is a permanent threat. It must be "
        "blockaded; it must be watched; and at some point it wants "
        "to march. Silman calls them 'a tireless soldier'."
    ),
    "Other Imbalances": (
        "Everything else: development leads, the bishop pair, weak "
        "color complexes, queenside vs kingside majorities, "
        "initiative, king safety mismatches. Together with the "
        "earlier parts, they cover virtually every positional "
        "decision in a chess game."
    ),
}


# ─────────────────────────────────────────────────────────────────────
# Lesson library — 64 chapters across the nine parts
# ─────────────────────────────────────────────────────────────────────

LESSONS: list[Lesson] = [

    # ── Part 1: The Concept of Imbalances ────────────────────────────
    Lesson(
        slug="imb_what_is",
        part="The Concept of Imbalances",
        title="What is an imbalance?",
        key_idea=(
            "An imbalance is any noticeable difference between the "
            "two camps that can be exploited. Material is the most "
            "obvious one, but space, structure, piece activity, king "
            "safety, the bishop pair, and even who-moves-first all "
            "count. Silman's central claim is that strategy is the "
            "art of working with imbalances — finding the ones that "
            "favor you, neutralizing the ones that favor the enemy."
        ),
        plan=[
            "List the imbalances for both sides.",
            "Decide which ones favor you, which favor the opponent.",
            "Pick a plan that uses your imbalance against theirs.",
        ],
    ),
    Lesson(
        slug="imb_list",
        part="The Concept of Imbalances",
        title="The imbalances breakdown",
        key_idea=(
            "Silman's catalog of imbalances: superior minor piece, "
            "pawn structure, space, material, control of a key file, "
            "control of a hole or weak square, lead in development, "
            "initiative ('pushing your own agenda'), king safety, "
            "and statics vs. dynamics. Memorize the list — it's "
            "your positional checklist for every position you "
            "reach."
        ),
        plan=[
            "Run the list mentally on every middlegame position.",
            "Even one match = a plan candidate.",
            "Multiple matches = prioritize the most permanent one.",
        ],
    ),
    Lesson(
        slug="imb_plan_creation",
        part="The Concept of Imbalances",
        title="Plan creation: from imbalance to move",
        key_idea=(
            "Once you've found your favorable imbalance, the plan "
            "writes itself: maneuver pieces toward the strong square "
            "/ file / sector, prevent the opponent from neutralizing "
            "it, and only then look for the tactical execution. The "
            "common mistake at club level is to skip steps and jump "
            "straight to a move — Silman calls this 'hoping' "
            "instead of thinking."
        ),
        plan=[
            "Identify the imbalance.",
            "Name the squares involved.",
            "Find the pieces that want to go there.",
            "Then — and only then — calculate concrete moves.",
        ],
    ),
    Lesson(
        slug="imb_dont_copy",
        part="The Concept of Imbalances",
        title="Don't blindly copy your opponent",
        key_idea=(
            "Beginners often mirror their opponent's moves out of a "
            "fear of doing the 'wrong' thing. Mirroring guarantees "
            "you never create an imbalance — and if you never "
            "create an imbalance, you can never play for a win. "
            "Pick a side of the board, a piece configuration, a "
            "pawn break — and commit to it."
        ),
        plan=[
            "Notice when you're matching the opponent's setup.",
            "Ask: 'what would I play if I were on this side fresh?'",
            "Choose a plan even if it feels less safe.",
        ],
    ),
    Lesson(
        slug="imb_assess_first",
        part="The Concept of Imbalances",
        title="Assess before you calculate",
        key_idea=(
            "Calculation without assessment is wasted energy. "
            "Before counting variations, name the imbalances aloud "
            "(in your head): 'I have the bishop pair, he has a "
            "knight outpost on d5, my king is safer, his rook is "
            "more active.' Now your calculation has a goal — you "
            "calculate toward the imbalance that favors you."
        ),
        plan=[
            "Pause. Don't move yet.",
            "Run the 30-second imbalance scan.",
            "Now calculate concrete moves to exploit one.",
        ],
    ),
    Lesson(
        slug="imb_static_vs_dyn_intro",
        part="The Concept of Imbalances",
        title="Permanent vs temporary imbalances",
        key_idea=(
            "Some imbalances stay forever (a doubled pawn, a "
            "weakened color complex, the bishop pair); others "
            "evaporate in two moves (a tempo, a threat, an "
            "initiative). When you have a permanent imbalance, you "
            "can play slowly. When you have a temporary one, you "
            "must strike now — by next move it may be gone."
        ),
        plan=[
            "Tag every imbalance: permanent or temporary?",
            "Temporary favorable imbalance = play sharp now.",
            "Permanent favorable imbalance = improve slowly.",
        ],
    ),

    # ── Part 2: Minor Pieces ─────────────────────────────────────────
    Lesson(
        slug="mp_knight_vs_bishop",
        part="Minor Pieces",
        title="Knight vs bishop — first principles",
        key_idea=(
            "Bishops love open positions with long diagonals. "
            "Knights love closed positions with stable support "
            "points. If the position has many pawns locked in the "
            "center, knights are usually better. If the center is "
            "open and pawns are mobile, bishops are usually better."
        ),
        plan=[
            "Look at the central pawns: locked or fluid?",
            "Locked → fight to keep your knight, trade the bishop.",
            "Fluid → fight to keep your bishop, trade the knight.",
        ],
        fen="r1bqk2r/ppp2ppp/2n2n2/3pp3/3PP3/2N2N2/PPP2PPP/R1BQK2R w KQkq - 0 6",
        fen_note=(
            "Closed-ish center. Each side has one knight and one "
            "bishop deployed; the imbalance question is who can "
            "trade off the wrong piece first."
        ),
    ),
    Lesson(
        slug="mp_good_vs_bad_bishop",
        part="Minor Pieces",
        title="Good bishop vs bad bishop",
        key_idea=(
            "A bishop is 'bad' when its own pawns block its "
            "diagonals — for example, a light-squared bishop "
            "trapped behind pawns on light squares. The classic "
            "club-level mistake is to keep your bad bishop alive "
            "out of attachment instead of trading it for the "
            "opponent's good one."
        ),
        plan=[
            "Identify your bishop's color complex.",
            "Are your pawns on that color or the opposite?",
            "If on the same color → bishop is bad. Trade it.",
        ],
        fen="4k3/p2b1ppp/1p2p3/2p1P3/2P5/1P3P2/P2B2PP/4K3 w - - 0 1",
        fen_note=(
            "White's d2 bishop is bad (pawns fix on light squares). "
            "Black's d7 bishop is even worse — even more pawns on "
            "the same color. Side with the *less-bad* bishop has "
            "the edge."
        ),
    ),
    Lesson(
        slug="mp_outpost_knight",
        part="Minor Pieces",
        title="The outpost knight",
        key_idea=(
            "A knight on an outpost — a square deep in the enemy "
            "camp that can't be challenged by an enemy pawn — is "
            "often worth more than a rook. The classic outposts are "
            "d5/e5 for White, d4/e4 for Black. If you have one, "
            "occupy it and defend it; if your opponent has one, "
            "exchange or evict the knight."
        ),
        plan=[
            "Spot squares that no enemy pawn can ever attack.",
            "Get a knight there. Defend it twice.",
            "Use it as a base for tactics elsewhere.",
        ],
        fen="r2q1rk1/pp2bppp/2n1pn2/2bpN3/3P4/2P1PN2/PP3PPP/R1BQ1RK1 w - - 0 1",
        fen_note=(
            "The Ne5 outpost — no Black pawn can challenge it. "
            "From here it attacks c6, d7, f7, g6 and supports a "
            "kingside attack."
        ),
    ),
    Lesson(
        slug="mp_bishop_pair",
        part="Minor Pieces",
        title="The bishop pair",
        key_idea=(
            "Two bishops covering both color complexes is a small "
            "but lasting advantage — usually worth about a quarter "
            "of a pawn in open positions, almost nothing in closed "
            "ones. The pair shines as the position opens; the side "
            "without the pair should keep things closed and try to "
            "trade one of the bishops off."
        ),
        plan=[
            "If you have the pair: open the position.",
            "If you don't: close the position, trade a bishop.",
            "Never blindly swap your bishop for a knight if it "
            "breaks the pair.",
        ],
    ),
    Lesson(
        slug="mp_knight_endgames",
        part="Minor Pieces",
        title="Knights in the endgame",
        key_idea=(
            "Knights are slow. In endgames where pawns exist on "
            "both sides of the board, a bishop is usually stronger "
            "because it can switch wings in one move while a knight "
            "needs three or four. Conversely, knights dominate "
            "endgames with pawns on only one side and a stable "
            "structure."
        ),
        plan=[
            "Count which wings have pawns.",
            "Pawns on both wings → favor the bishop side.",
            "Pawns on one wing only → favor the knight side.",
        ],
    ),
    Lesson(
        slug="mp_bishop_distance",
        part="Minor Pieces",
        title="The bishop's reach",
        key_idea=(
            "A bishop can attack a target on the far side of the "
            "board in one move. A knight on the same square may need "
            "three or four. This 'distance' advantage matters most "
            "in positions with weaknesses on both wings — the "
            "bishop can defend one and attack the other almost "
            "simultaneously."
        ),
        plan=[
            "In two-wing positions: keep the bishop.",
            "Look for diagonals that span both flanks.",
            "Use the bishop to defend at home, attack abroad.",
        ],
    ),
    Lesson(
        slug="mp_minor_piece_trades",
        part="Minor Pieces",
        title="Choosing which minor piece to trade",
        key_idea=(
            "A trade is never automatic — every exchange leaves the "
            "remaining pieces unbalanced in a specific way. Before "
            "trading, ask: which of *my* pieces is the bad one, "
            "and which of *his* is the good one? Aim to swap "
            "your-bad for his-good."
        ),
        plan=[
            "Rank your three minor pieces from best to worst.",
            "Rank his three the same way.",
            "Trade your worst for his best whenever possible.",
        ],
    ),
    Lesson(
        slug="mp_bishop_vs_knight_endgame_example",
        part="Minor Pieces",
        title="Practical conversion: B vs N",
        key_idea=(
            "Even a small bishop-vs-knight edge wins many endgames "
            "if you handle the technique correctly. Centralize the "
            "king, create a passed pawn on the wing far from the "
            "knight, and use the bishop's range to do two things at "
            "once. The knight side defends by reaching outposts "
            "near the action."
        ),
        plan=[
            "Activate your king first.",
            "Create a passer far from the knight.",
            "Force the knight to choose: defend or chase.",
        ],
    ),

    # ── Part 3: Rooks ────────────────────────────────────────────────
    Lesson(
        slug="rook_open_file",
        part="Rooks",
        title="Open files belong to rooks",
        key_idea=(
            "An open file (no pawns of either side) is a highway. "
            "Whichever side seizes it first gets to penetrate to "
            "the 7th or 8th rank. The fight for an open file is "
            "often the central drama of an entire middlegame: "
            "doubling rooks, contesting the file, trading off the "
            "opponent's pieces on it."
        ),
        plan=[
            "Spot every open and half-open file.",
            "Get a rook on it first.",
            "Double rooks if the opponent contests it.",
        ],
        fen="r1bq1rk1/pp3ppp/2n1pn2/3p4/3P4/2N1PN2/PP3PPP/R1BQ1RK1 w - - 0 1",
        fen_note=(
            "The c-file is half-open for White. Rook to c1 starts "
            "the campaign; eventually Black's c6 knight or c8 "
            "pieces will feel the pressure."
        ),
    ),
    Lesson(
        slug="rook_seventh_rank",
        part="Rooks",
        title="Rooks on the seventh",
        key_idea=(
            "A rook on the 7th rank attacks the enemy pawn base "
            "and cuts off the enemy king on the back rank. Two "
            "rooks on the 7th — the 'pigs on the seventh' — is "
            "usually decisive even at the cost of a pawn or two "
            "to get there. Endgame books are full of pure "
            "rook-on-7th wins."
        ),
        plan=[
            "Identify a route to the 7th rank.",
            "Pay material if needed to reach it.",
            "Two rooks on the 7th = look for back-rank mates.",
        ],
        fen="6k1/R6p/4p1p1/8/8/8/r4PPP/6K1 w - - 0 1",
        fen_note=(
            "White rook on the 7th attacks h7 and cuts off the "
            "king. Black's rook on the 2nd makes things mutual — "
            "but White moves first."
        ),
    ),
    Lesson(
        slug="rook_half_open",
        part="Rooks",
        title="Half-open files",
        key_idea=(
            "A half-open file has one of your pawns missing but an "
            "enemy pawn still on it. The enemy pawn becomes your "
            "target. Stack pieces against it — rook, queen, "
            "sometimes a second rook — and break through. This is "
            "the engine behind countless 'minority attack' and "
            "Sicilian-style operations."
        ),
        plan=[
            "Half-open file → enemy pawn on it = the target.",
            "Stack pieces against it.",
            "Add pawn breaks to expose it further.",
        ],
    ),
    Lesson(
        slug="rook_rook_lift",
        part="Rooks",
        title="The rook lift",
        key_idea=(
            "Rooks usually swing along the third rank to switch "
            "wings or join a kingside attack — Rf1-f3-h3 is the "
            "classic. The lift trades a tempo for activity, and it "
            "works because rooks behind their own pawns are slow "
            "to enter the game without it."
        ),
        plan=[
            "Identify which file is safe to lift behind.",
            "Get the rook to the 3rd (or 4th) rank.",
            "Swing to the wing where the action lives.",
        ],
    ),
    Lesson(
        slug="rook_passive_rook",
        part="Rooks",
        title="The passive rook problem",
        key_idea=(
            "A rook on a1 with no open file is just decoration. "
            "Many lost positions trace back to one rook that never "
            "got into the game. Before any maneuver, ask: 'will my "
            "rooks have files after this?' If both answers are no, "
            "find a different plan."
        ),
        plan=[
            "Count active rooks for both sides.",
            "If yours are passive, plan a pawn break to open lines.",
            "Otherwise consider a rook lift.",
        ],
    ),
    Lesson(
        slug="rook_doubling",
        part="Rooks",
        title="Doubling rooks",
        key_idea=(
            "Doubled rooks on a file double the pressure and prepare "
            "a sacrifice to break through. The order matters: "
            "doubling with the rook in front is usually wrong "
            "because it blocks its partner; the standard formation "
            "is queen behind both rooks (sometimes called Alekhine's "
            "gun)."
        ),
        plan=[
            "Decide which file to double on.",
            "Rook in front, rook behind — queen even further back.",
            "Now look for the breakthrough sacrifice.",
        ],
    ),

    # ── Part 4: Psychological Meanderings ────────────────────────────
    Lesson(
        slug="psy_no_no_plan",
        part="Psychological Meanderings",
        title="The 'no plan' problem",
        key_idea=(
            "Most amateur losses don't come from a bad plan — they "
            "come from no plan at all. Move-by-move reaction to "
            "opponent threats produces a position where you've "
            "drifted into something passive. The cure is the "
            "imbalance checklist: every five moves, stop and ask "
            "'what's my plan and what's his?'"
        ),
        plan=[
            "Every few moves: pause and articulate the plan.",
            "If you can't, your last few moves were drift.",
            "Pick a target based on the imbalances.",
        ],
    ),
    Lesson(
        slug="psy_fear_of_complications",
        part="Psychological Meanderings",
        title="Fear of complications",
        key_idea=(
            "Many players retreat when they should attack, simply "
            "because the resulting position feels 'scary.' But "
            "scary positions are usually scary for both sides — and "
            "if the imbalances favor you, the complications favor "
            "you too. Trust the assessment, not the feeling."
        ),
        plan=[
            "If the imbalances favor you, don't dodge complications.",
            "Calculate the line; don't rule it out emotionally.",
            "Bail-out moves are often the real losing moves.",
        ],
    ),
    Lesson(
        slug="psy_attachment",
        part="Psychological Meanderings",
        title="Attachment to a bad plan",
        key_idea=(
            "Once a player commits to a plan, they often refuse to "
            "abandon it even after the opponent's response makes "
            "it pointless. Silman calls this stubbornness — the "
            "ego of being 'right' overruling the evidence. "
            "Re-evaluate every move; if the imbalances changed, "
            "the plan should change."
        ),
        plan=[
            "After every opponent move, re-list the imbalances.",
            "If they changed, change your plan.",
            "Sunk cost doesn't exist in chess.",
        ],
    ),
    Lesson(
        slug="psy_overconfidence",
        part="Psychological Meanderings",
        title="Don't relax when winning",
        key_idea=(
            "A winning position is the most dangerous time to stop "
            "thinking. Many games swing from won to lost because "
            "the winning side started playing fast, played the "
            "'obvious' moves, and missed a tactic. Discipline says: "
            "the worse off the opponent is, the more carefully you "
            "should calculate."
        ),
        plan=[
            "When you're winning, slow down, not speed up.",
            "Recheck every tactic for two more moves.",
            "Look for desperate sacrifices.",
        ],
    ),
    Lesson(
        slug="psy_time_pressure",
        part="Psychological Meanderings",
        title="Time pressure & decision quality",
        key_idea=(
            "Players in time trouble make pattern-recognition moves "
            "instead of calculated ones. The fix is to spend more "
            "time *earlier* on quiet moves so that you have time "
            "in the critical phase. Don't waste 10 minutes on a "
            "forced recapture."
        ),
        plan=[
            "Save your time for non-forced positions.",
            "Make forced or obvious moves quickly.",
            "Spend the saved time on the imbalance-defining move.",
        ],
    ),
    Lesson(
        slug="psy_style_clash",
        part="Psychological Meanderings",
        title="Playing your style vs the opponent's",
        key_idea=(
            "Every player has a comfort zone — tactical, "
            "positional, defensive, attacking. A good opponent "
            "tries to drag you into theirs. Awareness is the "
            "defense: if you find yourself in a wild, open game "
            "and you're a positional player, simplify; if you're "
            "stuck in a slow grind and you're a tactician, look "
            "for a pawn break."
        ),
        plan=[
            "Name your style. Name the opponent's.",
            "If the position favors theirs, change the imbalances.",
            "Trades, breaks, and sacrifices all reshape the "
            "position's character.",
        ],
    ),
    Lesson(
        slug="psy_blunder_protocol",
        part="Psychological Meanderings",
        title="Blunder check before every move",
        key_idea=(
            "Even strong players blunder pieces. The discipline "
            "fix: before pressing the clock, run a 5-second "
            "blunder check — 'after my move, what does my opponent "
            "threaten that I haven't dealt with?' Five seconds "
            "saves thirty minutes of regret."
        ),
        plan=[
            "Pick your move.",
            "Pause. Visualize the position after your move.",
            "Ask: 'what's the most forcing reply?'",
            "Only then move.",
        ],
    ),

    # ── Part 5: Target Consciousness ─────────────────────────────────
    Lesson(
        slug="tgt_what_is_target",
        part="Target Consciousness",
        title="Spotting a target",
        key_idea=(
            "A target is a weakness — typically a pawn that can't "
            "be defended by another pawn, or a square that can't be "
            "challenged. Once you spot the target, the plan is "
            "obvious: bring more attackers than the opponent has "
            "defenders."
        ),
        plan=[
            "Look at every pawn and square: who defends it?",
            "Pawns with no pawn defender = candidate targets.",
            "Squares with no pawn cover = candidate weak squares.",
        ],
    ),
    Lesson(
        slug="tgt_isolated_pawn",
        part="Target Consciousness",
        title="The isolated queen pawn (IQP)",
        key_idea=(
            "An isolated pawn is one with no friendly pawns on "
            "either adjacent file. It can never be defended by a "
            "pawn, so it's always a long-term target. But it also "
            "controls two valuable central squares and gives the "
            "owner attacking chances. Whether IQP is good or bad "
            "depends on what stage of the game it's in."
        ),
        plan=[
            "Owner: use the IQP early — it gives space + attack.",
            "Owner: trade pieces only if the IQP isn't your target.",
            "Opponent: trade pieces; head for the endgame.",
        ],
        fen="r1bq1rk1/pp3ppp/2nbpn2/8/2BP4/2N1PN2/PP3PPP/R1BQR1K1 w - - 0 1",
        fen_note=(
            "Classic isolani: White's d4 pawn is isolated. White "
            "has space and active pieces; Black aims to blockade "
            "with a knight on d5 and trade down."
        ),
    ),
    Lesson(
        slug="tgt_backward_pawn",
        part="Target Consciousness",
        title="The backward pawn",
        key_idea=(
            "A backward pawn is behind its neighbors and can't "
            "advance safely. It's a target *and* the square in "
            "front of it is a hole for the opponent. Doubly bad: "
            "the pawn is weak, and an outpost sits right above it."
        ),
        plan=[
            "Side with the backward pawn: try to advance it.",
            "If the advance isn't possible, defend it with pieces.",
            "Opponent: occupy the hole; pressure the pawn.",
        ],
    ),
    Lesson(
        slug="tgt_weak_color_complex",
        part="Target Consciousness",
        title="Weak color complexes",
        key_idea=(
            "If all the pawns of one side stand on one color, the "
            "other-color squares are weak — and the bishop of that "
            "color is bad. Worse, if the opponent has the "
            "bishop-of-the-weak-color, those squares are doomed. "
            "The 'dark-square strategy' that wins so many king's "
            "indian games is exactly this."
        ),
        plan=[
            "Map your pawns by color. Look for imbalance.",
            "Lots of pawns on one color → opposite squares are weak.",
            "Trade your-bad-bishop, keep your-good-bishop.",
        ],
    ),
    Lesson(
        slug="tgt_weak_king_position",
        part="Target Consciousness",
        title="The weak king as target",
        key_idea=(
            "When an opponent's king lacks pawn cover or has a "
            "wandering monarch, the entire enemy position becomes "
            "a target. Even a small material investment "
            "(sacrificing a pawn, a piece) is worth it to expose "
            "the king further. The cure for the defender is "
            "ruthless simplification."
        ),
        plan=[
            "Count pawns/pieces shielding both kings.",
            "If one side's shield is thin, that's the target.",
            "Pour pieces toward it; consider sacrifices.",
        ],
    ),
    Lesson(
        slug="tgt_create_target",
        part="Target Consciousness",
        title="Creating targets when none exist",
        key_idea=(
            "Symmetrical positions have no targets — yet. Often "
            "the right plan is to *force* an imbalance by playing "
            "a pawn break (b4-b5, f4-f5, d4-d5) that creates a "
            "target where there was none. Once the structure "
            "fractures, normal target-consciousness takes over."
        ),
        plan=[
            "In symmetrical positions, look for a pawn break.",
            "The break either gains space or creates targets.",
            "Don't be afraid to commit — symmetry is its own loss.",
        ],
    ),
    Lesson(
        slug="tgt_pile_up_attackers",
        part="Target Consciousness",
        title="Attackers vs defenders count",
        key_idea=(
            "Once a target is fixed, the math is simple: count "
            "attackers and defenders. The opponent loses the "
            "target if you have more attackers than they have "
            "defenders, *and* the lowest-value attacker is no "
            "greater than the lowest-value defender."
        ),
        plan=[
            "Pick the target.",
            "Count attackers and defenders on that square.",
            "If attackers > defenders by one, look for a removal.",
        ],
    ),

    # ── Part 6: Statics vs. Dynamics ─────────────────────────────────
    Lesson(
        slug="sd_definition",
        part="Statics vs. Dynamics",
        title="What is static, what is dynamic",
        key_idea=(
            "Static factors are 'permanent' — pawn structure, "
            "weak squares, material balance. Dynamic factors are "
            "'temporary' — tempo, threats, initiative. Static "
            "advantages survive trades; dynamic advantages must be "
            "used immediately or they disappear."
        ),
        plan=[
            "Tag each advantage you have: static or dynamic.",
            "Static → play for the long term, trade pieces.",
            "Dynamic → play sharply, keep pieces on.",
        ],
    ),
    Lesson(
        slug="sd_sacrifice_for_dynamics",
        part="Statics vs. Dynamics",
        title="Sacrificing static for dynamic",
        key_idea=(
            "Gambits trade a static asset (material) for a dynamic "
            "one (development, attack, initiative). They work when "
            "the dynamics can be converted to a winning attack "
            "before the opponent stabilizes. They fail when the "
            "opponent simply gives back the material and reaches "
            "a safe position."
        ),
        plan=[
            "Static-for-dynamic offers: only if conversion is real.",
            "Calculate the attack to a forcing conclusion.",
            "If unclear, return the material and play position.",
        ],
    ),
    Lesson(
        slug="sd_convert_dynamic_to_static",
        part="Statics vs. Dynamics",
        title="Cashing dynamics into statics",
        key_idea=(
            "If you have temporary initiative, you must convert it "
            "into something permanent before it fades — win a "
            "pawn, weaken the enemy structure, or transition into "
            "a better endgame. Otherwise the opponent equalizes "
            "and your tempo edge evaporates."
        ),
        plan=[
            "While the initiative lasts: force concessions.",
            "Force a weak pawn, weak square, or trade off the "
            "active defenders.",
            "Then transition; static plus is converted.",
        ],
    ),
    Lesson(
        slug="sd_when_dynamics_win",
        part="Statics vs. Dynamics",
        title="When dynamics dominate",
        key_idea=(
            "In sharp positions with kings exposed or pieces "
            "swarming, dynamics simply outvote statics. A doubled "
            "pawn and an isolated rook don't matter if your queen "
            "and knight are about to mate the king. Read the "
            "tempo: how many forcing moves are still on the table?"
        ),
        plan=[
            "Count active pieces near the enemy king.",
            "Count forcing moves available (checks, captures, "
            "threats).",
            "If both numbers are high, dynamics rule — attack.",
        ],
    ),
    Lesson(
        slug="sd_when_statics_win",
        part="Statics vs. Dynamics",
        title="When statics dominate",
        key_idea=(
            "In quiet, simplified positions, statics rule. An "
            "endgame with an extra pawn wins — eventually — no "
            "matter how mobile the opponent's pieces feel. The "
            "trick is to defuse the dynamics first (trade queens, "
            "blunt the diagonals) and then convert."
        ),
        plan=[
            "If you have a static plus, simplify.",
            "Trade off the opponent's active pieces.",
            "Reach an endgame; the static advantage converts itself.",
        ],
    ),
    Lesson(
        slug="sd_assessment_balance",
        part="Statics vs. Dynamics",
        title="Balancing the assessment",
        key_idea=(
            "Almost every middlegame position is a tug-of-war "
            "between static and dynamic factors. The mistake is to "
            "look at only one side: 'I'm a pawn up, so I'm "
            "winning' (ignoring his initiative), or 'I'm "
            "attacking, so I'm winning' (ignoring his structure). "
            "Both lists matter."
        ),
        plan=[
            "Write the static factors on one mental column.",
            "Write the dynamic factors on the other.",
            "Compare. Don't sign off until both sides match.",
        ],
    ),

    # ── Part 7: Space ────────────────────────────────────────────────
    Lesson(
        slug="sp_definition",
        part="Space",
        title="What counts as space?",
        key_idea=(
            "Space is the territory behind your pawns — squares "
            "your pieces can safely use. You earn it with advanced "
            "pawns. More space means more piece mobility; less "
            "space means cramped, awkward, hard-to-maneuver pieces."
        ),
        plan=[
            "Count squares on your side of the 4th/5th ranks.",
            "More squares = more space.",
            "Use it: maneuver pieces; the opponent can't match.",
        ],
    ),
    Lesson(
        slug="sp_trades_when_cramped",
        part="Space",
        title="Cramped? Trade pieces.",
        key_idea=(
            "The classic rule: the side with less space wants to "
            "exchange pieces, because fewer pieces means each "
            "remaining piece needs less room. Cramped + many "
            "pieces = pieces stepping on each other. Cramped + few "
            "pieces = no problem."
        ),
        plan=[
            "If you're cramped, seek trades.",
            "Even uneven trades (knight for bishop) may be worth "
            "it.",
            "Trade off the most active enemy piece first.",
        ],
    ),
    Lesson(
        slug="sp_avoid_trades_with_space",
        part="Space",
        title="Space advantage? Avoid trades.",
        key_idea=(
            "If you have more space, every trade reduces your "
            "advantage. Your pieces need the room you've created. "
            "Keep them all on the board; the opponent's pieces "
            "will continue to bump into each other and create new "
            "weaknesses."
        ),
        plan=[
            "Side with space: dodge exchanges.",
            "Maneuver to the active wing.",
            "Let the opponent's pieces step on each other.",
        ],
    ),
    Lesson(
        slug="sp_pawn_breaks",
        part="Space",
        title="Pawn breaks against more space",
        key_idea=(
            "The defender of a cramped position can't just wait "
            "forever — they must find a pawn break to release the "
            "tension. Common breaks: ...c5 against the Saemisch, "
            "...f5 against the King's Indian-style space, ...b5 "
            "against queenside cramps. Without a break, the "
            "cramped side suffocates."
        ),
        plan=[
            "Identify candidate pawn breaks.",
            "Prepare each break with piece support.",
            "Play the break when defenders outnumber attackers.",
        ],
    ),
    Lesson(
        slug="sp_space_attack",
        part="Space",
        title="Converting space into attack",
        key_idea=(
            "Once you have a clear space advantage and the "
            "opponent is passive, transition into an attack. The "
            "advanced pawns themselves become a battering ram — "
            "push them further to break open the enemy king. "
            "King's Indian Saemisch, French Winawer, Benoni — all "
            "spaces converted to attacks."
        ),
        plan=[
            "Identify which wing your space favors.",
            "Look for a king on that wing.",
            "Push pawns + bring pieces to break it open.",
        ],
    ),
    Lesson(
        slug="sp_space_in_endgame",
        part="Space",
        title="Space in the endgame",
        key_idea=(
            "Even in the endgame, more space matters — your king "
            "infiltrates more easily; your rooks reach more "
            "squares; your pawns are closer to promotion. The "
            "side with less space in the endgame usually loses to "
            "zugzwang."
        ),
        plan=[
            "In endgames, push pawns to claim space.",
            "Centralize the king; use the room you have.",
            "Force the opponent into zugzwang.",
        ],
    ),

    # ── Part 8: Passed Pawns ─────────────────────────────────────────
    Lesson(
        slug="pp_definition",
        part="Passed Pawns",
        title="What makes a passed pawn",
        key_idea=(
            "A passed pawn has no enemy pawn ahead of it on its "
            "file or either adjacent file. It can therefore promote "
            "if not stopped. Even a passed pawn five squares from "
            "queening is a real, ongoing threat that ties down "
            "enemy pieces to block it."
        ),
        plan=[
            "Identify passed pawns for both sides.",
            "Tie up at least one enemy piece per passer (blockader).",
            "Use the freed-up tempo elsewhere on the board.",
        ],
        fen="8/8/3k4/8/3P4/3K4/8/8 w - - 0 1",
        fen_note=(
            "Pure king-and-pawn passer endgame. White's d4 pawn is "
            "passed — but with the kings opposed and Black's king "
            "in front of the pawn, the pawn alone doesn't win."
        ),
    ),
    Lesson(
        slug="pp_blockade",
        part="Passed Pawns",
        title="Blockading the passer",
        key_idea=(
            "The classical blockader is a knight — it controls "
            "diagonals from its square, can attack while "
            "blockading, and can't be challenged easily. Rooks "
            "make poor blockaders (too valuable to be tied to a "
            "square); bishops are mediocre (one diagonal). Knight "
            "blockade is the gold standard."
        ),
        plan=[
            "When facing a passer, blockade with a knight.",
            "Knight on the square directly in front of the pawn.",
            "Use the same knight to attack other targets.",
        ],
        fen="8/8/3k1p2/4p3/3pP3/3N4/3K1P2/8 w - - 0 1",
        fen_note=(
            "Knight on d3 blockades Black's d4 passer perfectly. "
            "From there it can still hop to b4, c5, e5 — never just "
            "a defender, always also a potential attacker."
        ),
    ),
    Lesson(
        slug="pp_outside_passer",
        part="Passed Pawns",
        title="The outside passed pawn",
        key_idea=(
            "An outside passer — one on the wing far from the main "
            "action — is a special weapon in king-and-pawn "
            "endgames. It pulls the enemy king toward it; then "
            "your king feasts on the abandoned pawns on the other "
            "wing. 'Decoy and harvest.'"
        ),
        plan=[
            "In K+P endgames, head for an outside passer.",
            "Push it to draw the enemy king.",
            "Then walk your king to the opposite wing pawns.",
        ],
    ),
    Lesson(
        slug="pp_protected_passer",
        part="Passed Pawns",
        title="The protected passed pawn",
        key_idea=(
            "A passed pawn supported by another pawn is a "
            "permanent fortress and a permanent threat. It can't "
            "be won by a single piece; it must always be watched. "
            "In equal-material endgames, a protected passer "
            "usually decides the result."
        ),
        plan=[
            "Cherish your protected passers; never trade them.",
            "If you're defending, find ways to neutralize them "
            "(blockade + trade pieces).",
            "Eventually the passer marches; plan accordingly.",
        ],
    ),
    Lesson(
        slug="pp_pawn_majority",
        part="Passed Pawns",
        title="Creating a passed pawn from a majority",
        key_idea=(
            "A pawn majority on one wing (3-vs-2, or 2-vs-1) can "
            "almost always create a passed pawn — push the "
            "unopposed pawn first. The technique is identical to "
            "every textbook: candidate pawn first, supporting "
            "pawn second."
        ),
        plan=[
            "Identify your majority wing.",
            "Push the 'candidate' pawn (the one without an "
            "opposite-file enemy pawn) first.",
            "Then push the supporters to clear the path.",
        ],
    ),
    Lesson(
        slug="pp_passer_in_middlegame",
        part="Passed Pawns",
        title="Passed pawns in the middlegame",
        key_idea=(
            "A central or queenside passer in the middlegame ties "
            "down two or three enemy pieces and effectively "
            "reduces the defender's army. Even if the pawn never "
            "queens, the piece bind on the rest of the board "
            "produces tactics elsewhere. Nimzowitsch called the "
            "passer 'a criminal that must be kept under lock and "
            "key.'"
        ),
        plan=[
            "Push the passer to demand attention.",
            "While defenders are tied up, attack elsewhere.",
            "Sometimes you sacrifice the passer for the broader "
            "attack — that's a feature, not a bug.",
        ],
    ),
    Lesson(
        slug="pp_endgame_techniques",
        part="Passed Pawns",
        title="Endgame conversion technique",
        key_idea=(
            "Converting a passer in the endgame demands king "
            "involvement. The king escorts the pawn forward, "
            "shouldering the enemy king aside. In rook endgames, "
            "the rook goes *behind* the passer (Tarrasch rule); "
            "the enemy rook stays passive behind it."
        ),
        plan=[
            "Bring the king to escort the passer.",
            "Rook behind the passer (yours and the enemy's).",
            "Use 'shouldering' to keep the enemy king out.",
        ],
    ),
    Lesson(
        slug="pp_passer_race",
        part="Passed Pawns",
        title="The pawn race",
        key_idea=(
            "When both sides have a passer racing to promote, "
            "count moves. A single tempo decides the game. Look "
            "for a queen-with-check after promotion — that's a "
            "common reason the 'losing' race wins anyway. "
            "Stalemate themes and skewer themes also bend the "
            "outcome."
        ),
        plan=[
            "Count moves to promotion for each side carefully.",
            "Check whether the new queen gives check.",
            "Look for skewers and stalemate ideas.",
        ],
    ),

    # ── Part 9: Other Imbalances ─────────────────────────────────────
    Lesson(
        slug="oth_development",
        part="Other Imbalances",
        title="Lead in development",
        key_idea=(
            "Pieces on good squares vs pieces still on the back "
            "rank is a temporary imbalance that must be exploited "
            "quickly. Open the position, attack the king, force "
            "trades that keep the lead intact. If you let your "
            "development edge dissolve, you've wasted it."
        ),
        plan=[
            "Count developed pieces. Difference of 2+ = act now.",
            "Open lines (pawn breaks, sacrifices if needed).",
            "Attack the side whose king is still uncastled.",
        ],
    ),
    Lesson(
        slug="oth_initiative",
        part="Other Imbalances",
        title="Initiative — pushing your agenda",
        key_idea=(
            "Initiative means you're the one making threats and "
            "the opponent is the one reacting. Even without "
            "material edge, initiative wins games because the "
            "defender eventually slips. Hold the initiative as "
            "long as you can: every move should pose a problem."
        ),
        plan=[
            "Every move: 'does this pose a problem?'",
            "If no, find a more forcing alternative.",
            "If the opponent's move was passive, escalate.",
        ],
    ),
    Lesson(
        slug="oth_king_safety_mismatch",
        part="Other Imbalances",
        title="King-safety mismatches",
        key_idea=(
            "When one king is safe and the other is exposed, the "
            "exposed king is the only imbalance that matters. "
            "Throw pieces at it; even sacrifices of material are "
            "justified. The defender must trade pieces and seek "
            "an endgame where bare kings level the field."
        ),
        plan=[
            "Assess both kings' shelters.",
            "If asymmetric, attack the weaker king.",
            "Defender: trade pieces ruthlessly.",
        ],
    ),
    Lesson(
        slug="oth_majorities",
        part="Other Imbalances",
        title="Pawn majorities on opposite wings",
        key_idea=(
            "If you have a queenside majority and your opponent a "
            "kingside majority, you're playing for the queenside "
            "passer and they're playing for the kingside attack. "
            "These positions are sharp — whoever creates their "
            "threat first usually wins. Common in Spanish and "
            "exchange-French structures."
        ),
        plan=[
            "Identify both sides' majorities.",
            "Race to mobilize yours first.",
            "Watch the opposite-wing king as the timing clock.",
        ],
    ),
    Lesson(
        slug="oth_files_squares",
        part="Other Imbalances",
        title="Key files and key squares",
        key_idea=(
            "Some files (open, half-open, near the king) and some "
            "squares (outposts, hole-squares, central squares) "
            "matter more than others. The team that controls them "
            "controls the position. Don't trade away a piece that "
            "controls a key square cheaply."
        ),
        plan=[
            "Mark the key files and squares for both sides.",
            "Compete for them with rooks (files) and knights "
            "(squares).",
            "Never trade off your key-square controller.",
        ],
    ),
    Lesson(
        slug="oth_material_imbalance",
        part="Other Imbalances",
        title="Material imbalances: minor for rook",
        key_idea=(
            "A rook is roughly worth 5 points; a minor piece is "
            "3 — but the difference shrinks when the position is "
            "closed or when the minor piece sits on a great "
            "square. 'Bishop and pawn for rook' is roughly even "
            "in many middlegames despite the point count. Trust "
            "imbalances, not point totals."
        ),
        plan=[
            "After exchange sacrifices, evaluate by imbalances.",
            "Closed positions favor the minor piece side.",
            "Open positions favor the rook side.",
        ],
    ),
    Lesson(
        slug="oth_exchange_sac",
        part="Other Imbalances",
        title="The exchange sacrifice",
        key_idea=(
            "Giving up a rook for a minor piece is justified when "
            "you gain a permanent imbalance in return: a "
            "dominating outpost knight, a strong color complex, "
            "an attack on a weakened king. Petrosian made a career "
            "of this trade."
        ),
        plan=[
            "Spot exchange sac candidates: rook for great minor.",
            "Verify the imbalance gained is permanent.",
            "Don't sac just to liven things up — you need a "
            "concrete return.",
        ],
    ),
    Lesson(
        slug="oth_minority_attack",
        part="Other Imbalances",
        title="The minority attack",
        key_idea=(
            "On the queenside, fewer pawns (a 'minority') push "
            "forward to break the enemy's pawn majority and leave "
            "behind a weak pawn on a half-open file. Standard plan "
            "in the Queen's Gambit exchange and in Caro-Kann "
            "structures. The follow-up: stack rooks on the "
            "half-open file against the weak pawn."
        ),
        plan=[
            "On the wing with fewer pawns: push them.",
            "Trade your pawns for theirs.",
            "Stack pieces on the half-open file you create.",
        ],
        fen="r2q1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PPQ2PPP/R4RK1 w - - 0 1",
        fen_note=(
            "Exchange QGD structure. White will play b4-b5 to break "
            "Black's c6 — the classic minority attack. Black needs "
            "kingside counterplay to balance."
        ),
    ),
    Lesson(
        slug="oth_prophylaxis",
        part="Other Imbalances",
        title="Prophylactic thinking",
        key_idea=(
            "Before every move, ask: 'what would my opponent play "
            "if it were their move?' Prevent *their* best plan "
            "with your move. Karpov's whole style was "
            "prophylactic — quietly anticipating and neutralizing "
            "before initiating his own play."
        ),
        plan=[
            "Each move: imagine you skipped — what would they play?",
            "Pick the move that prevents that.",
            "Even a small restraint compounds into long-term "
            "dominance.",
        ],
    ),
    Lesson(
        slug="oth_summary",
        part="Other Imbalances",
        title="Putting it all together",
        key_idea=(
            "Strong play is the constant application of the "
            "imbalance checklist. Every position has at least one "
            "favorable imbalance for one side; finding it and "
            "exploiting it is what separates club players from "
            "experts. Silman's promise is that this mindset, "
            "drilled into habit, will gain you 200-400 rating "
            "points."
        ),
        plan=[
            "Make the imbalance checklist automatic.",
            "Build plans, not move-by-move reactions.",
            "Trust the assessment over the feeling.",
        ],
    ),
]


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

def lessons_for_part(part: str) -> list[Lesson]:
    """Return every lesson whose `part` field matches `part`."""
    return [l for l in LESSONS if l.part == part]


def find_lesson(slug: str) -> Lesson | None:
    """Look up a lesson by its slug, returning None if not found."""
    for l in LESSONS:
        if l.slug == slug:
            return l
    return None


def lesson_count() -> int:
    """Total number of lessons across all parts."""
    return len(LESSONS)
