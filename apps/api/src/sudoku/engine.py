"""Pure-Python Sudoku validator and solver used by the API.

Mirrors `packages/sudoku-core` semantics so server-side validation produces
the same answers as the mobile client.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

GRID_SIZE = 9
BOX_SIZE = 3
TOTAL_CELLS = GRID_SIZE * GRID_SIZE
MIN_CLUES = 17
MAX_RANKED_MISTAKES = 3

Difficulty = Literal["easy", "medium", "hard", "expert"]

SUSPICIOUS_SOLVE_THRESHOLDS_SECONDS: dict[Difficulty, int] = {
    "easy": 60,
    "medium": 90,
    "hard": 150,
    "expert": 240,
}


@dataclass(frozen=True)
class GameRules:
    """Server-known rule presets used to validate attempts."""

    mode: Literal["ranked", "casual", "practice"]
    max_mistakes: int | None

    @classmethod
    def ranked(cls) -> GameRules:
        return cls(mode="ranked", max_mistakes=MAX_RANKED_MISTAKES)


class SudokuError(ValueError):
    """Raised for malformed inputs."""


def parse_grid(value: str) -> list[int]:
    """Parse an 81-char grid string ("0" or "." means empty)."""

    cleaned = "".join(ch for ch in value if not ch.isspace())
    if len(cleaned) != TOTAL_CELLS:
        raise SudokuError(
            f"Invalid grid string: expected {TOTAL_CELLS} cells, got {len(cleaned)}"
        )
    out: list[int] = []
    for i, ch in enumerate(cleaned):
        if ch in (".", "0"):
            out.append(0)
            continue
        if not ch.isdigit():
            raise SudokuError(f"Invalid cell character '{ch}' at index {i}")
        n = int(ch)
        if n < 1 or n > 9:
            raise SudokuError(f"Invalid cell value '{n}' at index {i}")
        out.append(n)
    return out


def serialize_grid(grid: list[int]) -> str:
    if len(grid) != TOTAL_CELLS:
        raise SudokuError(f"Grid must have {TOTAL_CELLS} cells")
    return "".join(str(v) if v else "0" for v in grid)


def _row(idx: int) -> int:
    return idx // GRID_SIZE


def _col(idx: int) -> int:
    return idx % GRID_SIZE


def _box(idx: int) -> int:
    return (_row(idx) // BOX_SIZE) * BOX_SIZE + (_col(idx) // BOX_SIZE)


def _grid_value_issues(grid: list[int], *, label: str) -> tuple[str, ...]:
    issues: list[str] = []
    for i, value in enumerate(grid):
        if type(value) is not int or value < 0 or value > 9:
            issues.append(
                f"{label} value at index {i} must be an integer 0..9 "
                f"(received {value!r})"
            )
    return tuple(issues)


def _box_indexes(box: int) -> list[int]:
    box_row = (box // BOX_SIZE) * BOX_SIZE
    box_col = (box % BOX_SIZE) * BOX_SIZE
    return [
        row * GRID_SIZE + col
        for row in range(box_row, box_row + BOX_SIZE)
        for col in range(box_col, box_col + BOX_SIZE)
    ]


def _conflict_issues_for_group(
    grid: list[int], *, indexes: list[int], label: str
) -> tuple[str, ...]:
    seen: dict[int, int] = {}
    issues: list[str] = []
    for idx in indexes:
        value = grid[idx]
        if value == 0:
            continue
        previous = seen.get(value)
        if previous is not None:
            issues.append(
                f"Given conflict: value {value} appears at indexes "
                f"{previous} and {idx} in {label}"
            )
        else:
            seen[value] = idx
    return tuple(issues)


def given_conflict_issues(grid: list[int]) -> tuple[str, ...]:
    """Return row/column/box duplicate conflicts among puzzle givens."""

    issues: list[str] = []
    for group in range(GRID_SIZE):
        row_indexes = [group * GRID_SIZE + col for col in range(GRID_SIZE)]
        col_indexes = [row * GRID_SIZE + group for row in range(GRID_SIZE)]
        issues.extend(
            _conflict_issues_for_group(
                grid, indexes=row_indexes, label=f"row {group + 1}"
            )
        )
        issues.extend(
            _conflict_issues_for_group(
                grid, indexes=col_indexes, label=f"column {group + 1}"
            )
        )
        issues.extend(
            _conflict_issues_for_group(
                grid, indexes=_box_indexes(group), label=f"box {group + 1}"
            )
        )
    return tuple(issues)


def _init_masks(grid: list[int]) -> tuple[list[int], list[int], list[int]] | None:
    rows = [0] * GRID_SIZE
    cols = [0] * GRID_SIZE
    boxes = [0] * GRID_SIZE
    for i, v in enumerate(grid):
        if v == 0:
            continue
        m = 1 << (v - 1)
        r, c, b = _row(i), _col(i), _box(i)
        if rows[r] & m or cols[c] & m or boxes[b] & m:
            return None
        rows[r] |= m
        cols[c] |= m
        boxes[b] |= m
    return rows, cols, boxes


def _popcount(n: int) -> int:
    return bin(n).count("1")


def _find_best(
    grid: list[int], rows: list[int], cols: list[int], boxes: list[int]
) -> tuple[int, int]:
    best_idx = -1
    best_candidates = 0
    best_count = 10
    for i in range(TOTAL_CELLS):
        if grid[i]:
            continue
        used = rows[_row(i)] | cols[_col(i)] | boxes[_box(i)]
        candidates = (~used) & 0x1FF
        count = _popcount(candidates)
        if count < best_count:
            best_count = count
            best_idx = i
            best_candidates = candidates
            if count <= 1:
                break
    return best_idx, best_candidates


def _search(
    grid: list[int],
    rows: list[int],
    cols: list[int],
    boxes: list[int],
    found: list[list[int]],
    limit: int,
) -> None:
    if len(found) >= limit:
        return
    idx, candidates = _find_best(grid, rows, cols, boxes)
    if idx == -1:
        found.append(grid.copy())
        return
    if candidates == 0:
        return
    r, c, b = _row(idx), _col(idx), _box(idx)
    remaining = candidates
    while remaining and len(found) < limit:
        m = remaining & -remaining
        remaining &= remaining - 1
        v = m.bit_length()
        grid[idx] = v
        rows[r] |= m
        cols[c] |= m
        boxes[b] |= m
        _search(grid, rows, cols, boxes, found, limit)
        grid[idx] = 0
        rows[r] &= ~m
        cols[c] &= ~m
        boxes[b] &= ~m


def find_solutions(grid: list[int], limit: int) -> list[list[int]]:
    state = _init_masks(grid)
    if state is None:
        return []
    rows, cols, boxes = state
    found: list[list[int]] = []
    _search(grid.copy(), rows, cols, boxes, found, limit)
    return found


def solve(grid: list[int]) -> list[int] | None:
    solutions = find_solutions(grid, 1)
    return solutions[0] if solutions else None


def has_unique_solution(grid: list[int]) -> bool:
    return len(find_solutions(grid, 2)) == 1


def is_complete_solution(grid: list[int]) -> bool:
    if len(grid) != TOTAL_CELLS:
        return False
    if any(v < 1 or v > 9 for v in grid):
        return False
    for group in range(GRID_SIZE):
        row_seen: set[int] = set()
        col_seen: set[int] = set()
        box_seen: set[int] = set()
        for k in range(GRID_SIZE):
            r_idx = group * GRID_SIZE + k
            c_idx = k * GRID_SIZE + group
            box_row = (group // BOX_SIZE) * BOX_SIZE + (k // BOX_SIZE)
            box_col = (group % BOX_SIZE) * BOX_SIZE + (k % BOX_SIZE)
            b_idx = box_row * GRID_SIZE + box_col
            rv, cv, bv = grid[r_idx], grid[c_idx], grid[b_idx]
            if rv in row_seen or cv in col_seen or bv in box_seen:
                return False
            row_seen.add(rv)
            col_seen.add(cv)
            box_seen.add(bv)
    return True


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    issues: tuple[str, ...]
    solution: tuple[int, ...] | None
    clue_count: int


def validate_puzzle(
    givens: list[int],
    *,
    solution: list[int] | None = None,
    min_clues: int = MIN_CLUES,
) -> ValidationResult:
    issues: list[str] = []
    if len(givens) != TOTAL_CELLS:
        return ValidationResult(
            False, (f"givens must have {TOTAL_CELLS} cells",), None, 0
        )

    value_issues = _grid_value_issues(givens, label="Given")
    if value_issues:
        return ValidationResult(
            False,
            value_issues,
            None,
            sum(1 for value in givens if type(value) is int and value != 0),
        )

    clue_count = sum(1 for v in givens if v != 0)
    if clue_count < min_clues:
        issues.append(f"Puzzle has {clue_count} clues; minimum is {min_clues}")

    conflict_issues = given_conflict_issues(givens)
    if conflict_issues:
        issues.extend(conflict_issues)
        return ValidationResult(False, tuple(issues), None, clue_count)

    sols = find_solutions(givens, 2)
    if not sols:
        issues.append("Puzzle has no solution")
        return ValidationResult(False, tuple(issues), None, clue_count)
    if len(sols) > 1:
        issues.append("Puzzle does not have a unique solution")

    canonical = sols[0]

    if solution is not None:
        if len(solution) != TOTAL_CELLS:
            issues.append(f"Solution must have {TOTAL_CELLS} cells")
        else:
            solution_value_issues = _grid_value_issues(solution, label="Solution")
            if solution_value_issues:
                issues.extend(solution_value_issues)
            elif not is_complete_solution(solution):
                issues.append("Provided solution is not a valid completed Sudoku grid")
            elif solution != canonical:
                issues.append(
                    "Provided solution does not match computed unique solution"
                )
            else:
                for i, (g, s) in enumerate(zip(givens, solution, strict=True)):
                    if g != 0 and g != s:
                        issues.append(f"Given at index {i} disagrees with solution")
                        break

    return ValidationResult(
        ok=not issues,
        issues=tuple(issues),
        solution=tuple(canonical),
        clue_count=clue_count,
    )


@dataclass(frozen=True)
class SubmissionResult:
    valid: bool
    mistakes: int
    wrong_indices: tuple[int, ...]


def validate_submission(submitted: list[int], solution: list[int]) -> SubmissionResult:
    """Compute the number of wrong cells in a submitted final grid.

    Returns ``valid=True`` only when the grid is fully populated and every
    cell matches the canonical solution.
    """

    if len(submitted) != TOTAL_CELLS or len(solution) != TOTAL_CELLS:
        raise SudokuError("submitted and solution must be 81 cells")
    wrong: list[int] = []
    full = True
    for i in range(TOTAL_CELLS):
        if not submitted[i]:
            full = False
            continue
        if submitted[i] != solution[i]:
            wrong.append(i)
    return SubmissionResult(
        valid=full and not wrong,
        mistakes=len(wrong),
        wrong_indices=tuple(wrong),
    )
