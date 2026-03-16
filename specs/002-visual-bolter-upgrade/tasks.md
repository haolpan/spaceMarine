# Tasks: Visual Fidelity & Bolter Upgrade System

**Input**: Design documents from `specs/002-visual-bolter-upgrade/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅

**Architecture constraints** (must not be violated):
- `game.py` — pure logic only; zero curses imports; fully unit-testable
- `space_marine.py` — curses renderer + input loop only; no game logic
- `tests/test_game.py` — unittest suite; no curses dependency
- stdlib only; no third-party packages

**TDD rule**: For every logic change in game.py — write the test first, confirm it FAILS, then implement, then confirm it PASSES. Renderer tasks for each story begin only after that story's logic tests are green.

---

## FR Traceability

| FR | Tasks |
|---|---|
| FR-001 | T013 |
| FR-002 | T013 |
| FR-003 | T013 (verified by design — anchor x unchanged throughout) |
| FR-004 | T011 |
| FR-005 | T011 |
| FR-006 | T011 |
| FR-007 | T011 |
| FR-008 | T014, T015 |
| FR-009 | T014, T015 |
| FR-010 | T023, T032 |
| FR-011 | T024, T031 |
| FR-012 | T024, T031 |
| FR-013 | T026, T031 |
| FR-014 | T038, T040 |
| FR-015 | T027, T034, T035 |
| FR-016 | T019, T030 |
| FR-017 | T019, T030 |
| FR-018 | T019, T020, T029, T030 |
| FR-019 | T028, T031 |
| FR-020 | T025, T031 |

---

## Phase 1: Setup

**Purpose**: Establish a clean, green baseline before any changes.

- [X] T001 Run `python -m unittest tests.test_game -v` from repo root and confirm all 32 tests pass; record output as baseline; abort if any test fails before investigating root cause

---

## Phase 2: Foundational Model Updates

**Purpose**: Add all new data structures to `game.py` additively — no behaviour changes yet. All 32 existing tests must remain green throughout this phase.

**⚠️ CRITICAL**: Complete this phase fully before any US1 or US2 work. All tasks in this phase are sequential (same file).

- [X] T002 Add `WeaponTier` enum to `game.py` after `BossMechanic` enum: three members `STANDARD = auto()`, `TWIN_LINKED = auto()`, `STORM_BOLTER = auto()`; import `field` from dataclasses at top of file for use in T003. **Acceptance**: `WeaponTier.STANDARD`, `.TWIN_LINKED`, `.STORM_BOLTER` accessible; no import errors.

- [X] T003 Add `weapon_tier: WeaponTier = field(default_factory=lambda: WeaponTier.STANDARD)` field to `Player` dataclass in `game.py`; add `from dataclasses import dataclass, field` if not already present. **Acceptance**: `Player(x=39).weapon_tier == WeaponTier.STANDARD`; existing `Player` construction with positional `x` still works.

- [X] T004 Add `dx: int = 0` field to `BolterRound` dataclass in `game.py` (additive, default 0). **Acceptance**: `BolterRound(x=10, y=5)` creates round with `dx=0`; `BolterRound(x=10, y=5, dx=-1)` creates round with `dx=-1`; all existing round creation sites unchanged.

- [X] T005 Add two balancing constants to the `# ── Layout constants` section in `game.py`: `POWERUP_DROP_CHANCE = 0.15` and `POWERUP_FALL_SPEED = 0.5`. **Acceptance**: Both names importable from game; values match spec FR-010 (15%) and FR-011 (0.5 rows/tick = 1 row per 2 ticks).

- [X] T006 Add `PowerUpToken` dataclass to `game.py` after `BossProjectile`: fields `x: int` and `y: float`. Add `PowerUpToken` to module-level docstring entity list comment. **Acceptance**: `PowerUpToken(x=10, y=5.0)` constructs without error; `token.x == 10`; `token.y == 5.0`.

- [X] T007 Add `self.tokens: List[PowerUpToken] = []` to `GameState.__init__` in `game.py` after `self.boss_rounds`. **Acceptance**: `GameState().tokens == []`.

- [X] T008 Add `self.tokens = []` to `GameState._spawn_wave()` in `game.py` alongside the existing `self.enemies = []` and `self.boss = None` resets. **Acceptance**: After `gs._spawn_wave(1)`, `gs.tokens == []` even if tokens were present before.

