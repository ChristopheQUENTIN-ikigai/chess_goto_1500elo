%% chess_rules.pl — Prolog rules for chess reasoning
%% Used by janus_swi from Python. Covers:
%%   - Principles of chess openings
%%   - Rules for stalemate, checkmate, castling
%%   - Pawn structures analysis
%%   - Famous main openings database
%%

%% ===================================================================
%%  PIECE VALUES
%% ===================================================================
piece_value(pawn, 1).
piece_value(knight, 3).
piece_value(bishop, 3).
piece_value(rook, 5).
piece_value(queen, 9).
piece_value(king, 0).

%% ===================================================================
%%  OPENING PRINCIPLES
%% ===================================================================

%% opening_principle(Name, Description, Priority).
opening_principle(control_center,
    'Control the center squares (e4, d4, e5, d5) with pawns and pieces.', 1).
opening_principle(develop_pieces,
    'Develop knights and bishops before moving the queen or rooks.', 2).
opening_principle(king_safety,
    'Castle early to protect the king and connect the rooks.', 3).
opening_principle(avoid_moving_twice,
    'Avoid moving the same piece twice in the opening without reason.', 4).
opening_principle(dont_move_queen_early,
    'Do not bring the queen out too early; it can be chased by minor pieces.', 5).
opening_principle(pawn_structure,
    'Maintain a solid pawn structure; avoid doubled and isolated pawns.', 6).
opening_principle(connect_rooks,
    'After castling, connect rooks by developing all minor pieces.', 7).
opening_principle(control_open_files,
    'Place rooks on open and semi-open files.', 8).

%% center_square(Square) — the classical center
center_square(e4).
center_square(d4).
center_square(e5).
center_square(d5).

%% extended_center(Square) — the extended center
extended_center(c3).
extended_center(d3).
extended_center(e3).
extended_center(f3).
extended_center(c4).
extended_center(f4).
extended_center(c5).
extended_center(f5).
extended_center(c6).
extended_center(d6).
extended_center(e6).
extended_center(f6).

%% ===================================================================
%%  CHECKMATE RULES
%% ===================================================================

%% checkmate(Color) succeeds if Color is in checkmate.
%% Called from Python with board state assertions.
checkmate(Color) :-
    in_check(Color),
    \+ has_legal_move(Color).

%% ===================================================================
%%  STALEMATE RULES
%% ===================================================================

stalemate(Color) :-
    \+ in_check(Color),
    \+ has_legal_move(Color).

%% Draw conditions
is_draw :- stalemate(white).
is_draw :- stalemate(black).
is_draw :- insufficient_material.

%% insufficient_material — basic cases
insufficient_material :-
    piece_count(Total),
    Total =< 2.  % King vs King

insufficient_material :-
    piece_count(Total),
    Total == 3,
    (has_piece(white, bishop, _) ; has_piece(black, bishop, _) ;
     has_piece(white, knight, _) ; has_piece(black, knight, _)).

%% ===================================================================
%%  CASTLING RULES
%% ===================================================================

%% can_castle(Color, Side) — checks castling legality
%% Side is kingside or queenside

can_castle(Color, kingside) :-
    king_unmoved(Color),
    rook_unmoved(Color, kingside),
    \+ in_check(Color),
    castling_path_clear(Color, kingside),
    \+ castling_path_attacked(Color, kingside).

can_castle(Color, queenside) :-
    king_unmoved(Color),
    rook_unmoved(Color, queenside),
    \+ in_check(Color),
    castling_path_clear(Color, queenside),
    \+ castling_path_attacked(Color, queenside).

%% castling_advice(Color, Advice)
castling_advice(Color, 'Castle kingside for safety — shorter and more common.') :-
    can_castle(Color, kingside).
castling_advice(Color, 'Castle queenside — good for launching a kingside pawn storm.') :-
    can_castle(Color, queenside),
    \+ can_castle(Color, kingside).
castling_advice(Color, 'Cannot castle — focus on king safety by other means.') :-
    \+ can_castle(Color, kingside),
    \+ can_castle(Color, queenside).

%% ===================================================================
%%  PAWN STRUCTURE ANALYSIS
%% ===================================================================

%% doubled_pawns(Color, File) — two+ pawns on same file
doubled_pawns(Color, File) :-
    pawn_on(Color, File, R1),
    pawn_on(Color, File, R2),
    R1 \= R2.

%% isolated_pawn(Color, File) — no friendly pawns on adjacent files
isolated_pawn(Color, File) :-
    pawn_on(Color, File, _),
    adjacent_file(File, AdjLeft),
    adjacent_file_right(File, AdjRight),
    \+ pawn_on(Color, AdjLeft, _),
    \+ pawn_on(Color, AdjRight, _).

