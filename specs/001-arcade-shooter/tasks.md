---

description: "Task list for Space Marine Arcade Shooter"
---

# Tasks: Space Marine Arcade Shooter

**Input**: Design documents from `/specs/001-arcade-shooter/`
**Prerequisites**: plan.md ✅, spec.md ✅, data-model.md ✅, contracts/controls.md ✅, research.md ✅

**Tests**: Unit tests are included per user request (game logic layer only; curses
renderer is excluded from automated testing per the constitution and plan).

**Ordering rule**: For each user story — implement `game.py` logic → run unit tests
(must pass) → implement renderer in `space_marine.py` → manual play-test. Never
touch the renderer for a story until its tests are green.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different code areas, no unresolved dependencies)
- **[Story]**: US1, US2, US3, US4 — maps to spec.md user stories
- File paths are relative to the repository root

---

## Phase 1: Setup

**Purpose**: Create the repository file structure and skeleton files so all subsequent
tasks have a known location to write into.

- [X] T001 Create directory layout: `game.py`, `space_marine.py`, `tests/__init__.py`, `tests/test_game.py` at repository root (all files empty)
- [X] T002 [P] Add all layout constants and stdlib imports to `game.py`: `from __future__ import annotations`, `from dataclasses import dataclass, field`, `from enum import Enum, auto`, `import random`, `import json`, `import os`; then define `SCREEN_ROWS = 24`, `SCREEN_COLS = 80`, `HUD_ROWS = 3`, `PLAY_AREA_TOP = 3`, `PLAYER_ROW = 23`, `PLAY_AREA_LEFT = 1`, `PLAY_AREA_RIGHT = 78`, `PLAYER_START_X = 39`, `FPS = 20`, `FRAME_DELAY = 0.05`, `TRANSITION_TICKS = 60`
- [X] T003 [P] Add unittest skeleton to `tests/test_game.py`: `import unittest`, `import sys`, `import os`, `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))`, `import game`; empty `class TestSpaceMarine(unittest.TestCase): pass`; `if __name__ == '__main__': unittest.main()`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define all data structures that every user story implementation depends
on. No user story work begins until this phase is complete.

**⚠️ CRITICAL**: All Phase 3+ tasks depend on these structures existing.

- [X] T004 [P] Implement `Phase` enum in `game.py`: `class Phase(Enum): START = auto(); PLAYING = auto(); WAVE_TRANSITION = auto(); GAME_OVER = auto(); QUIT = auto()`
- [X] T005 [P] Implement `EnemyType` enum in `game.py` with values `TERMAGANT`, `CHAOS_MARINE`, `ORK_BOY`; then define `ENEMY_DATA: dict` mapping each to `{"label": str, "symbol": str, "base_hp": int, "base_speed": float, "score_value": int}` using the values from data-model.md (Termagant: symbol T, HP 1, speed 1.0, score 10; Chaos Marine: C, 1, 0.7, 15; Ork Boy: O, 2, 0.5, 20)
- [X] T006 [P] Implement `BossMechanic` enum in `game.py` with `ZIGZAG`, `FIRES_BACK`, `SPLITS`; then define `BOSS_CATALOG: list[dict]` with three entries: index 0 Hive Tyrant (HP 10, ZIGZAG, score 200), index 1 Chaos Terminator (HP 15, FIRES_BACK, score 300), index 2 Ork Warboss (HP 12, SPLITS, score 250)
- [X] T007 [P] Implement `Player` dataclass in `game.py`: fields `x: int`, `lives: int = 3`, `score: int = 0`
- [X] T008 Implement `EnemyUnit` dataclass in `game.py`: fields `x: int`, `y: float`, `enemy_type: EnemyType`, `hp: int`, `speed: float`, `score_value: int`; add `@property symbol(self) -> str` returning `ENEMY_DATA[self.enemy_type]["symbol"]`; add `@property label(self) -> str` returning `ENEMY_DATA[self.enemy_type]["label"]`
- [X] T009 Implement `BossUnit` dataclass in `game.py` extending `EnemyUnit`; add fields `label: str`, `mechanic: BossMechanic`, `mechanic_tick: int = 0`, `direction: int = 1`, `phase: int = 0`; override `symbol` property to return first character of label wrapped in brackets (e.g. `[H]`)
- [X] T010 [P] Implement `BolterRound` dataclass in `game.py`: fields `x: int`, `y: int`
- [X] T011 [P] Implement `BossProjectile` dataclass in `game.py`: fields `x: int`, `y: int`
- [X] T012 Implement `GameState.__init__(self)` in `game.py`: set `phase = Phase.START`, `player = Player(x=PLAYER_START_X)`, `enemies: list[EnemyUnit] = []`, `boss: BossUnit | None = None`, `rounds: list[BolterRound] = []`, `boss_rounds: list[BossProjectile] = []`, `wave_number: int = 0`, `tick: int = 0`, `transition_ticks: int = 0`; read `high_score: int` from `~/.space_marine_score.json` if it exists (wrap in `try/except`, default to 0 on any error)