- [X] T009 Add `self.tokens = []` to `GameState.reset()` in `game.py` alongside other list resets. **Acceptance**: After `gs.reset()`, `gs.tokens == []`.

- [X] T010 Run `python -m unittest tests.test_game -v` — confirm all 32 tests still pass; no regressions from the additive model changes in T002–T009. **Checkpoint**: Do NOT proceed to Phase 3 if any test fails.

---

## Phase 3: US1 — Faction-Accurate Visual Silhouettes (Priority P1)

**Goal**: All entity types are visually distinct using single-width terminal-safe glyphs; bosses render with a decorative art row.

**Independent Test**: Launch `python space_marine.py`, play to wave 3+. Each enemy type (Termagant, Chaos Marine, Ork Boy) is visually distinguishable without reading labels. Boss has three visible rows. No layout corruption at 80×24.

**No logic tests required**: US1 changes are data (ENEMY_DATA symbols) and renderer-only. Existing tests verify no regressions.

- [X] T011 [US1] Update `ENEMY_DATA` symbol values in `game.py`: set `EnemyType.TERMAGANT` symbol to `"⟲"` (U+27F2), set `EnemyType.CHAOS_MARINE` symbol to `"✵"` (U+2735); `EnemyType.ORK_BOY` symbol `"₩"` (U+20A9) is already correct — do not change it. **Rationale**: single-width characters per research.md Decision 1; lore-accurate per user feedback_visual_symbols.md. **Acceptance**: `ENEMY_DATA[EnemyType.TERMAGANT]["symbol"] == "⟲"`; `ENEMY_DATA[EnemyType.CHAOS_MARINE]["symbol"] == "✵"`.

- [X] T012 [US1] Run `python -m unittest tests.test_game -v` — confirm all 32 tests pass after T011 symbol change. **Checkpoint**: symbol change must not break any existing test. If tests fail, revert T011 and investigate.

- [X] T013 [US1] [P] Document and verify player symbol compliance in `space_marine.py` — confirm `safe_addstr(PLAYER_ROW, gs.player.x - 1, "[℧]")` at line ~161: the symbol `[℧]` is 3 columns wide (`[`, `℧` U+2127 Inverted Ohm/Ultima mark, `]`), satisfying FR-001 (≥3 cols) and FR-002 (Ultima chapter mark). Confirm player collision anchor remains `player.x` (single column) per FR-003. **No code change required** — verify and leave a comment `# FR-001, FR-002: 3-col Ultramarine symbol; FR-003: collision anchor = player.x` on the player render line. **Acceptance**: Comment present; player render call unchanged; symbol renders without double-width issues.

- [X] T014 [US1] Add boss decorative art row in `draw_game()` in `space_marine.py`: in the boss rendering block, add a new `safe_addstr` call at `row - 2` (above the existing HP bar at `row - 1`) using boss-specific art strings — Hive Tyrant: `"/\\  /\\"`, Chaos Terminator: `"><><>"`, Ork Warboss: `"[|||]"` — use a dict keyed on `b.label` with fallback `"*****"`. Place this block BEFORE the existing HP-bar render so draw order is: art (row-2) → HP bar (row-1) → symbol (row). **Acceptance**: `draw_game()` renders three rows for boss when space is available; art string is 5–7 chars centred near `b.x`; existing HP bar and symbol code is unchanged.

- [X] T015 [US1] Add `PLAY_AREA_TOP` boundary guard for the boss art row in `draw_game()` in `space_marine.py`: wrap the T014 art render call in `if row - 2 >= PLAY_AREA_TOP:` to prevent rendering above the play area. **Acceptance**: When boss `int(b.y) - 2 < PLAY_AREA_TOP`, no art row is drawn and no `curses.error` is raised; FR-009 existing HP-bar logic is unchanged.

- [X] T016 [US1] Manual play-test SC-001 and SC-002: run `python space_marine.py`, play to wave 3 (all three enemy types on screen). Verify SC-001: each of the three enemy types is visually distinct from the others and from the player within 10 seconds of wave start, without reading labels. Verify SC-002: player character reads as an armoured Space Marine within 5 seconds. **Acceptance**: Both criteria confirmed; note any symbol rendering issues (double-width, missing glyph) and fix before marking done.

