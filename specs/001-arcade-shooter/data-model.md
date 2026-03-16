# Data Model: Space Marine Arcade Shooter

**Branch**: `001-arcade-shooter` | **Date**: 2026-03-15

## Entities

### Phase (enum)

Represents the current game phase / state machine node.

| Value | Meaning |
|-------|---------|
| `START` | Title screen — awaiting player input to begin |
| `PLAYING` | Active gameplay — input and physics processing active |
| `WAVE_TRANSITION` | Brief pause between waves — "Wave N incoming" message |
| `GAME_OVER` | Session ended — showing final score and restart prompt |
| `QUIT` | Exit signal — curses loop terminates |

**Transitions**:
```text
START           → PLAYING          (Enter or 'r' pressed)
PLAYING         → WAVE_TRANSITION  (all enemies destroyed and no boss alive)
WAVE_TRANSITION → PLAYING          (transition_ticks counter reaches 0; next wave spawned)
PLAYING         → GAME_OVER        (player.lives reaches 0)
GAME_OVER       → PLAYING          (Enter or 'r' pressed — reinitialises GameState)
Any             → QUIT             ('q' pressed)
```

---

### Player

The player-controlled Space Marine character.

| Field | Type | Description |
|-------|------|-------------|
| `x` | `int` | Current column position within play area (0 = leftmost valid column) |
| `lives` | `int` | Remaining lives; starts at 3; game over when 0 |
| `score` | `int` | Current session score; increments on enemy/boss destruction |

**Constraints**:
- `x` MUST remain within `[PLAY_AREA_LEFT, PLAY_AREA_RIGHT]` (inclusive).
- `lives` MUST NOT go below 0 (clamped on decrement).
- `score` MUST NOT go below 0.

---

### EnemyType (enum)

Defines the three standard enemy factions.

| Value | Label (player-facing) | Symbol | Base HP | Base speed | Score value |
|-------|-----------------------|--------|---------|------------|-------------|
| `TERMAGANT` | Tyranid Termagant | `T` | 1 | 1.00 | 10 |
| `CHAOS_MARINE` | Chaos Space Marine | `C` | 1 | 0.70 | 15 |
| `ORK_BOY` | Ork Boy | `O` | 2 | 0.50 | 20 |

---

### EnemyUnit

A single descending hostile unit. All standard enemies share this type.

| Field | Type | Description |
|-------|------|-------------|
| `x` | `int` | Current column position (character cell) |
| `y` | `float` | Current row position; fractional for smooth speed scaling |
| `enemy_type` | `EnemyType` | Determines label, symbol, base speed and score |
| `hp` | `int` | Remaining hit points; destroyed when 0 |
| `speed` | `float` | Row-descent rate per tick = `base_speed × wave_speed_mult` |
| `score_value` | `int` | Points awarded to player on destruction |

**Constraints**:
- `hp` MUST NOT be set to a value ≤ 0 at spawn time.
- `y` advances by `speed / FPS` per tick (where `FPS = 20`).
- When `int(y) >= PLAYER_ROW`: enemy has reached the player row → trigger life loss.
- `x` MUST remain within play area bounds; enemies do not move horizontally
  (except bosses — see BossUnit).

---

### BossMechanic (enum)

Defines the unique combat behaviour of each boss type.

| Value | Description |
|-------|-------------|
| `ZIGZAG` | Alternates horizontal direction every 15 ticks while descending |
| `FIRES_BACK` | Launches a `BossProjectile` toward the player's x position every 30 ticks |
| `SPLITS` | On death, spawns 3 `EnemyUnit` of type `ORK_BOY` at the boss position |

---

### BossUnit

A special high-HP enemy appearing at wave milestones (waves 5, 10, 15, …).
Extends `EnemyUnit` with boss-specific state.

| Field | Type | Description |
|-------|------|-------------|
| (all `EnemyUnit` fields) | | Inherited |
| `label` | `str` | Lore-accurate boss name (e.g., "Hive Tyrant") |
| `mechanic` | `BossMechanic` | Which unique behaviour this boss exhibits |
| `mechanic_tick` | `int` | Internal tick counter for mechanic timing |
| `direction` | `int` | `+1` or `-1`; used by `ZIGZAG` mechanic for horizontal movement |
| `phase` | `int` | Reserved for multi-phase behaviour (future use); defaults to 0 |

**Boss catalog** (cycle repeats after wave 15 with +5 HP per cycle):

| Boss index | Wave | Label | HP | Mechanic | Score |
|-----------|------|-------|----|----------|-------|
| 0 | 5, 20, 35… | Hive Tyrant | 10 | `ZIGZAG` | 200 |
| 1 | 10, 25, 40… | Chaos Terminator | 15 | `FIRES_BACK` | 300 |
| 2 | 15, 30, 45… | Ork Warboss | 12 | `SPLITS` | 250 |

HP for repeat cycles: `base_hp + 5 × cycle_number` where `cycle_number` = how many
times this boss index has appeared before (0 for first appearance).

---

### BolterRound

A projectile fired upward by the player. Multiple can exist simultaneously.

| Field | Type | Description |
|-------|------|-------------|
| `x` | `int` | Column position (fixed at fire time; does not change) |
| `y` | `int` | Current row; decrements by 1 per tick (moves upward) |

