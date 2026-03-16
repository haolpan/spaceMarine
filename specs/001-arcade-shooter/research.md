# Research: Space Marine Arcade Shooter

**Branch**: `001-arcade-shooter` | **Date**: 2026-03-15

## R-001: Non-Blocking Game Loop in Python curses

**Question**: How do we implement a responsive game loop in Python curses without
blocking on keyboard input?

**Decision**: Use `stdscr.nodelay(True)` to make `getch()` non-blocking (returns -1
when no key is pressed) combined with `time.sleep(FRAME_DELAY)` for frame pacing.

**Rationale**: This is the standard curses game loop pattern. It handles input
without blocking, allows game state to advance every tick, and keeps the frame rate
predictable. `stdscr.timeout(ms)` is an alternative but `nodelay + sleep` is simpler
to reason about and easier to unit test (the sleep can be mocked).

**Alternatives considered**:
- `select()` on stdin: more complex, non-portable on Windows, not needed here.
- Dedicated input thread: adds concurrency complexity; overkill for a single-player game.
- `stdscr.timeout(50)`: functionally equivalent but less readable alongside `sleep`.

---

## R-002: Separating Game Logic from curses for Testability

**Question**: How do we make game logic unit-testable without a real terminal?

**Decision**: Split into two files — `game.py` (zero curses imports, pure logic)
and `space_marine.py` (curses only). `game.py` exposes `GameState`, `handle_input()`,
and `update()`. The renderer in `space_marine.py` reads from `GameState` read-only.

**Rationale**: The constitution explicitly requires this separation. With `game.py`
having no curses dependency, `unittest` can import and exercise all game logic
(collision, wave progression, scoring, state transitions) in any environment.
The renderer is purely I/O and need not be tested.

**Alternatives considered**:
- Single file with curses mocked in tests: fragile mock maintenance, tightly coupled.
- Abstract renderer interface: unnecessary abstraction for two files; YAGNI.
- `game.py` + `entities.py` + `waves.py`: splits beyond the 3-file budget for no
  concrete testability gain at this scale.

---

## R-003: Enemy Movement and Frame-Rate Independence

**Question**: How do we vary enemy descent speed per wave without changing the frame rate?

**Decision**: Store enemy `y` position as `float`. Each tick, advance
`enemy.y += speed_multiplier / FPS` where `FPS = 20`. Collision checks use
`int(enemy.y)` for grid-cell matching. Wave speed multiplier scales the float
advancement rate.

**Rationale**: Fractional positions decouple speed from frame rate. A wave-1 enemy
at `speed_mult = 1.0` descends one row every 20 ticks (1 second). A wave-5 enemy
at `speed_mult = 1.60` descends the same row in ~12.5 ticks (~0.63s). This gives
a smooth, parameterizable difficulty curve without touching the game loop timer.

**Alternatives considered**:
- Integer positions with per-N-tick movement: produces stepped/discrete difficulty;
  harder to tune smoothly.
- Vary `FRAME_DELAY`: changes input responsiveness undesirably.

---

## R-004: Wave Difficulty Progression Formula

**Question**: What mathematical formula produces a difficulty curve that feels
appropriately escalating without becoming unplayable too quickly?

**Decision**:
```
speed_multiplier = 1.0 + (wave - 1) × 0.15   # 15% faster per wave
enemy_count      = min(8 + (wave - 1) × 2, 30) # +2 per wave, capped at 30
enemy_hp         = 1 + (wave - 1) // 3          # +1 HP every 3 waves
```

**Rationale**: A 15% speed increase per wave is a well-tested arcade ramp (similar
to the original Space Invaders speed escalation). It keeps wave 1 accessible to new
players while making wave 10 (2.35×) noticeably challenging. The count cap at 30
prevents the play area from being completely filled. HP increasing every 3 waves
rather than every wave gives players time to adjust to the speed increase first.

**Alternatives considered**:
- Exponential speed: `speed = 1.0 × 1.15^(wave-1)` — same as linear for small N
  but diverges faster at high waves; considered too punishing after wave 15.
