# Sudoke Pending Tasks

**Last audited:** 2026-07-01  
**Goal:** Finish the MVP so the only remaining work is submission/release through the iOS App Store and Google Play Store.

This file consolidates `EPIC_PLAN_UPDATED.md`, `INFRA_EPICS.md`, `MVP_EPIC_PLAN.md`, the current repository state, and the read-only Render workspace inventory.

## Current Snapshot

### Repository

- Git branch: `feature-testing`
- `git status --short --branch`: clean at audit time (`## feature-testing`)
- Important repo-side infra now exists: `render.yaml`, `apps/api/Dockerfile`, `apps/admin/Dockerfile`, `.github/workflows/ci.yml`, `docs/infra/staging.md`
- Still missing repo-side launch files: `eas.json`, dynamic `apps/mobile/app.config.ts`, Playwright config/workflow, deploy workflow, challenge landing/static link host, legal pages, production runbooks

### Render Workspace Inventory

Selected Render workspace: `tea-d3aqskemcj7s73edel30`

Sudoke services currently present:

| Service | Type | Env | Region | Status / notes |
|---|---:|---|---|---|
| `sudoke-api-staging` | Web service | staging | Oregon | Docker, branch `main`, health `/api/v1/health/ready`, auto-deploy on commit, public URL `https://sudoke-api-staging.onrender.com` |
| `sudoke-admin-staging` | Web service | staging | Oregon | Docker, branch `main`, health `/api/health`, public URL `https://sudoke-admin-staging.onrender.com` |
| `sudoke-cron-staging` | Cron job | staging | Oregon | Docker, schedule `*/5 * * * *`, command `python -m src.jobs.worker tick`, last successful run observed |
| `sudoke-postgres-staging` | Postgres | staging | Oregon | Available, PostgreSQL 16, `basic_1gb`, 15 GB disk |
| `sudoke-redis-staging` | Key Value | staging | Oregon | Available, Redis 8.1.4 compatible, starter plan, `noeviction` |

Render gaps:

- No Sudoke production API/admin/cron/Postgres/Redis services are listed.
- No Sudoke production environment/promotion flow is listed.
- No Sudoke custom domains are visible in the service inventory; staging uses `onrender.com` URLs.
- Staging admin and API services allow `0.0.0.0/0`; admin needs real auth and/or access restriction before production.
- `render.yaml` still sets `ADMIN_DEV_BYPASS_ENABLED=true` for staging API and `ADMIN_AUTH_PROVIDER_ID=admin-dev` for admin. This must not reach production.

## MVP Completion Path

Complete these in order unless a task explicitly says it can run in parallel.

## 1. Reconcile Plans With Current Reality

**Status:** Pending documentation cleanup. The planning docs still say live Render services were not created, but staging services now exist.

Steps to finish:

- Update `EPIC_PLAN_UPDATED.md` and `INFRA_EPICS.md` to say staging Render services are provisioned.
- Keep production marked incomplete until production Render services, domains, secrets, and promotion flow exist.
- Update `docs/infra/staging.md` to match live cron cadence (`*/5 * * * *`) or change the cron schedule if every-minute ticking is required.
- Add a short `docs/infra/production.md` covering production provisioning, promotion, rollback, backups, cron stability, and puzzle ingestion.

## 2. Render Production Environment

**Status:** Blocking launch. Staging exists; production does not.

Steps to finish:

- Create production Render Postgres, Key Value, API web service, admin web service, and cron job in the same region.
- Decide whether production is a separate Blueprint instance, manually managed services, or a promotion workflow from staging.
- Configure production secrets: `DATABASE_URL`, `REDIS_URL`, `ENVIRONMENT=production`, `API_V1_PREFIX`, `CORS_ALLOWED_ORIGINS`, Clerk, Sentry, PostHog, Expo push, and any deploy hooks.
- Disable all dev bypass paths in production: no `ADMIN_DEV_BYPASS_ENABLED=true`, no `ADMIN_AUTH_PROVIDER_ID=admin-dev`, no reliance on `X-Dev-Auth-User`.
- Add custom domains: `api.sudoke.app`, `admin.sudoke.app`, and `sudoke.app` or the final selected domain.
- Enable production Postgres backups/PITR and document restore steps.
- Run migrations via production deploy/release command and verify `/api/v1/health/ready`.
- Run the cron job for at least 7 consecutive days before public launch and alert on failures.

## 3. Render Staging Hardening

**Status:** Staging exists but is not production-like enough for launch validation.

Steps to finish:

