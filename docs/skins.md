# Custom skins

Po can wear a different character. A **skin** is a folder with two PNGs:

```
<skin-name>/
├── po_body.png   # head + torso, arms removed, transparent background
└── po_hand.png   # one glove/hand (mirrored in code for the other hand)
```

The keyboard and mouse are drawn procedurally, so a skin only replaces the
body and the hand — nothing else.

## Where to put a skin

Drop the folder in either location and it shows up in **Tray → 設定… → 造型**:

| Location | Path |
|----------|------|
| Per-user (recommended) | macOS `~/Library/Application Support/PoBongoCat/skins/<name>/`<br>Windows `%APPDATA%\PoBongoCat\skins\<name>\`<br>Linux `~/.config/PoBongoCat/skins/<name>/` |
| Bundled with the app | `assets/skins/<name>/` |

The settings panel re-scans this folder every time it opens, so you don't need
to restart after adding a skin.

## Authoring the art

The shared layout (hand rest spots, where the hand presses, how the body
floats) is tuned to Po's proportions, so cut your character to **roughly the
same shape and framing as the default Po art**:

- `po_body.png` — the character from the chest up, arms removed, with a clean
  transparent background. Keep it about square.
- `po_hand.png` — a single hand/glove on transparent background, sized similar
  to Po's glove (the default is ~130×132). It is drawn at `HAND_SCALE` and
  mirrored for the opposite hand.

### Slicing helper

`tools/build_parts.py` is the reference slicer that produced the default Po
parts from a single source sticker. It is **specific to Po's art style** (white
sticker outline, white gloves) — it is a starting point to adapt, not a
general one-click cutter for arbitrary images. For a different character,
either cut the two PNGs by hand or adapt that script to your source.

## Resetting

Pick **default** in the 造型 dropdown to return to the built-in Po.
