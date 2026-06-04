"""
headless_trainer.py — Headless AI vs AI training machine.
Different AI profiles fight each other to build chess repertoires.

Features:
  - Round-robin or matchup tournaments between AI profiles
  - Game results saved in PGN format
  - Opening repertoire extraction from winning games
  - Statistics tracking (wins, draws, losses, ELO estimates)
  - Repertoire export as Prolog facts for the reasoning engine
  - Multi-threaded parallel games

Usage:
    python headless_trainer.py                     # Default tournament
    python headless_trainer.py --games 100         # 100 games per matchup
    python headless_trainer.py --profiles master attacker fortress
    python headless_trainer.py --export-prolog     # Export repertoire to Prolog
    python headless_trainer.py --export-pgn        # Export all games to PGN
"""
import chess
import chess.pgn
import os
import sys
import json
import time
import datetime
import argparse
import threading
from collections import defaultdict
from typing import Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from ai_profiles import ProfiledAI, PROFILES, AIProfile


# ── Data Structures ──────────────────────────────────────────────────

@dataclass
class GameRecord:
    """Record of a single game."""
    white_profile: str
    black_profile: str
    result: str           # "1-0", "0-1", "1/2-1/2"
    moves_uci: list[str]
    moves_san: list[str]
    opening_name: str = ""
    opening_eco: str = ""
    ply_count: int = 0
    termination: str = ""  # checkmate, stalemate, 50-move, repetition, resign
    duration_ms: int = 0
    white_eval_final: int = 0
    black_eval_final: int = 0


@dataclass
class MatchupStats:
    """Stats for one AI vs another."""
    white_profile: str
    black_profile: str
    white_wins: int = 0
    black_wins: int = 0
    draws: int = 0
    total_games: int = 0
    avg_game_length: float = 0.0
    total_ply: int = 0

    @property
    def white_score(self) -> float:
        if self.total_games == 0:
            return 0.0
        return (self.white_wins + self.draws * 0.5) / self.total_games

    @property
    def black_score(self) -> float:
        return 1.0 - self.white_score


@dataclass
class RepertoireEntry:
    """A move recommendation in a specific position."""
    fen_key: str        # Simplified FEN (position only, no clocks)
    move_uci: str
    move_san: str
    score: float = 0.0  # Win rate when this move was played
    games: int = 0      # How many games used this move
    avg_eval: int = 0   # Average engine eval after this move


