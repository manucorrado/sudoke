from src import sudoku

EASY = (
    "530070000"
    "600195000"
    "098000060"
    "800060003"
    "400803001"
    "700020006"
    "060000280"
    "000419005"
    "000080079"
)

EASY_SOLUTION = (
    "534678912"
    "672195348"
    "198342567"
    "859761423"
    "426853791"
    "713924856"
    "961537284"
    "287419635"
    "345286179"
)

SCREENSHOT_INVALID = (
    "530070000"
    "060019500"
    "000980000"
    "060800006"
    "000340008"
    "030017000"
    "020006060"
    "000028000"
    "004190005"
)


def test_solve_easy() -> None:
    grid = sudoku.parse_grid(EASY)
    solution = sudoku.solve(grid)
    assert solution is not None
    assert sudoku.serialize_grid(solution) == EASY_SOLUTION


def test_validate_puzzle_ok() -> None:
    result = sudoku.validate_puzzle(sudoku.parse_grid(EASY))
    assert result.ok is True
    assert result.solution is not None


def test_validate_puzzle_non_unique() -> None:
    result = sudoku.validate_puzzle([0] * 81)
    assert result.ok is False


def test_validate_puzzle_reports_duplicate_givens() -> None:
    result = sudoku.validate_puzzle(sudoku.parse_grid("55" + "0" * 79))
    assert result.ok is False
    assert "given conflict" in " ".join(result.issues).lower()


def test_validate_puzzle_rejects_malformed_values() -> None:
    result = sudoku.validate_puzzle([10] + [0] * 80)
    assert result.ok is False
    assert "integer 0..9" in " ".join(result.issues)


def test_validate_puzzle_rejects_screenshot_invalid_grid() -> None:
    result = sudoku.validate_puzzle(sudoku.parse_grid(SCREENSHOT_INVALID))
    assert result.ok is False
    assert "given conflict" in " ".join(result.issues).lower()


def test_validate_submission_full_solution() -> None:
    solution = sudoku.parse_grid(EASY_SOLUTION)
    result = sudoku.validate_submission(solution, solution)
    assert result.valid is True
    assert result.mistakes == 0


def test_validate_submission_with_errors() -> None:
    solution = sudoku.parse_grid(EASY_SOLUTION)
    wrong = solution.copy()
    wrong[0] = 9 if solution[0] != 9 else 1
    result = sudoku.validate_submission(wrong, solution)
    assert result.valid is False
    assert result.mistakes == 1
    assert 0 in result.wrong_indices
