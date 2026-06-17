*Version v0.2 - Consolidated MVP PRD with Expert Review Decisions*

Includes Agentic Development Visibility Strategy

| Status           | MVP product requirements draft                         |
|------------------|--------------------------------------------------------|
| Primary platform | iOS and Android mobile app                             |
| Product focus    | Competitive daily Sudoku with social challenge sharing |
| Backend strategy | Render Cloud first; AWS only if needed later           |

# Contents

- 1\. Product Summary

- 2\. Goals and Success Metrics

- 3\. MVP Scope

- 4\. User Types

- 5\. Onboarding

- 6\. Core App Navigation

- 7\. Daily Ranked Puzzle

- 8\. Ranked Gameplay Ruleset - Expert Reviewed

- 9\. Casual / Practice Rules

- 10\. Puzzle Calendar and Difficulty

- 11\. Ranked Puzzle Fairness - Expert Reviewed

- 12\. Archive and Ghost Rank

- 13\. Gameplay UX

- 14\. Rating System

- 15\. Leaderboards

- 16\. Social and Challenges

- 17\. Post-Game Flow

- 18\. Streaks

- 19\. Notifications

- 20\. Monetization

- 21\. Admin Panel

- 22\. Puzzle Source and Licensing

- 23\. Technical Stack

- 24\. Agentic Development Visibility Strategy

- 25\. Ranked Attempt Lifecycle

- 26\. Elite Solve / Anti-Cheat Thresholds

- 27\. Database Entities

- 28\. API Contract

- 29\. Analytics

- 30\. Legal / Privacy / Compliance

- 31\. Release Plan

- 32\. Risks and Mitigation

- 33\. Non-Goals

- 34\. MVP Acceptance Criteria

- 35\. Soft Launch Success Criteria

- 36\. Remaining Future Analysis Areas

Version: v0.2 - Consolidated MVP PRD with Expert Review Decisions

Status: MVP product requirements draft

Primary platform: iOS and Android mobile app

Primary product focus: Competitive daily Sudoku with social challenge sharing

Primary backend strategy: Render Cloud first; AWS only if needed later

# 1. Product Summary

## 1.1 Product Vision

Build a mobile Sudoku app where players can compete seriously through a daily ranked puzzle while also challenging friends and family to beat their time.

The app should feel less like a generic Sudoku app with a leaderboard added on, and more like a competitive Sudoku product built around daily habit, skill rating, and social rivalry.

Reference product analogy:

- Chess.com-style competitive rating

- Wordle-style social sharing

- Polished mobile Sudoku controls

## 1.2 Core Player Fantasy

Primary fantasy:

- I want to prove I am faster/better than others at Sudoku.

Secondary fantasy:

- I want to share a puzzle with friends and family and see how we rank against each other.

The app should prioritize competitive credibility while making the social loop easy, personal, and low-friction.

## 1.3 Core MVP Loop

1.  User opens the app.

2.  User sees today's global Daily Ranked Puzzle.

3.  User sees difficulty and estimated solve-time range.

4.  User previews the puzzle.

5.  User starts one official ranked attempt.

6.  User solves as fast as possible under the ranked ruleset.

7.  Backend validates the attempt and records official time.

8.  User sees result, rank, percentile, and provisional rating movement.

9.  User is prompted to challenge friends/family.

10. Friend opens challenge link, installs/opens app, and plays as guest.

11. Friend signs up after result to claim/save/share/rank.

12. Both users return for future Daily Ranked Puzzles.

# 2. Goals and Success Metrics

## 2.1 Product Goals

The MVP should validate:

- whether users return for a Daily Ranked Sudoku habit,

- whether competitive ranking increases retention,

- whether social challenge links bring in new users,

- whether users care about friends/family comparison,

- whether free-with-ads monetization can work without damaging the ranked loop.

## 2.2 North-Star Metric

Weekly active users who complete at least one ranked puzzle and/or challenge another user.

This captures both:

- retention: users return and complete ranked puzzles,

- growth: users share challenges and invite others.

## 2.3 Primary Supporting Metrics

The MVP should track:

- D1 retention,

- D7 retention,

- weekly active users,

- Daily Ranked Puzzle start rate,

- Daily Ranked Puzzle completion rate,

- ranked completion-to-share rate,

- challenge links sent per active user,

- challenge link open rate,

- challenge install/open-app conversion,

- guest challenge completion rate,

- guest-to-account conversion rate,

- friend/family leaderboard engagement,

- repeat daily ranked participation.

# 3. MVP Scope

## 3.1 Included in MVP

The MVP includes:

- mobile app for iOS and Android,

- guest-first onboarding,

- account creation/login,

- user profiles,

- one global Daily Ranked Puzzle per day,

- one rating-eligible attempt per user per Daily Ranked Puzzle,

- capped optional preview before ranked attempt,

- notes/pencil marks in ranked mode,

- 3-mistake ranked system,

- no hints in ranked mode,

- no Auto-Fill Notes in ranked mode,

- server-owned ranked attempt lifecycle,

- provisional and final rating updates,

- one global competitive rating,

- daily leaderboard,

- nearby-my-rank leaderboard view,

- friends/family leaderboard view,

- global top leaderboard view,

- social challenge links,

- guest challenge play,

- guest result claim after signup,

- basic friends list,

- username search,

- profile/invite links,

- archived daily puzzles as non-ranked practice,

- ghost rank for archived puzzles,

- streaks with Streak Freezes,

- free-with-ads monetization,

- basic admin panel,

- puzzle import/review/scheduling,

- analytics instrumentation,

- privacy/legal foundation,

- agentic development visibility proxies.

## 3.2 Excluded From MVP

The MVP does not include:

- real-time multiplayer,

- live head-to-head races,

- persistent private groups/mini-leagues,

- phone contact discovery,

- chat,

- social feeds,

- custom puzzle editor,

- advanced coaching/training mode,

- tournament mode,

- multiple daily ranked puzzles,

- Expert ranked ladder,

- separate ratings by difficulty/mode,

- advanced anti-cheat case management,

- full playable web Sudoku,

- offline ranked mode,

- complex admin role hierarchy,

- manual rating edits,

- manual leaderboard moderation UI,

- emergency active-puzzle replacement UI,

- paid competitive advantages,

- deep cosmetic economy,

- haptics/sounds in MVP.

# 4. User Types

## 4.1 Guest User

A guest can:

- try a casual/sample puzzle,

- open a shared challenge link,

- play a challenge puzzle,

- see their result against the challenger.

A guest cannot:

- submit an official Daily Ranked result,

- receive rating,

- appear permanently on leaderboards,

- save ranked history,

- claim challenge results permanently,

- share official ranked results.

## 4.2 Registered User

A registered user can:

- play Daily Ranked Puzzle,

- receive rating,

- appear on leaderboards,

- build streaks,

- share challenge links,

- add friends,

- view profile/stats,

- claim guest results.

## 4.3 Admin User