**Checkpoint**: All data structures defined — user story implementation can now begin.

---

## Phase 3: User Story 1 - Player Movement & Firing (Priority: P1) 🎯 MVP

**Goal**: Controllable Space Marine in the terminal — moves left/right, fires Bolter
rounds upward. No enemies yet.

**Independent Test**: `python space_marine.py` → Space Marine appears on row 23 →
arrow keys and A/D move it left/right → Space fires `│` symbols upward → Q quits
cleanly. Fully demonstrable without enemies.

### Tests for User Story 1 ⚠️ — Write first, confirm they FAIL, then implement

- [X] T013 [P] [US1] In `tests/test_game.py` add `test_player_move_left_within_bounds`: create `GameState`, force `phase=Phase.PLAYING`, set `player.x = PLAY_AREA_LEFT + 5`; call `handle_input(curses.KEY_LEFT)`; assert `player.x == PLAY_AREA_LEFT + 4`
- [X] T014 [P] [US1] In `tests/test_game.py` add `test_player_move_left_clamps_at_boundary`: set `player.x = PLAY_AREA_LEFT`; call `handle_input(curses.KEY_LEFT)`; assert `player.x == PLAY_AREA_LEFT` (no wrap)
- [X] T015 [P] [US1] In `tests/test_game.py` add `test_player_move_right_clamps_at_boundary`: set `player.x = PLAY_AREA_RIGHT`; call `handle_input(curses.KEY_RIGHT)`; assert `player.x == PLAY_AREA_RIGHT`
- [X] T016 [P] [US1] In `tests/test_game.py` add `test_fire_creates_bolter_round_above_player`: set `player.x = 20`, `phase=Phase.PLAYING`; call `handle_input(ord(' '))`; assert `len(rounds) == 1` and `rounds[0].x == 20` and `rounds[0].y == PLAYER_ROW - 1`
- [X] T017 [P] [US1] In `tests/test_game.py` add `test_bolter_round_removed_at_top`: add a `BolterRound(x=10, y=PLAY_AREA_TOP)` to `rounds`; call `update()`; assert `len(rounds) == 0`
- [X] T018 [P] [US1] In `tests/test_game.py` add `test_start_to_playing_on_enter`: assert `phase == Phase.START` initially; call `handle_input(ord('\n'))`; assert `phase == Phase.PLAYING`

### Implementation for User Story 1