%% isolated_pawn for edge files
isolated_pawn(Color, a) :-
    pawn_on(Color, a, _),
    \+ pawn_on(Color, b, _).
isolated_pawn(Color, h) :-
    pawn_on(Color, h, _),
    \+ pawn_on(Color, g, _).

%% backward_pawn(Color, File, Rank) — pawn that cannot be supported by adjacent pawns
backward_pawn(Color, File, Rank) :-
    pawn_on(Color, File, Rank),
    adjacent_file(File, AdjLeft),
    adjacent_file_right(File, AdjRight),
    \+ (pawn_on(Color, AdjLeft, AR), behind_or_equal(Color, AR, Rank)),
    \+ (pawn_on(Color, AdjRight, AR2), behind_or_equal(Color, AR2, Rank)).

%% passed_pawn(Color, File, Rank) — no opposing pawns blocking or guarding
passed_pawn(Color, File, Rank) :-
    pawn_on(Color, File, Rank),
    opponent(Color, Opp),
    \+ blocking_pawn(Opp, File, Rank, Color),
    (adjacent_file(File, AdjL) ->
        \+ blocking_pawn(Opp, AdjL, Rank, Color) ; true),
    (adjacent_file_right(File, AdjR) ->
        \+ blocking_pawn(Opp, AdjR, Rank, Color) ; true).

%% blocking_pawn(Opp, File, Rank, FriendColor) — opp pawn ahead
blocking_pawn(Opp, File, Rank, white) :-
    pawn_on(Opp, File, OR),
    OR > Rank.
blocking_pawn(Opp, File, Rank, black) :-
    pawn_on(Opp, File, OR),
    OR < Rank.

behind_or_equal(white, AR, Rank) :- AR =< Rank.
behind_or_equal(black, AR, Rank) :- AR >= Rank.

%% pawn_chain(Color, File1, File2) — connected pawns on adjacent files
pawn_chain(Color, File1, File2) :-
    adjacent_file(File1, File2),
    pawn_on(Color, File1, R1),
    pawn_on(Color, File2, R2),
    abs(R1 - R2) =:= 1.

%% pawn_island_count(Color, Count) — number of pawn islands
%% (groups of connected pawns separated by empty files)
%% Computed in Python for efficiency.

%% pawn_structure_advice(Color, Advice)
pawn_structure_advice(Color, 'Doubled pawns detected — consider exchanging to fix structure.') :-
    doubled_pawns(Color, _).
pawn_structure_advice(Color, 'Isolated pawn weakness — protect or exchange it.') :-
    isolated_pawn(Color, _).
pawn_structure_advice(Color, 'Passed pawn advantage — push it forward!') :-
    passed_pawn(Color, _, _).
pawn_structure_advice(Color, 'Good pawn chain — maintain the chain and attack the base.') :-
    pawn_chain(Color, _, _).
pawn_structure_advice(Color, 'Solid pawn structure.') :-
    \+ doubled_pawns(Color, _),
    \+ isolated_pawn(Color, _).

%% ===================================================================
%%  FILE ADJACENCY
%% ===================================================================
adjacent_file(a, b).
adjacent_file(b, a). adjacent_file(b, c).
adjacent_file(c, b). adjacent_file(c, d).
adjacent_file(d, c). adjacent_file(d, e).
adjacent_file(e, d). adjacent_file(e, f).
adjacent_file(f, e). adjacent_file(f, g).
adjacent_file(g, f). adjacent_file(g, h).
adjacent_file(h, g).

adjacent_file_right(a, b).
adjacent_file_right(b, c).
adjacent_file_right(c, d).
adjacent_file_right(d, e).
adjacent_file_right(e, f).
adjacent_file_right(f, g).
adjacent_file_right(g, h).

%% ===================================================================
%%  OPPONENT
%% ===================================================================
opponent(white, black).
opponent(black, white).

%% ===================================================================
%%  FAMOUS OPENINGS DATABASE
%% ===================================================================

%% opening(Name, ECO, MovesSAN, Themes, Plan).
opening('Italian Game', 'C50',
    [e4, e5, 'Nf3', 'Nc6', 'Bc4'],
    [center_control, development],
    'Develop quickly, control center, prepare kingside castling.').

opening('Giuoco Piano', 'C53',
    [e4, e5, 'Nf3', 'Nc6', 'Bc4', 'Bc5'],
    [center_control, classical],
    'Both develop bishops. White aims for d4 break.').

opening('Evans Gambit', 'C51',
    [e4, e5, 'Nf3', 'Nc6', 'Bc4', 'Bc5', b4],
    [gambit, initiative],
    'White sacrifices b-pawn for rapid development and initiative.').

