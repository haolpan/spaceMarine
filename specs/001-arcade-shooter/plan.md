# Implementation Plan: Space Marine Arcade Shooter

**Branch**: `001-arcade-shooter` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-arcade-shooter/spec.md`

## Summary

A single-player terminal arcade game set in the Warhammer 40K universe. The player
controls a Space Marine that moves left/right and fires Bolter rounds upward at
descending waves of enemies (Tyranid Termagants, Chaos Space Marines, Ork Boyz).
Each wave escalates in difficulty; every fifth wave spawns a named Warhammer 40K
boss. Game ends when all 3 lives are lost; player restarts instantly with one key.

**Technical approach**: Two runtime Python files — `game.py` (pure game logic,
zero curses, fully unit-testable) and `space_marine.py` (curses renderer + entry
point). One test file `tests/test_game.py`. No third-party dependencies.

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**: stdlib only — `curses`, `json`, `time`, `random`, `dataclasses`, `enum`
**Storage**: Optional JSON file (`~/.space_marine_score.json`) for high score persistence
**Testing**: `unittest` (stdlib) — game.py logic layer only; curses layer excluded
**Target Platform**: macOS terminal (primary); Linux terminal (secondary, best-effort)
**Project Type**: CLI arcade game (terminal application)
**Performance Goals**: Responsive input with no perceptible lag; smooth frame updates at ~20 FPS
**Constraints**: 80×24 minimum terminal; stdlib only; 2 runtime Python files; single-command launch
**Scale/Scope**: 2 runtime files (~500 lines total); single-player; single session

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Zero-Dependency Portability ✅

Only stdlib modules are imported: `curses`, `json`, `time`, `random`, `sys`,
`dataclasses`, `enum`, `os`, `unittest`. No `pip install` required.

Entry point: `python space_marine.py` — no args, no config, no env vars, no install.

`game.py` has **zero** curses imports, making it safe to import in any environment.

### II. Warhammer 40K Authenticity ✅

All player-facing strings use lore-accurate terminology:

| Entity | Label used in UI |
|--------|-----------------|
| Player weapon | Bolter |
| Wave 1–2 enemies | Tyranid Termagants |
| Wave 3+ enemies | + Chaos Space Marines |
| Wave 5+ enemies | + Ork Boyz |
| Wave 5 boss | Hive Tyrant |
| Wave 10 boss | Chaos Terminator |
| Wave 15+ boss | Ork Warboss |

All three mandatory enemy types appear by wave 3 (before the wave 5 deadline).
No generic labels ("alien", "laser", "enemy unit") appear anywhere.

### III. Minimal Footprint ✅

Runtime files: 2 (`space_marine.py` + `game.py`).
Test files: 1 (`tests/test_game.py`).
Single-command launch: `python space_marine.py`.
No build step, no compilation, no tooling required.

### IV. Escalating Difficulty ✅

Per-wave difficulty formula (see Wave & Difficulty Design below):
- Speed multiplier: `1.0 + (wave − 1) × 0.15` (15% faster per wave)
- Enemy count: `min(8 + (wave − 1) × 2, 30)` (2 more per wave, capped at 30)
- Enemy HP: `1 + (wave − 1) // 3` (+1 HP every 3 waves)

No wave reduces any parameter vs. its predecessor — monotonically increasing.
Boss milestone: waves 5, 10, 15, … each spawn a named boss with a unique mechanic.

### V. Replayability ✅

HUD displays score, high score, wave counter, and lives throughout play.
Game Over screen: final score + wave reached + high score + restart prompt.
Instant restart: pressing `r` or Enter reinitialises `GameState` without exiting
the curses context.

**Constitution Check Result**: ✅ PASS — all five principles satisfied pre-design.

## Project Structure

### Documentation (this feature)

```text
specs/001-arcade-shooter/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── controls.md      # Key bindings + screen layout contract
└── tasks.md             # Phase 2 output (/speckit.tasks — not yet created)
```

### Source Code (repository root)

