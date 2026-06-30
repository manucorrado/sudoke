import path from 'node:path';
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  transpilePackages: ['@sudoke/sudoku-core'],
  output: 'standalone',
  // Trace from the monorepo root so the standalone bundle includes the
  // hoisted pnpm dependencies and the workspace packages.
  outputFileTracingRoot: path.join(__dirname, '../..'),
};

export default nextConfig;
