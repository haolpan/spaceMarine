# Data Model: Visual Fidelity & Bolter Upgrade System

**Feature**: `002-visual-bolter-upgrade`
**Date**: 2026-03-16

---

## New Entities

### WeaponTier (Enum)

Ordered three-level value representing the active Bolter upgrade state.

```
WeaponTier
├── STANDARD      (level 0 — default on game start and after life loss)
├── TWIN_LINKED   (level 1 — first upgrade)
└── STORM_BOLTER  (level 2 — max tier, collecting token at this level has no effect)
```

**Owned by**: `Player` dataclass (new field `weapon_tier: WeaponTier = WeaponTier.STANDARD`)
**Transitions**:
- STANDARD → TWIN_LINKED: token collected while at STANDARD
- TWIN_LINKED → STORM_BOLTER: token collected while at TWIN_LINKED
- STORM_BOLTER → STORM_BOLTER: token collected (no-op, capped — FR-013)
- any → STANDARD: life lost (FR-015)
- any → STANDARD: `reset()` called (new Player() defaults to STANDARD)

**HUD Labels** (FR-014):

| Tier | Label |
|---|---|
| STANDARD | `BOLTER` |
| TWIN_LINKED | `TWIN-LNK` |
| STORM_BOLTER | `STORM` |

---

### PowerUpToken (Dataclass)

Collectible object spawned on enemy death.

```python
@dataclass
class PowerUpToken:
    x: int       # column — equals enemy.x at time of death
    y: float     # row — starts at enemy y, descends each tick
```

**Spawn condition**: Enemy death triggers 15% random check (FR-010).
**Fall speed**: `POWERUP_FALL_SPEED = 0.5` rows/tick (1 row per 2 ticks — FR-011).
**Collection**: `int(token.y) == PLAYER_ROW and token.x == player.x` (FR-012).
**Removal**: `int(token.y) > PLAYER_ROW` — token passed player row without collection (FR-020).
**Render symbol**: `*` (single ASCII char, terminal-safe placeholder).

**Owned by**: `GameState.tokens: List[PowerUpToken]`
**Constraints**:
- Does NOT interact with BolterRounds (FR-019).
- Multiple tokens can exist simultaneously — each tracked independently.
- On `_spawn_wave()` / `reset()`: tokens list is cleared.
- Token falls past player row silently removed — no life loss, no score.

---

### BolterRound (Extended)

Existing dataclass extended with optional `dx` field for diagonal movement.

```python
@dataclass
class BolterRound:
    x: int
    y: int
    dx: int = 0   # NEW: column drift per tick (0 = straight, -1 = left, +1 = right)
```

**Standard round** (STANDARD tier): `dx=0` — travels straight up.
**Twin-Linked rounds** (TWIN_LINKED tier): two rounds at `(player.x - 1, dx=0)` and `(player.x + 1, dx=0)` — parallel straight shots.
**Storm Bolter rounds** (STORM_BOLTER tier): three rounds:
- Centre: `(player.x, dx=0)` — straight
- Left outer: `(player.x - 1, dx=-1)` — drifts left 1 col/tick
- Right outer: `(player.x + 1, dx=+1)` — drifts right 1 col/tick

**Movement per tick**: `round.x += round.dx; round.y -= 1`
**Removal**: existing `r.y >= PLAY_AREA_TOP` filter unchanged.
**Collision**: uses updated `r.x` (post-drift) against `e.x` — no code change needed beyond x update.

---

## Modified Entities

### Player (modified)

```python
@dataclass
class Player:
    x: int
    lives: int = 3
    score: int = 0
    weapon_tier: WeaponTier = field(default=WeaponTier.STANDARD)   # NEW
```

**Note**: `WeaponTier.STANDARD` is the default; `reset()` creates `Player(x=PLAYER_START_X)` which
automatically initialises `weapon_tier` to `STANDARD` — no extra reset code needed.

### GameState (modified)

New field added:
```python
self.tokens: List[PowerUpToken] = []   # NEW
```

New method added:
```python
def _update_tokens(self) -> None: ...  # NEW — called from update()
```

`_check_collisions()` modified: after enemy is confirmed dead, evaluate `POWERUP_DROP_CHANCE` and
conditionally spawn a `PowerUpToken`.

`_spawn_wave()` modified: `self.tokens = []` (clear tokens on new wave, same as enemies/boss).

