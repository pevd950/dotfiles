# GitHub media evidence

## Choose the upload path

Inspect and sanitize the smallest useful media before any authorized upload. Keep evidence beside its claim, use meaningful image alt text, and identify the tested commit/build, scenario, platform, device, and OS as relevant. Prefer before/after evidence for visual changes.

Check local `gh --version` and the intended command’s `--help`. Native `--attach` arrived in gh 2.99.0 for issue/PR create, edit, and comment commands. GitHub documents repository write access and OAuth or classic PAT authentication; the feature is available across GitHub plans, but not GitHub Enterprise Server. Do not assume an API-readable repository implies upload support. If capability, authentication, or host support is unavailable, use the supported browser attachment flow under the same publication authorization; do not change authentication or upgrade software implicitly.

## Place media in the body

Use `--body-file` for multiline Markdown. Repeat `--attach` for different files. Local references matching attached files are rewritten in place and preserve their Markdown alt text; otherwise files are appended. The `path#alt text` form sets alt text only for appended images. Videos have no alt text and need a standalone paragraph to render a player.

For an already-authorized PR edit, replace the repository and PR placeholders. Run from the directory containing the sanitized media. First fetch the saved description into an unused local body file (stop if the fetch fails):

```sh
gh pr view PR_NUMBER --repo OWNER/REPO --json body --jq .body > body.md
```

Edit that complete body to insert evidence beside its claim, preserving existing scope, validation details, and generated sections. `--body-file` replaces the entire description. Immediately before saving, reread the live body and reconcile any intervening edits, then upload:

```sh
gh pr edit PR_NUMBER --repo OWNER/REPO --body-file body.md \
  --attach ./before.png --attach ./after.png --attach ./interaction.mp4
```

Example fragment to insert into the complete `body.md`, not a replacement description (replace the test-context placeholders):

```markdown
Tested COMMIT_OR_BUILD: SCENARIO on PLATFORM / DEVICE / OS.

Before:

![Settings panel before the layout fix](./before.png)

After:

![Settings panel with the corrected layout](./after.png)

Interaction:

![](./interaction.mp4)
```

To append an image while retaining the existing PR body:

```sh
gh pr edit PR_NUMBER --repo OWNER/REPO \
  --attach './after.png#Settings panel with the corrected layout'
```

Consult current command help and the linked file documentation for supported formats and limits instead of assuming a remembered limit. Do not use undocumented upload endpoints, token-bearing raw URLs, or commits solely to transport screenshots. Legitimate tracked assets can remain with verified, access-appropriate links; changing a raw URL to a blob URL is not proof of rendering.

## Verify and recover

Read back the final saved issue, PR, or comment body and check the intended placement, alt text, and resolved attachment references. For a PR body, use `gh pr view PR_NUMBER --repo OWNER/REPO --json body,headRefOid`. Then inspect the actual saved page in a signed-in browser with repository access: images must display and videos must render/play as intended. A successful edit or body readback alone does not prove rendering. Report unavailable browser validation explicitly; do not claim it passed.

Public repository uploads are anonymously accessible; private/internal uploads require repository access. Limit anonymous checks to already-public assets. A private unauthenticated 404 or denial does not establish missing bytes or a failure for an authorized viewer. Check signed-in access before diagnosing rendering, and never publish private assets merely to test them.

Local `gh pr edit --help` (2.100.0) documents partial success: some uploads and the body update may succeed even when the command exits nonzero. After any failure or ambiguous result, reread the destination before retrying. Preserve successful uploads and retry only confirmed missing attachments, rebuilding any replacement body from the saved result to avoid duplicates or lost edits.

## Official references

Verified 2026-09-09; examples were checked against documentation and local CLI help, without test publication or public/private runtime rendering tests.

- [GitHub CLI media announcement: availability, access, and authentication](https://github.blog/changelog/2026-09-01-github-cli-media-in-issues-pull-requests-and-comments/)
- [Attaching files with GitHub CLI: commands and Markdown placement](https://docs.github.com/en/github-cli/github-cli/attaching-files-with-github-cli)
- [Attaching files: repository visibility, browser flow, formats, and limits](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files)