class RepertoireBook:
    """Opening repertoire built from game results."""

    def __init__(self):
        # Key: simplified FEN, Value: dict of move_uci -> RepertoireEntry
        self.positions: dict[str, dict[str, RepertoireEntry]] = {}

    @staticmethod
    def _simplify_fen(fen: str) -> str:
        """Remove move counters from FEN for position-only key."""
        parts = fen.split()
        return " ".join(parts[:4])  # pieces, turn, castling, en passant

    def add_game(self, moves_uci: list[str], result: str,
                 for_color: bool = chess.WHITE):
        """Add a game's opening moves to the repertoire."""
        board = chess.Board()
        # Score from the perspective of for_color
        if result == "1-0":
            game_score = 1.0 if for_color == chess.WHITE else 0.0
        elif result == "0-1":
            game_score = 0.0 if for_color == chess.WHITE else 1.0
        else:
            game_score = 0.5

        # Only record first 20 moves (40 ply) as opening repertoire
        max_ply = min(len(moves_uci), 40)
        for i in range(max_ply):
            if board.turn != for_color:
                try:
                    board.push(chess.Move.from_uci(moves_uci[i]))
                except:
                    break
                continue

            fen_key = self._simplify_fen(board.fen())
            move_uci = moves_uci[i]

            try:
                move = chess.Move.from_uci(move_uci)
                move_san = board.san(move)
            except:
                break

            if fen_key not in self.positions:
                self.positions[fen_key] = {}

            pos = self.positions[fen_key]
            if move_uci not in pos:
                pos[move_uci] = RepertoireEntry(
                    fen_key=fen_key, move_uci=move_uci, move_san=move_san)

            entry = pos[move_uci]
            entry.games += 1
            # Running average of score
            entry.score = ((entry.score * (entry.games - 1) + game_score)
                           / entry.games)

            board.push(move)

    def get_best_move(self, fen: str, min_games: int = 2) -> Optional[str]:
        """Get the best repertoire move for a position."""
        fen_key = self._simplify_fen(fen)
        if fen_key not in self.positions:
            return None

        candidates = [e for e in self.positions[fen_key].values()
                      if e.games >= min_games]
        if not candidates:
            return None

        # Sort by score (win rate), then by number of games
        candidates.sort(key=lambda e: (e.score, e.games), reverse=True)
        return candidates[0].move_uci

    def get_position_stats(self, fen: str) -> list[dict]:
        """Get all moves and stats for a position."""
        fen_key = self._simplify_fen(fen)
        if fen_key not in self.positions:
            return []

        stats = []
        for entry in sorted(self.positions[fen_key].values(),
                            key=lambda e: (e.score, e.games), reverse=True):
            stats.append({
                "move_uci": entry.move_uci,
                "move_san": entry.move_san,
                "score": round(entry.score, 3),
                "games": entry.games,
            })
        return stats

    def export_to_prolog(self, filepath: str, min_games: int = 2):
        """Export repertoire as Prolog facts for the reasoning engine."""
        with open(filepath, "w") as f:
            f.write("%% Auto-generated chess repertoire from AI training\n")
            f.write("%% repertoire_move(FEN, MoveUCI, MoveSAN, WinRate, Games).\n")
            f.write(":- discontiguous repertoire_move/5.\n")
            f.write(":- dynamic repertoire_move/5.\n\n")

            count = 0
            for fen_key, moves in sorted(self.positions.items()):
                for entry in moves.values():
                    if entry.games < min_games:
                        continue
                    # Escape single quotes in FEN
                    safe_fen = fen_key.replace("'", "\\'")
                    f.write(
                        f"repertoire_move('{safe_fen}', "
                        f"'{entry.move_uci}', '{entry.move_san}', "
                        f"{entry.score:.3f}, {entry.games}).\n")
                    count += 1

            f.write(f"\n%% Total entries: {count}\n")
        print(f"[Repertoire] Exported {count} entries to {filepath}")

    def export_to_json(self, filepath: str, min_games: int = 2):
        """Export repertoire as JSON."""
        data = {}
        for fen_key, moves in self.positions.items():
            entries = []
            for entry in moves.values():
                if entry.games < min_games:
                    continue
                entries.append({
                    "move_uci": entry.move_uci,
                    "move_san": entry.move_san,
                    "score": round(entry.score, 3),
                    "games": entry.games,
                })
            if entries:
                data[fen_key] = sorted(entries, key=lambda e: -e["score"])

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[Repertoire] Exported {len(data)} positions to {filepath}")

    @property
    def total_positions(self) -> int:
        return len(self.positions)

    @property
    def total_entries(self) -> int:
        return sum(len(moves) for moves in self.positions.values())


# ── Single Game Runner ───────────────────────────────────────────────

