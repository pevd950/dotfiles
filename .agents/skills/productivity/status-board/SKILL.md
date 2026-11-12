---
name: status-board
description: Build, refresh or correct the user's status board, one private page that shows where every project stands, on whatever publishing surface the agent has (a Claude Artifact, a ChatGPT Page, another tool's document). Use for the scheduled daily refresh, for an intraday correction after verifying a change at its source, or whenever the user asks to check, update or fix the status board.
---

# Status board

The status board is one private, phone-readable page that answers "where does everything stand" across projects. The user's daily page answers a different question, "what do I do next today", and has its own publisher; the board links to it and leaves today's next moves to it.

This skill is the contract for the board's content, whichever agent keeps it and wherever it is published. It names no private links or IDs: private routing gives each board's location, the navigation links and the role each agent plays.

## Surface and roles

An agent publishes the board on the surface it has: Claude on an Artifact, Codex on a ChatGPT Page, another agent on its own document tool. Each board lives on one surface and is written only by agents that have that surface. Two agent families each keep their own board from this same contract; neither tries to reach the other's page by another route.

| Role | Who | Writes |
| --- | --- | --- |
| Refresher | The agent private routing names for that board's daily refresh | The full refresh: every section is rebuilt from its sources, and the refresher owns the page's structure. |
| Coordinator | The agent private routing names as that board's coordinator | Intraday corrections only, limited to rows it has just verified at their source. It never rebuilds sections it didn't check. |
| Everyone else | Other threads, project sessions and agents without that surface | Doesn't publish. Sends the fact and its source link to the coordinator, which verifies it and edits the row. |

## Writing safely

1. Read the live board by its URL immediately before editing, and build on the version that comes back. Never publish from a local copy saved earlier, even one you wrote yourself.
2. Change only what you verified. A full refresh rebuilds everything; a correction touches only its rows and the header stamp.
3. Publish to the same location. If the publish is refused because a newer version exists, merge your change onto the newer version and publish again. Never overwrite a newer version to get yours through.
4. Read the board back after publishing and check that your change is there and the page still renders.

## Layout

Every board has the same sections in the same order: header stamp, navigation line, Changed, Today, This week, Needs you, In flight, Plans, Parked. On an HTML surface, start from [assets/board-template.html](assets/board-template.html) and fill the sections; on a document surface, use the section names as headings and the same row shapes. A redesign is the user's call. When a live board has drifted from this layout, bring it back during a full refresh.

- **Navigation line:** one compact line of the links private routing lists (the daily page, today's daily note, today's task views, the active-work view). Resolve today's daily note each time; never reuse yesterday's link.
- **Changed:** three to five lines on what moved since the previous full refresh: decided, merged and accepted, newly waiting on the user, newly blocked. Leave the section out when nothing moved.
- **Plans:** active plans in the table, newest first. Paused plans, and active plans with no change in two weeks, go in the collapsed lists under it.

## Sources

Every row comes from its owning system, read at refresh time. Never carry a row over from the previous version without rechecking it.

| Section | Sources |
| --- | --- |
| Today | The calendars private routing names, for today through the next few days; personal and household tasks due today or overdue. |
| This week | The user's active goals with dates, from personal tasks and active plans. |
| Needs you | High-priority personal tasks; approvals and decisions only the user can give; items held by the user's own call. |
| In flight | Open pull requests and the current step of each active project; live agent threads, whichever agent runs them. |
| Plans | Every plan document carrying the active or paused status marker, sorted by last update; open rows on each project's workboard. |
| Parked | Items the user explicitly put on hold. Keep each one until the user releases it. |

Read GitHub and live thread state last, right before publishing. Pull requests merge minutes before a refresh, and a board that lists them as open is wrong the moment it lands.

A source that fails or returns only part of its data is a gap, not an empty result: keep the previous rows for that section, mark them unchecked, and name the gap in the header stamp.

## Rows

- A row states what is true now, in the user's terms: the current step, what is left before it is accepted, who owns it, and a link. History stays in the sources, so a row has no list of merged pull requests.
- An In flight row carries one state: moving, in review, waiting, blocked, held, or not observed. A merged pull request is not acceptance, and a quiet thread is not a stall; say "not observed" when you could not check.
- A Needs you row says what the user has to do in one line and links both the task and the chat that owns the work. Use only links a tool returned: the task system's own link, and for a chat the host's link or the agent bus's link resolver. With no verified chat link, name the chat.
- A dated item whose date has passed gets a new date from its source or is flagged overdue.
- When two sources disagree, for example a plan's marker against its own text, fix the source or tell its owner, and show the row once the source is right.
- Private links are fine because the board is private. Leave secrets, tokens and credentials out, and leave the sharing settings as they are.

## Before publishing

Check the page you are about to publish:

1. No row lists history or merged pull requests.
2. No row shows a date that has passed without an overdue flag.
3. No row states a contradiction between two sources.
4. Every Needs you row has its task link, and its chat link or the chat's name.
5. The header stamp names every source read and every gap.

## Header stamp

The header records who last refreshed the board, when, and from what, for example `refreshed Wed Nov 11, 8:05 AM CT by <refresher> · read: tasks, calendars, plans, GitHub · not read: household tasks (tool unavailable)`. A correction appends what it rechecked, for example `GitHub rows rechecked 9:10 AM by <coordinator>`. The next full refresh replaces the whole stamp.

## Finishing

Report the board link and a short summary of what changed. When the user is away, a refresh with nothing new for them doesn't need a notification.
