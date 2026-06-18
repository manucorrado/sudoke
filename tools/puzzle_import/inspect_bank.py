from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()

    path = Path(args.path)

    difficulty_counts = Counter()
    status_counts = Counter()
    ranked_counts = Counter()
    clue_counts = Counter()

    total = 0

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            total += 1

            difficulty_counts[row["difficulty_band"]] += 1
            status_counts[row["status"]] += 1
            ranked_counts[str(row["ranked_candidate"])] += 1
            clue_counts[row["clue_count"]] += 1

    print(f"Total puzzles: {total}")

    print("\nBy difficulty:")
    for key, value in sorted(difficulty_counts.items()):
        print(f"  {key}: {value}")

    print("\nBy status:")
    for key, value in sorted(status_counts.items()):
        print(f"  {key}: {value}")

    print("\nRanked candidate:")
    for key, value in sorted(ranked_counts.items()):
        print(f"  {key}: {value}")

    print("\nMost common clue counts:")
    for key, value in clue_counts.most_common(10):
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()