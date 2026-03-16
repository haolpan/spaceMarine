# UI Contract: HUD Weapon Tier Display

**Feature**: `002-visual-bolter-upgrade`
**FR**: FR-014

---

## Contract: HUD Row 1 Stats Line

The HUD stats line (row 1 of the terminal, inside the border) MUST display the current weapon tier
label at all times during PLAYING phase.

### Current format (row 1):
```
║  SCORE: 00000   HI: 00000   WAVE: 01   ♥ ♥ ♥                              ║
```

### Required format (row 1):
```
║  SCORE: 00000   HI: 00000   WAVE: 01   ♥ ♥ ♥   BOLTER                     ║
```

### Tier label values

| WeaponTier | Label | Max width |
|---|---|---|
| STANDARD | `BOLTER` | 6 |
| TWIN_LINKED | `TWIN-LNK` | 8 |
| STORM_BOLTER | `STORM` | 5 |

### Constraints

- Label MUST update the **same frame** as the tier changes (SC-006).
- Label MUST be visible (not truncated) for all three tier values within the 80-col border.
- HUD row content MUST remain within columns 1–78 (border at cols 0 and 79).
- No other HUD row layout (row 0 title bar, row 2 separator) may change.

### Implementation note

In `draw_hud()` (space_marine.py), append the tier label to the `hud` string before padding
with `ljust(border_inner)`. Read `gs.player.weapon_tier` directly.

---

## Contract: Token Rendering

Power-up tokens are rendered in `draw_game()` alongside existing entity rendering.

### Symbol

`*` (ASCII asterisk, col = token.x, row = int(token.y))

### Constraints

- Token symbol MUST appear only within the play area (rows PLAY_AREA_TOP..PLAYER_ROW-1).
- Token symbol MUST NOT corrupt existing entity rendering (enemies, boss, rounds).
- Token and BolterRound may visually overlap in the same cell — no special handling required.

---

## Contract: Multi-Row Boss Art

The boss rendering in `draw_game()` gains one additional art row.

### Current layout

```
row-1: [label]  HP: ████████
row:   [X]
```

### Required layout

```
row-2: ╔══╗    ← new art row (decorative, boss-type specific)
row-1: [label]  HP: ████████   ← unchanged
row:   [X]                      ← unchanged
```

### Constraints

- Row `row-2` MUST only render when `row-2 >= PLAY_AREA_TOP` (boundary guard).
- Existing HP bar and symbol rows are unchanged (FR-009).
- Art at row-2 is decorative only; no collision or logic impact.
