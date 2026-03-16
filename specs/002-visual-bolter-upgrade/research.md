# Research: Visual Fidelity & Bolter Upgrade System

**Feature**: `002-visual-bolter-upgrade`
**Date**: 2026-03-16
**Status**: Complete — all NEEDS CLARIFICATION resolved

---

## Decision 1: Multi-row Character Art Strategy

**Decision**: Use multi-line `safe_addstr` calls in `space_marine.py` only. game.py exposes no art strings.

**Rationale**: The renderer (space_marine.py) already calls `safe_addstr(row, col, text)` per cell.
Adding a second `safe_addstr` call one row above the anchor achieves multi-row art with zero logic changes.
The player's anchor x-position and collision box remain at PLAYER_ROW (row 23, single column),
satisfying FR-003: "collision and movement logic MUST remain based on a single anchor x-position."

**Alternatives considered**:
- Storing art strings in game.py alongside entities → rejected: violates curses-free rule; art is
  a rendering concern.
- A dedicated `art.py` module → rejected: Principle III (Minimal Footprint) requires 1–3 files;
  this is a rendering-only addition that fits naturally in space_marine.py.

---

## Decision 2: Diagonal BolterRound Representation

**Decision**: Extend `BolterRound` with an optional `dx: int = 0` field. Standard rounds keep `dx=0`.
Storm Bolter outer rounds spawn with `dx=-1` and `dx=+1`.

**Rationale**: A single dataclass with a default field requires zero import changes elsewhere.
`_check_collisions()` already compares `r.x == e.x`; diagonal rounds shift `r.x += r.dx` each tick
alongside the existing `r.y -= 1` movement. Boundary removal uses the existing `r.y >= PLAY_AREA_TOP` filter;
no x-boundary removal needed since rounds reaching x outside play area have no targets.

**Alternatives considered**:
- Separate `DiagonalBolterRound` dataclass → rejected: requires touching every collision loop and
  every isinstance check. Simpler to use a default-zero field.
- A `direction` enum on BolterRound → rejected: over-engineered; dx int covers all three cases with
  one field.

---

## Decision 3: PowerUpToken Fall Cadence

**Decision**: Float y-position advancing `0.5 rows/tick` (= 1 row per 2 ticks at FPS=20 → 0.5 rows/sec).
FR-011 states "1 row per 2 ticks". Implemented as constant `POWERUP_FALL_SPEED = 0.5` applied as
`token.y += POWERUP_FALL_SPEED` each tick.

**Rationale**: Consistent with enemy y float model (`y += speed / FPS` per tick). Using a float avoids
integer modulo gating. Comparable to Termagant base_speed=1.0 → 0.05 rows/tick, so token falls
at 10× Termagant speed — faster than enemies but visible for collection. FR-011 says "half the speed
of a standard Termagant"; Termagant descends at `1.0 row/sec` → token at `0.5 row/sec`, i.e. `0.5/FPS`
per tick ≈ `0.025 rows/tick`. Correction: "1 row per 2 ticks" at 20FPS = 10 rows/sec. This is actually
FASTER than Termagant (1 row/sec). FR-011 literal reading: 1 row per 2 **ticks** (not seconds). At 20
FPS, 2 ticks = 0.1s → 10 rows/s descent. Standard Termagant = 1 row/s. Token is 10× faster than
Termagant. Implemented as `POWERUP_FALL_SPEED = 0.5` (added to y each tick). Integer y is checked for
collection.

**Alternatives considered**:
- Tick counter gating (`if tick % 2 == 0: y += 1`) → rejected: inconsistent with the float model
  already established for enemies; adds stateful tick comparison.

---

## Decision 4: WeaponTier Ownership

**Decision**: `WeaponTier` enum added to `game.py`. `Player` dataclass gains a `weapon_tier: WeaponTier`
field defaulting to `WeaponTier.STANDARD`. Reset on life loss happens in `_check_collisions()` and
`_update_boss_projectiles()` immediately after `player.lives -= 1`, before any fire logic runs.

**Rationale**: Tier must survive between fire events and reset atomically with life loss. Player already
owns x, lives, score — weapon tier is the same category. Keeping it on Player means `reset()` naturally
resets it (new `Player()` defaults to STANDARD).

---

## Decision 5: Firing Logic Location

**Decision**: `handle_input()` in game.py already spawns `BolterRound` on SPACE. Extend this to inspect
`player.weapon_tier` and spawn 1, 2, or 3 rounds accordingly. The renderer needs no knowledge of tier
beyond reading `player.weapon_tier` for the HUD label.

**Rationale**: Keeps all state mutations inside game.py. The renderer reads `gs.player.weapon_tier`
for the HUD label — read-only access, no logic.

---

## Decision 6: Token Collection Detection

**Decision**: Token collection checked in a new `_update_tokens()` method called from `update()`.
Collection condition: `int(token.y) == PLAYER_ROW and token.x == player.x`. Removal condition:
`int(token.y) > PLAYER_ROW` (passed player row without collection). Tokens do not interact with
BolterRounds (FR-019) — token list is entirely separate from collision resolution.

**Rationale**: Mirrors the `_descend_enemies()` / `_update_boss_projectiles()` pattern. Clean separation
avoids modifying existing collision code.

---

## Decision 7: HUD Weapon Tier Label

**Decision**: Add weapon tier label to the existing `draw_hud()` row 1 stats line.
Labels: `BOLTER` (Standard), `TWIN-LNK` (Twin-Linked), `STORM` (Storm Bolter).
The label is appended after the lives display. Max label width is 8 chars; HUD row 1 has
~70 chars of free space at typical values.

**Rationale**: FR-014 requires HUD display. Row 1 (HUD stats) already shows SCORE, HI, WAVE, lives.
Adding the tier label is a safe addstr after lives string. No layout restructuring needed.

---

## Resolved Clarifications

| Question | Resolution |
|---|---|
| Does multi-row art affect collision boxes? | No — FR-003 explicitly constrains collision to anchor x; art is cosmetic only. |
| Should diagonal rounds collide at original x or drifted x? | Drifted x — round.x updates each tick before collision check, consistent with existing model. |
| Should token spawn position use float or int x? | Int x = enemy.x at time of death (no float x for enemies). |
| Can multiple tokens exist simultaneously? | Yes — tokens list; each tracked/collected independently (Edge Case in spec). |
| What happens to tokens during wave transition? | Tokens list cleared in `_spawn_wave()` (part of full state reset). |