- Set staging custom domains: `api.staging.sudoke.app`, `admin.staging.sudoke.app`, and `staging.sudoke.app`.
- Replace staging admin dev bypass with Clerk-authenticated admin access.
- Restrict admin access with Clerk role checks and optionally an IP allowlist or access proxy.
- Confirm API, admin, cron, Postgres, and Redis all use internal/private URLs where possible.
- Verify all `sync: false` values in `render.yaml` are filled in Render.
- Run a staging smoke checklist: health, sign-in, daily puzzle, attempt submit, leaderboard, admin import/schedule, cron activation/finalization.

## 4. Clerk Auth, Admin Auth, and Account Deletion

**Status:** Partial. Mobile Clerk bridge and API JWKS verification exist; real envs, admin middleware, webhooks, and deletion are pending.

Steps to finish:

- Create separate Clerk applications for development, staging, and production.
- Configure mobile OAuth redirect URLs for iOS, Android, and Expo development builds.
- Set API Clerk secrets and issuer/JWKS values in staging and production.
- Add Clerk auth middleware to `apps/admin` and remove dependency on `X-Dev-Auth-User`.
- Map Clerk users to API users/admin roles and enforce admin-only routes in both admin UI and API.
- Implement Clerk webhook routes on the API for `user.created`, `user.updated`, and `user.deleted`.
- Implement account deletion/anonymization: delete or detach personal data, anonymize historical leaderboard display as "Deleted Player", and remove analytics person data where required.
- Add tests for forged JWT rejection, valid Clerk JWT acceptance, admin authorization, and account deletion effects.
- Native QA: sign up, sign in, sign out, token refresh, guest-to-account claim, and failure states on both iOS and Android.

## 5. Mobile Build and Store Distribution Pipeline

**Status:** Missing. `apps/mobile/app.json` exists, but there is no `eas.json` or dynamic `app.config.ts`.

Steps to finish:

- Create an Expo/EAS project and add `extra.eas.projectId`.
- Replace or complement `app.json` with `app.config.ts` so staging/production values are build-profile driven.
- Add `eas.json` profiles for development, preview/staging, and production.
- Configure bundle IDs/package names, icons, splash assets, version/build number strategy, and runtime update policy.
- Add environment values per build profile: API URL, Clerk publishable key, challenge web URL, Sentry DSN, PostHog key/host, AdMob IDs.
- Add iOS credentials: Apple distribution certificate, provisioning profiles, APNs key.
- Add Android credentials: keystore, Firebase project, FCM v1 service account, `google-services.json`.
- Build and install TestFlight/Internal Testing versions that point to staging.
- Run native QA for deep links, backgrounding during ranked play, push permissions, ads, Clerk OAuth, and offline/error states.

## 6. Domains, Universal Links, and Challenge Web Landing

**Status:** Partial in-app deep link support exists; public web link infrastructure is missing.

Steps to finish:

- Purchase/configure the final domain, for example `sudoke.app`.
- Add DNS records for API, admin, staging, and public challenge landing.
- Create a non-playable challenge landing site or minimal web app for `/c/{code}`.
- The landing page should show challenger context, puzzle/day metadata that does not leak the solution, App Store/Play CTAs, and app-open fallback behavior.
- Host `/.well-known/apple-app-site-association` and `/.well-known/assetlinks.json`.
- Add iOS `associatedDomains` and Android `intentFilters` in mobile config.
- Set `EXPO_PUBLIC_CHALLENGE_WEB_BASE_URL` and API `CHALLENGE_SHARE_BASE_URL` for staging and production.
- Test installed-app open, uninstalled-user landing, and context preservation through install/open on both platforms.

## 7. Daily Ranked, Rating, and Cron Stability

**Status:** Core implementation exists, but cloud validation and production stability are pending.

Steps to finish:

- On staging, load scheduled puzzles and verify one global daily puzzle activates at the expected UTC time.
- Validate preview/start/submit/abandon/timeout transitions against the API.
- Confirm server-owned timing and one-attempt rules on iOS and Android while backgrounding/foregrounding the app.
- Verify anti-cheat thresholds flag ultra-fast solves as under review without exposing rules.
- Confirm finalization cron writes final ranks/rating deltas and does not double-apply if run repeatedly.
- Wire rating history into the Profile UI using the existing rating-history API/SDK surface.
- Implement leaderboard default selection rules: friends-first when opened from a challenge/post-game context, otherwise nearby/global per product rules.
- Add the post-game completion animation before the result card, then keep the result/share/leaderboard flow order intact.
- Add operational alerts for activation and finalization failures.
- Run a 7-day staging stability test with real cron runs before production promotion.

