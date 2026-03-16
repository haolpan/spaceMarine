import unittest
import sys
import os
import curses
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import game
from game import (
    GameState, Phase,
    PLAY_AREA_LEFT, PLAY_AREA_RIGHT, PLAY_AREA_TOP, PLAYER_ROW, PLAYER_START_X,
    TRANSITION_TICKS, FPS,
    KEY_LEFT, KEY_RIGHT,
    BolterRound, BossProjectile, EnemyUnit, BossUnit, EnemyType, BossMechanic,
    ENEMY_DATA,
    wave_difficulty,
    WeaponTier, PowerUpToken, POWERUP_DROP_CHANCE, POWERUP_FALL_SPEED,
)


class TestPlayerMovement(unittest.TestCase):
    def setUp(self):
        self.gs = GameState()
        self.gs.phase = Phase.PLAYING

    def test_player_move_left_within_bounds(self):
        self.gs.player.x = PLAY_AREA_LEFT + 5
        self.gs.handle_input(KEY_LEFT)
        self.assertEqual(self.gs.player.x, PLAY_AREA_LEFT + 4)

    def test_player_move_left_clamps_at_boundary(self):
        self.gs.player.x = PLAY_AREA_LEFT
        self.gs.handle_input(KEY_LEFT)
        self.assertEqual(self.gs.player.x, PLAY_AREA_LEFT)

    def test_player_move_right_clamps_at_boundary(self):
        self.gs.player.x = PLAY_AREA_RIGHT
        self.gs.handle_input(KEY_RIGHT)
        self.assertEqual(self.gs.player.x, PLAY_AREA_RIGHT)

    def test_fire_creates_bolter_round_above_player(self):
        self.gs.player.x = 39
        self.gs.handle_input(ord(" "))
        self.assertEqual(len(self.gs.rounds), 1)
        self.assertEqual(self.gs.rounds[0].x, 39)
        self.assertEqual(self.gs.rounds[0].y, PLAYER_ROW - 1)

    def test_bolter_round_removed_at_top(self):
        # Place a round exactly at PLAY_AREA_TOP so update() moves it above the boundary
        self.gs.phase = Phase.PLAYING
        self.gs.rounds = [BolterRound(x=39, y=PLAY_AREA_TOP)]
        self.gs.update()
        self.assertEqual(len(self.gs.rounds), 0)

    def test_start_to_playing_on_enter(self):
        gs = GameState()  # fresh state in Phase.START
        gs.handle_input(ord("\n"))
        self.assertEqual(gs.phase, Phase.PLAYING)
        self.assertEqual(gs.wave_number, 1)


class TestWaveDifficulty(unittest.TestCase):
    def test_wave_difficulty_wave1(self):
        d = wave_difficulty(1)
        self.assertEqual(d.speed_multiplier, 1.0)
        self.assertEqual(d.enemy_count, 8)
        self.assertEqual(d.enemy_hp_mult, 1)
        self.assertFalse(d.has_boss)
        self.assertIn(EnemyType.TERMAGANT, d.enemy_types)

    def test_wave_difficulty_wave3_has_chaos_marines(self):
        d = wave_difficulty(3)
        self.assertIn(EnemyType.CHAOS_MARINE, d.enemy_types)
        self.assertIn(EnemyType.TERMAGANT, d.enemy_types)

    def test_wave_difficulty_wave5_has_all_types_and_boss(self):
        d = wave_difficulty(5)
        self.assertIn(EnemyType.TERMAGANT, d.enemy_types)
        self.assertIn(EnemyType.CHAOS_MARINE, d.enemy_types)
        self.assertIn(EnemyType.ORK_BOY, d.enemy_types)
        self.assertTrue(d.has_boss)


class TestSpawnWave(unittest.TestCase):
    def setUp(self):
        self.gs = GameState()
        self.gs.wave_number = 1
        self.gs.phase = Phase.PLAYING

    def test_spawn_wave_creates_correct_enemy_count_wave1(self):
        self.gs._spawn_wave(1)
        self.assertEqual(len(self.gs.enemies), 8)

    def test_spawn_wave_creates_correct_enemy_count_wave2(self):
        self.gs._spawn_wave(2)
        self.assertEqual(len(self.gs.enemies), 10)