- [X] T019 [US1] Implement `GameState.handle_input(self, key: int)` in `game.py` for `Phase.START`: on `key in (ord('\n'), ord('\r'), ord('r'))` → set `phase = Phase.PLAYING`, `wave_number = 1`, call `_spawn_wave(1)` (stub for now: `self.enemies = []`); on `key == ord('q')` → `phase = Phase.QUIT`
- [X] T020 [US1] Implement `GameState.handle_input()` in `game.py` for `Phase.PLAYING`: on `curses.KEY_LEFT` or `ord('a')` → `player.x = max(PLAY_AREA_LEFT, player.x - 1)`; on `curses.KEY_RIGHT` or `ord('d')` → `player.x = min(PLAY_AREA_RIGHT, player.x + 1)`; on `ord(' ')` → append `BolterRound(x=player.x, y=PLAYER_ROW - 1)` to `rounds`; on `ord('q')` → `phase = Phase.QUIT`
- [X] T021 [US1] Implement `GameState.update()` in `game.py` for BolterRound movement: if `phase != Phase.PLAYING` return early; for each round decrement `y` by 1; remove rounds where `y < PLAY_AREA_TOP`
- [X] T022 [US1] Run unit tests: `python -m unittest tests.test_game -v` — all T013–T018 tests MUST pass before proceeding to renderer tasks
- [X] T023 [US1] Implement terminal size check at top of `run_game(stdscr)` in `space_marine.py`: call `stdscr.getmaxyx()`; if `rows < SCREEN_ROWS or cols < SCREEN_COLS` display `"Terminal too small. Minimum 80x24 required. Press any key."` centered on screen, call `stdscr.getch()`, then `return`
- [X] T024 [US1] Implement start screen renderer `draw_start_screen(stdscr)` in `space_marine.py`: clear screen; draw title `"*** SPACE MARINE ***"` centered on row 8; draw subtitle `"A Warhammer 40,000 Arcade Experience"` on row 9; draw controls block (rows 12–15: movement, fire, quit keys); draw `"Press ENTER or R to begin"` on row 17; draw `"For the Emperor!"` on row 18
- [X] T025 [US1] Implement main game loop `run_game(stdscr)` in `space_marine.py` and `curses.wrapper(run_game)` entry at module bottom: `stdscr.nodelay(True)`, `curses.curs_set(0)`, `game = GameState()`; `while game.phase != Phase.QUIT`: call `key = stdscr.getch()`; `game.handle_input(key)`; `game.update()`; dispatch to appropriate draw function by phase; `time.sleep(FRAME_DELAY)`; add `import curses, time, sys` and `from game import *` at top of `space_marine.py`
- [X] T026 [US1] Implement `draw_game(stdscr, game)` in `space_marine.py` for Phase.PLAYING: clear screen; draw border (row 0: title bar, row 2 and row 21: `═` separator lines); draw player `[◙]` at `(PLAYER_ROW, player.x - 1)` (3-char wide, centered on `player.x`); draw each BolterRound `│` at `(round.y, round.x)`; draw status line row 22 `"← → move  SPACE fire  Q quit"`
- [X] T027 [US1] Manual play-test US1: run `python space_marine.py` → confirm start screen appears → press Enter → Space Marine `[◙]` visible on row 23 → arrow keys move left/right and stop at boundaries → Space fires `│` rounds that travel upward and disappear at top → Q quits and terminal restored

**Checkpoint**: ✅ US1 complete — first playable build. Controllable Space Marine with Bolter fire.

---

## Phase 4: User Story 2 - Enemy Wave Combat (Priority: P2)

**Goal**: Enemies spawn in formation, descend toward the player, can be shot. Waves
auto-advance. Game Over when lives reach zero.

**Independent Test**: Play through waves 1–3 — enemies appear, descend, are destroyed
by Bolter rounds; player loses a life when an enemy passes; new wave spawns after
clearing; Game Over screen appears after all lives are lost.

### Tests for User Story 2 ⚠️ — Write first, confirm they FAIL, then implement

- [X] T028 [P] [US2] In `tests/test_game.py` add `test_wave_difficulty_wave1`: call `wave_difficulty(1)`; assert `speed_multiplier == 1.0`, `enemy_count == 8`, `enemy_hp_mult == 1`, `has_boss == False`, `EnemyType.TERMAGANT in enemy_types`
- [X] T029 [P] [US2] In `tests/test_game.py` add `test_wave_difficulty_wave3_has_chaos_marines`: call `wave_difficulty(3)`; assert `EnemyType.CHAOS_MARINE in enemy_types` and `EnemyType.TERMAGANT in enemy_types`
- [X] T030 [P] [US2] In `tests/test_game.py` add `test_wave_difficulty_wave5_has_all_types_and_boss`: call `wave_difficulty(5)`; assert all three `EnemyType` values in `enemy_types` and `has_boss == True`
- [X] T031 [P] [US2] In `tests/test_game.py` add `test_spawn_wave_creates_correct_enemy_count`: call `game._spawn_wave(1)`; assert `len(game.enemies) == 8`; call `game._spawn_wave(2)`; assert `len(game.enemies) == 10`
- [X] T032 [P] [US2] In `tests/test_game.py` add `test_round_hits_enemy_removes_both`: manually place one `EnemyUnit` (type TERMAGANT, hp=1) at `(x=20, y=10.0)` and one `BolterRound` at `(x=20, y=10)` in `game.enemies` and `game.rounds`; set `phase=Phase.PLAYING`; call `game.update()`; assert `len(game.enemies) == 0` and `len(game.rounds) == 0`
- [X] T033 [P] [US2] In `tests/test_game.py` add `test_round_hit_adds_score`: same setup as T032; assert `game.player.score == 10` after `update()`
- [X] T034 [P] [US2] In `tests/test_game.py` add `test_enemy_reaching_player_row_decrements_lives`: place one `EnemyUnit` at `(x=20, y=float(PLAYER_ROW))`; set `phase=Phase.PLAYING`, `player.lives=3`; call `update()`; assert `player.lives == 2` and `len(game.enemies) == 0`
- [X] T035 [P] [US2] In `tests/test_game.py` add `test_all_enemies_cleared_triggers_wave_transition`: set `phase=Phase.PLAYING`, `enemies=[]`, `boss=None`; call `update()`; assert `phase == Phase.WAVE_TRANSITION` and `transition_ticks == TRANSITION_TICKS`
- [X] T036 [P] [US2] In `tests/test_game.py` add `test_wave_transition_countdown_spawns_next_wave`: set `phase=Phase.WAVE_TRANSITION`, `wave_number=1`, `transition_ticks=1`; call `update()`; assert `phase == Phase.PLAYING` and `wave_number == 2` and `len(game.enemies) > 0`
- [X] T037 [P] [US2] In `tests/test_game.py` add `test_lives_zero_triggers_game_over`: set `phase=Phase.PLAYING`, `player.lives=0`; call `update()`; assert `phase == Phase.GAME_OVER`