opening('Ruy Lopez', 'C60',
    [e4, e5, 'Nf3', 'Nc6', 'Bb5'],
    [strategic, pressure],
    'Long-term pressure on e5 pawn. Prepare d4 and slow build-up.').

opening('Ruy Lopez Morphy Defense', 'C65',
    [e4, e5, 'Nf3', 'Nc6', 'Bb5', a6],
    [strategic, bishop_pair],
    'Black challenges the bishop. Rich middlegame possibilities.').

opening('Scotch Game', 'C45',
    [e4, e5, 'Nf3', 'Nc6', d4],
    [open_center, tactical],
    'White opens the center immediately for active piece play.').

opening('Kings Gambit', 'C30',
    [e4, e5, f4],
    [gambit, kingside_attack],
    'Sacrifice f-pawn for center and kingside initiative. Sharp play.').

opening('Petrov Defense', 'C42',
    [e4, e5, 'Nf3', 'Nf6'],
    [symmetrical, solid],
    'Black mirrors. Leads to solid, equal positions.').

opening('Sicilian Defense', 'B20',
    [e4, c5],
    [asymmetric, complex],
    'Fight for d4 asymmetrically. Rich, complex middlegames.').

opening('Sicilian Najdorf', 'B90',
    [e4, c5, 'Nf3', d6, d4, cxd4, 'Nxd4', 'Nf6', 'Nc3', a6],
    [complex, queenside_expansion],
    'Prepares e5 or b5. Enormous theory. Bobby Fischers favorite.').

opening('Sicilian Dragon', 'B70',
    [e4, c5, 'Nf3', d6, d4, cxd4, 'Nxd4', 'Nf6', 'Nc3', g6],
    [fianchetto, sharp],
    'Fianchetto on g7. White attacks kingside, Black counterattacks queenside.').

opening('French Defense', 'C00',
    [e4, e6],
    [solid, pawn_chain],
    'Solid pawn chain. Black undermines with d5 and c5.').

opening('French Advance', 'C02',
    [e4, e6, d4, d5, e5],
    [pawn_chain, strategic],
    'White gains space. Black targets the d4-e5 pawn chain.').

opening('Caro-Kann Defense', 'B10',
    [e4, c6],
    [solid, reliable],
    'Prepares d5 while keeping light-squared bishop active.').

opening('Queens Gambit', 'D06',
    [d4, d5, c4],
    [center_control, classical],
    'Challenge d5 pawn. Classical center control strategy.').

opening('Queens Gambit Declined', 'D30',
    [d4, d5, c4, e6],
    [solid, strategic],
    'Solid defense of d5. Strategic, positional middlegames.').

opening('Queens Gambit Accepted', 'D20',
    [d4, d5, c4, dxc4],
    [gambit_accepted, development],
    'Black takes pawn. White gains center advantage.').

opening('Slav Defense', 'D10',
    [d4, d5, c4, c6],
    [solid, light_bishop],
    'Supports d5 with c6. Light-squared bishop stays free.').

opening('London System', 'D00',
    [d4, d5, 'Bf4'],
    [system, solid],
    'Bishop to f4 early. Solid, low-theory system.').

opening('Kings Indian Defense', 'E60',
    [d4, 'Nf6', c4, g6],
    [fianchetto, kingside_attack],
    'Fianchetto bishop. Prepare e5 counter-attack.').

opening('Kings Indian Classical', 'E90',
    [d4, 'Nf6', c4, g6, 'Nc3', 'Bg7', e4, d6, 'Nf3'],
    [fianchetto, pawn_storm],
    'Black plays e5, White expands queenside. A race of attacks.').

opening('Nimzo-Indian Defense', 'E20',
    [d4, 'Nf6', c4, e6, 'Nc3', 'Bb4'],
    [pin, strategic],
    'Pin the knight on c3. Rich strategic play with doubled pawns.').

opening('Grunfeld Defense', 'D70',
    [d4, 'Nf6', c4, g6, 'Nc3', d5],
    [counter_attack, dynamic],
    'Challenge center with d5. Very dynamic, tactical defense.').

opening('English Opening', 'A10',
    [c4],
    [flank, flexible],
    'Control d5 from the flank. Very flexible setup.').

opening('Reti Opening', 'A04',
    ['Nf3', d5, c4],
    [hypermodern, flank],
    'Hypermodern approach: undermine d5 from the flanks.').

opening('Dutch Defense', 'A80',
    [d4, f5],
    [aggressive, kingside],
    'Grab kingside space immediately. Unbalanced positions.').

opening('Catalan Opening', 'E00',
    [d4, 'Nf6', c4, e6, g3],
    [fianchetto, positional],
    'Fianchetto kingside bishop. Long-term positional pressure.').

opening('Scandinavian Defense', 'B01',
    [e4, d5],
    [early_queen, simple],
    'Challenges e4 immediately. Simple but solid.').

