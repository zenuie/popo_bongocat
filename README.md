# Po Bongo Cat 🤖⌨️

A cross-platform desktop pet. **Po** sits at the bottom of your screen behind a
little keyboard + mouse and reacts to your real input, **Bongo Cat style**:

- **Type anywhere** → the matching hand reaches over and presses the key you hit,
  and that key lights up. Po leans toward whatever it's reaching.
- **Click / scroll anywhere** → Po reaches over to the mouse and the
  left/right button or wheel lights up.
- Idle → Po rests its hands on the keyboard and floats gently.

Transparent, always-on-top, draggable, click-through on empty pixels.

Built with **Python + PySide6** (Qt6) and **pynput** for global input.

## Run from source

```bash
python -m venv .venv && source .venv/bin/activate   # or use uv
pip install -r requirements.txt
python -m src.main
```

> **macOS:** global input needs permission. Grant **Input Monitoring** and
> **Accessibility** to your terminal (or the app) in
> *System Settings → Privacy & Security*, then relaunch. Without it Po still
> runs and is draggable — it just won't react to other apps.

## Download (v1.0.0)

Pre-built installers are attached to the
[latest release](https://github.com/zenuie/popo_bongocat/releases/latest):

- **macOS** — `PoBongoCat-macOS.zip` (unzip → run `PoBongoCat.app`; first launch:
  right-click → Open to bypass Gatekeeper, since it's unsigned)
- **Windows** — `PoBongoCat.exe`

## Project layout

```
src/
├─ main.py            entry: app, window, tray, global input listener
├─ pet_window.py      transparent always-on-top window; composes body+desk+hands
├─ hands.py           program-controlled gloves (reach keys/mouse, tap, lean)
├─ desk.py            keyboard + mouse graphics (rotated 180°) + key/mouse targets
├─ keyboard.py        drawn QWERTY: token→key map + per-key lighting
├─ mouse.py           drawn mouse: left / right / wheel lighting
├─ animator.py        idle float + activity nod
├─ input_listener.py  pynput global keyboard/mouse → Qt signals
├─ tray.py            system-tray menu (reset position / quit)
├─ resources.py       asset path resolver (dev + PyInstaller)
└─ config.py          all layout & handfeel tuning lives here
assets/
├─ idle.png           original Po art (tray icon)
└─ parts/             po_body.png, po_hand.png + source_po_idle.png
tools/build_parts.py  regenerate body/hand sprites from the source art
```

Tune the feel (lean, hand speed, tap depth, mouse position, colors) in
`src/config.py`. Regenerate the sprites with `python tools/build_parts.py`.

See [PLAN.md](PLAN.md) for the original spec.
