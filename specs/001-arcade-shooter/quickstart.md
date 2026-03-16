# Quickstart: Space Marine Arcade Shooter

## Requirements

- Python 3.8 or later
- macOS or Linux terminal (80×24 minimum size)
- No installation, no dependencies

## Launch

```bash
python space_marine.py
```

That's it.

## Controls

| Key | Action |
|-----|--------|
| `←` / `a` | Move left |
| `→` / `d` | Move right |
| `Space` | Fire Bolter |
| `Enter` / `r` | Start / Restart |
| `q` | Quit |

## Gameplay

1. Press **Enter** or **R** on the title screen to begin.
2. Move left/right to dodge descending enemies.
3. Fire Bolter rounds upward to destroy enemies before they reach you.
4. Clear all enemies to advance to the next wave.
5. Every **5th wave** a boss enemy appears — it takes more hits and has a unique mechanic.
6. You have **3 lives**. Losing all lives ends the session.
7. Press **Enter** or **R** on the Game Over screen to play again immediately.

## Enemies

| Enemy | Appears from |
|-------|-------------|
| Tyranid Termagants | Wave 1 |
| Chaos Space Marines | Wave 3 |
| Ork Boyz | Wave 5 |

## Bosses

| Boss | Wave | Special |
|------|------|---------|
| Hive Tyrant | 5, 20, 35… | Zigzag movement |
| Chaos Terminator | 10, 25, 40… | Fires back at you |
| Ork Warboss | 15, 30, 45… | Splits into 3 Ork Boyz on death |

## Troubleshooting

**"Terminal too small. Minimum 80x24 required."**
Resize your terminal window to at least 80 columns × 24 rows and relaunch.

**Game exits immediately on macOS**
Ensure you are using `python3` if `python` points to Python 2:
```bash
python3 space_marine.py
```

**Colours look wrong**
The game uses no colours — only standard terminal characters. If symbols appear
garbled, your terminal may not support UTF-8. Try setting `LANG=en_US.UTF-8`.