opening('Pirc Defense', 'B07',
    [e4, d6, d4, 'Nf6', 'Nc3', g6],
    [hypermodern, fianchetto],
    'Let White build center, then attack it. Flexible.').

opening('Alekhine Defense', 'B02',
    [e4, 'Nf6'],
    [hypermodern, provocative],
    'Provokes pawns forward, then undermines the center.').

opening('Vienna Game', 'C25',
    [e4, e5, 'Nc3'],
    [flexible, delayed_f4],
    'Flexible setup. May transpose to Vienna Gambit with f4.').

%% ===================================================================
%%  OPENING CLASSIFICATION
%% ===================================================================

%% classify_opening(MovesUCI, Name, ECO, Plan)
%% Called from Python with the UCI move list.
%% We match by prefix — longest match wins.
%% This is done primarily in Python; Prolog provides the knowledge base.

%% opening_advice(MoveNumber, Color, Advice)
opening_advice(MoveNum, _, 'Focus on controlling the center with pawns (e4/d4 or e5/d5).') :-
    MoveNum =< 3.
opening_advice(MoveNum, _, 'Develop knights and bishops toward the center.') :-
    MoveNum > 3, MoveNum =< 6.
opening_advice(MoveNum, Color, Advice) :-
    MoveNum > 6, MoveNum =< 10,
    castling_advice(Color, Advice).
opening_advice(MoveNum, _, 'Transition to middlegame: connect rooks and find a plan.') :-
    MoveNum > 10.

%% ===================================================================
%%  TACTICAL PATTERNS (detected from asserted board facts)
%% ===================================================================

%% hanging_piece(Color, Square, PieceType) — undefended piece under attack
hanging_piece(Color, Square, PieceType) :-
    piece_at(Square, Color, PieceType),
    PieceType \= king,
    opponent(Color, Opp),
    attacks(Opp, Square),
    \+ defends(Color, Square).

%% fork_target(AttackerSq, Target1, Target2) — piece attacking 2+ valuable pieces
fork_target(AttackerSq, T1, T2) :-
    attacks_from(AttackerSq, T1),
    attacks_from(AttackerSq, T2),
    T1 \= T2,
    piece_at(T1, _, PT1), piece_value(PT1, V1), V1 >= 3,
    piece_at(T2, _, PT2), piece_value(PT2, V2), V2 >= 3.

%% ===================================================================
%%  ENDGAME PRINCIPLES
%% ===================================================================
endgame_principle(king_activity,
    'In the endgame, activate your king — it becomes a strong piece.').
endgame_principle(passed_pawn_push,
    'Push passed pawns in the endgame — they are very dangerous.').
endgame_principle(rook_behind_passer,
    'Place rooks behind passed pawns, whether yours or your opponents.').
endgame_principle(opposition,
    'King opposition is key in king-and-pawn endgames.').
endgame_principle(zugzwang,
    'In endgames, sometimes the obligation to move is a disadvantage (zugzwang).').

%% ===================================================================
%%  DYNAMIC FACTS (asserted from Python at runtime)
%% ===================================================================
%% These are asserted/retracted by the Python reasoner:
%%   piece_at(Square, Color, PieceType)
%%   pawn_on(Color, File, Rank)
%%   in_check(Color)
%%   has_legal_move(Color)
%%   attacks(Color, Square)
%%   defends(Color, Square)
%%   attacks_from(FromSquare, ToSquare)
%%   king_unmoved(Color)
%%   rook_unmoved(Color, Side)
%%   castling_path_clear(Color, Side)
%%   castling_path_attacked(Color, Side)
%%   has_piece(Color, PieceType, Square)
%%   piece_count(N)

:- discontiguous piece_at/3.
:- discontiguous pawn_on/3.
:- discontiguous in_check/1.
:- discontiguous has_legal_move/1.
:- discontiguous attacks/2.
:- discontiguous defends/2.
:- discontiguous attacks_from/2.
:- discontiguous king_unmoved/1.
:- discontiguous rook_unmoved/2.
:- discontiguous castling_path_clear/2.
:- discontiguous castling_path_attacked/2.
:- discontiguous has_piece/3.
:- discontiguous piece_count/1.

:- dynamic piece_at/3.
:- dynamic pawn_on/3.
:- dynamic in_check/1.
:- dynamic has_legal_move/1.
:- dynamic attacks/2.
:- dynamic defends/2.
:- dynamic attacks_from/2.
:- dynamic king_unmoved/1.
:- dynamic rook_unmoved/2.
:- dynamic castling_path_clear/2.
:- dynamic castling_path_attacked/2.
:- dynamic has_piece/3.
:- dynamic piece_count/1.
