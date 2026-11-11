---
name: status-board
description: Refresh or correct the user's shared status board, a private claude.ai Artifact that more than one agent publishes to. Use for the scheduled daily refresh, for an intraday correction after verifying a change at its source, or whenever the user asks to check, update or fix the status board.
---

# Status board

The status board is one private, phone-readable page that answers "where do things stand" across projects. Several agents keep it current, so this skill is the single contract they all follow. It names no private links or IDs: private routing gives the board's URL and the role each agent plays.

## Roles

| Role | Who | Writes |
| --- | --- | --- |
| Refresher | The agent private routing names for the daily refresh | The full refresh: every section is rebuilt from its sources, and the refresher owns the page's structure. |
| Coordinator | The agent private routing names as coordinator | Intraday corrections only, limited to rows it has just verified at their source. It never rebuilds sections it didn't check. |
| Everyone else | Codex threads, project sessions, chat assistants | Doesn't publish. Sends the fact and its source link to the coordinator, which verifies it and edits the row. |

Only agents with the Artifact tool can publish. An agent without it (Codex, for example) reports to the coordinator instead of finding another route to the page.

## Writing safely

1. Read the live board by its URL immediately before editing, and build on the version that comes back. Never publish from a local copy saved earlier, even one you wrote yourself.
2. Change only what you verified. A full refresh rebuilds everything; a correction touches only its rows and the header stamp.
3. Publish to the same URL. If the publish is refused because a newer version exists, merge your change onto the version the refusal returns and publish again. Never use `force`.
4. Read the board back after publishing and check that your change is there and the page still renders.

## Sources

Every row comes from its owning system, read at refresh time. Never carry a row over from the previous version without rechecking it.

| Section | Sources |
| --- | --- |
| Today | The calendars private routing names, for today through the next few days; personal tasks due today or overdue. |
| This week | The user's active goals with dates, from personal tasks and active plans. |
| Needs you | High-priority personal tasks; approvals and decisions only the user can give; items held by the user's own call. |
| In flight | Open and recently merged pull requests in each active repository; live agent threads, including Codex. |
| Plans | Every plan document carrying the active or paused status marker, sorted by last update. |
| Parked | Items the user explicitly put on hold. Keep each one until the user releases it. |

Read GitHub and live thread state last, right before publishing. Pull requests merge minutes before a refresh, and a board that lists them as open is wrong the moment it lands.

## Content rules

- State what is true now, in the user's terms. Don't keep history; the sources hold it.
- When two sources disagree, for example a plan's marker against its own text, fix the source or tell its owner. Don't publish the contradiction as a row.
- A row waiting on the user says what they need to do, in one line.
- A dated item whose date has passed either gets a new date or is flagged as overdue. Don't leave the stale date showing.
- Never include secrets, tokens or credentials. Private links are fine because the board is private. Don't change who it's shared with.
- Keep the existing layout and visual design. A redesign is the user's call.

## Header stamp

The header records who last refreshed the board and when, for example `updated Wed Nov 11, 8:05 AM CT by <refresher>`. A correction appends what it rechecked, for example `GitHub rows rechecked 9:10 AM by <coordinator>`. The next full refresh replaces the whole stamp.

## Finishing

Report the board link and a short summary of what changed. When the user is away, a refresh with nothing new for them doesn't need a notification.