- [X] T017 [US1] Non-regression check: with `python space_marine.py` at an 80×24 terminal, verify SC-007 — HUD rows 0–2 (title bar, stats, separator) display without corruption; side borders `║` appear correctly on every play-area row; row 21 separator intact; row 22 flavor text visible; row 23 player renders correctly; boss HP bar and art rows do not overwrite borders or HUD. **Acceptance**: No visual artefacts or layout corruption observed at 80×24.

---

## Phase 4: US2 — Bolter Upgrade & Power-Up System (Priority P2)

**Goal**: Full three-tier Bolter upgrade system with collectible tokens, tier-aware firing, HUD display, and life-loss tier reset.

**Independent Test**: `python space_marine.py` → collect a `*` token → HUD changes from `BOLTER` to `TWIN-LNK` → firing produces two rounds → collect another token → HUD shows `STORM` → firing produces three fanning rounds → lose a life → HUD reverts to `BOLTER`.

**Test-first rule**: Tasks T018–T028 write failing tests. Tasks T029–T036 implement logic. T037 confirms all tests green. Tasks T038–T041 implement renderer. Task T042 is the manual play-test.

### US2 — Logic Tests (write failing tests first)

- [X] T018 [US2] Add `from game import WeaponTier, PowerUpToken, POWERUP_DROP_CHANCE, POWERUP_FALL_SPEED` to the import block in `tests/test_game.py`. Add a new test class `class TestWeaponTier(unittest.TestCase)`. Write `test_default_tier_is_standard`: create `GameState()`, set phase to PLAYING, assert `gs.player.weapon_tier == WeaponTier.STANDARD`. Run `python -m unittest tests.test_game.TestWeaponTier.test_default_tier_is_standard -v` and **confirm it FAILS** (WeaponTier not yet in game.py imports or attribute not on Player). **Acceptance**: Test exists and fails with `AttributeError` or `ImportError`.

- [X] T019 [US2] In `TestWeaponTier` in `tests/test_game.py`, write three firing tests: (1) `test_standard_fires_one_round` — set `gs.player.weapon_tier = WeaponTier.STANDARD`, call `gs.handle_input(ord(' '))`, assert `len(gs.rounds) == 1` and `gs.rounds[0].x == gs.player.x`; (2) `test_twin_linked_fires_two_rounds` — set tier to `TWIN_LINKED`, fire, assert `len(gs.rounds) == 2`, assert round x values are `player.x - 1` and `player.x + 1`; (3) `test_storm_bolter_fires_three_rounds` — set tier to `STORM_BOLTER`, fire, assert `len(gs.rounds) == 3`. Run these three tests and **confirm all FAIL**. **Acceptance**: All three tests exist and produce failures (not errors from missing attributes — if import fails, check T018 imports are present).

- [X] T020 [US2] In `TestWeaponTier` in `tests/test_game.py`, write two diagonal round tests: (1) `test_storm_outer_rounds_have_dx` — at STORM tier, fire and assert the two outer rounds have `dx=-1` and `dx=+1` (centre round has `dx=0`); (2) `test_diagonal_rounds_drift_x_each_tick` — create a `BolterRound(x=10, y=10, dx=-1)`, add to `gs.rounds`, call `gs.update()` once, assert round x is now `9` (drifted left). Run and **confirm FAILING**. **Acceptance**: Both tests exist and fail before implementation.

- [X] T021 [US2] In `TestWeaponTier` in `tests/test_game.py`, write three tier advancement tests: (1) `test_tier_advance_standard_to_twin` — place a `PowerUpToken(x=gs.player.x, y=float(PLAYER_ROW))` in `gs.tokens`, call `gs.update()`, assert `gs.player.weapon_tier == WeaponTier.TWIN_LINKED`; (2) `test_tier_advance_twin_to_storm` — same but start at TWIN_LINKED, assert result is STORM_BOLTER; (3) `test_tier_capped_at_storm` — start at STORM_BOLTER, collect token, assert still STORM_BOLTER (FR-013). Run and **confirm FAILING**. **Acceptance**: All three tests exist and fail before T031 is implemented.

