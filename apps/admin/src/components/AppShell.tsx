import Link from 'next/link';
import type { ReactNode } from 'react';
import styles from '@/lib/styles.module.css';

interface AppShellProps {
  readonly title: string;
  readonly children: ReactNode;
}

const NAV_ITEMS = [
  { href: '/', label: 'Overview' },
  { href: '/puzzles', label: 'Puzzles' },
  { href: '/puzzles/import', label: 'Import' },
  { href: '/daily', label: 'Daily' },
] as const;

export function AppShell({ title, children }: AppShellProps) {
  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.headerTitle}>{title}</h1>
        <nav className={styles.headerNav}>
          {NAV_ITEMS.map((item) => (
            <Link key={item.href} href={item.href} className={styles.headerLink}>
              {item.label}
            </Link>
          ))}
        </nav>
      </header>
      {children}
    </main>
  );
}