---

## Constants (all in game.py)

```python
POWERUP_DROP_CHANCE  = 0.15   # FR-010 — 15% per enemy kill
POWERUP_FALL_SPEED   = 0.5    # FR-011 — 0.5 rows/tick = 1 row per 2 ticks
```

---

## State Transition Diagram

```
[Enemy killed]
    └── random() < 0.15 ?
            YES → PowerUpToken spawned at (enemy.x, enemy.y)
            NO  → nothing

[Token exists in gs.tokens]
    └── each tick: token.y += POWERUP_FALL_SPEED
            int(token.y) == PLAYER_ROW and token.x == player.x ?
                YES → collect → WeaponTier advances (if not STORM_BOLTER)
                int(token.y) > PLAYER_ROW ?
                YES → remove token (FR-020)

[Player life lost]
    └── player.weapon_tier = WeaponTier.STANDARD   (FR-015)

[Player fires SPACE]
    STANDARD     → 1 BolterRound(x=player.x, y=PLAYER_ROW-1, dx=0)
    TWIN_LINKED  → 2 rounds: (x-1, dx=0), (x+1, dx=0)
    STORM_BOLTER → 3 rounds: (x, dx=0), (x-1, dx=-1), (x+1, dx=+1)
```

---

## Entity Relationships

```
GameState
├── player: Player
│   └── weapon_tier: WeaponTier   (NEW)
├── enemies: List[EnemyUnit]
├── boss: Optional[BossUnit]
├── rounds: List[BolterRound]      (dx field added)
├── boss_rounds: List[BossProjectile]
├── tokens: List[PowerUpToken]     (NEW)
└── ...
```

---

## Visual Art (Renderer-Only — space_marine.py)

Multi-row art is entirely in `space_marine.py`. No art strings in game.py.

### Player (FR-001, FR-002)

Anchor row: `PLAYER_ROW` (row 23). Art row above: `PLAYER_ROW - 1` (row 22, shared with flavor text row).

> **Constraint**: PLAYER_ROW - 1 = row 22 is the flavor text + controls row. The player art head/weapon
> row must fit within the play area. Row 21 is the separator. Render player body at row 23, arm/weapon
> at row 22 only when flavor text is not rendered (NOT feasible — row 22 is always the status bar).

**Revised approach**: Player art fits in a single row at PLAYER_ROW using a wider symbol.
Current symbol `[℧]` is 3 chars. Expand to include weapon shape within same row: `[℧]` stays
as the clean Ultramarine badge. For the body row above, since row 22 is fixed as the flavor bar,
the player visual is necessarily single-row at PLAYER_ROW. FR-001 "minimum 2 rows and 3 columns"
is addressed by the symbol width (3 cols: `[`, `℧`, `]`) and height within the play area constraints.

> **Note for tasks**: Confirm during implementation whether a second player row is feasible without
> HUD/border corruption (SC-007). If row 22 cannot host player art, the spec's multi-row intent
> is satisfied by width (3 cols) + lore-accurate Ultima mark (FR-002). The implementation plan
> treats this as rendering-only with no logic impact.

### Enemy Symbols (FR-004..FR-007)

| Entity | Current | Proposed | Rationale |
|---|---|---|---|
| Termagant | `🌀` (emoji — potentially double-width) | `⟲` (U+27F2) | Anticlockwise arrow, insectoid motion, single-width |
| Chaos Marine | `☸️` (emoji variant) | `✵` (U+2735) | Eight-spoked asterisk, Chaos Undivided, single-width |
| Ork Boy | `₩` | `₩` (U+20A9) | Keep — jagged Won sign, brutish, already single-width |

> These symbols were selected by the user based on lore accuracy (see memory: feedback_visual_symbols.md).
> Do not change without user confirmation.

### Boss Art (FR-008, FR-009)

Bosses currently render: symbol at `(row, b.x-1)` + HP bar at `(row-1, ...)`.
FR-008 requires minimum 3 cols wide × 2 rows tall. Current symbol `[H]`, `[X]`, `[W]` = 3 cols.
Add a top art row at `row-2` (above the HP bar at `row-1`) showing an imposing glyph.
FR-009: "additional visual row MUST appear above the existing label/HP-bar row; existing label logic unchanged."

Boss art rows: `row-2` (new art), `row-1` (existing HP bar), `row` (existing symbol).