An admin can access the internal admin dashboard.

Admin can:

- import puzzles,

- review puzzles,

- playtest puzzles,

- approve/reject puzzles,

- bulk schedule puzzles,

- view scheduled puzzle table,

- view basic user/result data.

Admin cannot in MVP:

- directly edit ratings,

- manually change leaderboard placement,

- manually hide/restore results through UI,

- replace active daily puzzle through UI.

# 5. Onboarding

## 5.1 Guest-First Onboarding

The app should not force signup before gameplay.

A new user can:

- open the app,

- start a casual/sample puzzle,

- understand the controls,

- experience timer/results,

- see the ranked/social concept.

Account creation is required before:

- submitting Daily Ranked Puzzle attempt,

- receiving rating,

- appearing on leaderboards,

- saving ranked history,

- sharing official results,

- participating in permanent friend/family comparison,

- claiming challenge-link results permanently.

## 5.2 Shared Challenge Link Onboarding

When a user opens a shared challenge link, the app should show a lightweight challenge landing card.

Example:

- Peter challenged you to beat his Sudoku time: 04:38.

Primary CTA:

- Play in the app

Flow:

13. Recipient opens shared link.

14. If app installed, app opens directly into challenge.

15. If app not installed, lightweight web challenge card appears.

16. User installs/opens app.

17. App preserves challenge context where possible.

18. User plays as guest.

19. User sees result.

20. User is prompted to sign up to claim/save/share/rank.

MVP does not include playable web Sudoku.

# 6. Core App Navigation

The app should use five main tabs.

## 6.1 Today

Main home tab.

Includes:

- Daily Ranked Puzzle,

- difficulty,

- estimated solve-time range,

- countdown to global reset,

- preview/start ranked attempt,

- ranked status,

- post-completion result card,

- share/challenge CTA,

- final ranking notification.

## 6.2 Play

Casual/practice area.

Includes:

- practice puzzles,

- archive puzzles,

- replay completed puzzles,

- hints where allowed,

- non-ranked modes.

## 6.3 Leaderboard

Competitive comparison area.

Includes:

- Daily leaderboard,

- nearby-my-rank view,

- friends/family leaderboard,

- global top view,

- historical results.

## 6.4 Social

Social/challenge area.

Includes:

- active challenges,

- received challenges,

- sent challenges,

- friends list,

- username search,

- invite/profile links.

## 6.5 Profile

User identity and stats area.

Includes:

- username,

- display name,

- avatar,

- current rating,

- rating tier,

- rating history,

- streaks,

- stats,

- settings,

- notification preferences,

- account management.

# 7. Daily Ranked Puzzle

## 7.1 Global Daily Puzzle

The app uses one global Daily Ranked Puzzle for all players.

The puzzle resets at one fixed global time, such as 00:00 UTC.

Users see the countdown in local time.

Each Daily Ranked Puzzle has:

- one puzzle ID,

- one global start time,

- one global end time,

- one global ranked cohort,

- one global leaderboard,

- one final rating calculation window.

## 7.2 One Ranked Attempt

Each registered user gets one rating-eligible attempt per Daily Ranked Puzzle.

The ranked attempt begins only when:

- the user taps Begin, or

- the user remains actively on the preview screen and the preview timer expires.

Once started:

- the attempt is consumed,

- timer starts,

- user cannot restart for rating,

- later attempts are practice-only.

## 7.3 Preview Flow

Before ranked start, user can preview the actual puzzle grid.

Preview rules:

- optional,

- capped at N seconds, initially 30 seconds,

- user may tap Begin at any time,

- no entries allowed,

- no notes allowed,

- no hints,

- timer has not started,

- exiting preview before Begin does not consume attempt,

- auto-start only occurs if user remains actively present on preview screen.

## 7.4 Ranked Pause / Resume

Ranked mode has no true pause.

If user backgrounds app, locks phone, receives call, or switches apps:

- board may hide/blur,

- official timer continues,

- user can resume,

- elapsed time includes interruption.

Auto-forfeit occurs only after long timeout, such as:

- global daily reset,

- or several-hour safety timeout.

## 7.5 Abandon / Failure

User may manually abandon ranked attempt.

Abandoning:

- consumes daily ranked attempt,

- counts as failed/no-completion,

- does not create official solve time,

- does not appear as public leaderboard completion,

- does not directly penalize rating in MVP,

- may affect streak/completion stats.

# 8. Ranked Gameplay Ruleset - Expert Reviewed

## 8.1 Mistake System

Daily Ranked Puzzle uses a Lives / Strikes mistake model.

Rules:

- Wrong final answers are detected immediately.

- Each wrong final entry counts as one mistake.

- The player is allowed 3 mistakes.

- The 4th mistake fails the ranked attempt.

- Failed attempts consume the player's one rating-eligible attempt for that daily puzzle.

- Failed attempts do not directly create a rating penalty in MVP.

- Failed attempts may affect completion rate and streak status.

## 8.2 Wrong Entry Display

When a player enters an incorrect final number:

- the wrong number remains visible on the board,

- the cell is visually marked as incorrect,

- the mistake counter increases by 1,

- the player can erase or replace the entry,

- the ranked timer continues.

The app should not reveal the correct answer after a wrong entry.

## 8.3 Repeated Wrong Entries

Mistakes are counted by wrong final-entry action, not by unique wrong cell/value pair.

If a player enters a wrong number, deletes it, and later enters the same wrong number again, that counts as another mistake.

If the cell already contains wrong red 7 and the player taps 7 again without changing the value, that tap is a no-op and should not count as another mistake.

## 8.4 Notes and Mistake Counting

Only wrong final answers count as mistakes.

The app does not penalize:

- wrong notes,

- unnecessary notes,

- missing notes,

- candidate marks that later become impossible,

- messy note-taking.

## 8.5 Mistake Counter Visibility

The ranked puzzle UI should show the mistake counter during play.

Example:

- Mistakes: 1/3

After the player makes the 3rd mistake, the UI should show a non-blocking warning.

Example:

- Final mistake - one more wrong answer ends this run.

The warning should not pause the timer, block gameplay, or reveal solution information.

## 8.6 Conflict / Duplicate Highlighting

Conflict and duplicate highlighting is allowed in ranked mode.

If the player creates a duplicate number in the same row, column, or 3x3 box, the conflicting cells should be visually highlighted.

Because ranked mode already uses immediate wrong-answer detection and a 3-mistake limit, duplicate-conflict highlighting is treated as readability rather than prohibited assistance.

## 8.7 Duplicate Conflict vs Cell Correctness

The app should validate each final entry against the solution for that specific cell.

A correct entry should not count as a mistake merely because another wrong entry elsewhere creates a duplicate conflict.

Example:

- Cell A incorrectly contains 5.

- Cell B correctly should be 5.

- Player enters 5 in Cell B.

- Cell B is treated as correct and does not count as a mistake.

- Duplicate conflict may still be visually highlighted.

