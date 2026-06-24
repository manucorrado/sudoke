# Developer Setup Guide

Local environment setup for **Sudoke** — competitive daily Sudoku with ranked play, social challenges, and leaderboards.

For a quick overview of the monorepo, see [README.md](./README.md).

---

## What you need

| Tool | Version | Used for |
|------|---------|----------|
| **Git** | latest | Clone the repo |
| **Node.js** | 20+ (see `.nvmrc`) | Mobile app, admin dashboard, shared packages |
| **pnpm** | 9.15.4 | JS/TS monorepo package manager |
| **Python** | 3.11+ | FastAPI backend |
| **Docker Desktop** | latest | Local Postgres + Redis |
| **Java JDK** | 17 | Android Gradle builds |
| **Expo Go** (optional) | latest on phone | Quick JS-only smoke tests |
| **Xcode** (macOS only) | latest | iOS Simulator |
| **Android Studio** | latest | Android Emulator (AVD) |

---

## Platform-specific prerequisites

### macOS

1. **Node.js 20+**
   ```bash
   # With nvm (recommended)
   nvm install
   nvm use
   ```

2. **pnpm**
   ```bash
   corepack enable
   corepack prepare pnpm@9.15.4 --activate
   ```

3. **Python 3.11+**
   ```bash
   # Homebrew
   brew install python@3.11
   ```

4. **Docker Desktop**
   - Install from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
   - Start Docker Desktop before running `docker compose`

5. **iOS Simulator** (optional, macOS only)
   - Install **Xcode** from the Mac App Store
   - Open Xcode once and accept the license
   - Install iOS Simulator: Xcode → Settings → Platforms → iOS