```text
space_marine.py          # Entry point + curses renderer (~250 lines)
game.py                  # Game logic — entities, state, wave, collision (~300 lines)

tests/
└── test_game.py         # Unit tests for game.py logic layer (~150 lines)
```

**Structure Decision**: Two-file runtime split chosen to satisfy both Minimal
Footprint (≤3 files) and the constitution's testability requirement (game logic
separated from curses). `game.py` is importable as a pure Python module with zero
curses references — all unit tests run without a terminal. `space_marine.py` owns
the curses lifecycle, render loop, and input dispatch only.

A third file (e.g., `constants.py`) is explicitly rejected: all constants fit
naturally in `game.py` and do not warrant a separate module at this scale.

## Complexity Tracking

> No Constitution Check violations. No entries required.

## Architecture Design

### Layer Separation

```text
┌─────────────────────────────────────┐
│          space_marine.py            │  ← curses only, not tested
│  curses.wrapper → run_game(stdscr)  │
│  Input dispatch → game.handle_input │
│  Renderer → draw_*(stdscr, state)   │
└──────────────┬──────────────────────┘
               │ calls (no curses import flows back up)
┌──────────────▼──────────────────────┐
│             game.py                 │  ← pure Python, fully tested
│  GameState, Player, EnemyUnit,      │
│  BossUnit, BolterRound, Wave        │
│  handle_input(), update(), scoring  │
└─────────────────────────────────────┘
```

### Game Loop

```text
curses.wrapper(run_game)
  └── run_game(stdscr):
        stdscr.nodelay(True)          # non-blocking getch
        game = GameState()
        while game.phase != QUIT:
            key = stdscr.getch()      # -1 if no key pressed
            game.handle_input(key)
            game.update()             # advance physics one tick
            render(stdscr, game)      # full redraw each frame
            time.sleep(FRAME_DELAY)   # ~20 FPS (0.05s)
```

`FRAME_DELAY = 0.05` seconds (20 FPS). Enemy movement uses a fractional position
(`y: float`) advanced by `speed / FPS` per tick, so speed changes affect descent
rate without changing the frame rate.

### State Machine

```text
   ┌────────────────────────────────────┐
   │           Phase.START              │
   │  (title screen, press Enter/R)     │
   └────────────────┬───────────────────┘
                    │ Enter or 'r'
   ┌────────────────▼───────────────────┐
   │           Phase.PLAYING            │◄────────────────────┐
   │  enemies descend, input active     │                     │
   └──┬─────────────────────────────────┘                     │
      │ all enemies dead                │ lives == 0          │
   ┌──▼──────────────────────────────┐  │                     │
   │     Phase.WAVE_TRANSITION       │  │                     │
   │  "Wave N incoming" for 60 ticks │  │                     │
   └──┬──────────────────────────────┘  │                     │
      │ timer expires                   │                     │
      │ (spawn next wave)               │                     │
      └────────────────────────────────►┘                     │
                                                              │
   ┌─────────────────────────────────────────────────────┐    │
   │                 Phase.GAME_OVER                     │    │
   │   final score + wave + high score + restart prompt  │    │
   └─────────────────────────────────┬───────────────────┘    │
                                     │ Enter or 'r'           │
                                     └────────────────────────┘

   Any phase → Phase.QUIT on 'q'
```

### Collision Detection

Grid-based exact-cell matching (curses renders per character cell):

1. **Round hits enemy**: `round.x == enemy.x and round.y == int(enemy.y)`
   → decrement `enemy.hp`; if `hp <= 0` remove enemy; remove round; add score.

2. **Enemy reaches player row**: `int(enemy.y) >= PLAYER_ROW`
   → decrement `player.lives`; remove enemy.
   If `player.lives == 0` → transition to `GAME_OVER`.

3. **Boss projectile hits player** (Chaos Terminator mechanic only):
   `boss_round.x == player.x and boss_round.y == PLAYER_ROW`
   → decrement `player.lives`.

Collision is processed once per `update()` tick after positions are advanced.

## Wave & Difficulty Design

### Per-Wave Parameters