## 8. Puzzle Content and Production Data Load

**Status:** Tooling exists; production content is not loaded.

Steps to finish:

- Ensure easy, medium, and hard puzzle bank source files are available in the production ingestion environment.
- Run `scripts.ingest_puzzle_bank` against staging first with `--schedule --weekly-rotation`.
- Review imported puzzle metadata, license/source fields, duplicate rejection, difficulty rotation, and scheduled dates.
- Repeat ingestion against production Postgres using the confirmed launch day.
- Verify at least 90 approved/scheduled production puzzles and no expert puzzles in ranked rotation.
- Add an operator runbook for replacing or voiding a bad daily puzzle.
- Add a pre-launch admin checklist for reviewing upcoming schedule, source/license completeness, and active puzzle state.

## 9. Admin Dashboard Production Readiness

**Status:** Admin UI and Dockerfile exist; production auth and operational hardening are pending.

Steps to finish:

- Wire `apps/admin` to Clerk server-side auth.
- Replace `ADMIN_AUTH_PROVIDER_ID` dev principal with real Clerk sessions/API bearer propagation.
- Enforce admin role checks before rendering admin routes and before API mutations.
- Confirm admin can import, review, playtest, approve, reject, schedule, and inspect daily status on staging.
- Add admin error/loading states for failed API calls and unauthorized sessions.
- Restrict production admin access via Clerk roles and optionally IP/access proxy.
- Add smoke tests for admin health and key operator flows.

## 10. Push Notifications

**Status:** Backend preferences, push token registry, and Expo dispatch service exist. Native client integration and most triggers are pending.

Steps to finish:

- Add `expo-notifications` to mobile dependencies and config plugins.
- Implement permission prompt timing after a meaningful action, not during onboarding.
- Register and unregister Expo push tokens through `POST`/`DELETE /me/push-tokens`.
- Add notification handling UX for foreground, background, and opened-from-notification states.
- Provision APNs and FCM credentials through EAS/Firebase.
- Enable `EXPO_PUSH_ENABLED=true` only after credentials and staging QA pass.
- Implement and test all MVP triggers: daily reminder, friend challenged you, someone beat your time, final ranking ready.
- Respect `/me/notifications/preferences` for every trigger.
- Native QA delivery on iOS and Android staging builds.

## 11. Analytics and Monitoring

**Status:** API has structured logging and optional Sentry dependency; PostHog and mobile Sentry initialization are pending.

Steps to finish:

- Create Sentry projects for API, mobile, and admin.
- Initialize Sentry in mobile app startup and admin if desired.
- Add release/environment tags for API/admin/mobile deploys.
- Add Sentry cron monitors or equivalent alerts for activation, timeout, and finalization jobs.
- Create a PostHog project and add client/server SDKs.
- Implement privacy-safe event tracking for ranked funnel, onboarding/auth, challenge funnel, streaks, notifications, ads, and retention.
- Do not send full puzzle grids, solutions, emails, raw device IDs, or sensitive auth data to analytics.
- Build PostHog dashboards for D1/D7 retention, ranked completion rate, share rate, guest conversion, notification opt-in, and ad performance.
- Configure alerts for API 5xx spikes, submission failures, cron failures, and mobile crash spikes.

## 12. Monetization / AdMob

**Status:** Not started. No AdMob SDK/dependencies/config are present.

Steps to finish:

- Create Google AdMob account and register iOS/Android apps.
- Add test and production ad unit IDs per placement.
- Add a React Native compatible AdMob SDK and any required native config.
- Add GDPR/UMP consent flow before serving ads where required.
- Implement allowed placements only: after ranked result and share CTA, after casual completion, archive/practice transitions, and after challenge comparison.
- Explicitly block ads during ranked preview, ranked gameplay, before submission, before result reveal, and before the first share CTA.
- Add conservative frequency caps and cooldowns.
- Track `ad_requested`, `ad_shown`, `ad_completed`, and `ad_failed_to_load`.
- Native QA with test ads on staging and production ad units only after store approval.

## 13. Social Challenge Final Mile

**Status:** In-app challenge loop is largely implemented; web landing, native deep link QA, and analytics are pending.

Steps to finish:

- Verify challenge create/share/open/play/compare/claim on staging with real Clerk accounts and guest users.
- Confirm daily eligibility behavior when the recipient has already used the daily attempt.
- Confirm guest result claim after sign-up does not duplicate or overwrite non-conflicting ranked attempts.
- Add challenge funnel analytics: opened, CTA clicked, started, completed, compared, claimed.
- Complete web landing and universal/app links from Task 6.
- Add native E2E QA for share sheets and incoming links on iOS and Android.

