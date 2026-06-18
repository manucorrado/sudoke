from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import requests


BASE_RAW_URL = "https://raw.githubusercontent.com/grantm/sudoku-exchange-puzzle-bank/master"

FILES_BY_SOURCE_BUCKET = {
    "easy": "easy.txt",
    "medium": "medium.txt",
    "hard": "hard.txt",
    "diabolical": "diabolical.txt",
}

DIFFICULTY_MAP = {
    "easy": "easy",
    "medium": "medium",
    "hard": "hard",
    "diabolical": "expert",
}

ALL_DIGITS_MASK = sum(1 << n for n in range(1, 10))

def popcount(value: int) -> int:
    return bin(value).count("1")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def download_file(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        print(f"Already downloaded: {output_path}")
        return

    print(f"Downloading: {url}")
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    output_path.write_bytes(response.content)


def download_sudoku_exchange(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)

    filenames = [
        "README.md",
        "LICENSE.txt",
        *FILES_BY_SOURCE_BUCKET.values(),
    ]

    for filename in filenames:
        download_file(
            url=f"{BASE_RAW_URL}/{filename}",
            output_path=raw_dir / filename,
        )

    manifest_lines = []

    for filename in filenames:
        path = raw_dir / filename
        manifest_lines.append(f"{sha256_file(path)}  {filename}")

    (raw_dir / "manifest.sha256").write_text("\n".join(manifest_lines) + "\n")


def normalize_puzzle(raw: str) -> str:
    puzzle = raw.strip().replace(".", "0")

    if len(puzzle) != 81:
        raise ValueError(f"Puzzle must be 81 chars, got {len(puzzle)}")

    if any(ch not in "0123456789" for ch in puzzle):
        raise ValueError("Puzzle contains invalid characters")

    return puzzle


def clue_count(puzzle: str) -> int:
    return sum(1 for ch in puzzle if ch != "0")


def box_index(row: int, col: int) -> int:
    return (row // 3) * 3 + (col // 3)


def solve_unique(puzzle: str, solution_limit: int = 2) -> tuple[bool, str | None, int, str | None]:
    """
    Returns:
      is_unique_valid, solution, solution_count, rejection_reason

    Counts up to 2 solutions.
    0 solutions -> invalid
    1 solution  -> valid unique puzzle
    2 solutions -> valid grid but non-unique, reject for product use
    """
    try:
        puzzle = normalize_puzzle(puzzle)
    except ValueError as exc:
        return False, None, 0, str(exc)

    grid = [int(ch) for ch in puzzle]

    rows = [0] * 9
    cols = [0] * 9
    boxes = [0] * 9

    for idx, value in enumerate(grid):
        if value == 0:
            continue

        row = idx // 9
        col = idx % 9
        box = box_index(row, col)
        bit = 1 << value

        if rows[row] & bit or cols[col] & bit or boxes[box] & bit:
            return False, None, 0, "duplicate given conflict"

        rows[row] |= bit
        cols[col] |= bit
        boxes[box] |= bit

    solutions: list[str] = []

    def find_best_empty_cell() -> tuple[int, int] | None:
        best_idx = -1
        best_mask = 0
        best_count = 10

        for idx, value in enumerate(grid):
            if value != 0:
                continue

            row = idx // 9
            col = idx % 9
            box = box_index(row, col)

            used = rows[row] | cols[col] | boxes[box]
            mask = ALL_DIGITS_MASK & ~used
            count = popcount(mask)

            if count == 0:
                return idx, 0

            if count < best_count:
                best_idx = idx
                best_mask = mask
                best_count = count

                if count == 1:
                    break

        if best_idx == -1:
            return None

        return best_idx, best_mask

    def dfs() -> None:
        if len(solutions) >= solution_limit:
            return

        found = find_best_empty_cell()

        if found is None:
            solutions.append("".join(str(n) for n in grid))
            return

        idx, mask = found

        if mask == 0:
            return

        row = idx // 9
        col = idx % 9
        box = box_index(row, col)

        while mask:
            bit = mask & -mask
            value = bit.bit_length() - 1
            mask -= bit

            grid[idx] = value
            rows[row] |= bit
            cols[col] |= bit
            boxes[box] |= bit

            dfs()

            grid[idx] = 0
            rows[row] &= ~bit
            cols[col] &= ~bit
            boxes[box] &= ~bit

            if len(solutions) >= solution_limit:
                return

    dfs()

    if len(solutions) == 0:
        return False, None, 0, "no solution"

    if len(solutions) > 1:
        return False, solutions[0], len(solutions), "non-unique solution"

    return True, solutions[0], 1, None


def parse_source_file(path: Path, source_bucket: str):
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            stripped = line.strip()

            if not stripped:
                continue

            parts = stripped.split()

            if len(parts) != 3:
                raise ValueError(f"Bad row at {path}:{line_number}: {stripped}")

            source_hash, puzzle_digits, source_rating = parts

            yield {
                "source_file": path.name,
                "source_line": line_number,
                "source_hash": source_hash,
                "source_bucket": source_bucket,
                "source_rating": float(source_rating),
                "puzzle": normalize_puzzle(puzzle_digits),
            }


def import_bank(
    raw_dir: Path,
    output_path: Path,
    limit_per_bucket: int,
) -> None:
    download_sudoku_exchange(raw_dir)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    seen_hashes: set[str] = set()

    total_seen = 0
    total_written = 0
    total_duplicates = 0
    total_rejected = 0

    started_at = time.time()

    with output_path.open("w", encoding="utf-8") as out:
        for source_bucket, filename in FILES_BY_SOURCE_BUCKET.items():
            path = raw_dir / filename
            written_for_bucket = 0

            print(f"\nProcessing {filename} -> {DIFFICULTY_MAP[source_bucket]}")

            for row in parse_source_file(path, source_bucket):
                if limit_per_bucket > 0 and written_for_bucket >= limit_per_bucket:
                    break

                total_seen += 1

                puzzle = row["puzzle"]
                puzzle_hash = sha256_text(puzzle)

                if puzzle_hash in seen_hashes:
                    total_duplicates += 1
                    continue

                is_valid, solution, solution_count, rejection_reason = solve_unique(puzzle)

                if not is_valid or solution is None:
                    total_rejected += 1
                    continue

                seen_hashes.add(puzzle_hash)

                difficulty_band = DIFFICULTY_MAP[source_bucket]
                ranked_candidate = difficulty_band in {"easy", "medium", "hard"}

                record = {
                    "puzzle_id": puzzle_hash,
                    "puzzle": puzzle,
                    "solution": solution,
                    "puzzle_hash": puzzle_hash,
                    "solution_hash": sha256_text(solution),
                    "clue_count": clue_count(puzzle),
                    "difficulty_band": difficulty_band,
                    "ranked_candidate": ranked_candidate,
                    "ranked_suitable": False,
                    "status": "needs_review",
                    "validation": {
                        "unique_solution": True,
                        "solution_count_checked_up_to": 2,
                        "no_guessing_validated": False,
                    },
                    "source": {
                        "name": "Sudoku Exchange Puzzle Bank",
                        "url": "https://github.com/grantm/sudoku-exchange-puzzle-bank",
                        "license": "Public Domain",
                        "source_file": row["source_file"],
                        "source_line": row["source_line"],
                        "source_hash": row["source_hash"],
                        "source_bucket": row["source_bucket"],
                        "source_rating": row["source_rating"],
                    },
                }

                out.write(json.dumps(record, separators=(",", ":")) + "\n")

                total_written += 1
                written_for_bucket += 1

                if total_written % 500 == 0:
                    print(
                        f"Written={total_written} "
                        f"Seen={total_seen} "
                        f"Rejected={total_rejected} "
                        f"Duplicates={total_duplicates}"
                    )

    elapsed = round(time.time() - started_at, 2)

    summary = {
        "output_path": str(output_path),
        "total_seen": total_seen,
        "total_written": total_written,
        "total_rejected": total_rejected,
        "total_duplicates": total_duplicates,
        "elapsed_seconds": elapsed,
        "limit_per_bucket": limit_per_bucket,
    }

    summary_path = output_path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")

    print("\nDone.")
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw-dir",
        default="data/raw/sudoku_exchange",
    )
    parser.add_argument(
        "--output",
        default="data/processed/puzzles/sudoku_exchange_bank.jsonl",
    )
    parser.add_argument(
        "--limit-per-bucket",
        type=int,
        default=1000,
        help="Use 0 for no limit.",
    )

    args = parser.parse_args()

    import_bank(
        raw_dir=Path(args.raw_dir),
        output_path=Path(args.output),
        limit_per_bucket=args.limit_per_bucket,
    )


if __name__ == "__main__":
    main()