class TestCombat(unittest.TestCase):
    def _make_enemy(self, x, y, hp=1, etype=EnemyType.TERMAGANT):
        data = ENEMY_DATA[etype]
        return EnemyUnit(
            x=x, y=float(y),
            enemy_type=etype, hp=hp,
            speed=data["base_speed"],
            score_value=data["score_value"],
        )

    def setUp(self):
        self.gs = GameState()
        self.gs.phase = Phase.PLAYING

    def test_round_hits_enemy_removes_both(self):
        self.gs.enemies = [self._make_enemy(x=20, y=10)]
        self.gs.rounds = [BolterRound(x=20, y=10)]
        self.gs.update()
        self.assertEqual(len(self.gs.enemies), 0)
        self.assertEqual(len(self.gs.rounds), 0)

    def test_round_hit_adds_score(self):
        self.gs.enemies = [self._make_enemy(x=20, y=10)]
        self.gs.rounds = [BolterRound(x=20, y=10)]
        self.gs.update()
        self.assertEqual(self.gs.player.score, 10)

    def test_enemy_reaching_player_row_decrements_lives(self):
        self.gs.enemies = [self._make_enemy(x=20, y=PLAYER_ROW)]
        self.gs.player.lives = 3
        self.gs.update()
        self.assertEqual(self.gs.player.lives, 2)
        self.assertEqual(len(self.gs.enemies), 0)

    def test_all_enemies_cleared_triggers_wave_transition(self):
        self.gs.enemies = []
        self.gs.boss = None
        self.gs.update()
        self.assertEqual(self.gs.phase, Phase.WAVE_TRANSITION)
        self.assertEqual(self.gs.transition_ticks, TRANSITION_TICKS)

    def test_wave_transition_countdown_spawns_next_wave(self):
        self.gs.phase = Phase.WAVE_TRANSITION
        self.gs.wave_number = 1
        self.gs.transition_ticks = 1
        self.gs.update()
        self.assertEqual(self.gs.phase, Phase.PLAYING)
        self.assertEqual(self.gs.wave_number, 2)
        self.assertGreater(len(self.gs.enemies), 0)

    def test_lives_zero_triggers_game_over(self):
        self.gs.player.lives = 0
        self.gs.update()
        self.assertEqual(self.gs.phase, Phase.GAME_OVER)


class TestScoreAndReplayability(unittest.TestCase):
    def _make_enemy(self, x, y, hp=1, etype=EnemyType.TERMAGANT):
        data = ENEMY_DATA[etype]
        return EnemyUnit(x=x, y=float(y), enemy_type=etype, hp=hp,
                         speed=data["base_speed"], score_value=data["score_value"])

    def _make_boss_unit(self, x=20, y=5.0, hp=1, mechanic=BossMechanic.ZIGZAG,
                        label="Hive Tyrant", score_value=200):
        return BossUnit(x=x, y=y, hp=hp, speed=0.3, score_value=score_value,
                        label=label, mechanic=mechanic)

    def test_score_increments_by_enemy_type_value(self):
        gs = GameState()
        gs.phase = Phase.PLAYING
        gs.enemies = [self._make_enemy(x=20, y=10, etype=EnemyType.TERMAGANT)]
        gs.rounds = [BolterRound(x=20, y=10)]
        gs.update()
        self.assertEqual(gs.player.score, 10)
        # reset phase — first kill emptied enemies → WAVE_TRANSITION triggered
        gs.phase = Phase.PLAYING
        gs.enemies = [self._make_enemy(x=30, y=10, etype=EnemyType.CHAOS_MARINE)]
        gs.rounds = [BolterRound(x=30, y=10)]
        gs.update()
        self.assertEqual(gs.player.score, 25)

    def test_boss_score_exceeds_standard_enemy(self):
        gs = GameState()
        gs.phase = Phase.PLAYING
        gs.enemies = [self._make_enemy(x=20, y=10, etype=EnemyType.TERMAGANT)]
        gs.rounds = [BolterRound(x=20, y=10)]
        gs.update()  # +10, enemies empty → WAVE_TRANSITION
        gs.phase = Phase.PLAYING
        gs.enemies = []
        gs.boss = self._make_boss_unit(x=40, y=5.0, hp=1, score_value=200)
        gs.rounds = [BolterRound(x=40, y=5)]
        gs.update()  # +200
        self.assertEqual(gs.player.score, 210)
        self.assertGreater(200, 10)  # boss score > standard enemy

    def test_high_score_updates_on_game_over(self):
        gs = GameState()
        gs.phase = Phase.PLAYING
        gs.player.score = 500
        gs.high_score = 100
        gs.player.lives = 0
        gs.update()
        self.assertEqual(gs.high_score, 500)

    def test_high_score_not_updated_if_lower(self):
        gs = GameState()
        gs.phase = Phase.PLAYING
        gs.player.score = 50
        gs.high_score = 200
        gs.player.lives = 0
        gs.update()
        self.assertEqual(gs.high_score, 200)

    def test_reset_preserves_high_score_clears_score(self):
        gs = GameState()
        gs.high_score = 999
        gs.player.score = 500
        gs.reset()
        self.assertEqual(gs.high_score, 999)
        self.assertEqual(gs.player.score, 0)
        self.assertEqual(gs.player.lives, 3)
        self.assertEqual(gs.wave_number, 1)

    def test_wave_number_increments_after_transition(self):
        gs = GameState()
        gs.phase = Phase.WAVE_TRANSITION
        gs.wave_number = 1
        gs.transition_ticks = 1
        gs.update()
        self.assertEqual(gs.wave_number, 2)

    def test_restart_from_game_over_via_enter(self):
        gs = GameState()
        gs.phase = Phase.GAME_OVER
        gs.player.score = 300
        gs.handle_input(ord('\n'))
        self.assertEqual(gs.phase, Phase.PLAYING)
        self.assertEqual(gs.player.lives, 3)
        self.assertEqual(gs.player.score, 0)


