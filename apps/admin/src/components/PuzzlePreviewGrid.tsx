interface PuzzlePreviewGridProps {
  readonly grid: string;
  readonly highlight?: 'givens' | 'solution';
}

/**
 * Read-only Sudoku visualization for admin review.
 * Mirrors the mobile board's box-border styling.
 */
export function PuzzlePreviewGrid({ grid, highlight = 'givens' }: PuzzlePreviewGridProps) {
  const cells = Array.from(grid);
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(9, 32px)',
        width: 'fit-content',
        border: '2px solid #1a1a2e',
        borderRadius: 4,
        background: '#fff',
      }}
      role="grid"
      aria-label={highlight === 'givens' ? 'Puzzle givens' : 'Puzzle solution'}
    >
      {cells.map((ch, i) => {
        const row = Math.floor(i / 9);
        const col = i % 9;
        const value = ch === '0' || ch === '.' ? '' : ch;
        return (
          <div
            key={i}
            style={{
              width: 32,
              height: 32,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 14,
              fontWeight: value ? 600 : 400,
              color: value ? '#1a1a2e' : '#bbb',
              borderRight: col === 8 ? 'none' : col % 3 === 2 ? '1.5px solid #1a1a2e' : '1px solid #ececf2',
              borderBottom: row === 8 ? 'none' : row % 3 === 2 ? '1.5px solid #1a1a2e' : '1px solid #ececf2',
              background:
                highlight === 'solution' && value
                  ? '#fbfbfd'
                  : value
                    ? '#fff'
                    : '#fafafd',
            }}
            role="gridcell"
          >
            {value}
          </div>
        );
      })}
    </div>
  );
}
