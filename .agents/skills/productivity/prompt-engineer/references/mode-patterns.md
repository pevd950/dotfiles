# Mode Patterns

Load only the section needed for the current request.

## Image generation

```text
Create [goal/use case]. Show [setting and subject]. Compose it as [framing, camera angle, lens feel, depth]. Use [style or medium]. Light it with [direction and mood] using [palette and materials]. Include the exact text "[text]" in [typography, placement, hierarchy]. [Constraints.] No other text.
```

Avoid generic `8K`, `masterpiece`, `award-winning`, and long negative lists unless the user deliberately wants that vocabulary.

## Image edit

```text
Using the provided image, change only:
- [specific change]

Keep unchanged:
- identity, face, age, body proportions, expression, and pose
- camera angle, perspective, crop, and lens feel
- lighting direction, shadows, color temperature, and grain
- background and surrounding objects
- text, logos, and layout unless explicitly changed

Constraints:
- No other changes.
- No extra text, logos, or watermarks.
```

For a small revision:

```text
Keep everything the same except:
- Change: [one thing]
- Do not change: [two to four critical invariants]
```

For multiple images, refer to inputs by index and say exactly what to preserve, edit, combine, transfer, or blend from each.

## Video

```text
[Visual style and era.] [Framing] with [one camera move].

Beat 1: [one subject action].
Beat 2: [one subject action].
Beat 3: [one subject action].

Setting and light: [location, lighting, palette].

Dialogue:
[Speaker]: "[exact line]"

Background Sound:
[ambient sound, music, effects]

Constraints: [continuity, anatomy, branding, text, or realism requirements].
```

## Raycast

Use placeholders only when helpful: `{selection}`, `{clipboard}`, `{argument}`, `{browser-tab format="markdown"}`, and `{date format="yyyy-MM-dd"}`. Use raw modifiers when formatting must remain untouched. Return only the command prompt unless setup notes are requested.

## Prompt review

Judge the prompt on whether the goal and done state are clear, the instructions agree with each other, it fits the named target (see [current-models.md](current-models.md)), and the output is controlled. Then return:

```text
Verdict: [Ready to ship | Needs revision] — [one sentence]

Top fixes:
1. ...
2. ...
3. ...

Revised prompt:
[paste-ready prompt]
```

List only fixes that change the result, up to three. Say when the revision still needs a run on real tasks to confirm it is better.