**Constraints**:
- Removed from `GameState.rounds` when `y < PLAY_AREA_TOP` (exits screen).
- Removed (along with hit enemy) when `x == enemy.x and y == int(enemy.y)`.
- `x` is the player's `x` at the moment of firing.

---

### BossProjectile

A projectile fired downward by a `FIRES_BACK` boss. Moves toward the player row.

| Field | Type | Description |
|-------|------|-------------|
| `x` | `int` | Column position (player's x at time of firing) |
| `y` | `int` | Current row; increments by 1 per tick (moves downward) |

**Constraints**:
- Removed when `y >= PLAYER_ROW` (reaches bottom) or when it hits the player
  (`x == player.x and y == PLAYER_ROW`).
- Hitting player: decrement `player.lives`.

---

### WaveDifficulty

Value object describing the parameters for a specific wave number. Not stored in
`GameState` persistently — computed fresh by `wave_difficulty(wave_number)`.

| Field | Type | Description |
|-------|------|-------------|
| `wave_number` | `int` | 1-based wave index |
| `speed_multiplier` | `float` | Applied to all enemy base speeds this wave |
| `enemy_count` | `int` | Total enemies to spawn (including boss slot) |
| `enemy_hp_mult` | `int` | HP multiplier applied at spawn time |
| `enemy_types` | `list[EnemyType]` | Pool of enemy types available this wave |
| `has_boss` | `bool` | `True` when `wave_number % 5 == 0` |

**Computation**:
```text
speed_multiplier = 1.0 + (wave_number - 1) × 0.15
enemy_count      = min(8 + (wave_number - 1) × 2, 30)
enemy_hp_mult    = 1 + (wave_number - 1) // 3
enemy_types      = [TERMAGANT]
                 + ([CHAOS_MARINE] if wave_number >= 3)
                 + ([ORK_BOY]     if wave_number >= 5)
has_boss         = (wave_number % 5 == 0)
```

---

### GameState

The root state object. Owns all mutable game data. `game.py` exposes only this
class to the renderer; the renderer reads fields but never writes them directly.

| Field | Type | Description |
|-------|------|-------------|
| `phase` | `Phase` | Current game phase / state machine node |
| `player` | `Player` | The player character |
| `enemies` | `list[EnemyUnit]` | All active standard enemies on screen |
| `boss` | `Optional[BossUnit]` | Active boss, or `None` when no boss present |
| `rounds` | `list[BolterRound]` | All active player projectiles |
| `boss_rounds` | `list[BossProjectile]` | Active boss projectiles (FIRES_BACK mechanic) |
| `wave_number` | `int` | Current wave index (1-based) |
| `high_score` | `int` | Highest score achieved this process session |
| `tick` | `int` | Frame counter since last phase transition; resets on transition |
| `transition_ticks` | `int` | Remaining ticks in WAVE_TRANSITION phase (counts down from 60) |

**Key methods** (implemented in `game.py`):
- `handle_input(key: int) -> None` — dispatches key to phase-appropriate handler.
- `update() -> None` — advances one game tick: moves enemies/rounds, checks
  collisions, evaluates phase transitions.
- `_spawn_wave(wave_number: int) -> None` — populates `self.enemies` and
  optionally `self.boss` for the given wave.
- `_check_collisions() -> None` — resolves round/enemy and enemy/player overlaps.
- `reset() -> None` — reinitialises all fields to start-of-session defaults
  while preserving `high_score`.

## State Transitions — Detail

```text
WAVE_TRANSITION entry:
  transition_ticks = 60  (3 seconds at 20 FPS)

WAVE_TRANSITION tick:
  transition_ticks -= 1
  if transition_ticks == 0:
    wave_number += 1
    _spawn_wave(wave_number)
    phase = PLAYING

GAME_OVER entry:
  if player.score > high_score:
    high_score = player.score
    _write_high_score_file()  # silent fail-safe

reset() (called on restart):
  player = Player(x=PLAYER_START_X, lives=3, score=0)
  enemies = []
  boss = None
  rounds = []
  boss_rounds = []
  wave_number = 0
  tick = 0
  transition_ticks = 0
  phase = PLAYING
  _spawn_wave(1)
  # high_score is NOT reset
```

## Layout Constants (defined in `game.py`)

| Constant | Value | Description |
|----------|-------|-------------|
| `SCREEN_ROWS` | 24 | Minimum required terminal rows |
| `SCREEN_COLS` | 80 | Minimum required terminal columns |
| `HUD_ROWS` | 3 | Rows consumed by top HUD (rows 0–2) |
| `PLAY_AREA_TOP` | 3 | First row of the play area |
| `PLAYER_ROW` | 23 | Row where the Space Marine stands |
| `PLAY_AREA_LEFT` | 1 | Leftmost valid column for player and enemies |
| `PLAY_AREA_RIGHT` | 78 | Rightmost valid column for player and enemies |
| `PLAYER_START_X` | 39 | Starting column (center) |
| `FPS` | 20 | Target frames per second |
| `FRAME_DELAY` | 0.05 | Sleep duration per tick (seconds) |
| `TRANSITION_TICKS` | 60 | Ticks spent in WAVE_TRANSITION phase |
| `BOSS_MECHANIC_TICK` | 15/30 | Ticks between mechanic activations (zigzag/fire) |