```text
wave_number │ speed_mult │ enemy_count │ enemy_hp │ boss?
─────────────┼────────────┼─────────────┼──────────┼──────
     1       │    1.00    │      8      │    1     │  No
     2       │    1.15    │     10      │    1     │  No
     3       │    1.30    │     12      │    2     │  No
     4       │    1.45    │     14      │    2     │  No
     5       │    1.60    │     16      │    2     │  Hive Tyrant
     6       │    1.75    │     18      │    3     │  No
    10       │    2.35    │     26      │    4     │  Chaos Terminator
    15       │    3.10    │     30(cap) │    5     │  Ork Warboss
    20       │    3.85    │     30(cap) │    7     │  Hive Tyrant×2 HP
```

Formulas:
- `speed_mult  = round(1.0 + (wave - 1) * 0.15, 2)`
- `enemy_count = min(8 + (wave - 1) * 2, 30)`
- `enemy_hp    = 1 + (wave - 1) // 3`

### Enemy Roster by Wave

| Wave range | Enemy types in pool |
|-----------|---------------------|
| 1 – 2     | Tyranid Termagant only |
| 3 – 4     | Termagant + Chaos Space Marine |
| 5+        | Termagant + Chaos Space Marine + Ork Boy |

Enemy formation: two rows of N/2 enemies each, evenly spaced across the play area,
starting at row 2. Enemies within a row descend at the same speed.

### Boss Catalog

| Milestone | Boss name | HP | Unique mechanic |
|-----------|-----------|-----|-----------------|
| Wave 5    | Hive Tyrant     | 10 | Zigzag movement: changes horizontal direction every 15 ticks |
| Wave 10   | Chaos Terminator| 15 | Fires back: launches a projectile toward player every 30 ticks |
| Wave 15+  | Ork Warboss     | 12 | Splits on death: spawns 3 Ork Boyz at death position |

Beyond wave 15, boss cycle repeats with `+5 HP per cycle` (wave 20 boss has HP + 5,
wave 25 boss has HP + 10, etc.).

Boss appears alone at the top-center of the play area. Standard enemies also spawn
on boss waves, filling the remaining slots.

## Screen Layout

```text
Col:  0         20        40        60        80
Row 0: ╔══ SPACE MARINE ═════════════════════════╗
Row 1: ║ SCORE: 00000  HI: 00000  WAVE:01  ♥♥♥  ║
Row 2: ╠══════════════════════════════════════════╣
Rows 3–20: Play area — enemies descend here
Row 21: ╠══════════════════════════════════════════╣
Row 22: ║  [ FOR THE EMPEROR! ]                   ║  ← flavor / status
Row 23: ║  [◙] ← Space Marine                    ║  ← player row
       ╚══════════════════════════════════════════╝
```

Minimum terminal: 80 columns × 24 rows. If terminal is smaller, show:
`"Terminal too small. Minimum 80x24 required."` and exit.

## Key Bindings

| Key | Action |
|-----|--------|
| `←` / `a` | Move Space Marine left |
| `→` / `d` | Move Space Marine right |
| `Space` | Fire Bolter round |
| `Enter` / `r` | Start game (from Start screen) / Restart (from Game Over) |
| `q` | Quit game, restore terminal |

## Post-Design Constitution Re-Check

All five principles remain satisfied after the full design:

- **I. Zero-Dependency**: confirmed — `game.py` imports: `dataclasses`, `enum`,
  `random`, `json`, `os`. `space_marine.py` imports: `curses`, `time`, `sys`,
  `game`. All stdlib.
- **II. Authenticity**: confirmed — full enemy/boss label table above; no generic
  names anywhere.
- **III. Minimal Footprint**: confirmed — 2 runtime files, 1 test file.
- **IV. Escalating Difficulty**: confirmed — wave parameters table above shows
  monotonic increase across all axes.
- **V. Replayability**: confirmed — HUD always visible; instant restart in same
  curses session; high score tracked in-session (optional file persistence).

**Post-Design Result**: ✅ PASS — no violations introduced during design.