- [X] T022 [US2] In `TestWeaponTier` in `tests/test_game.py`, write two tier-reset tests: (1) `test_tier_resets_on_enemy_breach` — set `gs.player.weapon_tier = WeaponTier.TWIN_LINKED`, place an enemy at `y=float(PLAYER_ROW - 0.1)` with `speed=FPS` (will reach player row in one tick), call `gs.update()`, assert `gs.player.weapon_tier == WeaponTier.STANDARD` (FR-015); (2) `test_tier_resets_on_boss_projectile_hit` — set tier to TWIN_LINKED, place `BossProjectile(x=gs.player.x, y=PLAYER_ROW - 1)` in `gs.boss_rounds`, call `gs.update()`, assert tier is STANDARD. Run and **confirm FAILING**. **Acceptance**: Both tests exist and fail before T034/T035.

- [X] T023 [US2] Add a new test class `class TestPowerUpToken(unittest.TestCase)` in `tests/test_game.py`. Write two spawn tests: (1) `test_token_spawns_on_kill_with_mocked_random` — use `unittest.mock.patch('game.random.random', return_value=0.10)` as context manager, kill an enemy via collision (place round at enemy position, call `gs.update()`), assert `len(gs.tokens) == 1` and `gs.tokens[0].x == enemy_x` (FR-010); (2) `test_no_token_spawn_above_chance` — same but `return_value=0.20`, assert `len(gs.tokens) == 0`. Run and **confirm FAILING**. **Note**: `unittest.mock` is stdlib (Python 3.3+). Add `from unittest.mock import patch` import at top of test file. **Acceptance**: Both tests fail before T032.

- [X] T024 [US2] In `TestPowerUpToken` in `tests/test_game.py`, write two fall/collection tests: (1) `test_token_descends_by_fall_speed_each_tick` — place `PowerUpToken(x=10, y=5.0)` in `gs.tokens`, call `gs.update()`, assert `gs.tokens[0].y == 5.0 + POWERUP_FALL_SPEED` (FR-011); (2) `test_token_collected_at_player_row_and_column` — place `PowerUpToken(x=gs.player.x, y=float(PLAYER_ROW - POWERUP_FALL_SPEED))` so after one tick `int(token.y) == PLAYER_ROW`, call `gs.update()`, assert `gs.tokens == []` and `gs.player.weapon_tier == WeaponTier.TWIN_LINKED` (FR-012). Run and **confirm FAILING**. **Acceptance**: Both tests fail before T031.

- [X] T025 [US2] In `TestPowerUpToken` in `tests/test_game.py`, write two removal tests: (1) `test_token_not_collected_at_wrong_column` — place `PowerUpToken(x=gs.player.x + 3, y=float(PLAYER_ROW))`, call `gs.update()`, assert tier unchanged and token gone (passed row, FR-020); (2) `test_token_removed_past_player_row` — place `PowerUpToken(x=gs.player.x + 3, y=float(PLAYER_ROW + 1))`, call `gs.update()`, assert `gs.tokens == []` (FR-020). Run and **confirm FAILING**. **Acceptance**: Both tests fail before T031.

- [X] T026 [US2] In `TestPowerUpToken` in `tests/test_game.py`, write `test_multiple_simultaneous_tokens_tracked_independently` — place two tokens: `PowerUpToken(x=gs.player.x, y=float(PLAYER_ROW - POWERUP_FALL_SPEED))` (will be collected) and `PowerUpToken(x=gs.player.x + 5, y=5.0)` (still falling); call `gs.update()`; assert `len(gs.tokens) == 1` (the falling one survives) and `gs.player.weapon_tier == WeaponTier.TWIN_LINKED` (edge case: multiple simultaneous tokens). Run and **confirm FAILING**. **Acceptance**: Test fails before T031.

- [X] T027 [US2] In `TestPowerUpToken` in `tests/test_game.py`, write `test_bolter_round_does_not_destroy_token` — place a `PowerUpToken(x=20, y=10.0)` and a `BolterRound(x=20, y=10)` in `gs.rounds`; call `gs.update()`; assert the token is NOT removed by the round (rounds only interact with enemies/boss, not tokens — FR-019). **Acceptance**: Token still present (or removed only if it reaches player row, not due to round); test fails before T031.