## 14. Practice, Archive, and Ghost Rank QA

**Status:** MVP exit criteria are marked complete in the updated epic plan; launch QA remains.

Steps to finish:

- Verify archive list only exposes closed/past-window dailies.
- Verify upcoming calendar shows difficulty only and never puzzle content.
- Verify archive replay does not create ranked attempts, mutate rating, or alter historical leaderboards.
- Verify ghost rank is clearly labeled unofficial.
- Verify the user's original historical result appears when available.
- Decide whether persisted practice attempts are required for MVP. Current plan treats them as optional and not a launch blocker.

## 15. Gameplay, Accessibility, and Device QA

**Status:** Core gameplay exists; final native/manual QA and screenshots are pending.

Steps to finish:

- Run casual, ranked, archive replay, failed attempt, completed board, hints, notes, auto-fill notes, undo, mistake limit, and auto-submit flows on iOS and Android.
- Verify touch targets, focus states, color-blind-safe conflict cues, timer readability, pencil marks, and high-contrast states.
- Verify ranked rules under app backgrounding, app kill/reopen, network failure, slow API, and daily reset.
- Add or update dev screens/Storybook equivalents for major board states if missing.
- Add Playwright or screenshot coverage for Today, board, result, leaderboard, archive, and social challenge states.

## 16. CI/CD and Quality Gates

**Status:** CI exists for Node lint/typecheck/unit tests and API ruff/pytest. Playwright and deploy automation are missing.

Steps to finish:

- Add Playwright config and CI job for Expo Web/dev screens.
- Add mobile UI screenshots for core MVP states.
- Add staging deploy workflow or documented Render auto-deploy/promotion process.
- Add post-deploy smoke tests for API health, admin health, and a minimal ranked flow where practical.
- Add branch protection requiring CI before merge.
- Decide whether EAS builds should run from CI for preview/release branches.
- Keep production deploy manual or protected by tag/promotion until launch process is stable.

## 17. Legal, Privacy, and Support

**Status:** Missing for launch.

Steps to finish:

- Draft and publish Privacy Policy, Terms of Service, competitive/community rules, and support policy.
- Create support email, for example `support@sudoke.app`.
- Link legal/support pages from the mobile app, app store listings, and public web landing.
- Replace any placeholder legal URLs in the mobile app with the real hosted Privacy Policy and Terms URLs.
- Add an in-app account deletion entry point in Profile/account settings.
- Implement account deletion request path in-app and via Clerk/API webhook.
- Document GDPR/ad consent behavior and analytics deletion behavior.
- Confirm no phone contact discovery or out-of-MVP personal data collection is introduced.

## 18. App Store / Play Store Readiness

**Status:** Not started.

Steps to finish:

- Create Apple Developer and Google Play Console app records.
- Prepare app name, subtitle/short description, long description, category, age rating, screenshots, privacy nutrition labels, data safety form, support URL, privacy URL, and marketing URL.
- Upload TestFlight and Play Internal Testing builds from EAS.
- Complete review notes explaining guest mode, account creation, ads, notifications, and support/deletion flows.
- Run release candidate QA on production-pointing builds before submission.
- Freeze production config and content schedule before submitting.

## 19. Final MVP Acceptance Audit

**Status:** Must happen after Tasks 2-18.

Steps to finish:

- Verify all Epic 10 launch gates are green.
- Confirm production has at least 90 scheduled daily puzzles.
- Confirm production cron has been stable for 7+ consecutive days.
- Confirm real Clerk auth, challenge links, push notifications, AdMob, PostHog, Sentry, legal pages, admin auth, and account deletion all work in production-like builds.
- Confirm no dev bypasses, test secrets, test ad units, or staging URLs remain in production builds.
- Produce one release checklist with owner/date/status for each launch gate.

## Condensed Critical Path

1. Update docs to reflect live staging and missing production.
2. Harden staging auth/secrets/domains and run smoke tests.
3. Provision production Render stack and production secrets.
4. Build EAS preview/production profiles and native credentials.
5. Finish Clerk admin auth, webhooks, and account deletion.
6. Ship challenge web landing plus universal/app links.
7. Finish push, analytics, Sentry monitoring, and AdMob.
8. Load production puzzle schedule and run 7-day cron stability gate.
9. Complete legal/support/store assets.
10. Run final native QA and submit to app stores.