### Implementation for User Story 2

- [X] T038 [US2] Implement `wave_difficulty(wave_number: int) -> WaveDifficulty` as a module-level function in `game.py`: compute `speed_multiplier = round(1.0 + (wave_number - 1) * 0.15, 2)`, `enemy_count = min(8 + (wave_number - 1) * 2, 30)`, `enemy_hp_mult = 1 + (wave_number - 1) // 3`, `enemy_types` list starting with TERMAGANT + CHAOS_MARINE if wave>=3 + ORK_BOY if wave>=5, `has_boss = (wave_number % 5 == 0)`; return a `WaveDifficulty` dataclass (or namedtuple) with these fields
- [X] T039 [US2] Implement `WaveDifficulty` dataclass in `game.py`: fields `wave_number: int`, `speed_multiplier: float`, `enemy_count: int`, `enemy_hp_mult: int`, `enemy_types: list`, `has_boss: bool`
- [X] T040 [US2] Implement `GameState._spawn_wave(self, wave_number: int)` in `game.py`: call `wave_difficulty(wave_number)` to get params; clear `self.enemies`; distribute `enemy_count` enemies evenly across two rows starting at `y = float(PLAY_AREA_TOP)` and `y = float(PLAY_AREA_TOP + 1)` with `x` positions spread between `PLAY_AREA_LEFT + 2` and `PLAY_AREA_RIGHT - 2`; pick enemy type randomly from `difficulty.enemy_types` for each; set `hp = ENEMY_DATA[type]["base_hp"] * difficulty.enemy_hp_mult`; set `speed = ENEMY_DATA[type]["base_speed"] * difficulty.speed_multiplier`; set `score_value = ENEMY_DATA[type]["score_value"]`; if `has_boss` set `self.boss = None` (boss spawning added in US3); set `self.boss = None` for now
- [X] T041 [US2] Implement enemy descent in `GameState.update()` in `game.py`: for each enemy in `self.enemies` increment `enemy.y += enemy.speed / FPS`; use `list` comprehension — create new list excluding enemies where `int(enemy.y) >= PLAYER_ROW`, decrement `player.lives` and clamp to 0 for each removed enemy
- [X] T042 [US2] Implement `GameState._check_collisions(self)` in `game.py` for round-hits-enemy: iterate all `(round, enemy)` pairs; when `round.x == enemy.x and round.y == int(enemy.y)`: decrement `enemy.hp`, add `enemy.score_value` to `player.score` if `hp <= 0`; collect indices to remove; rebuild `self.enemies` and `self.rounds` without removed items (avoid mutating lists while iterating)
- [X] T043 [US2] Add `_check_collisions()` call inside `update()` in `game.py` after enemy positions are advanced; add PLAYING→WAVE_TRANSITION check: if `phase == Phase.PLAYING` and `len(enemies) == 0` and `boss is None` → set `phase = Phase.WAVE_TRANSITION`, `transition_ticks = TRANSITION_TICKS`
- [X] T044 [US2] Implement `Phase.WAVE_TRANSITION` handling in `GameState.update()` in `game.py`: decrement `transition_ticks`; when `transition_ticks == 0`: increment `wave_number`, call `_spawn_wave(wave_number)`, set `phase = Phase.PLAYING`
- [X] T045 [US2] Implement lives==0 → GAME_OVER check in `GameState.update()` in `game.py`: after collision processing, if `player.lives <= 0`: update `high_score` if `player.score > high_score`; write high score to `~/.space_marine_score.json` (wrap in `try/except`); set `phase = Phase.GAME_OVER`
- [X] T046 [US2] Run unit tests: `python -m unittest tests.test_game -v` — all T028–T037 tests MUST pass before renderer tasks
- [X] T047 [US2] Add enemy renderer to `draw_game(stdscr, game)` in `space_marine.py`: for each enemy draw `enemy.symbol` at `(int(enemy.y), enemy.x)` (skip if y < PLAY_AREA_TOP or y > PLAYER_ROW - 1)
- [X] T048 [US2] Implement `draw_wave_transition(stdscr, game)` in `space_marine.py`: clear screen; draw `"=== WAVE {game.wave_number + 1} INCOMING ==="` centered on row 10; draw `"Prepare, Battle-Brother."` on row 12; draw remaining `transition_ticks` as countdown bar
- [X] T049 [US2] Implement `draw_game_over(stdscr, game)` in `space_marine.py`: clear screen; draw `"*** BATTLE CONCLUDED ***"` centered on row 7; draw final score on row 10, wave reached on row 11, high score on row 12; draw `"Press ENTER or R to fight again"` on row 15; draw `"Press Q to retreat"` on row 16
- [X] T050 [US2] Implement `GameState.handle_input()` for `Phase.GAME_OVER` in `game.py`: on `key in (ord('\n'), ord('\r'), ord('r'))` → call `reset()`; on `ord('q')` → `phase = Phase.QUIT`; implement `reset()`: restore `player = Player(x=PLAYER_START_X)`, `enemies=[]`, `boss=None`, `rounds=[]`, `boss_rounds=[]`, `wave_number=1`, `tick=0`, `transition_ticks=0`, `phase=Phase.PLAYING`, then call `_spawn_wave(1)` (preserve `high_score`)
- [X] T051 [US2] Manual play-test US2: run `python space_marine.py` → play through waves 1–3 → confirm enemies spawn in two rows → Bolter rounds destroy enemies → player loses life when enemy passes → wave transition screen appears → wave 3 has Chaos Space Marines → losing all lives shows Game Over screen → pressing R restarts