- [X] T028 [US2] In `TestPowerUpToken` in `tests/test_game.py`, write `test_tokens_cleared_on_spawn_wave` and `test_tokens_cleared_on_reset` — (1) place a token in `gs.tokens`, call `gs._spawn_wave(1)`, assert `gs.tokens == []`; (2) place a token, call `gs.reset()`, assert `gs.tokens == []` (edge case: life loss / wave reset clears tokens). Run and **confirm FAILING**. **Acceptance**: Both tests fail before T008/T009 (which were already implemented in Phase 2 — these tests should now actually PASS if Phase 2 was done correctly; confirm they PASS).

### US2 — Logic Implementation

- [X] T029 [US2] In `GameState.update()` in `game.py`, update the Bolter round movement loop: add `r.x += r.dx` BEFORE `r.y -= 1` so diagonal rounds drift by dx each tick before travelling upward. The existing removal filter `r.y >= PLAY_AREA_TOP` is unchanged. **Acceptance**: `test_diagonal_rounds_drift_x_each_tick` passes; a `BolterRound(x=10, y=10, dx=-1)` has `x=9, y=9` after one tick.

- [X] T030 [US2] Replace the single-round fire in `handle_input()` in `game.py` with tier-aware multi-round spawning: `STANDARD` → one `BolterRound(x=px, y=PLAYER_ROW-1, dx=0)`; `TWIN_LINKED` → two rounds at `(px-1, dx=0)` and `(px+1, dx=0)`; `STORM_BOLTER` → three rounds: `(px, dx=0)`, `(px-1, dx=-1)`, `(px+1, dx=+1)`. The `px = self.player.x` and `tier = self.player.weapon_tier` are read before creating rounds. **Acceptance**: T019 and T020 (firing/dx tests) pass; existing `test_fire_creates_bolter_round_above_player` still passes (fires STANDARD by default).

- [X] T031 [US2] Add `_update_tokens()` method to `GameState` in `game.py`. Logic: iterate `self.tokens`, add `POWERUP_FALL_SPEED` to each `token.y`; if `int(token.y) == PLAYER_ROW and token.x == self.player.x`: advance tier (`STANDARD→TWIN_LINKED`, `TWIN_LINKED→STORM_BOLTER`, `STORM_BOLTER` no-op per FR-013), do not add to survivors; elif `int(token.y) <= PLAYER_ROW`: add to survivors; else (past row): drop silently per FR-020. Assign `self.tokens = survivors`. **Acceptance**: T021 (tier advance), T024 (descend + collection), T025 (wrong col/past row), T026 (multiple tokens), T027 (round-token no interaction) all pass.

- [X] T032 [US2] In `_check_collisions()` in `game.py`, after `self.player.score += e.score_value` and before `dead_enemy_indices.add(ei)`, add: `if random.random() < POWERUP_DROP_CHANCE: self.tokens.append(PowerUpToken(x=e.x, y=float(int(e.y))))` (FR-010). **Acceptance**: T023 (token spawn on kill) passes; existing collision tests unaffected.

- [X] T033 [US2] In `_check_collisions()` boss kill block in `game.py`, after `self.player.score += b.score_value` and before `self.boss = None`, add the same 15% token spawn: `if random.random() < POWERUP_DROP_CHANCE: self.tokens.append(PowerUpToken(x=b.x, y=float(int(b.y))))`. **Acceptance**: Boss kill can spawn a token; existing boss collision and SPLITS mechanic unchanged.

- [X] T034 [US2] In `_descend_enemies()` in `game.py`, after every `self.player.lives = max(0, self.player.lives - 1)` decrement, add `self.player.weapon_tier = WeaponTier.STANDARD` (FR-015). **Acceptance**: T022 `test_tier_resets_on_enemy_breach` passes; existing life-loss test `test_life_lost_when_enemy_reaches_player_row` still passes.

- [X] T035 [US2] In `_update_boss_projectiles()` in `game.py`, after `self.player.lives = max(0, self.player.lives - 1)` decrement, add `self.player.weapon_tier = WeaponTier.STANDARD` (FR-015). **Acceptance**: T022 `test_tier_resets_on_boss_projectile_hit` passes; existing boss projectile test still passes.

