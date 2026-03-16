# Contract: Controls & Screen Layout

**Branch**: `001-arcade-shooter` | **Date**: 2026-03-15
**Type**: UI contract — key bindings and screen layout specification

This document defines the stable interface between the player and the game. Any
change to key bindings or layout requires a constitution-compliant plan amendment.

---

## Key Bindings

### Gameplay (Phase.PLAYING)

| Key(s) | Action | Behaviour |
|--------|--------|-----------|
| `←` (left arrow) or `a` | Move left | Space Marine moves one column left; stops at column 1 |
| `→` (right arrow) or `d` | Move right | Space Marine moves one column right; stops at column 78 |
| `Space` | Fire Bolter | Spawns a `BolterRound` above current player position; multiple rounds allowed simultaneously |
| `q` | Quit | Transitions to `Phase.QUIT`; restores terminal state |

### Start Screen (Phase.START)

| Key(s) | Action |
|--------|--------|
| `Enter` or `r` | Begin new game session |
| `q` | Quit |

### Game Over Screen (Phase.GAME_OVER)

| Key(s) | Action |
|--------|--------|
| `Enter` or `r` | Restart immediately — reinitialises `GameState`, preserves high score |
| `q` | Quit |

### Wave Transition (Phase.WAVE_TRANSITION)

No input accepted during transition (automatic after 60 ticks / 3 seconds).
`q` still accepted for quit.

---

## Screen Layout Contract

Minimum terminal size: **80 columns × 24 rows**.

```text
     0         1         2         3         4         5         6         7
     0123456789012345678901234567890123456789012345678901234567890123456789012345678
 0  ╔══════════════════ SPACE MARINE ══════════════════════════════════════════════╗
 1  ║  SCORE: 00000   HI: 00000   WAVE: 01   ♥ ♥ ♥                               ║
 2  ╠══════════════════════════════════════════════════════════════════════════════╣
 3  ║                          [ play area top ]                                  ║
    │                                                                              │
    │   T  T  T  T  T  T  T  T     ← Tyranid Termagants (Wave 1)                 │
    │                                                                              │
    │   C  C  C  C  C  C  C        ← Chaos Space Marines (Wave 3+)                │
    │                                                                              │
    │           H                  ← Hive Tyrant boss (Wave 5)                    │
    │                                                                              │
    │                  |           ← Active Bolter round                          │
    │                  |                                                           │
20  ║                          [ play area bottom ]                               ║
21  ╠══════════════════════════════════════════════════════════════════════════════╣
22  ║  FOR THE EMPEROR!  [controls: ←/→ move  SPACE fire  Q quit]                ║
23  ║                         [◙]                                                 ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
```

### Row Assignments

| Row(s) | Content | Notes |
|--------|---------|-------|
| 0 | Title bar | "SPACE MARINE" centered |
| 1 | HUD | Score, high score, wave number, lives (♥ symbols) |
| 2 | Separator | `═` border line |
| 3–20 | Play area | Enemies descend from row 3 toward row 20 |
| 21 | Separator | `═` border line |
| 22 | Status / flavor | Active controls hint + lore flavor text ("FOR THE EMPEROR!") |
| 23 | Player row | Space Marine character `[◙]` at current `x` position |

### HUD Format (Row 1)

```text
  SCORE: 00000   HI: 00000   WAVE: 01   ♥ ♥ ♥
```

- Score: zero-padded to 5 digits, left-justified after label.
- High score: same format.
- Wave: zero-padded to 2 digits.
- Lives: one `♥` per remaining life, separated by spaces. Empty = no lives (should
  never render — game over triggers first).

### Entity Symbols

| Entity | Symbol | Notes |
|--------|--------|-------|
| Space Marine (player) | `[◙]` | 3 characters wide; `x` refers to center column |
| Tyranid Termagant | `T` | 1 character |
| Chaos Space Marine | `C` | 1 character |
| Ork Boy | `O` | 1 character |
| Hive Tyrant (boss) | `[H]` | 3 characters wide; displayed with label above |
| Chaos Terminator (boss) | `[X]` | 3 characters wide |
| Ork Warboss (boss) | `[W]` | 3 characters wide |
| Bolter round | `│` | 1 character; travels upward |
| Boss projectile | `↓` | 1 character; travels downward |

### Start Screen Layout

```text
     ╔══════════════════════════════════════════════════════════════╗
     ║                                                              ║
     ║              *** SPACE MARINE ***                            ║
     ║         A Warhammer 40,000 Arcade Experience                 ║
     ║                                                              ║
     ║    Defend the Imperium against the enemies of Mankind.       ║
     ║                                                              ║
     ║    CONTROLS:                                                  ║
     ║      ←/→  or  A/D   Move Space Marine                        ║
     ║      SPACE           Fire Bolter                             ║
     ║      R / ENTER       Start / Restart                         ║
     ║      Q               Quit                                    ║
     ║                                                              ║
     ║              Press ENTER or R to begin                       ║
     ║                    For the Emperor!                          ║
     ║                                                              ║
     ╚══════════════════════════════════════════════════════════════╝
```

### Game Over Screen Layout

```text
     ╔══════════════════════════════════════════════════════════════╗
     ║                                                              ║
     ║              *** BATTLE CONCLUDED ***                        ║
     ║                                                              ║
     ║    The Space Marine has fallen in glorious combat.           ║
     ║                                                              ║
     ║    FINAL SCORE:    00000                                     ║
     ║    WAVE REACHED:   01                                        ║
     ║    SESSION BEST:   00000                                     ║
     ║                                                              ║
     ║          Press ENTER or R to fight again                     ║
     ║          Press Q to retreat                                  ║
     ║                                                              ║
     ╚══════════════════════════════════════════════════════════════╝
```

---

## Invariants

1. The HUD (rows 0–2) MUST always be visible and accurate during `Phase.PLAYING`.
2. The player character MUST always render on row 23.
3. No enemy symbol MUST appear on rows 0–2 (HUD) or row 23 (player row).
4. All player-visible text strings (labels, flavor text, screen titles) MUST use
   Warhammer 40K lore-accurate terminology (enforced by Constitution Principle II).
5. Controls hint on row 22 MUST be visible at all times during `Phase.PLAYING`.