**Checkpoint**: ✅ US2 complete — full combat loop playable. Wave → shoot → advance.

---

## Phase 5: User Story 3 - Escalating Difficulty & Boss Encounters (Priority: P3)

**Goal**: Each wave is measurably harder. Wave 5 spawns a Hive Tyrant with zigzag
movement. Wave 10 spawns a Chaos Terminator that fires back. Wave 15 spawns an Ork
Warboss that splits into Ork Boyz on death.

**Independent Test**: Play to wave 6 — observe wave 2 faster than wave 1; wave 5
spawns `[H]` Hive Tyrant that zigzags; boss requires many shots; wave does not end
until boss is defeated.

### Tests for User Story 3 ⚠️ — Write first, confirm they FAIL, then implement

- [X] T052 [P] [US3] In `tests/test_game.py` add `test_wave5_spawns_boss`: call `game._spawn_wave(5)`; assert `game.boss is not None` and `game.boss.label == "Hive Tyrant"` and `game.boss.hp == 10`
- [X] T053 [P] [US3] In `tests/test_game.py` add `test_boss_requires_multiple_hits`: set up a `BossUnit` with `hp=10` at `(x=20, y=5.0)` and a `BolterRound` at `(x=20, y=5)`; call `update()`; assert `game.boss is not None` (not dead) and `game.boss.hp == 9`
- [X] T054 [P] [US3] In `tests/test_game.py` add `test_wave_not_complete_while_boss_alive`: set `enemies=[]`, `boss=BossUnit(...)` with hp=1; call `update()`; assert `phase == Phase.PLAYING` (not WAVE_TRANSITION)
- [X] T055 [P] [US3] In `tests/test_game.py` add `test_boss_zigzag_reverses_direction`: create `BossUnit` with `mechanic=BossMechanic.ZIGZAG`, `direction=1`, `mechanic_tick=14`, `x=20`; call `game._update_boss()` (or `update()` with only boss set); after 1 more tick assert `direction == -1`
- [X] T056 [P] [US3] In `tests/test_game.py` add `test_boss_fires_back_spawns_projectile`: create `BossUnit` with `mechanic=FIRES_BACK`, `mechanic_tick=29`, `x=20, y=5.0`; set `player.x=39`; call `update()`; assert `len(game.boss_rounds) == 1` and `game.boss_rounds[0].x == 39`
- [X] T057 [P] [US3] In `tests/test_game.py` add `test_boss_splits_on_death_spawns_ork_boyz`: create `BossUnit` with `mechanic=SPLITS`, `hp=1`, `x=20, y=5.0`; add `BolterRound(x=20, y=5)`; call `update()`; assert `game.boss is None` and `len(game.enemies) == 3` and all have `enemy_type == EnemyType.ORK_BOY`
- [X] T058 [P] [US3] In `tests/test_game.py` add `test_consecutive_waves_increase_difficulty`: for waves 1–5, call `wave_difficulty(n)` and `wave_difficulty(n+1)`; assert `speed_multiplier` and `enemy_count` are non-decreasing across all transitions
- [X] T059 [P] [US3] In `tests/test_game.py` add `test_boss_projectile_hits_player_decrements_lives`: add `BossProjectile(x=39, y=PLAYER_ROW)` to `game.boss_rounds`; set `player.x=39`, `player.lives=3`; call `update()`; assert `player.lives == 2` and `len(game.boss_rounds) == 0`