- Cell A remains marked wrong until corrected.

## 8.8 Correct Entry Locking

The app should not allow players to remove or replace correct final entries once entered.

When a player enters a correct final number:

- the entry is accepted,

- the cell becomes locked,

- the player cannot erase it,

- the player cannot replace it,

- the entry remains part of the board for the rest of the attempt.

Incorrect final entries remain editable.

## 8.9 Undo Behavior Update

Undo is allowed in ranked mode, but it cannot remove or replace a correct locked final entry.

Undo can revert:

- wrong final entries,

- notes,

- note clearing,

- manual candidate changes,

- non-final editing actions.

Undo cannot revert:

- correct final answers once locked,

- submitted attempts,

- failed attempts,

- server-owned ranked state,

- official timer state.

## 8.10 Correct Entry Visual Confirmation

Correct player-entered final answers should receive subtle visual confirmation when accepted and locked.

Possible treatments:

- slight color change,

- subtle pop/settle animation,

- brief highlight,

- lock/progress styling.

This confirmation is not configurable in MVP.

## 8.11 Givens vs Player-Entered Locked Numbers

Given puzzle numbers should be visually distinct from player-entered locked correct numbers.

Both are locked, but givens should appear as original puzzle clues while player-entered correct numbers should appear as solved progress.

## 8.12 Wrong Entry Replacement

Wrong final entries may be replaced directly.

If a cell contains an incorrect final entry, the player may tap another number to replace it without erasing first.

Replacement validation:

- if the replacement is correct, the cell locks,

- if the replacement is wrong, the mistake counter increases again,

- if the replacement reaches the mistake limit, the ranked attempt fails.

## 8.13 Final Answer Input Confirmation

Final answers should not require an extra confirmation step.

In number-first mode:

- player selects a number,

- taps a target cell,

- final answer is entered immediately.

In cell-first mode:

- player selects a cell,

- taps a number,

- final answer is entered immediately.

## 8.14 Auto-Submit

Ranked puzzles should auto-submit immediately when the board is fully completed and ready for validation.

There is no manual Submit button in ranked mode.

Auto-submit occurs only when:

- the board is full,

- there are zero visible wrong entries.

If visible wrong entries remain, the attempt does not submit and the timer continues until corrected.

## 8.15 Notes / Pencil Marks

Manual notes are allowed in ranked mode.

The app should use a visible Notes / Pencil Mode toggle.

Default mode:

- tap cell,

- tap number,

- number enters as final answer.

Notes mode:

- toggle Notes,

- tap cell,

- tap numbers,

- numbers enter as candidates.

## 8.16 Notes in Final-Answer Cells

The app should not allow players to place notes in a cell that already has a final answer.

If a cell contains a final answer:

- the player cannot add notes,

- the player cannot edit notes,

- the cell behaves as a final-answer cell.

## 8.17 Conflicting Notes

If Auto-Clear Notes is off, the player may manually add any note candidate to an empty cell, even if that candidate conflicts with a locked correct number in the same row, column, or 3x3 box.

Conflicting notes do not count as mistakes.

## 8.18 Auto-Clear Notes

Auto-Clear Notes is implemented and allowed in both casual and ranked modes.

Default setting: ON.

Player may turn it off globally in settings.

Auto-Clear Notes behavior:

- after a correct final entry is accepted and locked, remove that same candidate from relevant notes in the same row, column, and 3x3 box,

- do not run Auto-Clear from incorrect entries,

- do not clear unrelated candidates.

Auto-Clear is value-specific.

Example:

- Cell has notes 2, 4, 7.

- Player enters correct final 4.

- Candidate 4 is removed/covered by final placement logic.

- Candidates 2 and 7 are not wiped as part of a generic clear-all-notes action.

## 8.19 Auto-Fill Notes

Auto-Fill Notes is disabled in ranked mode.

Auto-Fill Notes may be available as a toggleable casual/practice feature.

Auto-Fill Notes is closer to assisted solving because it generates candidate information across the board.

## 8.20 Completed Number Pad State

The app should automatically indicate when a number is complete.

If all nine instances of a number have been correctly placed:

- the number-pad button becomes visually disabled, greyed out, or marked complete,

- the player cannot enter that number into additional cells.

A number is marked complete only when all nine placements are correct.

The app should not show remaining count per number in MVP.

Disallowed examples:

- 5 - 2 left

- 3 remaining

- only 1 left

## 8.21 Candidate Highlighting

Candidate highlighting is allowed in ranked mode.

When the player selects a number, the app may highlight:

- placed instances of that number,

- cells containing that number as a visible note/candidate.

Candidate highlighting applies to whatever notes are currently visible in that mode.

Ranked mode has no Auto-Fill Notes, so this applies to user-entered notes.

## 8.22 Disallowed Ranked Assistance

The following are not allowed in ranked mode:

- Auto-Fill Notes,

- hints,

- solution reveal,

- single-candidate highlighting,

- legal placement highlighting,

- highlighting all empty cells where a selected number could legally go,

- final-answer number painting.

## 8.23 Number Painting / Rapid Fill

Number painting / rapid-fill is allowed only for notes, not final answers.

Allowed:

- player enables Notes Mode,

- selects 5,

- taps multiple cells,

- candidate 5 is added/toggled in those cells.

Disallowed:

- rapidly painting final answers across multiple cells.

# 9. Casual / Practice Rules

Casual and practice modes use the 3-mistake system by default, but allow player adjustment.

Adjustable casual/practice settings may include:

- mistake checking on/off,

- mistake limit,

- unlimited mistakes,

- hints on/off,

- Auto-Fill Notes on/off.

Ranked rules remain fixed.

# 10. Puzzle Calendar and Difficulty

## 10.1 Difficulty Bands

MVP uses four difficulty bands:

21. Easy

22. Medium

23. Hard

24. Expert

Expert exists as a flagged future band and is not part of the default MVP daily ranked loop.

## 10.2 MVP Weekly Rotation

Launch rotation:

- Monday: Easy

- Tuesday: Medium

- Wednesday: Medium

- Thursday: Hard

- Friday: Medium

- Saturday: Hard

- Sunday: Hard

Expert/Special Sunday is post-MVP.

The rotation should be configurable by backend/admin config, not hard-coded in the client.

## 10.3 Difficulty Visibility

The app shows today's difficulty before the user starts ranked attempt.

Example:

- Today's Ranked Puzzle: Medium

## 10.4 Estimated Solve-Time Range

The app shows a broad estimated solve-time range.

Example:

- Medium - typical solve: 6-12 min

This appears on:

- Today screen,

- pre-start screen,

- shared challenge landing card where relevant.

## 10.5 Upcoming Difficulty Calendar

Users can see upcoming difficulty bands, but not actual puzzles.

Allowed:

- Today: Medium

- Tomorrow: Hard

- Sunday: Hard

Restricted before puzzle activation:

- grid,

- givens,

- solution,

- exploitable puzzle ID,