- [X] T036 [US2] In `GameState.update()` in `game.py`, add a call to `self._update_tokens()` after the existing `self._update_boss_projectiles()` call. **Acceptance**: Token lifecycle methods are called each tick during PLAYING phase; game loop integration complete.

### US2 — Logic Tests Green (checkpoint)

- [X] T037 [US2] Run `python -m unittest tests.test_game -v` — all tests (original 32 + all new US2 tests from T018–T028) must pass. **Checkpoint**: Do NOT proceed to renderer tasks T038–T041 until this command exits with 0 errors and 0 failures. If any test fails, fix logic in T029–T036 before continuing.

### US2 — Renderer

- [X] T038 [US2] In `space_marine.py`, add `WeaponTier` to the import from `game` at the top of the file. **Acceptance**: `from game import ..., WeaponTier` present; `python space_marine.py` starts without `ImportError`.

- [X] T039 [US2] In `space_marine.py`, add `WEAPON_TIER_LABELS` dict after `FLAVOR_TEXT`: `{ WeaponTier.STANDARD: "BOLTER", WeaponTier.TWIN_LINKED: "TWIN-LNK", WeaponTier.STORM_BOLTER: "STORM" }`. **Acceptance**: Dict present and all three keys defined with correct label strings from FR-014.

- [X] T040 [US2] In `draw_hud()` in `space_marine.py`, append the weapon tier label to the HUD stats string: read `tier_label = WEAPON_TIER_LABELS.get(gs.player.weapon_tier, "BOLTER")` and append `f"   {tier_label}"` to the `hud` string before `ljust(border_inner)`. **Acceptance** (per hud-contract.md): HUD row 1 shows e.g. `SCORE: 00000   HI: 00000   WAVE: 01   ♥ ♥ ♥   BOLTER` within cols 1–78; label updates same frame as tier change (SC-006); no truncation of existing stats.

- [X] T041 [US2] [P] In `draw_game()` in `space_marine.py`, add a token rendering block after boss projectile rendering: iterate `gs.tokens`, for each token compute `row = int(token.y)`, if `PLAY_AREA_TOP <= row < PLAYER_ROW` call `safe_addstr(row, token.x, "*")`. **Acceptance**: Tokens appear as `*` in the play area during gameplay; token does not render outside play bounds; no layout corruption.

- [X] T042 [US2] Manual play-test SC-003, SC-004, SC-005, SC-006: run `python space_marine.py`, play until a `*` token appears (SC-003: at least one token in 3-wave session); walk under it and verify HUD label changes (SC-004: upgrade visible within one fire); lose a life and verify HUD reverts to `BOLTER` (SC-005: tier resets within one tick); confirm HUD tier label is readable at all times (SC-006: updates same frame). **Acceptance**: All four criteria confirmed; record any visual or timing issues.

---

## Phase 5: Polish & Verification

**Purpose**: Final regression sweep, full test suite confirmation, and complete manual playtest.

- [X] T043 Run `python -m unittest tests.test_game -v` — confirm all tests pass (final count expected: original 32 + all US2 tests). Record exact pass count.

- [X] T044 Run `python -m unittest discover tests -v` — confirm test discovery finds `tests/test_game.py` and all tests pass. **Acceptance**: Zero failures, zero errors.

- [X] T045 Non-regression layout check: run `python space_marine.py` at an 80×24 terminal, play waves 1–5 (reaching first boss). Verify: HUD rows 0–2 intact with tier label added; side borders on every play-area row; row 21 separator; row 22 flavor text (cycling every ~3s); row 23 player `[℧]`; boss renders with art row, HP bar, and symbol; no cell overlaps, shifted columns, or curses errors. **Acceptance**: SC-007 confirmed — no layout corruption, overlap, or visual artefact.

- [X] T046 Final manual playtest SC-001..SC-007 full checklist: run `python space_marine.py` and verify all success criteria:
  - **SC-001**: Every enemy type correctly identified by visual appearance alone within 10s of wave start
  - **SC-002**: Player character recognised as armoured Space Marine by first-time observer within 5s
  - **SC-003**: At least one `*` token appears during a standard 3-wave session
  - **SC-004**: Weapon tier upgrade visible within one fire action of collecting a token
  - **SC-005**: Weapon tier reverts to `BOLTER` within one tick of a life being lost
  - **SC-006**: HUD weapon tier label readable at all times during PLAYING phase; updates same frame
  - **SC-007**: No layout corruption, overlap, or visual artefact in HUD, border, or play area