### Implementation for User Story 3

- [X] T060 [US3] Update `GameState._spawn_wave()` in `game.py` to spawn boss when `has_boss` is True: compute boss index `= ((wave_number // 5) - 1) % 3`; compute cycle `= (wave_number // 5 - 1) // 3`; look up `BOSS_CATALOG[boss_index]`; set `boss.hp = catalog_hp + 5 * cycle`; position boss at center `x = PLAYER_START_X`, `y = float(PLAY_AREA_TOP)`; add boss as `BossUnit`; standard enemies fill remaining `enemy_count - 1` slots
- [X] T061 [US3] Implement `GameState._update_boss(self)` in `game.py`: descend boss `boss.y += boss.speed / FPS`; increment `boss.mechanic_tick`; for `ZIGZAG`: every 15 ticks flip `boss.direction`; move `boss.x += boss.direction`; clamp to `[PLAY_AREA_LEFT, PLAY_AREA_RIGHT]`; for `FIRES_BACK`: every 30 ticks append `BossProjectile(x=player.x, y=int(boss.y) + 1)` to `boss_rounds`; for `SPLITS`: no per-tick action (handled on death)
- [X] T062 [US3] Implement boss collision in `GameState._check_collisions()` in `game.py`: check each `BolterRound` against `boss` position (`round.x == boss.x and round.y == int(boss.y)`); if hit: decrement `boss.hp`, remove round; if `boss.hp <= 0`: add `boss.score_value` to `player.score`; if `mechanic == SPLITS` spawn 3 `EnemyUnit` of `ORK_BOY` at `boss.x-1`, `boss.x`, `boss.x+1` at current `boss.y`; set `self.boss = None`
- [X] T063 [US3] Implement BossProjectile movement in `GameState.update()` in `game.py`: advance each `boss_round.y += 1` per tick; check if `boss_round.x == player.x and boss_round.y >= PLAYER_ROW`: if so decrement `player.lives`; remove projectiles that reach or pass `PLAYER_ROW`
- [X] T064 [US3] Update PLAYING→WAVE_TRANSITION gate in `GameState.update()` in `game.py` to require `boss is None` in addition to `enemies == []` (this prevents wave ending while boss lives)
- [X] T065 [US3] Call `_update_boss()` inside `GameState.update()` in `game.py` when `phase == Phase.PLAYING` and `boss is not None`
- [X] T066 [US3] Run unit tests: `python -m unittest tests.test_game -v` — all T052–T059 tests MUST pass before renderer tasks
- [X] T067 [US3] Implement boss renderer in `draw_game(stdscr, game)` in `space_marine.py`: draw `boss.symbol` (3-char `[H]`/`[X]`/`[W]`) at `(int(boss.y), boss.x - 1)`; on the row above boss draw `boss.label` and HP bar as `"Hive Tyrant  HP: ##########"` truncated to screen width
- [X] T068 [US3] Implement BossProjectile renderer in `draw_game()` in `space_marine.py`: draw `↓` at `(boss_round.y, boss_round.x)` for each active boss round
- [X] T069 [US3] Manual play-test US3: play to wave 5 → confirm `[H]` Hive Tyrant appears with HP bar → observe zigzag movement → confirm boss requires many hits → wave does not end until boss killed → play to wave 6 and confirm it is noticeably faster than wave 1

**Checkpoint**: ✅ US3 complete — full escalating difficulty and all three boss types playable.

---

## Phase 6: User Story 4 - Replayability & Score Tracking (Priority: P4)

**Goal**: HUD always shows score, high score, wave, and lives. Game Over screen shows
final stats. Restart is instant from game-over screen. High score persists in session.

