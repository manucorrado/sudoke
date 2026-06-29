# Build context is the monorepo root (see render.yaml dockerContext: .).
FROM node:20-slim AS base
ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH
RUN corepack enable
WORKDIR /app

# ── Dependencies ──────────────────────────────────────────────
FROM base AS deps
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/admin/package.json apps/admin/package.json
COPY packages/sudoku-core/package.json packages/sudoku-core/package.json
RUN pnpm install --frozen-lockfile

# ── Build ─────────────────────────────────────────────────────
FROM base AS build
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/admin/node_modules ./apps/admin/node_modules
COPY tsconfig.base.json ./
COPY packages/sudoku-core ./packages/sudoku-core
COPY apps/admin ./apps/admin
RUN pnpm --filter @sudoke/admin build

# ── Runtime ───────────────────────────────────────────────────
FROM base AS runtime
ENV NODE_ENV=production
COPY --from=build /app/apps/admin/.next/standalone ./
COPY --from=build /app/apps/admin/.next/static ./apps/admin/.next/static

EXPOSE 3001
CMD ["node", "apps/admin/server.js"]