- metadata that leaks puzzle.

## 10.6 Pre-Launch Inventory

Before public launch, team must prepare at least 90 approved Daily Ranked Puzzles.

Each puzzle must have:

- puzzle grid,

- solution grid,

- difficulty band,

- estimated solve-time range,

- source/license metadata,

- unique solution validation,

- admin review,

- approval,

- scheduled date.

# 11. Ranked Puzzle Fairness - Expert Reviewed

## 11.1 Speed-Friendly Human Solving

For MVP, Daily Ranked Puzzles should favor clean, human-solvable, speed-friendly logic.

The team should reject puzzles that are technically valid but poorly suited for ranked speed competition.

Reject or avoid puzzles that are:

- overly grindy,

- dependent on obscure solving techniques,

- likely to create extreme frustration,

- poorly suited for speed-solving,

- too bifurcation-heavy,

- too guess-like for normal human solving,

- valid but not enjoyable competitively.

## 11.2 No Guessing / Backtracking

MVP Daily Ranked Puzzles should be solvable without guessing or backtracking.

Players should not need to:

- guess,

- brute force,

- bifurcate,

- use trial-and-error,

- rely on backtracking.

## 11.3 Solve Path Documentation

Daily Ranked Puzzles do not need a documented intended solve path or technique profile in MVP.

Admin review should confirm:

- valid puzzle,

- unique solution,

- human-solvable,

- solvable without guessing/backtracking,

- appropriate difficulty band,

- suitable for ranked speed play.

Full solve-path documentation is post-MVP.

## 11.4 Expert Puzzle Handling

Expert puzzles are excluded from MVP Daily Ranked mode.

For MVP, Expert puzzles may exist only as non-ranked practice/archive content.

Expert puzzles should not appear as:

- Daily Ranked Puzzles,

- rating-eligible puzzles,

- default Sunday ranked puzzles,

- main leaderboard-driving puzzles.

Allowed MVP use:

- non-ranked practice puzzles,

- optional archive/practice content,

- casual challenge content,

- internal test content.

# 12. Archive and Ghost Rank

## 12.1 Archive

After a Daily Ranked Puzzle closes, it becomes available in archive.

Archive attempts are:

- practice-only,

- non-ranked,

- not rating-eligible,

- not modifying historical leaderboard.

## 12.2 Historical Leaderboard

Archived Daily Ranked Puzzles preserve original leaderboard as read-only.

Users can see:

- original date,

- original difficulty,

- original global leaderboard,

- their original result if they played,

- final rating impact,

- friends/family original results.

## 12.3 Ghost Rank

If a user missed a Daily Ranked Puzzle, they can play it later from archive and see unofficial ghost rank.

Example:

- You would have ranked \#842 globally on May 12.

Ghost rank:

- does not affect rating,

- does not alter historical leaderboard,

- is clearly marked unofficial.

# 13. Gameplay UX

## 13.1 Input Modes

MVP supports both:

- cell-first input,

- number-first input.

Players can switch easily.

## 13.2 Timer

Ranked timer is visible by default but hideable during play.

Hiding timer:

- only changes UI,

- does not pause timer,

- does not affect official time.

## 13.3 Highlighting

Allowed in ranked:

- matching number highlighting,

- candidate highlighting,

- selected row/column/box highlighting,

- duplicate/conflict highlighting,

- wrong final-entry highlighting.

Not allowed in ranked:

- legal placement highlighting,

- single-candidate highlighting,

- next-move assistance.

## 13.4 Haptics and Sound

Excluded from MVP.

Post-MVP optional/toggleable feature.

## 13.5 Theme

Support light and dark mode only if cheap through design system.

If not cheap:

- launch with one excellent light theme,

- add dark mode post-MVP.

Design with theme tokens from beginning.

## 13.6 Accessibility

MVP should support:

- large tap targets,

- high contrast,

- readable pencil marks,

- color-blind-safe highlights,

- conflicts not relying only on color,

- clear focus state,

- accessible labels for major controls,

- reduced clutter during ranked attempts.

Accessibility features that improve readability/input clarity should not affect rating eligibility.

# 14. Rating System

## 14.1 Product-Facing Rating

Use product-facing terms:

- Rating

- Competitive Rating

- Ranked Rating

Avoid strict ELO language unless later implementation justifies it.

## 14.2 MVP Rating Philosophy

The system is Elo-like but cohort-based.

A player's rating changes based on:

- current rating,

- percentile finish within same ranked puzzle cohort,

- puzzle difficulty,

- cohort size,

- provisional status,

- movement caps.

Plain English:

- Your rating goes up if you perform better than expected for your rating.

- Your rating goes down if you perform worse than expected.

## 14.3 Rating Cohort

Only valid completed ranked attempts count for rating.

Excluded:

- abandoned attempts,

- timed-out attempts,

- invalid submissions,

- under-review attempts,

- hidden suspicious attempts,

- archive attempts,

- social-only challenge attempts.

Started-but-not-completed attempts still count for:

- completion rate,

- abandon stats,

- timeout stats,

- streak status,

- analytics.

## 14.4 Percentile Metric

Rating uses continuous percentile within daily cohort.

Example:

- If player finishes faster than 82% of valid completed players, performance percentile is 82.

UI may show friendly bands:

- Top 1%

- Top 5%

- Top 10%

- Top 25%

- Top 50%

Internal system uses continuous percentile.

## 14.5 Starting Rating and Floor

All users start at rating 1000.

Minimum rating is 100.

## 14.6 Provisional Rating

First 10 valid ranked completions are provisional.

During provisional period:

- rating is visible,

- label shows Provisional,

- movement can be larger,

- player placement adjusts faster.

Example:

- Provisional Rating - 6/10 placement puzzles completed

## 14.7 Rating Movement Caps

Provisional players:

- max gain: +80

- max loss: -80

Normal players:

- max gain: +35

- max loss: -35

## 14.8 Difficulty Multiplier

Suggested MVP multiplier:

- Easy: 0.85x

- Medium: 1.0x

- Hard: 1.1x

- Expert: pending future review

## 14.9 Small Cohort Dampening

Suggested thresholds:

- fewer than 10 valid completions: no/minimal movement,

- 10-49 completions: reduced movement,

- 50+ completions: normal movement.

## 14.10 Provisional vs Final Rating

Immediately after completion:

- show projected/provisional rating movement.

After daily close:

- calculate final rank,

- final percentile,

- final rating delta.

## 14.11 No Inactivity Decay

MVP has no rating decay.

## 14.12 Rating Tiers

Cosmetic tiers:

- Bronze: 100-799

- Silver: 800-999

- Gold: 1000-1199

- Platinum: 1200-1499

- Diamond: 1500-1799

- Master: 1800+

Tiers do not create separate rating pools.

## 14.13 Formula Versioning

Every rating update stores calculation_version.

## 14.14 Completion vs Rating

Valid completion does not guarantee rating gain.