def _make_boss(x=20, y=5.0, hp=10, mechanic=BossMechanic.ZIGZAG,
               mechanic_tick=0, direction=1) -> BossUnit:
    return BossUnit(
        x=x, y=y, hp=hp, speed=0.5, score_value=200,
        label="Hive Tyrant", mechanic=mechanic,
        mechanic_tick=mechanic_tick, direction=direction,
    )


class TestBossSpawn(unittest.TestCase):
    def test_wave5_spawns_boss(self):
        gs = GameState()
        gs._spawn_wave(5)
        self.assertIsNotNone(gs.boss)
        self.assertEqual(gs.boss.label, "Hive Tyrant")
        self.assertEqual(gs.boss.hp, 10)

    def test_boss_requires_multiple_hits(self):
        gs = GameState()
        gs.phase = Phase.PLAYING
        gs.boss = _make_boss(x=20, y=5.0, hp=10)
        gs.rounds = [BolterRound(x=20, y=5)]
        gs.update()
        self.assertIsNotNone(gs.boss)
        self.assertEqual(gs.boss.hp, 9)

    def test_wave_not_complete_while_boss_alive(self):
        gs = GameState()
        gs.phase = Phase.PLAYING
        gs.enemies = []
        gs.boss = _make_boss(hp=1)
        gs.update()
        self.assertEqual(gs.phase, Phase.PLAYING)


class TestBossMechanics(unittest.TestCase):
    def test_boss_zigzag_reverses_direction(self):
        gs = GameState()
        gs.phase = Phase.PLAYING
        gs.enemies = []
        gs.boss = _make_boss(mechanic=BossMechanic.ZIGZAG, direction=1,
                             mechanic_tick=14, x=20, y=5.0)
        gs._update_boss()
        self.assertEqual(gs.boss.direction, -1)

    def test_boss_fires_back_spawns_projectile(self):
        gs = GameState()
        gs.phase = Phase.PLAYING
        gs.enemies = []
        gs.boss = _make_boss(mechanic=BossMechanic.FIRES_BACK, mechanic_tick=29,
                             x=20, y=5.0)
        gs.player.x = PLAYER_START_X
        gs._update_boss()
        self.assertEqual(len(gs.boss_rounds), 1)
        self.assertEqual(gs.boss_rounds[0].x, PLAYER_START_X)

    def test_boss_splits_on_death_spawns_ork_boyz(self):
        gs = GameState()
        gs.phase = Phase.PLAYING
        gs.enemies = []
        gs.boss = _make_boss(mechanic=BossMechanic.SPLITS, hp=1, x=20, y=5.0)
        gs.rounds = [BolterRound(x=20, y=5)]
        gs.update()
        self.assertIsNone(gs.boss)
        self.assertEqual(len(gs.enemies), 3)
        for e in gs.enemies:
            self.assertEqual(e.enemy_type, EnemyType.ORK_BOY)

    def test_consecutive_waves_increase_difficulty(self):
        for n in range(1, 6):
            d1 = wave_difficulty(n)
            d2 = wave_difficulty(n + 1)
            self.assertLessEqual(d1.speed_multiplier, d2.speed_multiplier)
            self.assertLessEqual(d1.enemy_count, d2.enemy_count)

    def test_boss_projectile_hits_player_decrements_lives(self):
        gs = GameState()
        gs.phase = Phase.PLAYING
        gs.player.x = 39
        gs.player.lives = 3
        gs.boss_rounds = [BossProjectile(x=39, y=PLAYER_ROW)]
        gs.update()
        self.assertEqual(gs.player.lives, 2)
        self.assertEqual(len(gs.boss_rounds), 0)


