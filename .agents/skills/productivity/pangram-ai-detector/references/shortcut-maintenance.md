# Maintaining the Pangram shortcut

Use Shortcuts Playground for authoring rules and validation. For an existing shortcut, inspect the live library and export the installed artifact before rebuilding; historical generators can omit user-added actions.

## Input and output contract

When the user requests input visibility, append the exact submitted Input Text beneath the result. Show, Copy, and Share must use the same assembled result. Include it in both percentage and classification-only branches. Do not re-read the clipboard after the request. This explicit user-requested input inclusion is distinct from the CLI helper's default omission of source text.

## Update workflow

- Resolve a unique existing name and record its identifier. Preserve its name, identifier, folder, icon, triggers, and unrelated actions. Do not create version-suffixed copies by default.
- For small edits, prefer the native Shortcuts editor. Its saved changes can propagate through enabled iCloud Sync without importing a replacement.
- For new shortcuts, validate and sign a canonical-name file, then use the native import flow and inspect the resulting library. Use the configured AI inbox only when an import handoff is needed.
- The public CLI supports list, view, run, and sign; do not invent import/update commands. Do not mutate Shortcuts SQLite or CloudKit records.
- Treat same-name import behavior as unverified until the native dialog and final identity are checked. Do not automatically delete an existing shortcut to work around an import limitation.
- Preserve custom third-party actions. An unavailable app on the current Mac does not prove that its action is unwanted or broken on the phone.
- Treat preview, copy, share, and post-copy integrations as separate runtime outcomes. A failed action after Copy may leave a valid clipboard result.

## Verification

1. Validate generated plists and variable ranges; use WFTextTokenString for dynamic Show Result content.
2. Inspect/export the saved installed artifact and verify both result templates bind to the submitted text.
3. Run synthetic non-private text through the actual installed shortcut. Compare the rendered and copied text with that input.
4. Verify the library still contains one canonical shortcut with the original identifier.
5. Report local runtime, clipboard, third-party integration, iCloud convergence, and physical iPhone checks separately. A successful Mac run does not prove phone execution or sync.

Native UI notes: runtime dialogs may belong to com.apple.WorkflowKit.ShortcutsViewService rather than the main Shortcuts editor. Rebind and inspect its current UI after transitions. When editing tokenized Text, insert around existing tokens; setting the whole text field can discard variable attachments. Use the editor's Insert Variable menu and verify the exported graph.
