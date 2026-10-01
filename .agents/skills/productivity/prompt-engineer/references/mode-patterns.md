# Mode Patterns

Load only the section needed for the current request.

## Image generation

```text
Create [goal/use case]. Show [setting and subject]. Compose it as [framing, camera angle, lens feel, depth]. Use [style or medium]. Light it with [direction and mood] using [palette and materials]. Include the exact text "[text]" in [typography, placement, hierarchy]. [Constraints.] No other text.
```

Avoid generic `8K`, `masterpiece`, `award-winning`, and long negative lists unless the user deliberately wants that vocabulary.

## Image edit

```text
Using the provided image, change ONLY:
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

Score each dimension from 0–10: clarity, completeness, model fit, output control, and practicality. Report the overall score as their rounded average. Then return:

```text
Overall score: [0-10]
Verdict: [Ready to ship | Needs revision] — [one sentence]

Top 3 fixes:
1. ...
2. ...
3. ...

Revised prompt:
[paste-ready prompt]
```
