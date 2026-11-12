---
name: screenshot-review
description: "Improve an app screen through rounds of independent screenshot review: Claude and Codex reviewers judge screenshots of the running app against a written rubric, the building agent fixes what fails, and the loop ends at a pass, a plateau or the round cap. Use when the user asks for a multi-model UI review, screenshot scoring, a design review loop, or to iterate a screen until reviewers pass it."
---

# Screenshot review

Independent reviewers look at screenshots of the running app, judge them against a rubric, and the building agent fixes what fails. The loop is decided by pass or fail on each criterion and by comparing rounds, because a model's 1–10 score for a screen is noisy and a loop that chases 10/10 either never ends or ends when a judge talks itself into it. Each reviewer still gives one overall 1–10 score so the user can see the trend.

## Workflow

1. **Write the rubric before the first round.** Use pass/fail criteria that a screenshot can show, drawn from the task's acceptance criteria, the project's design system and reference screens, and the platform's design skill (`apple-ui-design`, `frontend-design`, `home-assistant-dashboards`). Cover at least:
   - the most important information or action reads first;
   - spacing, alignment and type are consistent with the rest of the app;
   - text is legible and has enough contrast;
   - nothing is clipped, overlapping or truncated;
   - the states that matter hold up: empty, loading, error, long content, dark mode, largest text size;
   - the copy matches the product's voice and density.
2. **Capture the real app.** Take screenshots of each state on the smallest and largest supported sizes, in light and dark, using the project's run tooling (`ios-run-and-verify` for iOS). Name files by round and state, and keep every round.
3. **Review with two reviewers:** Claude and Codex, each on its strongest model, through the image commands in the [second-opinion routes](../second-opinion/references/reviewer-routes.md). Claude is the preferred judge of visual quality: when the two disagree on a visual call, go with Claude's read unless the screenshot shows otherwise. The building agent's vendor reviews from a fresh context; the builder itself is not a reviewer. Give each reviewer the screenshots, the rubric, the reference screens and what the screen is for. Leave out the code, your rationale and any earlier praise. From round two, add the previous round's screenshots and ask which round is better on each criterion, whether each earlier failure is fixed, and what got worse.
4. **Ask each reviewer for:** pass, fail or "cannot tell from the screenshot" on every criterion, with where it is visible; at most five issues ranked by impact; one overall 1–10 score.
5. **Check each failure in the screenshot yourself.** Reject a finding that contradicts the rubric, the design system or what the user asked for, and record why. Fix the failures that held, most important first, and leave what passed alone.
6. **Stop** when every criterion passes for both reviewers, when a round fixes nothing new or loses the comparison with the round before, or after three rounds. Ask before running more. Keep the best round, which is not always the last: restore the earlier one when the latest loses the comparison.
7. **Report:** first-round and final screenshots side by side, the rubric results and scores for each round, what changed, the findings rejected, and what still fails. The reviewers passing a screen is not the user accepting it.
