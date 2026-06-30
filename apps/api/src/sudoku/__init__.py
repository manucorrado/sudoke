"""Python port of the shared Sudoku rules.

Keeps backend authoritative — never trust client-submitted grids.
Mirrors the contract in ``packages/sudoku-core``.
"""

from src.sudoku.engine import (
    SUSPICIOUS_SOLVE_THRESHOLDS_SECONDS,
    GameRules,
    SudokuError,
    ValidationResult,
    find_solutions,
    given_conflict_issues,
    has_unique_solution,
    is_complete_solution,
    parse_grid,
    serialize_grid,
    solve,
    validate_puzzle,
    validate_submission,
)

__all__ = [
    "SUSPICIOUS_SOLVE_THRESHOLDS_SECONDS",
    "GameRules",
    "SudokuError",
    "ValidationResult",
    "find_solutions",
    "given_conflict_issues",
    "has_unique_solution",
    "is_complete_solution",
    "parse_grid",
    "serialize_grid",
    "solve",
    "validate_puzzle",
    "validate_submission",
]