---

## Dependencies

```
T001
  └── T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010
                                                                   └── Phase 3 (US1)
                                                                         └── T011 → T012 → T013 (P with T014)
                                                                               └── T014 → T015 → T016 → T017
                                                                                                           └── Phase 4 (US2)
                                                                                                                 US2 tests: T018 → T019 → T020 → T021 → T022
                                                                                                                            T023 → T024 → T025 → T026 → T027 → T028
                                                                                                                 US2 logic: T029 → T030 → T031 → T032 → T033 → T034 → T035 → T036
                                                                                                                            T037 (all tests green)
                                                                                                                 US2 render: T038 → T039 → T040
                                                                                                                                         T041 (P with T040, depends T038)
                                                                                                                            T042
                                                                                                                               └── Phase 5: T043 → T044 → T045 → T046
```

**Story dependency**: US1 (Phase 3) has no dependency on US2. US2 (Phase 4) foundational data model (Phase 2) must be complete first. US1 and US2 are otherwise independent.

---

## Parallelization Guidance

### Phase 2 Foundational
No parallelization — all tasks modify `game.py`. Run sequentially T002→T003→T004→T005→T006→T007→T008→T009.

### Phase 3 US1
- T013 (player symbol verification/comment) can run in parallel with T011 (enemy symbol update) since T013 is `space_marine.py` and T011 is `game.py`.
- T014 and T015 can begin once T012 (tests pass) is confirmed.

### Phase 4 US2 — Test Writing
- TestWeaponTier tests (T018–T022) and TestPowerUpToken tests (T023–T028) are in the same file but different classes — they can be written in parallel if two engineers are working simultaneously. For a single session, write sequentially.

### Phase 4 US2 — Renderer
- T040 (`draw_hud`) and T041 (`draw_game` token loop) both require T038 (import) but are independent functions in `space_marine.py` — mark T041 as [P] with T040.

### Phase 5
All sequential (final verification must confirm all prior work is integrated).

---

## Independent Test Criteria

### US1 (Visual Silhouettes)
Run `python space_marine.py`. Without reading any label:
1. Identify all three enemy types as distinct within 10 seconds.
2. Identify the player as an armoured Space Marine within 5 seconds.
3. On wave 5, confirm the boss renders with 3 visible rows (art + HP bar + symbol).

### US2 (Bolter Upgrades)
Run `python -m unittest tests.test_game.TestWeaponTier tests.test_game.TestPowerUpToken -v` → all tests pass.
Then run `python space_marine.py` → collect token → verify tier, HUD, and firing behavior.

---

## Implementation Strategy (MVP Scope)

**MVP = Phase 1 + Phase 2 + Phase 4 (US2 logic only, no renderer)**
This delivers a fully-tested Bolter upgrade system before any visual work. The HUD label and token rendering (T038–T041) are the "visible" part of MVP that ships together with the logic.

**Full delivery order**:
1. Foundational models (Phase 2) — additive, zero risk
2. US2 logic + tests (T018–T037) — highest value, test coverage first
3. US2 renderer (T038–T042) — short, completes the user-visible feature
4. US1 visuals (Phase 3) — independent, ships as a visual-only increment
5. Polish (Phase 5) — final gate

---

## Summary

| Phase | Tasks | Story | Key Deliverable |
|---|---|---|---|
| 1 Setup | T001 | — | Baseline 32 tests green |
| 2 Foundational | T002–T010 | — | WeaponTier, PowerUpToken, BolterRound.dx, constants |
| 3 US1 Visuals | T011–T017 | US1 | Faction symbols, boss art, player symbol verified |
| 4 US2 Bolter | T018–T042 | US2 | Full upgrade system: logic + tests + HUD + token render |
| 5 Polish | T043–T046 | — | Full test suite + SC-001..SC-007 confirmed |

**Total tasks**: 46 (T001–T046)
**US1 tasks**: 7 (T011–T017)
**US2 tasks**: 25 (T018–T042, including 11 test-writing + 8 logic + 5 renderer + 1 verification + manual test)
**Parallel opportunities**: T013‖T011, T041‖T040