6. **Java JDK 17** (required for Android development builds)
   ```bash
   # Homebrew
   brew install --cask temurin@17

   # Current shell
   export JAVA_HOME=$(/usr/libexec/java_home -v 17)
   java -version
   ```

   If Homebrew is not available, install the macOS JDK 17 `.pkg` from
   [Adoptium Temurin](https://adoptium.net/temurin/releases/?version=17), then restart your terminal and run the `JAVA_HOME` command above.

7. **Android Emulator** (optional)
   - Install [Android Studio](https://developer.android.com/studio)
   - Open **SDK Manager** → install:
     - **Android SDK Platform 35**
     - **Android SDK Build-Tools 35.0.0**
     - **Android SDK Platform-Tools**
   - Open **Virtual Device Manager** → **Create Device**
   - Recommended AVD: **Pixel 7** (or similar) · **API 35** · **Google APIs** image · enable hardware acceleration
   - Add Android SDK tools to your shell:

   ```bash
   export ANDROID_HOME="$HOME/Library/Android/sdk"
   export ANDROID_SDK_ROOT="$ANDROID_HOME"
   export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
   ```

### Windows

1. **Node.js 20+**
   - Install from [nodejs.org](https://nodejs.org/) or use [nvm-windows](https://github.com/coreybutler/nvm-windows)

2. **pnpm**
   ```powershell
   corepack enable
   corepack prepare pnpm@9.15.4 --activate
   ```

3. **Python 3.11+**
   - Install from [python.org](https://www.python.org/downloads/)
   - Check **“Add python.exe to PATH”** during setup

4. **Docker Desktop**
   - Install from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
   - Enable **WSL 2** backend (recommended): Settings → General → *Use the WSL 2 based engine*
   - Install [WSL 2](https://learn.microsoft.com/en-us/windows/wsl/install) if prompted

5. **Android Emulator** (recommended on Windows — no iOS Simulator)
   - Install [Android Studio](https://developer.android.com/studio)
   - **Tools → SDK Manager** → install Android SDK Platform 35, Build-Tools 35.0.0, and Platform-Tools
   - **Tools → Device Manager → Create Virtual Device**
   - Recommended: **Pixel 7** · **API 35** · **x86_64** Google APIs image
   - Ensure **Intel HAXM** or **Windows Hypervisor Platform** is enabled for performance

> **Note:** iOS Simulator is **macOS only**. On Windows, use **Expo Web** or an **Android AVD** for native testing.

---

## 1. Clone and install

```bash
git clone <repo-url> sudoke
cd sudoke
pnpm install
```

---

## 2. Start infrastructure (Postgres + Redis)

From the repo root:

```bash
docker compose up -d postgres redis
```

Verify containers are healthy:

```bash
docker compose ps
```

Default connection strings (also in `.env.example`):

- Postgres: `postgresql+asyncpg://postgres:postgres@localhost:5432/sudoke`
- Redis: `redis://localhost:6379/0`

---

## 3. Set up the API

```bash
cd apps/api

# Copy env template
cp .env.example .env

# Create and activate a virtual environment
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
# .venv\Scripts\Activate.ps1

pip install -e ".[dev]"

# Run database migrations
alembic upgrade head
```

### Run the API server

With the venv activated, from `apps/api/`:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Or run the full stack via Docker (API + Postgres + Redis):

```bash
# From repo root
docker compose up api
```

**Verify:**

- Health: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

> **Note:** `pnpm dev:api` at the repo root expects a Node wrapper that is not yet wired up. Use `uvicorn` directly or `docker compose up api`.

---

## 4. Seed local data (recommended)

Without seeded puzzles the **Today** tab will be empty.

### Option A — Quick demo (single daily puzzle + leaderboard)

```bash
cd apps/api
source .venv/bin/activate   # or .venv\Scripts\Activate.ps1 on Windows
python -m scripts.seed_demo
```

### Option B — Full puzzle bank (100+ scheduled days)

Requires the raw Sudoku Exchange bank under `data/raw/sudoku_exchange/`:

```bash
cd apps/api
source .venv/bin/activate

python -m scripts.ingest_puzzle_bank \
  --source ../../data/raw/sudoku_exchange/easy.txt \
  --difficulty easy \
  --limit 120 \
  --schedule \
  --schedule-start $(date -u +%Y-%m-%d)
```

On Windows (PowerShell), replace the date with an explicit UTC date, e.g. `--schedule-start 2026-06-24`.

### Background jobs (daily activation / finalization)

In production these run on a cron worker. Locally, trigger them manually:

```bash
cd apps/api
source .venv/bin/activate
python -m src.jobs.worker tick
```

For continuous local testing:

```bash
python -m src.jobs.worker loop --interval 60
```

---

## 5. Run the mobile app

From the **repo root**:

### Expo Web (fastest — no simulator required)

Best for UI development and agent-style browser testing. Matches PRD §24 agent visibility strategy.

```bash
pnpm dev:mobile:web
```

Open the URL shown in the terminal (usually [http://localhost:8081](http://localhost:8081)).

Useful routes:

- `/` — Today tab (daily ranked)
- `/dev` — Dev screen index (board states, casual mode, etc.)
- `/onboarding`, `/sign-in` — Auth flows
- `/c/[code]` — Challenge deep link stub

### iOS Simulator (macOS only)

```bash
pnpm dev:mobile
# Then press `i` in the Expo terminal, or:
pnpm --filter @sudoke/mobile ios
```

Requires Xcode + iOS Simulator installed.

### Android Emulator / AVD (macOS or Windows)

Use a **development build** for Android native testing. The mobile app uses Expo SDK 53 / React Native 0.79, and development builds avoid stale Expo Go/native-shell mismatches and Android 16 KB page-size compatibility warnings.

1. Start your AVD from Android Studio (**Device Manager → Play**).
2. Confirm the emulator is visible:

```bash
adb devices
```

3. From the repo root, configure Java and Android SDK paths for the current shell.

macOS:

```bash
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
export ANDROID_HOME="$HOME/Library/Android/sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
```

Windows PowerShell:

```powershell
$env:ANDROID_HOME="$env:LOCALAPPDATA\Android\Sdk"
$env:ANDROID_SDK_ROOT=$env:ANDROID_HOME
$env:Path="$env:ANDROID_HOME\platform-tools;$env:ANDROID_HOME\emulator;$env:ANDROID_HOME\cmdline-tools\latest\bin;$env:Path"
```

4. Ensure Gradle can find the Android SDK:

macOS:

```bash
printf "sdk.dir=%s\n" "$ANDROID_HOME" > apps/mobile/android/local.properties
```

Windows PowerShell:

```powershell
"sdk.dir=$($env:ANDROID_HOME -replace '\\','/')" | Out-File -Encoding ascii apps/mobile/android/local.properties
```

5. Install/build the Android development app:

```bash
pnpm --filter @sudoke/mobile exec expo run:android
```

6. Start Metro for the installed development build:

```bash
pnpm --filter @sudoke/mobile exec expo start --dev-client --clear
```

Then press `a`, or open the installed **Sudoke** app on the AVD.

Only rerun `expo prebuild --clean --platform android` after native config changes, dependency changes with native modules, or when the generated `apps/mobile/android/` project needs to be regenerated.

#### First-time Android native setup

If `apps/mobile/android/` does not exist yet, run this once before `expo run:android`:

```bash
pnpm --filter @sudoke/mobile exec expo install expo-dev-client
pnpm --filter @sudoke/mobile exec expo prebuild --clean --platform android
```

#### Android API URL note

The mobile client currently points at `http://localhost:8000/api/v1` (see `apps/mobile/src/lib/api.ts`).

| Target | API base URL |
|--------|----------------|
| Expo Web / iOS Simulator | `http://localhost:8000/api/v1` |
| Android Emulator | `http://10.0.2.2:8000/api/v1` |
| Physical device (same Wi‑Fi) | `http://<your-lan-ip>:8000/api/v1` |

For Android emulator or physical device testing, temporarily update `BASE_URL` in `apps/mobile/src/lib/api.ts`, or set up port forwarding:

```bash
adb reverse tcp:8000 tcp:8000
```

### Physical device with Expo Go

1. Install **Expo Go** from the App Store / Play Store
2. Run `pnpm dev:mobile`
3. Scan the QR code (same Wi‑Fi network as your machine)
4. Point the API URL at your machine's LAN IP (see table above)

---

## 6. Run the admin dashboard

```bash
pnpm dev:admin
```

Open [http://localhost:3001](http://localhost:3001).

The admin UI talks to the API at `http://localhost:8000/api/v1` by default. In development it can authenticate via the `X-Dev-Auth-User` header (no Clerk required).

Features: puzzle import/review/schedule, playtest on puzzle detail pages.

---

## 7. Auth in local development

Clerk is **optional** for local dev.

| Flow | How |
|------|-----|
| **Guest** | Automatic — app creates a guest session on first launch |
| **Registered user (dev)** | Open `/sign-in` → paste a dev bearer token, or use the dev auth bypass |
| **Clerk (optional)** | Set `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY` for mobile and `CLERK_*` keys in `apps/api/.env` |

The API accepts `X-Dev-Auth-User: <user-id>` when `ENVIRONMENT=development` for admin and testing.

---

## 8. Environment variables

### API (`apps/api/.env`)

Copy from `apps/api/.env.example`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sudoke
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=development
API_V1_PREFIX=/api/v1

# Optional
CLERK_SECRET_KEY=
CLERK_PUBLISHABLE_KEY=
SENTRY_DSN=
```

### Mobile (optional)

Create `apps/mobile/.env` if using Clerk:

```env
EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
```

Expo inlines `EXPO_PUBLIC_*` at bundle time — restart the dev server after changing.

---

## 9. Verify your setup

Run from the **repo root**:

```bash
# Lint + typecheck + tests (matches CI)
pnpm lint
pnpm typecheck
pnpm test

# API tests
cd apps/api && .venv/bin/pytest -q    # macOS/Linux
# cd apps/api && .venv\Scripts\pytest -q   # Windows
```

Manual smoke test:

1. `docker compose up -d postgres redis`
2. API running on port 8000, migrations applied, demo data seeded
3. `pnpm dev:mobile:web` → Today tab shows a daily puzzle
4. Play through preview → start → submit
5. Leaderboard tab loads (may be empty until others submit)
6. `/dev` screens render board states

---

## 10. Common issues

| Problem | Fix |
|---------|-----|
| **`node: not found` / `pnpm: not found`** | Install Node 20+ (see §Platform-specific prerequisites). Cursor's bundled Node is **not** on your shell PATH — you need a system/user Node install with `npm`/`corepack`. |
| **`adb: not found`** | Add Android SDK to PATH: `export PATH="$HOME/Library/Android/sdk/platform-tools:$PATH"` (macOS). Install platform-tools via Android Studio → SDK Manager if missing. |
| **`Unable to locate a Java Runtime` during `expo run:android`** | Install JDK 17, then set `JAVA_HOME=$(/usr/libexec/java_home -v 17)` in the shell running the build. |
| **`SDK location not found` during Android Gradle build** | Set `ANDROID_HOME` to your Android SDK and write `apps/mobile/android/local.properties` with `sdk.dir=<android-sdk-path>` (see §5 Android Emulator / AVD). |
| **`No development build (com.sudoke.app) ... is installed`** | Run `pnpm --filter @sudoke/mobile exec expo run:android` with the AVD running, then start Metro with `expo start --dev-client --clear`. |
| **Android shows `This app isn't 16 KB compatible`** | Rebuild and reinstall the Android development build after SDK/native dependency changes. Do not use a stale Expo Go/native shell for SDK 53 testing. |
| **Android `Invalid hook call` immediately after SDK upgrade** | Uninstall stale Expo Go/dev builds from the AVD, rebuild with `expo run:android`, and launch through the installed dev client. |
| **Today tab empty** | Run `python -m scripts.seed_demo` or ingest puzzles; then `python -m src.jobs.worker tick` |
| **Mobile can't reach API (Android)** | Use `10.0.2.2` or `adb reverse tcp:8000 tcp:8000` |
| **Mobile can't reach API (physical device)** | Use LAN IP; ensure firewall allows port 8000 |
| **Port 5432 already in use** | Stop local Postgres or change the Docker Compose port mapping |
| **`pnpm dev:api` fails** | Use `uvicorn` directly (see §3) |
| **Docker not starting (Windows)** | Enable WSL 2 and virtualization in BIOS |
| **Expo Metro cache issues** | `pnpm --filter @sudoke/mobile start -- --clear` |

---

## 11. Recommended dev workflow

**Minimal (UI + gameplay):**

```bash
docker compose up -d postgres redis
# terminal 1 — API
cd apps/api && source .venv/bin/activate && uvicorn src.main:app --reload
# terminal 2 — seed once
python -m scripts.seed_demo
# terminal 3 — mobile web
pnpm dev:mobile:web
```

**Full stack:**

Add `pnpm dev:admin` and optionally `python -m src.jobs.worker loop --interval 60` for cron behaviour.

**Native QA:**

Use iOS Simulator (macOS) or an Android AVD development build when testing deep links, secure storage, or platform-specific behaviour. Expo Web covers most product flows for day-to-day development (PRD §24).

---

## Reference

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Admin | http://localhost:3001 |
| Mobile (Expo Web) | http://localhost:8081 |
| Postgres | localhost:5432 |
| Redis | localhost:6379 |