**Independent Test**: Play full session to game over → score increments correctly by
enemy type → Game Over screen shows final score and wave → press R → new session
starts with 0 score / 3 lives / wave 1 → high score preserved across restarts.

### Tests for User Story 4 ⚠️ — Write first, confirm they FAIL, then implement

- [X] T070 [P] [US4] In `tests/test_game.py` add `test_score_increments_by_enemy_type_value`: kill a TERMAGANT (score_value=10) via collision; assert `player.score == 10`; kill a CHAOS_MARINE (15); assert `player.score == 25`
- [X] T071 [P] [US4] In `tests/test_game.py` add `test_boss_score_exceeds_standard_enemy`: kill a TERMAGANT (10 pts) and a Hive Tyrant boss (200 pts); assert `player.score == 210` and boss score > any standard enemy score
- [X] T072 [P] [US4] In `tests/test_game.py` add `test_high_score_updates_on_game_over`: set `player.score=500`, `high_score=100`; trigger GAME_OVER (set `player.lives=0`); call `update()`; assert `game.high_score == 500`
- [X] T073 [P] [US4] In `tests/test_game.py` add `test_high_score_not_updated_if_lower`: set `player.score=50`, `high_score=200`; trigger GAME_OVER; call `update()`; assert `game.high_score == 200`
- [X] T074 [P] [US4] In `tests/test_game.py` add `test_reset_preserves_high_score_clears_score`: set `high_score=999`, `player.score=500`; call `game.reset()`; assert `game.high_score == 999` and `game.player.score == 0` and `game.player.lives == 3` and `game.wave_number == 1`
- [X] T075 [P] [US4] In `tests/test_game.py` add `test_wave_number_increments_after_transition`: set `wave_number=1`, `transition_ticks=1`, `phase=Phase.WAVE_TRANSITION`; call `update()`; assert `wave_number == 2`
- [X] T076 [P] [US4] In `tests/test_game.py` add `test_restart_from_game_over_via_enter`: set `phase=Phase.GAME_OVER`; call `handle_input(ord('\n'))`; assert `phase == Phase.PLAYING` and `player.lives == 3` and `player.score == 0`

### Implementation for User Story 4

Score tracking was already wired in T042/T062 (`player.score += score_value`). These
tasks add the HUD display and complete the game-over/restart flow.

- [X] T077 [US4] Implement full HUD renderer `draw_hud(stdscr, game)` in `space_marine.py`: draw row 0 as `"╔══ SPACE MARINE ══╗"` spanning full width; draw row 1 as `"  SCORE: {:05d}   HI: {:05d}   WAVE: {:02d}   {}".format(score, high_score, wave_number, "♥ " * lives)`; draw row 2 as full-width `═` separator; call `draw_hud()` from `draw_game()` on every frame
- [X] T078 [US4] Update `draw_game_over()` in `space_marine.py` to show `game.player.score`, `game.wave_number`, and `game.high_score` with correct values (replace any placeholder 0s from T049)
- [X] T079 [US4] Run unit tests: `python -m unittest tests.test_game -v` — all T070–T076 tests MUST pass
- [X] T080 [US4] Manual play-test US4: play full session → HUD always visible with accurate score/wave/lives → kill a Termagant (score +10) and a Chaos Marine (score +15) → reach game over → Game Over screen shows correct final score and wave → press R → new session starts at score 0, lives 3, wave 1 → previous session's best score shown as HI score

**Checkpoint**: ✅ US4 complete — full replayable game. All user stories verified.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, flavor text, edge case fixes, and full end-to-end validation.