Completion is rewarded through:

- streak,

- Streak Freeze progress,

- stats,

- sharing,

- result card,

- leaderboard comparison.

Rating remains a competitive skill signal, not XP.

## 14.15 Post-MVP Rating Flags

Post-MVP analysis:

- Top 1/3/10 bonuses,

- Expert-specific handling,

- separate ladders,

- advanced cohort models,

- TrueSkill/OpenSkill-like systems.

# 15. Leaderboards

## 15.1 Daily Leaderboard Views

MVP supports:

- nearby-my-rank,

- friends/family,

- global top,

- historical read-only leaderboard.

## 15.2 Default View Logic

After completion, leaderboard preview defaults to most emotionally relevant view.

Logic:

25. If user came from friend/family challenge: show friends/family first.

26. If friends/family have completed puzzle: show friends/family first.

27. Otherwise show nearby-my-rank.

28. Global top is available but not default for most users.

## 15.3 Failed Attempts Visibility

Failed/no-completion attempts are tracked privately but not publicly shamed.

Private stats may show:

- started attempts,

- completed attempts,

- completion rate,

- no-completion count,

- abandoned attempts,

- timeout attempts.

Public leaderboard does not show failed users as failures.

# 16. Social and Challenges

## 16.1 Social Model

MVP social model includes:

- friends list,

- username search,

- profile/invite links,

- shared challenge links,

- challenge-specific leaderboards,

- friends/family leaderboard filter.

Post-MVP:

- phone contacts,

- private groups,

- mini-leagues,

- group streaks,

- group notifications.

## 16.2 Challenge Link Types

Challenge links can share:

29. Daily Ranked Puzzle

30. Non-daily/archive/casual puzzle

If shared puzzle is active Daily Ranked Puzzle:

- recipients can still be rating-eligible if they have not consumed attempt and daily window is active.

If shared puzzle is not active Daily Ranked Puzzle:

- social-only,

- no rating impact.

## 16.3 Friend Discovery

MVP supports:

- username search,

- profile links,

- challenge links.

Phone contacts are post-MVP.

## 16.4 Private Groups

Persistent private groups are post-MVP.

Future group examples:

- family group,

- office league,

- friend league,

- weekly group ranking,

- group streaks,

- group challenge history.

# 17. Post-Game Flow

After Daily Ranked Puzzle completion, user lands on results-first screen.

Flow:

31. Completion animation

32. Official solve time

33. Personal result card

34. Rank / percentile / rating impact

35. Main CTA: Challenge friends/family

36. Leaderboard preview

37. Optional ad placement

38. Replay / practice / next puzzle actions

Ads must not block:

- result reveal,

- first share CTA.

Product rationale:

- results create dopamine,

- sharing creates acquisition,

- leaderboard creates competition,

- ads come after value.

# 18. Streaks

## 18.1 Streak Rule

Completing active Daily Ranked Puzzle during official global window extends streak.

Streak timing follows global daily reset, not local midnight.

UI must show local countdown:

- Today's puzzle ends in 5h 12m.

## 18.2 Streak Freezes

Players can hold up to 2 Streak Freezes.

If player misses a day:

- one freeze is automatically consumed,

- streak number preserved,

- missed day marked frozen/protected,

- no ranked completion granted,

- no rating effect,

- no leaderboard effect.

## 18.3 Replenishment

Earn 1 Streak Freeze after every 7 completed Daily Ranked Puzzles.

Rules:

- max 2 freezes,

- only official Daily Ranked completions count,

- archive/practice/social-only puzzles do not count,

- no purchase,

- no ads for freezes in MVP.

# 19. Notifications

Notifications are requested only after meaningful action, not during initial onboarding.

Good permission moments:

- after first Daily Ranked completion,

- after first challenge share,

- after accepting/receiving challenge,

- after final ranking ready moment.

MVP notification types:

- daily puzzle reminder,

- friend challenged you,

- someone beat your time,

- final ranking ready.

# 20. Monetization

## 20.1 Model

MVP monetization is free with ads.

The app should maximize access to:

- Daily Ranked Puzzle,

- practice puzzles,

- archive puzzles,

- challenge links,

- casual modes.

## 20.2 Ad Network

Use Google AdMob as default MVP ad network.

## 20.3 Allowed Placements

Allowed:

- after ranked result and share CTA,

- after casual/practice completion,

- before/after archive/practice content where non-disruptive,

- after challenge result comparison.

## 20.4 Disallowed Placements

Ads must not appear:

- during ranked gameplay,

- during ranked preview,

- before ranked submission,

- before first result reveal,

- before first share CTA,

- in ways affecting solve timing.

## 20.5 Rewarded Ads

Allowed only for casual/practice benefits.

Allowed examples:

- extra casual hints,

- optional practice puzzle packs,

- casual analysis,

- cosmetic themes.

Not allowed:

- ranked hints,

- ranked retries,

- extra ranked attempts,

- rating boosts,

- leaderboard boosts,

- streak freezes.

## 20.6 Frequency Caps

Conservative frequency caps required.

No interstitial:

- immediately after app open,

- before user completes meaningful action,

- during first-time ranked flow before value is understood.

# 21. Admin Panel

## 21.1 Architecture

Admin panel is part of same FastAPI/Render backend as a simple protected web dashboard.

MVP role model:

- normal user,

- admin.

## 21.2 MVP Admin Functions

Admin panel supports:

- CSV/JSON puzzle import,

- puzzle validation,

- source/license tracking,

- duplicate detection,

- puzzle preview/playtest,

- playtest result saving,

- approve/reject puzzle,

- bulk schedule approved puzzles,

- scheduled puzzle table/list,

- basic user lookup,

- basic attempt lookup,

- admin audit log.

## 21.3 Puzzle Import

Import requires:

- puzzle grid,

- solution grid,

- difficulty band,

- estimated solve-time range,

- source,

- license metadata,

- optional intended publish date.

Backend independently validates:

- grid format,

- solution correctness,

- unique solution,

- duplicate puzzle,

- required metadata.

## 21.4 Puzzle Approval

Imported puzzles require explicit admin approval before scheduling.

States:

- imported,

- needs_review,

- approved,

- scheduled,

- published,

- archived,

- rejected.

One admin approval required in MVP.

Store:

- reviewer ID,

- timestamp,

- notes,

- source/license data.

## 21.5 Scheduled Puzzles

MVP uses table/list view, not full calendar UI.

Fields:

- publish date,

- weekday,

- puzzle ID,

- difficulty,

- estimated solve-time range,

- status,

- reviewer,

- approval timestamp,

- source/license indicator,

- notes.

## 21.6 Not in MVP Admin

Excluded:

- editing already scheduled puzzles,

- emergency active-puzzle replacement UI,

- manual rating edits,

- manual leaderboard moderation workflow,

- complex role hierarchy,

- advanced analytics dashboards.

# 22. Puzzle Source and Licensing

MVP may use existing open puzzle archives only if license explicitly allows:

- commercial use,

- redistribution,

- modification,

- storage in app database,

- use in monetized mobile app.

Do not scrape random Sudoku websites.

Every puzzle must track:

- source name,

- source URL/reference,

- license type,

- commercial-use permission,

- redistribution permission,

- modification permission,

- import date,

- imported by,

- reviewed by,

- notes.

Puzzle cannot be approved without source/license metadata.

# 23. Technical Stack

## 23.1 Frontend

- Expo React Native

- TypeScript

- Expo Router

- TanStack Query

- Zustand

- React Hook Form + Zod

- MMKV / SecureStore

- Expo Notifications

- Sentry

## 23.2 Backend

- FastAPI

- Python

- PostgreSQL

- SQLAlchemy or SQLModel

- Alembic

- Redis-compatible cache/queue

- Background worker service

- Cron jobs

- Docker-based deployment

## 23.3 Deployment

Primary: Render Cloud

Render services:

- API web service,

- Postgres database,

- Redis/key-value instance,

- background worker,

- cron jobs.

AWS only if Render becomes insufficient.

Potential AWS future:

- ECS/Fargate or App Runner,

- RDS Postgres,

- ElastiCache,

- EventBridge,

- S3,

- CloudWatch/OpenTelemetry,

- SES/SNS/Pinpoint.

## 23.4 Auth

Use dedicated auth provider.

Recommended default:

- Clerk + FastAPI JWT validation

Alternative:

- Firebase Auth

Avoid custom auth for MVP.

## 23.5 Sudoku Core Package

Create shared package:

- packages/sudoku-core

Contains:

- puzzle representation,

- solution validation,

- puzzle validation,

- note rules,

- difficulty metadata,

- deterministic serialization,

- test fixtures.

Server remains final authority for ranked validation.

# 24. Agentic Development Visibility Strategy

Because Codex agents, Cursor agents, and similar coding agents often run in cloud or containerized environments that cannot reliably launch iOS/Android simulators, the project should provide non-native proxies that let agents inspect, test, and iterate on the app UI.

## 24.1 Primary Proxy: Expo Web / React Native Web

The primary proxy should be an Expo Web / React Native Web build running in a normal browser.

This gives agents a browser-visible version of the same screen structure, routing, layout, state, and most interaction flows.

Agents can use it to inspect and iterate on:

- Today screen,

- ranked preview/start flow,

- Sudoku board interactions,

- result screens,

- leaderboard states,

- challenge landing states,

- profile screens,

- admin-adjacent flows.

This does not replace native QA, but it gives agents a reliable browser-visible approximation of the mobile app.

## 24.2 Secondary Proxy: Component Preview Harness

The second proxy should be a component preview harness, such as Storybook or a lightweight internal /dev/screens route, with mocked app states.

Each major app state should be directly viewable:

- new user,

- guest challenge recipient,

- previewing ranked puzzle,

- in-progress ranked attempt,

- submitted result,

- final ranking ready,

- empty leaderboard,

- populated leaderboard,

- ad-eligible post-result state,

- error state,

- loading state.

The goal is to let agents and developers jump directly into important UI states without manually navigating through the app every time.

## 24.3 Browser-Based Automated Tests and Screenshots

The third proxy should be browser-based automated tests and screenshots.

Agents should be able to run Playwright against the web build at mobile viewport sizes, capture screenshots, and compare expected UI states.

This is not a full replacement for native QA, but it gives agents a reliable visual feedback loop.

Recommended test targets:

- Today screen loads correctly,

- ranked preview displays correct puzzle and timer state,

- Begin starts ranked flow,

- Sudoku board responds to cell-first and number-first input,

- notes mode behaves correctly,

- wrong entry state appears correctly,

- result screen renders correctly,

- leaderboard empty/populated states render correctly,

- challenge landing card preserves challenge context,

- profile/settings states render correctly.

## 24.4 Native-Only Validation Still Required

Native-only behavior still requires human/device validation or dedicated CI/device-farm testing.

This includes:

- Expo Notifications,

- AdMob behavior,

- deep links/app links,

- secure storage,

- native keyboard quirks,

- platform-specific gestures,

- app backgrounding,

- push permissions,

- real iOS/Android performance.

## 24.5 Product Rationale

The project should be built so coding agents can meaningfully inspect and improve UI without needing mobile simulators.

A browser-visible proxy increases agent productivity, shortens feedback loops, and reduces the risk of agents making blind UI changes.

Native QA remains mandatory before release, but day-to-day agentic development should not depend on simulator availability.

# 25. Ranked Attempt Lifecycle

## 25.1 Normal Path

not_started -\> previewing -\> started -\> in_progress -\> submitted -\> validated -\> provisional_ranked -\> finalized

## 25.2 Terminal / Exception States

- abandoned,

- timed_out,

- invalid,

- under_review,

- voided.

## 25.3 State Rules

Preview does not consume attempt.

Started consumes attempt.

Server owns:

- started_at,

- submitted_at,

- validated_at,

- finalized_at,

- abandoned_at,

- timed_out_at.

Official duration:

- submitted_at - started_at

Client timer is display-only.

## 25.4 Under Review

High-confidence suspicious results are hidden immediately.

User-facing message remains vague:

- Your result is under review and is not currently eligible for ranking.

Do not reveal detection rules.

# 26. Elite Solve / Anti-Cheat Thresholds

The MVP should use a hybrid anti-cheat threshold model.

## 26.1 MVP Approach

Use conservative absolute solve-time thresholds from day one, then add more data-driven anomaly detection as real completion data accumulates.

## 26.2 Absolute Thresholds

The app may define minimum plausible solve-time thresholds by difficulty band.

Example structure:

- Easy: below X seconds is suspicious

- Medium: below Y seconds is suspicious

- Hard: below Z seconds is suspicious

The exact thresholds should be set extremely conservatively to avoid false positives.

## 26.3 Data-Driven Thresholds

As the app collects real solve-time data, anti-cheat detection can incorporate:

- cohort solve-time distribution,

- user rating,

- user historical performance,

- solve-time percentile,

- repeated outlier behavior,

- app/device integrity signals,

- event sequence anomalies,

- suspiciously low interaction count,

- suspicious background/resume behavior.

## 26.4 False Positive Rule

Fast time alone should almost never be enough to punish a player unless it crosses an extreme impossibility threshold.

The system should require high confidence before hiding results.

## 26.5 MVP Behavior

If a result crosses a high-confidence suspicious threshold:

- hide it from public leaderboard,

- exclude it from provisional rating,

- show vague under-review message,

- allow later restoration through internal process if needed.

## 26.6 Product Rationale

The app must protect competitive integrity without punishing legitimate elite players.

Early thresholds should catch impossible cases, not merely impressive ones.

# 27. Database Entities

MVP database domains:

39. Users and profiles

40. Puzzle content

41. Daily scheduling

42. Ranked attempts

43. Leaderboards