- HP increases every wave: too punishing in combination with speed increases.
- No HP scaling: makes higher waves feel the same; rejected.

---

## R-005: Boss Mechanic Feasibility in a Terminal

**Question**: What boss mechanics are actually implementable and observable in a
character-cell terminal game?

**Decision**: Three mechanics selected, each feasible within curses character rendering:

1. **Zigzag movement** (Hive Tyrant): Boss moves horizontally left/right while
   descending, reversing direction every 15 ticks. Visible as diagonal/zigzag
   path. Implementation: `boss.direction` flips sign; `boss.x += boss.direction`
   every 15 ticks.

2. **Return fire** (Chaos Terminator): Boss emits a `BossProjectile` downward
   toward the player's x position every 30 ticks. Player loses a life if projectile
   reaches player row. Implementation: a `boss_rounds: list[BossProjectile]` list
   in `GameState`, advancing downward each tick.

3. **Split on death** (Ork Warboss): When boss HP reaches 0, instead of simply
   removing it, spawn 3 `EnemyUnit` of type `"ork_boy"` at positions
   `boss.x - 1`, `boss.x`, `boss.x + 1` at `boss.y`. Implementation:
   `GameState.update()` checks death and calls `spawn_split_enemies()`.

**Alternatives considered**:
- Teleportation: disorienting in a small play area; rejected.
- Shield mechanic (requires hitting weak spot): ASCII art constraints make it hard
  to communicate visually; rejected.
- Speed burst: too similar to normal wave speed increase; rejected.

---

## R-006: High Score Persistence

**Question**: Should high score persist across process restarts, and if so, how?

**Decision**: In-session persistence is mandatory (FR-016). File-based persistence
is optional (constitution: "SHOULD, not MUST"). Implement as optional: on startup,
attempt to read `~/.space_marine_score.json`; on game over, write if new high score.
Wrap in try/except — failure to read/write is silently ignored.

**Rationale**: The player should not need a writable filesystem to play the game.
Silent fail-safe makes persistence a bonus, not a requirement. `json` is the
simplest stdlib choice; `pickle` offers no advantage here.

**Alternatives considered**:
- Always required persistence: violates zero-dependency portability in read-only
  environments.
- `pickle`: binary format, no human readability benefit over json for a single int.
- SQLite: massively overengineered for one integer.

---

## R-007: Minimum Terminal Size Enforcement

**Question**: How do we detect and handle a terminal that is too small?

**Decision**: At the start of `run_game(stdscr)`, call `stdscr.getmaxyx()` to get
`(rows, cols)`. If `rows < 24 or cols < 80`, print a clear message using
`stdscr.addstr(0, 0, "Terminal too small. Minimum 80x24 required.")`, call
`stdscr.getch()` once (wait for acknowledgement), then raise `SystemExit`.
`curses.wrapper` handles terminal cleanup on exit.

**Rationale**: Attempting to render outside terminal bounds raises a curses exception
(`_curses.error: addstr() returned ERR`). Proactive checking with a readable message
is more user-friendly than an unhandled exception stack trace.

**Alternatives considered**:
- `try/except _curses.error`: catches but doesn't explain; poor UX.
- Dynamic layout that adapts to terminal size: scope creep; violates constitution
  "no required terminal configuration".

---

## All Unknowns Resolved

| Unknown | Resolution |
|---------|------------|
| Game loop pattern | `nodelay(True)` + `time.sleep(0.05)` |
| Testability approach | Two-file split: `game.py` (no curses) + `space_marine.py` |
| Speed parameterization | Float `y` positions, `speed_mult / FPS` advancement |
| Difficulty formula | Linear speed 15%/wave, count +2/wave (cap 30), HP +1/3waves |
| Boss mechanics | Zigzag, Return fire, Split — all feasible in curses |
| High score persistence | Optional JSON file, silent fail-safe |
| Terminal size check | `getmaxyx()` at startup with readable error message |