def play_single_game(white_profile: str, black_profile: str,
                     max_moves: int = 200, verbose: bool = False) -> GameRecord:
    """Play one complete game between two AI profiles. No GUI needed."""
    white_ai = ProfiledAI(white_profile)
    black_ai = ProfiledAI(black_profile)
    board = chess.Board()
    start_time = time.time()

    moves_uci = []
    moves_san = []

    for ply in range(max_moves * 2):
        if board.is_game_over():
            break

        ai = white_ai if board.turn == chess.WHITE else black_ai

        move = ai.get_move(board)
        if move is None or move not in board.legal_moves:
            # No legal move found — shouldn't happen, but safety
            legal = list(board.legal_moves)
            if legal:
                move = legal[0]
            else:
                break

        san = board.san(move)
        moves_san.append(san)
        moves_uci.append(move.uci())
        board.push(move)

        if verbose and ply < 20:
            turn_num = (ply // 2) + 1
            side = "W" if ply % 2 == 0 else "B"
            print(f"  {turn_num}.{side}: {san}", end="  ")
            if ply % 2 == 1:
                print()

    # Determine result
    if board.is_checkmate():
        result = "0-1" if board.turn == chess.WHITE else "1-0"
        termination = "checkmate"
    elif board.is_stalemate():
        result = "1/2-1/2"
        termination = "stalemate"
    elif board.is_insufficient_material():
        result = "1/2-1/2"
        termination = "insufficient_material"
    elif board.can_claim_fifty_moves():
        result = "1/2-1/2"
        termination = "fifty_moves"
    elif board.is_repetition(3):
        result = "1/2-1/2"
        termination = "repetition"
    elif len(moves_uci) >= max_moves * 2:
        result = "1/2-1/2"
        termination = "max_moves"
    else:
        result = "1/2-1/2"
        termination = "unknown"

    elapsed = int((time.time() - start_time) * 1000)

    return GameRecord(
        white_profile=white_profile,
        black_profile=black_profile,
        result=result,
        moves_uci=moves_uci,
        moves_san=moves_san,
        ply_count=len(moves_uci),
        termination=termination,
        duration_ms=elapsed,
    )


# ── Tournament Runner ────────────────────────────────────────────────

class Tournament:
    """Run AI vs AI tournaments and build repertoires."""

    def __init__(self, profiles: list[str] = None,
                 games_per_matchup: int = 10,
                 max_moves: int = 150,
                 num_threads: int = 1,
                 output_dir: str = "training_output"):
        self.profiles = profiles or list(PROFILES.keys())
        self.games_per_matchup = games_per_matchup
        self.max_moves = max_moves
        self.num_threads = num_threads
        self.output_dir = output_dir

        self.game_records: list[GameRecord] = []
        self.matchup_stats: dict[tuple[str, str], MatchupStats] = {}
        self.repertoires: dict[str, RepertoireBook] = {}

        os.makedirs(output_dir, exist_ok=True)

        # Initialize repertoires for each profile
        for p in self.profiles:
            self.repertoires[p] = RepertoireBook()

    def run_round_robin(self, verbose: bool = True):
        """Run a round-robin tournament: every profile plays every other."""
        matchups = []
        for i, wp in enumerate(self.profiles):
            for j, bp in enumerate(self.profiles):
                if i == j:
                    continue
                matchups.append((wp, bp))

        total_games = len(matchups) * self.games_per_matchup
        print(f"\n{'='*60}")
        print(f"  CHESS AI TRAINING TOURNAMENT")
        print(f"  Profiles: {', '.join(self.profiles)}")
        print(f"  Games per matchup: {self.games_per_matchup}")
        print(f"  Total games: {total_games}")
        print(f"  Threads: {self.num_threads}")
        print(f"{'='*60}\n")

        game_num = 0
        start = time.time()

        for wp, bp in matchups:
            key = (wp, bp)
            self.matchup_stats[key] = MatchupStats(wp, bp)

            if verbose:
                wp_name = PROFILES[wp].name
                bp_name = PROFILES[bp].name
                print(f"\n--- {wp_name} (W) vs {bp_name} (B) ---")

            if self.num_threads > 1:
                self._run_matchup_parallel(wp, bp, verbose)
            else:
                self._run_matchup_serial(wp, bp, verbose)

            game_num += self.games_per_matchup
            elapsed = time.time() - start
            rate = game_num / elapsed if elapsed > 0 else 0
            if verbose:
                stats = self.matchup_stats[key]
                print(f"  Result: W:{stats.white_wins} B:{stats.black_wins} "
                      f"D:{stats.draws}  "
                      f"({game_num}/{total_games} games, {rate:.1f} g/s)")

        total_time = time.time() - start
        print(f"\n{'='*60}")
        print(f"  Tournament complete: {total_games} games in {total_time:.1f}s")
        print(f"  ({total_games / total_time:.1f} games/sec)")
        print(f"{'='*60}")

    def _run_matchup_serial(self, wp: str, bp: str, verbose: bool):
        """Run games sequentially."""
        for g in range(self.games_per_matchup):
            record = play_single_game(wp, bp, self.max_moves,
                                      verbose=(verbose and g == 0))
            self._record_game(record)
            if verbose:
                print(f"  Game {g + 1}: {record.result} "
                      f"({record.ply_count} ply, {record.termination}, "
                      f"{record.duration_ms}ms)")

    def _run_matchup_parallel(self, wp: str, bp: str, verbose: bool):
        """Run games in parallel threads."""
        with ThreadPoolExecutor(max_workers=self.num_threads) as ex:
            futures = [
                ex.submit(play_single_game, wp, bp, self.max_moves, False)
                for _ in range(self.games_per_matchup)
            ]
            for i, future in enumerate(as_completed(futures)):
                record = future.result()
                self._record_game(record)
                if verbose:
                    print(f"  Game {i + 1}: {record.result} "
                          f"({record.ply_count} ply, {record.termination})")

    def _record_game(self, record: GameRecord):
        """Record a completed game's results."""
        self.game_records.append(record)

        # Update matchup stats
        key = (record.white_profile, record.black_profile)
        stats = self.matchup_stats.setdefault(
            key, MatchupStats(record.white_profile, record.black_profile))
        stats.total_games += 1
        stats.total_ply += record.ply_count
        stats.avg_game_length = stats.total_ply / stats.total_games

        if record.result == "1-0":
            stats.white_wins += 1
        elif record.result == "0-1":
            stats.black_wins += 1
        else:
            stats.draws += 1

        # Update repertoires
        if record.white_profile in self.repertoires:
            self.repertoires[record.white_profile].add_game(
                record.moves_uci, record.result, chess.WHITE)
        if record.black_profile in self.repertoires:
            self.repertoires[record.black_profile].add_game(
                record.moves_uci, record.result, chess.BLACK)

    # ── Export Methods ────────────────────────────────────────────────

    def export_pgn(self, filepath: str = None):
        """Export all games to PGN file."""
        if filepath is None:
            filepath = os.path.join(self.output_dir, "tournament_games.pgn")

        with open(filepath, "w") as f:
            for record in self.game_records:
                game = chess.pgn.Game()
                game.headers["Event"] = "AI Training Tournament"
                game.headers["Date"] = datetime.date.today().isoformat()
                game.headers["White"] = PROFILES[record.white_profile].name
                game.headers["Black"] = PROFILES[record.black_profile].name
                game.headers["Result"] = record.result
                game.headers["WhiteElo"] = str(
                    PROFILES[record.white_profile].elo_estimate)
                game.headers["BlackElo"] = str(
                    PROFILES[record.black_profile].elo_estimate)
                game.headers["Termination"] = record.termination
                game.headers["PlyCount"] = str(record.ply_count)

                # Build move tree
                node = game
                board = chess.Board()
                for uci in record.moves_uci:
                    try:
                        move = chess.Move.from_uci(uci)
                        node = node.add_variation(move)
                        board.push(move)
                    except:
                        break

                f.write(str(game) + "\n\n")

        print(f"[PGN] Exported {len(self.game_records)} games to {filepath}")

    def export_repertoires(self, min_games: int = 2):
        """Export all repertoires."""
        for profile_name, book in self.repertoires.items():
            if book.total_positions == 0:
                continue

            # JSON
            json_path = os.path.join(
                self.output_dir, f"repertoire_{profile_name}.json")
            book.export_to_json(json_path, min_games)

            # Prolog
            pl_path = os.path.join(
                self.output_dir, f"repertoire_{profile_name}.pl")
            book.export_to_prolog(pl_path, min_games)

    def export_stats(self, filepath: str = None):
        """Export tournament statistics."""
        if filepath is None:
            filepath = os.path.join(self.output_dir, "tournament_stats.json")

        stats = {
            "tournament": {
                "profiles": self.profiles,
                "games_per_matchup": self.games_per_matchup,
                "total_games": len(self.game_records),
                "date": datetime.date.today().isoformat(),
            },
            "matchups": [],
            "profile_summary": {},
        }

        # Per-matchup stats
        for key, ms in sorted(self.matchup_stats.items()):
            stats["matchups"].append({
                "white": ms.white_profile,
                "black": ms.black_profile,
                "white_wins": ms.white_wins,
                "black_wins": ms.black_wins,
                "draws": ms.draws,
                "total": ms.total_games,
                "white_score": round(ms.white_score, 3),
                "avg_length": round(ms.avg_game_length, 1),
            })

        # Per-profile aggregate
        profile_totals = defaultdict(lambda: {"wins": 0, "losses": 0,
                                               "draws": 0, "games": 0})
        for record in self.game_records:
            w = profile_totals[record.white_profile]
            b = profile_totals[record.black_profile]
            w["games"] += 1
            b["games"] += 1
            if record.result == "1-0":
                w["wins"] += 1
                b["losses"] += 1
            elif record.result == "0-1":
                w["losses"] += 1
                b["wins"] += 1
            else:
                w["draws"] += 1
                b["draws"] += 1

        for pname, pt in sorted(profile_totals.items()):
            total = pt["games"]
            score = (pt["wins"] + pt["draws"] * 0.5) / total if total else 0
            stats["profile_summary"][pname] = {
                "name": PROFILES[pname].name,
                "elo_estimate": PROFILES[pname].elo_estimate,
                "wins": pt["wins"],
                "losses": pt["losses"],
                "draws": pt["draws"],
                "total_games": total,
                "overall_score": round(score, 3),
                "repertoire_positions": self.repertoires.get(
                    pname, RepertoireBook()).total_positions,
            }

        with open(filepath, "w") as f:
            json.dump(stats, f, indent=2)
        print(f"[Stats] Exported to {filepath}")

    def print_summary(self):
        """Print a human-readable summary."""
        print(f"\n{'='*60}")
        print("  TOURNAMENT RESULTS SUMMARY")
        print(f"{'='*60}")

        # Profile rankings
        profile_scores = defaultdict(lambda: {"score": 0.0, "games": 0})
        for record in self.game_records:
            for pname, color in [(record.white_profile, chess.WHITE),
                                  (record.black_profile, chess.BLACK)]:
                ps = profile_scores[pname]
                ps["games"] += 1
                if record.result == "1-0" and color == chess.WHITE:
                    ps["score"] += 1.0
                elif record.result == "0-1" and color == chess.BLACK:
                    ps["score"] += 1.0
                elif record.result == "1/2-1/2":
                    ps["score"] += 0.5

        ranked = sorted(profile_scores.items(),
                        key=lambda x: x[1]["score"] / max(x[1]["games"], 1),
                        reverse=True)

        print(f"\n  {'Rank':<6}{'Profile':<22}{'Score':<10}{'Games':<8}{'Win%':<8}")
        print(f"  {'-'*54}")
        for i, (pname, ps) in enumerate(ranked, 1):
            pct = (ps["score"] / ps["games"] * 100) if ps["games"] else 0
            print(f"  {i:<6}{PROFILES[pname].name:<22}"
                  f"{ps['score']:<10.1f}{ps['games']:<8}{pct:<8.1f}")

        # Repertoire sizes
        print(f"\n  Repertoire Sizes:")
        for pname, book in sorted(self.repertoires.items()):
            print(f"    {PROFILES[pname].name}: "
                  f"{book.total_positions} positions, "
                  f"{book.total_entries} move entries")


# ── CLI Entry Point ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Chess AI Training Machine — AI vs AI tournaments")
    parser.add_argument("--profiles", nargs="+",
                        default=["beginner", "casual", "intermediate",
                                 "advanced", "attacker", "fortress"],
                        help="AI profiles to include")
    parser.add_argument("--games", type=int, default=4,
                        help="Games per matchup (default: 4)")
    parser.add_argument("--max-moves", type=int, default=150,
                        help="Max moves per game (default: 150)")
    parser.add_argument("--threads", type=int, default=1,
                        help="Parallel game threads (default: 1)")
    parser.add_argument("--output", type=str, default="training_output",
                        help="Output directory")
    parser.add_argument("--export-pgn", action="store_true",
                        help="Export games to PGN")
    parser.add_argument("--export-prolog", action="store_true",
                        help="Export repertoires as Prolog facts")
    parser.add_argument("--verbose", action="store_true", default=True,
                        help="Verbose output")
    parser.add_argument("--quick", action="store_true",
                        help="Quick test: 2 games, 3 profiles")

    args = parser.parse_args()

    if args.quick:
        args.profiles = ["beginner", "casual", "intermediate"]
        args.games = 2

    # Validate profiles
    valid = [p for p in args.profiles if p in PROFILES]
    if len(valid) < 2:
        print(f"Need at least 2 valid profiles. Available: {list(PROFILES.keys())}")
        sys.exit(1)

    # Run tournament
    tournament = Tournament(
        profiles=valid,
        games_per_matchup=args.games,
        max_moves=args.max_moves,
        num_threads=args.threads,
        output_dir=args.output,
    )

    tournament.run_round_robin(verbose=args.verbose)
    tournament.print_summary()

    # Exports
    tournament.export_stats()

    if args.export_pgn or True:  # Always export PGN
        tournament.export_pgn()

    if args.export_prolog or True:  # Always export Prolog repertoires
        tournament.export_repertoires(min_games=1)

    print(f"\nAll output saved to: {args.output}/")


if __name__ == "__main__":
    main()