44. Ratings

45. Streaks

46. Social/friends/challenges

47. Guest sessions

48. Archive/ghost ranks

49. Ads

50. Notifications

51. Analytics

52. Admin/audit/config

Core tables:

- users

- user_profiles

- puzzles

- puzzle_playtests

- daily_puzzles

- ranked_attempts

- ranked_attempt_events

- daily_leaderboard_entries

- user_ratings

- rating_history

- user_streak_events

- friendships

- challenge_links

- challenge_attempts

- guest_sessions

- archive_attempts

- ghost_rank_results, optional/deferred

- ad_events

- notification_preferences

- notification_events

- analytics_events

- admin_audit_log

- app_config

Post-MVP tables:

- private groups,

- group memberships,

- group leaderboards,

- phone contact matching,

- manual moderation cases,

- tournaments,

- separate ladders,

- advanced anti-cheat case management.

# 28. API Contract

API base path:

- /api/v1

## 28.1 User/Profile

- GET /me

- PATCH /me/profile

## 28.2 Daily Puzzle

- GET /daily/current

- POST /daily/{daily_puzzle_id}/preview

- POST /daily/{daily_puzzle_id}/start

## 28.3 Ranked Attempts

- GET /ranked-attempts/{attempt_id}

- POST /ranked-attempts/{attempt_id}/events

- POST /ranked-attempts/{attempt_id}/submit

- POST /ranked-attempts/{attempt_id}/abandon

## 28.4 Leaderboards

- GET /daily/{daily_puzzle_id}/leaderboard

- GET /daily/{daily_puzzle_id}/my-result

## 28.5 Challenges

- POST /challenges

- GET /challenges/{share_token}

- POST /challenges/{share_token}/start

- POST /challenge-attempts/{challenge_attempt_id}/submit

- POST /challenge-attempts/{challenge_attempt_id}/claim

## 28.6 Friends

- GET /friends

- GET /friends/search?username=...

- POST /friends/requests

- POST /friends/requests/{request_id}/accept

- POST /friends/requests/{request_id}/decline

- DELETE /friends/{friend_user_id}

## 28.7 Archive

- GET /archive

- GET /archive/{daily_puzzle_id}

- POST /archive/{daily_puzzle_id}/start

- POST /archive-attempts/{attempt_id}/submit

## 28.8 Notifications

- GET /notifications/preferences

- PATCH /notifications/preferences

- POST /notifications/register-device

## 28.9 Analytics

- POST /events

## 28.10 Admin

- POST /admin/puzzles/import

- GET /admin/puzzles

- GET /admin/puzzles/{puzzle_id}

- POST /admin/puzzles/{puzzle_id}/playtest

- POST /admin/puzzles/{puzzle_id}/approve

- POST /admin/puzzles/{puzzle_id}/reject

- POST /admin/daily-puzzles/bulk-schedule

- GET /admin/daily-puzzles

- GET /admin/users/{user_id}

- GET /admin/ranked-attempts/{attempt_id}

# 29. Analytics

## 29.1 Provider

Use PostHog for MVP.

## 29.2 Source of Truth

Postgres is source of truth.

PostHog is for analytics.

Store authoritative state in Postgres first:

- ranked lifecycle,

- solve times,

- validation,

- leaderboard entries,

- rating changes,

- streak events,

- challenge attempts,

- guest claims,

- ad events where needed.

## 29.3 Instrumentation Principle

Do not over-instrument every tap.

Do instrument major funnel transitions.

## 29.4 Required Event Coverage

Core lifecycle:

- app_opened

- signup_started

- signup_completed

- login_completed

Daily ranked:

- daily_puzzle_viewed

- ranked_preview_started

- ranked_preview_exited

- ranked_attempt_started

- ranked_attempt_submitted

- ranked_attempt_validated

- ranked_attempt_abandoned

- ranked_attempt_timed_out

- ranked_result_viewed

- final_rating_viewed

Social:

- result_shared

- challenge_link_opened

- challenge_landing_cta_clicked

- challenge_started

- challenge_completed

- guest_result_claimed

Leaderboards:

- leaderboard_viewed

- leaderboard_filter_changed

Streaks:

- streak_extended

- streak_freeze_earned

- streak_freeze_consumed

- streak_broken

Archive:

- archive_puzzle_viewed

- archive_attempt_started

- archive_attempt_completed

- ghost_rank_viewed

Ads:

- ad_requested

- ad_shown

- ad_completed

- ad_failed_to_load

## 29.5 Privacy

Do not send to third-party analytics:

- full submitted grids,

- full board histories,

- email addresses,

- private admin notes,

- raw device identifiers.

Use internal IDs:

- user_id,

- guest_session_id,

- daily_puzzle_id,

- ranked_attempt_id,

- challenge_link_id.

# 30. Legal / Privacy / Compliance

Before launch, app must have:

- Privacy Policy,

- Terms of Service,

- basic community/competitive rules,

- support/contact email,

- account deletion path,

- GDPR-aware consent,

- ad consent handling,

- no phone contacts in MVP,

- no unnecessary sensitive data,

- no full Sudoku grids to third-party analytics.

## 30.1 Account Deletion

User can delete account.

Historical leaderboard records may remain anonymized as:

- Deleted Player

This preserves leaderboard integrity.

## 30.2 Children

MVP is not child-targeted.

Avoid:

- child-directed marketing,

- school/children positioning,

- collecting age-sensitive data unnecessarily.

## 30.3 Public Leaderboard Privacy

Public leaderboard may show:

- username/display name,

- avatar,

- rating/tier,

- solve time,

- rank/percentile.

Do not show:

- email,

- raw real name unless chosen,

- precise location,

- device data,

- private metadata.

# 31. Release Plan

## 31.1 Milestone 1 - Gameplay Prototype

Includes:

- Sudoku board,

- input modes,

- notes,

- undo,

- highlighting,

- timer,

- completion.

## 31.2 Milestone 2 - Ranked Alpha

Includes:

- accounts,

- Today screen,

- global Daily Ranked Puzzle,

- preview/start,

- backend attempt lifecycle,

- basic leaderboard,

- provisional result.

## 31.3 Milestone 3 - Content Ops/Admin Alpha

Includes:

- puzzle import,

- validation,

- source/license,

- playtest,

- approval,

- bulk scheduling,

- 90-day inventory.

## 31.4 Milestone 4 - Social Beta

Includes:

- challenge links,

- app open/install landing,

- guest challenge,

- result comparison,

- guest claim,

- username search,

- friends.

## 31.5 Milestone 5 - Rating Beta

Includes:

- global rating,

- provisional period,

- percentile cohort rating,

- dampening,

- caps,

- rating history,

- tiers.

## 31.6 Milestone 6 - Monetization Beta

Includes:

- AdMob,

- post-result ads,

- practice ads,

- frequency caps,

- consent flow,

- ad analytics.

## 31.7 Milestone 7 - Soft Launch

Includes:

- production backend,

- real daily puzzle schedule,

- real challenge sharing,

- analytics dashboards,

- monitoring,

- support flow.

## 31.8 Milestone 8 - Public Launch

Requires:

- 90-day inventory,

- stable ranked lifecycle,

- stable rating jobs,

- working challenge links,

- active analytics,

- privacy/legal ready,

- ads validated,

- monitoring in place.

# 32. Risks and Mitigation

## 32.1 Retention Risk

Risk: users do not return daily.

Mitigation:

- streaks,

- Streak Freezes,

- countdown,

- final ranking notifications,

- daily reminders,

- friend comparison,

- ghost ranks.

## 32.2 Social Growth Risk

Risk: challenge links do not convert.

Mitigation:

- strong challenge card,

- guest play,

- post-result signup,

- preserved challenge context,

- full funnel analytics.

## 32.3 Competitive Integrity Risk

Risk: users do not trust rankings.

Mitigation:

- server-owned timing,

- one ranked attempt,

- no offline ranked,

- no hints,

- no Auto-Fill Notes,

- high-confidence suspicious hiding,

- formula versioning,

- no manual rating edits.

## 32.4 Rating Risk

Risk: rating feels punitive/unfair.

Mitigation:

- provisional rating,

- movement caps,

- soft negative messaging,

- no rating penalty for abandon,

- completion rewards separate from rating.

## 32.5 Small Cohort Risk

Risk: early leaderboards feel empty/noisy.

Mitigation:

- one global cohort,

- cohort-size dampening,

- friends/nearby views,

- challenge sharing.

## 32.6 Puzzle Quality Risk

Risk: bad puzzles damage trust.

Mitigation:

- curated bank,

- admin review,

- playtesting,

- unique solution validation,

- no-guessing requirement,

- 90-day inventory.

## 32.7 Ads Risk

Risk: ads hurt retention/sharing.

Mitigation:

- ads only after value,

- no ads during ranked,

- no ads before result/share CTA,

- conservative frequency caps.

## 32.8 Scope Creep Risk

Risk: too many platform features before validation.

Mitigation:

- strict non-goals,

- staged release plan,

- post-MVP list preserved but excluded.

## 32.9 Agentic Development Blindness Risk

Risk: coding agents make UI changes without being able to visually inspect native mobile screens.

Mitigation:

- Expo Web / React Native Web proxy,

- component preview harness,

- Playwright screenshot tests,

- mocked app states,

- native QA reserved for native-only behavior.

# 33. Non-Goals

MVP does not include:

- real-time multiplayer,

- persistent private groups,

- phone contacts,

- chat/feed,

- custom puzzle editor,

- advanced coaching,

- tournaments,

- multiple daily ranked puzzles,

- Expert ranked ladder,

- separate public ratings,

- advanced moderation tools,

- full web gameplay,

- offline ranked,

- complex admin platform,

- paid competitive advantages,

- deep cosmetics,

- haptics/sounds.

# 34. MVP Acceptance Criteria

The MVP is launch-ready only if all launch-blocking criteria are met.

## 34.1 Core Gameplay

Must support:

- playable board,

- cell-first,

- number-first,

- notes toggle,

- 3-mistake ranked system,

- locked correct entries,

- editable wrong entries,

- undo within the updated rules,

- note clearing,

- Auto-Clear Notes default ON,

- highlighting,

- timer,

- auto-submit on valid full board,

- completion flow.

## 34.2 Daily Ranked Puzzle

Must support:

- one global daily puzzle,

- global reset,

- visible difficulty,

- estimated solve time,

- preview/start,

- one ranked attempt,

- replay as practice.

## 34.3 Ranked Lifecycle

Must support:

- server start timestamp,

- server submission timestamp,

- validation,

- provisional result,

- final result,

- abandon,

- timeout,

- invalid,

- under-review.

## 34.4 Rating

Must support:

- starting rating 1000,

- floor 100,

- one global rating,

- provisional first 10 completions,

- percentile-based cohort rating,

- difficulty multiplier,

- cohort dampening,

- movement caps,

- rating history,

- formula versioning.

## 34.5 Leaderboards

Must support:

- nearby-my-rank,

- friends/family,

- global top,

- historical read-only leaderboard.

## 34.6 Social Links

Must support:

- challenge link creation,

- app open/install landing,

- guest play,

- result comparison,

- result claim after signup,

- daily ranked eligibility rules.

## 34.7 Streaks

Must support:

- global reset streak,

- local countdown,

- up to 2 Streak Freezes,

- automatic freeze consumption,

- freeze earning every 7 ranked completions.

## 34.8 Admin

Must support:

- import,

- validation,

- license tracking,

- duplicate detection,

- playtest,

- approval,

- bulk scheduling,

- scheduled table,

- audit log.

## 34.9 Ads

Must support:

- AdMob,

- no ads during ranked,

- no ads before result/share CTA,

- frequency caps,

- casual-only rewarded ads.

## 34.10 Analytics

Must support:

- PostHog,

- Postgres source of truth,

- major funnel events,

- social conversion events,

- ranked lifecycle events,

- ad events.

## 34.11 Legal/Privacy

Must support:

- privacy policy,

- terms,

- account deletion,

- GDPR/ad consent,

- no phone contacts,

- no unnecessary sensitive data.

## 34.12 Monitoring

Must support:

- crash reporting,

- backend logging,

- daily puzzle job monitoring,

- rating job monitoring,

- ranked submission monitoring.

## 34.13 Agentic Development Visibility

Must support at least one reliable non-native UI inspection path for coding agents.

Minimum acceptable MVP development setup:

- Expo Web / React Native Web build runs in browser,

- core screens are navigable in browser,

- major states can be rendered through Storybook or /dev/screens route,

- Playwright can capture mobile-viewport screenshots of important states.

# 35. Soft Launch Success Criteria

The MVP is promising if it shows:

- users return after first session,

- users complete multiple Daily Ranked Puzzles,

- users build streaks,

- users check results/leaderboards,

- users share challenge links,

- recipients open/install/play,

- guests convert to accounts,

- ads do not damage retention,

- daily puzzle operations are stable,

- rating feels understandable and fair.

Primary evaluation metrics:

- D1 retention,

- D7 retention,

- ranked completion rate,

- ranked completion-to-share rate,

- challenge link open rate,

- guest completion rate,

- guest-to-account conversion,

- repeat participation after rating loss,

- ad impact on session continuation,

- valid completions per daily cohort.

# 36. Remaining Future Analysis Areas

The expert review resolved the MVP ranked ruleset. Remaining future analysis areas are post-MVP or data-driven:

- Expert ranked puzzle introduction,

- Top 1/3/10 rating or prestige bonuses,

- advanced anti-cheat case management,

- data-driven elite solve-time thresholds,

- separate ladders by difficulty/mode,

- advanced coaching/training,

- private groups/mini-leagues,

- full playable web mode,

- native-device performance tuning.
