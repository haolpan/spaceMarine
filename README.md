# Space Marine

A Warhammer 40,000 arcade shooter for your terminal. Defend the Imperium against waves of Tyranids, Chaos Space Marines, and Ork Boyz. Survive long enough and face the Boss.

```
╔══════════ SPACE MARINE ══════════╗
║  SCORE: 00420   HI: 01200        ║
║  WAVE: 03   ♥ ♥ ♥   TWIN-LNK    ║
╠══════════════════════════════════╣
║         T   T   T   T            ║
║                                  ║
║              C                   ║
║                                  ║
║             [℧]                  ║
╠══════════════════════════════════╣
║  [← → move  SPACE fire  Q quit]  ║
╚══════════════════════════════════╝
```

## Requirements

- Python 3 (no dependencies, stdlib only)
- A terminal at least 80×24 characters
- macOS or Linux

## Play

```bash
git clone <this repo>
cd space-marine
python3 space_marine.py
```

## Controls

| Key | Action |
|-----|--------|
| `←` / `→` or `A` / `D` | Move |
| `Space` | Fire Bolter |
| `R` / `Enter` | Start / Restart |
| `Q` | Quit |

## Weapon Upgrades

Kill enemies for a chance to collect a power-up (`*`). Each pickup upgrades your Bolter:

```
BOLTER → TWIN-LNK → STORM
```

Your weapon resets to BOLTER if you lose a life.

## Enemies

| Symbol | Enemy |
|--------|-------|
| `T` | Termagant (Tyranid) |
| `C` | Chaos Space Marine |
| `₩` | Ork Boy |
| Boss | Hive Tyrant / Chaos Terminator / Ork Warboss |

Waves get faster and denser. Good luck, Battle-Brother.
