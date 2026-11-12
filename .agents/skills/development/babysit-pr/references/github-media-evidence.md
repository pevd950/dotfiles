# GitHub media evidence

Inspect and sanitize the smallest useful media before any authorized upload. Keep evidence beside its claim, use meaningful image alt text, and identify the tested commit/build, scenario, platform, device, and OS as relevant. Prefer before/after evidence for visual changes.

`--attach` needs gh 2.99 or later on issue/PR create, edit and comment commands (`gh pr edit --help` shows it). Where it is missing or the host is GitHub Enterprise Server, use the browser attachment flow under the same authorization.

## Commands

Run from the directory that holds the media. Repeat `--attach` for each file. A body reference that matches an attached path, such as `![alt](./after.png)`, is rewritten to the uploaded asset and keeps its alt text. Unreferenced files are appended, with alt text taken from `path#alt text`. A video has no alt text and needs its own paragraph to render a player.

`--body-file` replaces the whole description, so fetch the body, insert the evidence beside its claim, and send it back. Run both blocks in one shell session. The body lives in a private temporary directory outside the checkout, so a repository-supplied `body.md` or symlink is never written through, and a failed fetch stops the run before any upload:

```sh
umask 077
pr_body_dir="$(mktemp -d /tmp/github-pr-body.XXXXXXXXXX)" || exit 1
trap 'rm -rf -- "$pr_body_dir"' EXIT
pr_body_file="$pr_body_dir/body.md"
gh pr view PR_NUMBER --repo OWNER/REPO --json body --jq .body > "$pr_body_file" || exit 1
```

Edit the file at `"$pr_body_file"`, keeping the existing scope, validation details and generated sections, then upload:

```sh
gh pr edit PR_NUMBER --repo OWNER/REPO --body-file "$pr_body_file" \
  --attach ./before.png --attach ./after.png --attach ./interaction.mp4
```

Example fragment to insert:

```markdown
Tested COMMIT_OR_BUILD: SCENARIO on PLATFORM / DEVICE / OS.

![Settings panel before the layout fix](./before.png)
![Settings panel with the corrected layout](./after.png)

![](./interaction.mp4)
```

Append to the existing body, or attach to a comment:

```sh
gh pr edit PR_NUMBER --repo OWNER/REPO \
  --attach './after.png#Settings panel with the corrected layout'
gh pr comment PR_NUMBER --repo OWNER/REPO --body-file /tmp/pr-evidence.md \
  --attach ./after.png
```

Upload only through `--attach` or the browser flow, never through token-bearing raw URLs or commits made just to carry screenshots.

## Verify

Read the saved body or comment back (`gh pr view PR_NUMBER --repo OWNER/REPO --json body,headRefOid`) and check placement, alt text and that each reference resolved to an uploaded asset. When a signed-in browser is available, open the page and confirm images display and videos play; otherwise say rendering was not checked. Uploads to a private repository need repository access, so an anonymous 404 is not a failure.

A nonzero exit can still mean some uploads and the body update succeeded. Reread the destination before retrying, and re-attach only what is missing.

## Official references

- [GitHub CLI media announcement](https://github.blog/changelog/2026-09-01-github-cli-media-in-issues-pull-requests-and-comments/)
- [Attaching files with GitHub CLI](https://docs.github.com/en/github-cli/github-cli/attaching-files-with-github-cli)
- [Attaching files: visibility, browser flow, formats and limits](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files)