- [X] T081 [P] Add Warhammer 40K flavor text rotation on row 22 in `space_marine.py`: define a list of lore phrases (`"For the Emperor!"`, `"By the Omnissiah!"`, `"Death to the Xenos!"`, `"Hold the line, Battle-Brother!"`) and display one based on `game.tick % len(FLAVOR_TEXT)` during PLAYING phase
- [X] T082 [P] Harden terminal size enforcement in `space_marine.py`: if `stdscr.getmaxyx()` returns size below 80×24 during gameplay (terminal resized mid-game) — pause rendering and show resize message on row 0 until size is restored
- [X] T083 [P] Add `tests/__init__.py` (empty file) and verify `python -m unittest discover tests` discovers and runs all tests from repository root
- [X] T084 Run complete test suite: `python -m unittest tests.test_game -v` — ALL tests T013–T076 must pass with zero failures or errors before this task is marked done
- [ ] T085 End-to-end validation per `specs/001-arcade-shooter/quickstart.md`: run `python space_marine.py` from a fresh terminal; confirm 30-second-or-less time from launch to playing; verify SC-001 through SC-008 from spec.md are all observable
- [X] T086 [P] Review all player-facing strings in `space_marine.py` and `game.py` for any generic labels ("alien", "laser", "enemy") — replace with lore-accurate Warhammer 40K terminology per Constitution Principle II

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Requires Phase 1 complete — BLOCKS all user stories
- **US1 logic (T013–T021)**: Requires Phase 2 complete
- **US1 renderer (T023–T026)**: Requires US1 tests (T022) green ✅
- **US2 logic (T028–T045)**: Requires US1 logic complete (T021)
- **US2 renderer (T047–T049)**: Requires US2 tests (T046) green ✅
- **US3 logic (T052–T065)**: Requires US2 logic complete (T045)
- **US3 renderer (T067–T068)**: Requires US3 tests (T066) green ✅
- **US4 renderer (T077–T078)**: Requires US4 tests (T079) — score already wired; only display tasks here
- **Polish (Phase N)**: Requires all user stories complete

### User Story Dependencies

- **US1 (P1)**: Can start immediately after Foundational — no story dependencies
- **US2 (P2)**: Depends on US1 logic (movement/firing must exist for combat to work)
- **US3 (P3)**: Depends on US2 logic (_spawn_wave must exist; boss extends wave spawning)
- **US4 (P4)**: Depends on US2 logic (scoring wired in collision; high score needs game-over flow)

### Within Each User Story

1. Tests written (all marked FAIL on first run)
2. `game.py` logic implemented
3. Tests run — MUST all pass before renderer work begins
4. `space_marine.py` renderer implemented for this story's entities
5. Manual play-test
6. Story checkpoint marked

---

## Parallel Opportunities

### Phase 2 — All dataclass/enum tasks are parallel

```bash
# These can all be written simultaneously:
T004  # Phase enum
T005  # EnemyType enum + ENEMY_DATA
T006  # BossMechanic enum + BOSS_CATALOG
T007  # Player dataclass
T008  # EnemyUnit dataclass
T009  # BossUnit dataclass (after T005, T006)
T010  # BolterRound dataclass
T011  # BossProjectile dataclass
```

### Phase 3 (US1) — All test tasks are parallel

```bash
# Write all US1 tests simultaneously:
T013  # move_left_boundary
T014  # move_left_clamp
T015  # move_right_clamp
T016  # fire_creates_round
T017  # round_exits_top
T018  # start_to_playing_transition
```

### Phase 4 (US2) — All test tasks are parallel

```bash
T028  # wave_difficulty_wave1
T029  # wave_difficulty_wave3
T030  # wave_difficulty_wave5
T031  # spawn_wave_count
T032  # round_hits_enemy
T033  # round_hit_adds_score
T034  # enemy_at_player_row
T035  # all_enemies_cleared
T036  # wave_transition_countdown
T037  # lives_zero_game_over
```

---

## Implementation Strategy

### MVP First (US1 + US2 only)

1. Complete Phase 1 (Setup) — 3 tasks
2. Complete Phase 2 (Foundational) — 9 tasks
3. Complete Phase 3 (US1) tests + logic → green → renderer — 13 tasks
   → **First playable build: controllable Space Marine**
4. Complete Phase 4 (US2) tests + logic → green → renderer — 20 tasks
   → **Playable combat loop: enemies, waves, game over**
5. STOP and validate SC-001 through SC-003 from spec.md

### Incremental Delivery

- After US1: demo controllable player with Bolter fire
- After US2: demo full wave-based combat loop
- After US3: demo escalating waves and boss encounters
- After US4: demo complete replayable game with HUD and restart

### Solo Developer Sequence (recommended)

```text
Phase 1 → Phase 2 → US1 logic → US1 tests green → US1 renderer → play-test
                 → US2 logic → US2 tests green → US2 renderer → play-test
                 → US3 logic → US3 tests green → US3 renderer → play-test
                 → US4 renderer → play-test
                 → Polish
```

---

## Notes

- `[P]` tasks = can be worked simultaneously if different sections of same file
  are being edited, OR if working on different files altogether
- Tests MUST fail before implementation (Red-Green-Refactor)
- Never write renderer code until the corresponding logic tests are green
- `game.py` must have zero `curses` imports at all times (breaks unit testing)
- Commit after each story checkpoint — gives clean rollback points
- Run `python -m unittest tests.test_game -v` after EVERY logic task to catch regressions