# ── T018–T022: WeaponTier logic tests (TDD — written before T029–T035 implementation) ──────────────

class TestWeaponTier(unittest.TestCase):
    def setUp(self):
        self.gs = GameState()
        self.gs.phase = Phase.PLAYING

    # T018: default tier
    def test_default_tier_is_standard(self):
        """Player starts at STANDARD tier. (FR-016 baseline, T018)"""
        self.assertEqual(self.gs.player.weapon_tier, WeaponTier.STANDARD)

    # T019: tier-aware firing
    def test_standard_fires_one_round(self):
        """STANDARD tier fires exactly 1 round at player.x. (FR-016, T019)"""
        self.gs.player.weapon_tier = WeaponTier.STANDARD
        self.gs.handle_input(ord(' '))
        self.assertEqual(len(self.gs.rounds), 1)
        self.assertEqual(self.gs.rounds[0].x, self.gs.player.x)

    def test_twin_linked_fires_two_rounds(self):
        """TWIN_LINKED fires 2 rounds at player.x-1 and player.x+1. (FR-017, T019)"""
        self.gs.player.weapon_tier = WeaponTier.TWIN_LINKED
        px = self.gs.player.x
        self.gs.handle_input(ord(' '))
        self.assertEqual(len(self.gs.rounds), 2)
        xs = sorted(r.x for r in self.gs.rounds)
        self.assertEqual(xs, [px - 1, px + 1])

    def test_storm_bolter_fires_three_rounds(self):
        """STORM_BOLTER fires 3 rounds. (FR-018, T019)"""
        self.gs.player.weapon_tier = WeaponTier.STORM_BOLTER
        self.gs.handle_input(ord(' '))
        self.assertEqual(len(self.gs.rounds), 3)

    # T020: diagonal dx field
    def test_storm_outer_rounds_have_dx(self):
        """Storm outer rounds carry dx=-1 and dx=+1; centre round dx=0. (FR-018, T020)"""
        self.gs.player.weapon_tier = WeaponTier.STORM_BOLTER
        px = self.gs.player.x
        self.gs.handle_input(ord(' '))
        dx_map = {r.x: r.dx for r in self.gs.rounds}
        self.assertEqual(dx_map.get(px, None), 0)       # centre straight
        self.assertEqual(dx_map.get(px - 1, None), -1)  # left outer drifts left
        self.assertEqual(dx_map.get(px + 1, None), 1)   # right outer drifts right

    def test_diagonal_rounds_drift_x_each_tick(self):
        """A BolterRound with dx=-1 shifts x by -1 per tick. (FR-018, T020)"""
        self.gs.player.weapon_tier = WeaponTier.STANDARD  # no extra rounds
        self.gs.rounds = [BolterRound(x=20, y=15, dx=-1)]
        self.gs.update()
        # After one tick: x should be 20 + (-1) = 19
        self.assertEqual(self.gs.rounds[0].x, 19)

    # T021: tier advancement via token collection
    def test_tier_advance_standard_to_twin(self):
        """Collecting a token at STANDARD advances to TWIN_LINKED. (FR-012, FR-013 step, T021)"""
        self.gs.player.weapon_tier = WeaponTier.STANDARD
        # Place token so that after POWERUP_FALL_SPEED addition: int(y) == PLAYER_ROW
        start_y = float(PLAYER_ROW) - POWERUP_FALL_SPEED
        self.gs.tokens = [PowerUpToken(x=self.gs.player.x, y=start_y)]
        self.gs.update()
        self.assertEqual(self.gs.player.weapon_tier, WeaponTier.TWIN_LINKED)

    def test_tier_advance_twin_to_storm(self):
        """Collecting a token at TWIN_LINKED advances to STORM_BOLTER. (FR-013 step, T021)"""
        self.gs.player.weapon_tier = WeaponTier.TWIN_LINKED
        start_y = float(PLAYER_ROW) - POWERUP_FALL_SPEED
        self.gs.tokens = [PowerUpToken(x=self.gs.player.x, y=start_y)]
        self.gs.update()
        self.assertEqual(self.gs.player.weapon_tier, WeaponTier.STORM_BOLTER)

    def test_tier_capped_at_storm(self):
        """Collecting a token at STORM_BOLTER has no effect — tier stays STORM_BOLTER. (FR-013, T021)"""
        self.gs.player.weapon_tier = WeaponTier.STORM_BOLTER
        start_y = float(PLAYER_ROW) - POWERUP_FALL_SPEED
        self.gs.tokens = [PowerUpToken(x=self.gs.player.x, y=start_y)]
        self.gs.update()
        self.assertEqual(self.gs.player.weapon_tier, WeaponTier.STORM_BOLTER)

    # T022: tier reset on life loss
    def test_tier_resets_on_enemy_breach(self):
        """Weapon tier resets to STANDARD when enemy reaches PLAYER_ROW. (FR-015, T022)"""
        self.gs.player.weapon_tier = WeaponTier.TWIN_LINKED
        data = ENEMY_DATA[EnemyType.TERMAGANT]
        # Enemy already at PLAYER_ROW — descend check removes it and deducts a life
        self.gs.enemies = [EnemyUnit(
            x=30, y=float(PLAYER_ROW),
            enemy_type=EnemyType.TERMAGANT,
            hp=1, speed=data["base_speed"],
            score_value=data["score_value"],
        )]
        self.gs.update()
        self.assertEqual(self.gs.player.weapon_tier, WeaponTier.STANDARD)

    def test_tier_resets_on_boss_projectile_hit(self):
        """Weapon tier resets to STANDARD when a boss projectile hits the player. (FR-015, T022)"""
        self.gs.player.weapon_tier = WeaponTier.TWIN_LINKED
        self.gs.player.x = 39
        self.gs.boss_rounds = [BossProjectile(x=39, y=PLAYER_ROW)]
        self.gs.update()
        self.assertEqual(self.gs.player.weapon_tier, WeaponTier.STANDARD)


# ── T023–T028: PowerUpToken lifecycle tests ──────────────────────────────────────────────────────

class TestPowerUpToken(unittest.TestCase):
    def _make_enemy(self, x, y, hp=1, etype=EnemyType.TERMAGANT):
        data = ENEMY_DATA[etype]
        return EnemyUnit(x=x, y=float(y), enemy_type=etype, hp=hp,
                         speed=data["base_speed"], score_value=data["score_value"])

    def setUp(self):
        self.gs = GameState()
        self.gs.phase = Phase.PLAYING

    # T023: token spawn on kill
    def test_token_spawns_on_kill_with_mocked_random(self):
        """Enemy kill with random < DROP_CHANCE spawns a token at kill site. (FR-010, T023)"""
        self.gs.enemies = [self._make_enemy(x=20, y=10)]
        self.gs.rounds = [BolterRound(x=20, y=10)]
        with patch('game.random.random', return_value=0.10):
            self.gs.update()
        self.assertEqual(len(self.gs.tokens), 1)
        self.assertEqual(self.gs.tokens[0].x, 20)

    def test_no_token_spawn_above_chance(self):
        """Enemy kill with random >= DROP_CHANCE spawns no token. (FR-010, T023)"""
        self.gs.enemies = [self._make_enemy(x=20, y=10)]
        self.gs.rounds = [BolterRound(x=20, y=10)]
        with patch('game.random.random', return_value=0.20):
            self.gs.update()
        self.assertEqual(len(self.gs.tokens), 0)

    # T024: descent and collection
    def test_token_descends_by_fall_speed_each_tick(self):
        """Token y increases by POWERUP_FALL_SPEED each tick. (FR-011, T024)"""
        token = PowerUpToken(x=20, y=5.0)
        self.gs.tokens = [token]
        self.gs.enemies = [self._make_enemy(x=50, y=5)]  # keep playing phase
        self.gs.update()
        self.assertAlmostEqual(self.gs.tokens[0].y, 5.0 + POWERUP_FALL_SPEED)

    def test_token_collected_at_player_row_and_column(self):
        """Token reaching PLAYER_ROW at player.x is collected; tier advances. (FR-012, T024)"""
        self.gs.player.weapon_tier = WeaponTier.STANDARD
        start_y = float(PLAYER_ROW) - POWERUP_FALL_SPEED
        self.gs.tokens = [PowerUpToken(x=self.gs.player.x, y=start_y)]
        self.gs.update()
        self.assertEqual(len(self.gs.tokens), 0)
        self.assertEqual(self.gs.player.weapon_tier, WeaponTier.TWIN_LINKED)

    # T025: non-collection and removal
    def test_token_not_collected_at_wrong_column(self):
        """Token at PLAYER_ROW but wrong column is not collected; removed since it passed. (FR-020, T025)"""
        wrong_x = self.gs.player.x + 5
        start_y = float(PLAYER_ROW) - POWERUP_FALL_SPEED
        self.gs.tokens = [PowerUpToken(x=wrong_x, y=start_y)]
        self.gs.update()
        # Token reached PLAYER_ROW at wrong column: should be removed (passed player row), tier unchanged
        self.assertEqual(self.gs.player.weapon_tier, WeaponTier.STANDARD)
        self.assertEqual(len(self.gs.tokens), 0)

    def test_token_removed_past_player_row(self):
        """Token already past PLAYER_ROW is removed from game state. (FR-020, T025)"""
        self.gs.tokens = [PowerUpToken(x=self.gs.player.x + 3, y=float(PLAYER_ROW + 1))]
        self.gs.update()
        self.assertEqual(len(self.gs.tokens), 0)

    # T026: multiple simultaneous tokens
    def test_multiple_simultaneous_tokens_tracked_independently(self):
        """Two tokens: one collected, one still falling — each tracked independently. (edge case, T026)"""
        self.gs.player.weapon_tier = WeaponTier.STANDARD
        px = self.gs.player.x
        collect_y = float(PLAYER_ROW) - POWERUP_FALL_SPEED  # will reach PLAYER_ROW after 1 tick
        falling_y = 5.0                                      # still high up
        self.gs.tokens = [
            PowerUpToken(x=px, y=collect_y),        # will be collected
            PowerUpToken(x=px + 5, y=falling_y),    # still falling, different column
        ]
        self.gs.update()
        # One collected → tier advanced; one still falling
        self.assertEqual(self.gs.player.weapon_tier, WeaponTier.TWIN_LINKED)
        self.assertEqual(len(self.gs.tokens), 1)
        self.assertAlmostEqual(self.gs.tokens[0].y, falling_y + POWERUP_FALL_SPEED)

    # T027: token not affected by bolter rounds (FR-019)
    def test_bolter_round_does_not_destroy_token(self):
        """A BolterRound passing through a token's cell does NOT remove the token. (FR-019, T027)"""
        token = PowerUpToken(x=20, y=10.0)
        self.gs.tokens = [token]
        self.gs.rounds = [BolterRound(x=20, y=10)]
        # Keep an enemy alive so phase stays PLAYING, and the enemy is far from round
        self.gs.enemies = [self._make_enemy(x=50, y=5)]
        self.gs.update()
        # Token should still exist (not destroyed by round)
        self.assertTrue(any(t.x == 20 for t in self.gs.tokens))

    # T028: tokens cleared on wave spawn and reset
    def test_tokens_cleared_on_spawn_wave(self):
        """_spawn_wave() clears all tokens. (edge case: wave transition, T028)"""
        self.gs.tokens = [PowerUpToken(x=20, y=10.0), PowerUpToken(x=30, y=12.0)]
        self.gs._spawn_wave(1)
        self.assertEqual(self.gs.tokens, [])

    def test_tokens_cleared_on_reset(self):
        """reset() clears all tokens. (edge case: game restart, T028)"""
        self.gs.tokens = [PowerUpToken(x=20, y=10.0)]
        self.gs.reset()
        self.assertEqual(self.gs.tokens, [])


if __name__ == "__main__":
    unittest.main()
