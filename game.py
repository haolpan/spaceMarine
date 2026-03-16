"""
game.py — Space Marine Arcade Shooter: pure game logic
No curses imports. Fully unit-testable without a terminal.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional
import random
import json
import os

# ── Layout constants ───────────────────────────────────────────────────────────
SCREEN_ROWS     = 24
SCREEN_COLS     = 80
HUD_ROWS        = 3
PLAY_AREA_TOP   = 3
PLAYER_ROW      = 23
PLAY_AREA_LEFT  = 1
PLAY_AREA_RIGHT = 78
PLAYER_START_X  = 39
FPS             = 20
FRAME_DELAY     = 0.05
TRANSITION_TICKS    = 60
POWERUP_DROP_CHANCE = 0.15   # FR-010: 15% chance to drop a token on enemy kill
POWERUP_FALL_SPEED  = 0.5    # FR-011: 0.5 rows/tick = 1 row per 2 ticks

# Key constants — match curses values on Unix/macOS (safe to define without importing curses)
KEY_LEFT  = 260   # curses.KEY_LEFT
KEY_RIGHT = 261   # curses.KEY_RIGHT

_HIGH_SCORE_FILE = os.path.expanduser("~/.space_marine_score.json")

# ── Phase state machine ────────────────────────────────────────────────────────
class Phase(Enum):
    START           = auto()
    PLAYING         = auto()
    WAVE_TRANSITION = auto()
    GAME_OVER       = auto()
    QUIT            = auto()

# ── Enemy data ─────────────────────────────────────────────────────────────────
class EnemyType(Enum):
    TERMAGANT    = auto()
    CHAOS_MARINE = auto()
    ORK_BOY      = auto()

ENEMY_DATA = {
    EnemyType.TERMAGANT:    {"label": "Tyranid Termagant",  "symbol": "T", "base_hp": 1, "base_speed": 1.0, "score_value": 10},
    EnemyType.CHAOS_MARINE: {"label": "Chaos Space Marine", "symbol": "C", "base_hp": 1, "base_speed": 0.7, "score_value": 15},
    EnemyType.ORK_BOY:      {"label": "Ork Boy",            "symbol": "₩", "base_hp": 2, "base_speed": 0.5, "score_value": 20},
}

# ── Boss data ──────────────────────────────────────────────────────────────────
class BossMechanic(Enum):
    ZIGZAG     = auto()   # Hive Tyrant: zigzag horizontal movement
    FIRES_BACK = auto()   # Chaos Terminator: fires projectiles at player
    SPLITS     = auto()   # Ork Warboss: spawns 3 Ork Boyz on death

# ── Weapon tier ────────────────────────────────────────────────────────────────
class WeaponTier(Enum):
    STANDARD     = auto()   # Single round (default)
    TWIN_LINKED  = auto()   # Two parallel rounds at x-1 and x+1
    STORM_BOLTER = auto()   # Three rounds: centre straight + outer two diagonal

BOSS_CATALOG: List[dict] = [
    {"label": "Hive Tyrant",      "base_hp": 10, "mechanic": BossMechanic.ZIGZAG,     "score_value": 200, "symbol": "H"},
    {"label": "Chaos Terminator", "base_hp": 15, "mechanic": BossMechanic.FIRES_BACK, "score_value": 300, "symbol": "X"},
    {"label": "Ork Warboss",      "base_hp": 12, "mechanic": BossMechanic.SPLITS,     "score_value": 250, "symbol": "W"},
]

# ── Data classes ───────────────────────────────────────────────────────────────
@dataclass
class Player:
    x: int
    lives: int = 3
    score: int = 0
    weapon_tier: WeaponTier = field(default_factory=lambda: WeaponTier.STANDARD)


@dataclass
class EnemyUnit:
    x: int
    y: float
    enemy_type: EnemyType
    hp: int
    speed: float
    score_value: int

    @property
    def symbol(self) -> str:
        return ENEMY_DATA[self.enemy_type]["symbol"]

    @property
    def label(self) -> str:
        return ENEMY_DATA[self.enemy_type]["label"]


@dataclass
class BossUnit:
    """Boss enemy with elevated HP and a unique mechanic."""
    x: int
    y: float
    hp: int
    speed: float
    score_value: int
    label: str
    mechanic: BossMechanic
    mechanic_tick: int = 0
    direction: int = 1
    phase: int = 0

    @property
    def symbol(self) -> str:
        return f"[{self.label[0]}]"


@dataclass
class BolterRound:
    """Player projectile — travels upward one row per tick. dx!=0 for diagonal Storm Bolter rounds."""
    x: int
    y: int
    dx: int = 0   # column drift per tick: 0=straight, -1=drift-left, +1=drift-right (FR-018)


@dataclass
class BossProjectile:
    """Boss projectile (FIRES_BACK mechanic) — travels downward."""
    x: int
    y: int


@dataclass
class PowerUpToken:
    """Collectible token dropped on enemy kill. Descends toward player; collected on contact."""
    x: int
    y: float   # float for smooth descent matching enemy model


# ── Wave difficulty value object ───────────────────────────────────────────────
@dataclass
class WaveDifficulty:
    wave_number: int
    speed_multiplier: float
    enemy_count: int
    enemy_hp_mult: int
    enemy_types: List[EnemyType]
    has_boss: bool


def wave_difficulty(wave_number: int) -> WaveDifficulty:
    """Compute difficulty parameters for a given wave number."""
    speed_multiplier = round(1.0 + (wave_number - 1) * 0.15, 2)
    enemy_count      = min(8 + (wave_number - 1) * 2, 30)
    enemy_hp_mult    = 1 + (wave_number - 1) // 3
    enemy_types: List[EnemyType] = [EnemyType.TERMAGANT]
    if wave_number >= 3:
        enemy_types.append(EnemyType.CHAOS_MARINE)
    if wave_number >= 5:
        enemy_types.append(EnemyType.ORK_BOY)
    has_boss = (wave_number % 5 == 0)
    return WaveDifficulty(
        wave_number=wave_number,
        speed_multiplier=speed_multiplier,
        enemy_count=enemy_count,
        enemy_hp_mult=enemy_hp_mult,
        enemy_types=enemy_types,
        has_boss=has_boss,
    )


# ── GameState ──────────────────────────────────────────────────────────────────
class GameState:
    """Root mutable state. Owned entirely by game.py; renderer reads it read-only."""

    def __init__(self) -> None:
        self.phase:            Phase                = Phase.START
        self.player:           Player               = Player(x=PLAYER_START_X)
        self.enemies:          List[EnemyUnit]      = []
        self.boss:             Optional[BossUnit]   = None
        self.rounds:           List[BolterRound]    = []
        self.boss_rounds:      List[BossProjectile] = []
        self.tokens:           List[PowerUpToken]   = []
        self.wave_number:      int                  = 0
        self.tick:             int                  = 0
        self.transition_ticks: int                  = 0
        self.high_score:       int                  = self._read_high_score()

    # ── Persistence ────────────────────────────────────────────────────────────
    def _read_high_score(self) -> int:
        try:
            with open(_HIGH_SCORE_FILE) as f:
                return int(json.load(f).get("high_score", 0))
        except Exception:
            return 0

    def _write_high_score(self) -> None:
        try:
            with open(_HIGH_SCORE_FILE, "w") as f:
                json.dump({"high_score": self.high_score}, f)
        except Exception:
            pass

    # ── Input handling ─────────────────────────────────────────────────────────
    def handle_input(self, key: int) -> None:
        """Dispatch keyboard input to the appropriate phase handler."""
        # Quit from any phase
        if key == ord('q'):
            self.phase = Phase.QUIT
            return

        if self.phase == Phase.START:
            if key in (ord('\n'), ord('\r'), ord('r')):
                self.phase = Phase.PLAYING
                self.wave_number = 1
                self._spawn_wave(1)

        elif self.phase == Phase.PLAYING:
            if key in (KEY_LEFT, ord('a')):
                self.player.x = max(PLAY_AREA_LEFT, self.player.x - 1)
            elif key in (KEY_RIGHT, ord('d')):
                self.player.x = min(PLAY_AREA_RIGHT, self.player.x + 1)
            elif key == ord(' '):
                px   = self.player.x
                tier = self.player.weapon_tier
                if tier == WeaponTier.STANDARD:
                    self.rounds.append(BolterRound(x=px, y=PLAYER_ROW - 1, dx=0))
                elif tier == WeaponTier.TWIN_LINKED:
                    self.rounds.append(BolterRound(x=px - 1, y=PLAYER_ROW - 1, dx=0))
                    self.rounds.append(BolterRound(x=px + 1, y=PLAYER_ROW - 1, dx=0))
                elif tier == WeaponTier.STORM_BOLTER:
                    self.rounds.append(BolterRound(x=px,     y=PLAYER_ROW - 1, dx=0))
                    self.rounds.append(BolterRound(x=px - 1, y=PLAYER_ROW - 1, dx=-1))
                    self.rounds.append(BolterRound(x=px + 1, y=PLAYER_ROW - 1, dx=+1))

        elif self.phase == Phase.GAME_OVER:
            if key in (ord('\n'), ord('\r'), ord('r')):
                self.reset()

    # ── Game tick ──────────────────────────────────────────────────────────────
    def update(self) -> None:
        """Advance the game by one tick."""
        if self.phase == Phase.WAVE_TRANSITION:
            self._update_wave_transition()
            return
        if self.phase != Phase.PLAYING:
            return

        self.tick += 1

        # Collision detection at current positions (before anything moves)
        self._check_collisions()

        # Move Bolter rounds upward (apply x drift first for diagonal Storm rounds — T029)
        for r in self.rounds:
            r.x += r.dx   # FR-018: diagonal drift (0 for standard/twin-linked rounds)
            r.y -= 1
        self.rounds = [r for r in self.rounds if r.y >= PLAY_AREA_TOP]

        # Enemy descent
        self._descend_enemies()

        # Boss update — implemented in US3 (T061, T065)
        if self.boss is not None:
            self._update_boss()

        # Move boss projectiles — implemented in US3 (T063)
        self._update_boss_projectiles()

        # Power-up token descent, collection, and cleanup (FR-011..FR-013, FR-020)
        self._update_tokens()

        # Phase transition checks
        self._check_phase_transitions()

    def _update_wave_transition(self) -> None:
        self.transition_ticks -= 1
        if self.transition_ticks <= 0:
            self.wave_number += 1
            self._spawn_wave(self.wave_number)
            self.phase = Phase.PLAYING

    def _descend_enemies(self) -> None:
        """Move enemies downward. Enemies reaching player row cost a life. (US2 T041)"""
        for e in self.enemies:
            e.y += e.speed / FPS
        survivors = []
        for e in self.enemies:
            if int(e.y) >= PLAYER_ROW:
                self.player.lives = max(0, self.player.lives - 1)
                self.player.weapon_tier = WeaponTier.STANDARD   # FR-015: reset on life loss
            else:
                survivors.append(e)
        self.enemies = survivors

    def _check_collisions(self) -> None:
        """Resolve round/enemy collisions. (US2 T042)"""
        dead_enemy_indices: set = set()
        dead_round_indices: set = set()

        for ri, r in enumerate(self.rounds):
            for ei, e in enumerate(self.enemies):
                if r.x == e.x and r.y == int(e.y):
                    e.hp -= 1
                    dead_round_indices.add(ri)
                    if e.hp <= 0:
                        self.player.score += e.score_value
                        if random.random() < POWERUP_DROP_CHANCE:   # FR-010: 15% drop
                            self.tokens.append(PowerUpToken(x=e.x, y=float(int(e.y))))
                        dead_enemy_indices.add(ei)

        self.enemies = [e for i, e in enumerate(self.enemies) if i not in dead_enemy_indices]
        self.rounds = [r for i, r in enumerate(self.rounds) if i not in dead_round_indices]

        # Boss collision
        if self.boss is not None:
            b = self.boss
            surviving_rounds = []
            for r in self.rounds:
                if r.x == b.x and r.y == int(b.y):
                    b.hp -= 1
                    if b.hp <= 0:
                        self.player.score += b.score_value
                        if random.random() < POWERUP_DROP_CHANCE:   # FR-010: boss kill also triggers drop
                            self.tokens.append(PowerUpToken(x=b.x, y=float(int(b.y))))
                        if b.mechanic == BossMechanic.SPLITS:
                            for dx in (-1, 0, 1):
                                data = ENEMY_DATA[EnemyType.ORK_BOY]
                                self.enemies.append(EnemyUnit(
                                    x=b.x + dx, y=b.y,
                                    enemy_type=EnemyType.ORK_BOY,
                                    hp=data["base_hp"],
                                    speed=data["base_speed"],
                                    score_value=data["score_value"],
                                ))
                        self.boss = None
                        break  # boss dead, discard the hitting round
                else:
                    surviving_rounds.append(r)
            if self.boss is None:
                self.rounds = surviving_rounds
            else:
                self.rounds = surviving_rounds

    def _update_boss(self) -> None:
        """Advance boss position and trigger mechanic. (US3 T061, T065)"""
        b = self.boss
        b.y += b.speed / FPS
        b.mechanic_tick += 1

        if b.mechanic == BossMechanic.ZIGZAG:
            if b.mechanic_tick % 15 == 0:
                b.direction = -b.direction
            b.x += b.direction
            b.x = max(PLAY_AREA_LEFT, min(PLAY_AREA_RIGHT, b.x))

        elif b.mechanic == BossMechanic.FIRES_BACK:
            if b.mechanic_tick % 30 == 0:
                self.boss_rounds.append(
                    BossProjectile(x=self.player.x, y=int(b.y) + 1)
                )

    def _update_boss_projectiles(self) -> None:
        """Move boss projectiles downward; hit player when they reach PLAYER_ROW."""
        survivors = []
        for bp in self.boss_rounds:
            bp.y += 1
            if bp.y >= PLAYER_ROW:
                if bp.x == self.player.x:
                    self.player.lives = max(0, self.player.lives - 1)
                    self.player.weapon_tier = WeaponTier.STANDARD   # FR-015: reset on life loss
            else:
                survivors.append(bp)
        self.boss_rounds = survivors

    def _update_tokens(self) -> None:
        """Descend tokens, collect on contact, remove past player row. (FR-011..FR-013, FR-020)"""
        surviving = []
        for token in self.tokens:
            token.y += POWERUP_FALL_SPEED
            row = int(token.y)
            if row == PLAYER_ROW and token.x == self.player.x:
                # Collect — advance tier by one step, capped at STORM_BOLTER (FR-013)
                if self.player.weapon_tier == WeaponTier.STANDARD:
                    self.player.weapon_tier = WeaponTier.TWIN_LINKED
                elif self.player.weapon_tier == WeaponTier.TWIN_LINKED:
                    self.player.weapon_tier = WeaponTier.STORM_BOLTER
                # STORM_BOLTER: no-op
            elif row < PLAYER_ROW:
                surviving.append(token)   # still above player row, keep falling
            # row >= PLAYER_ROW and not collected: remove (FR-020 — passed player row)
        self.tokens = surviving

    def _check_phase_transitions(self) -> None:
        """Evaluate PLAYING → WAVE_TRANSITION / GAME_OVER. (US2 T043, T045)"""
        if self.player.lives <= 0:
            if self.player.score > self.high_score:
                self.high_score = self.player.score
            self._write_high_score()
            self.phase = Phase.GAME_OVER
            return

        if len(self.enemies) == 0 and self.boss is None:
            self.phase = Phase.WAVE_TRANSITION
            self.transition_ticks = TRANSITION_TICKS

    # ── Wave spawning ──────────────────────────────────────────────────────────
    def _spawn_wave(self, wave_number: int) -> None:
        """Populate enemies (and optionally a boss) for the given wave."""
        diff = wave_difficulty(wave_number)
        self.enemies = []
        self.boss = None
        self.tokens = []

        count = diff.enemy_count
        # Spread enemies across two rows
        x_positions = list(range(PLAY_AREA_LEFT + 2, PLAY_AREA_RIGHT - 1,
                                  max(1, (PLAY_AREA_RIGHT - PLAY_AREA_LEFT - 4) // max(1, count))))
        x_positions = x_positions[:count]
        # If we got fewer x slots than count, pad by repeating
        while len(x_positions) < count:
            x_positions.append(x_positions[len(x_positions) % max(1, len(x_positions))])

        for i, x in enumerate(x_positions):
            row = PLAY_AREA_TOP if i % 2 == 0 else PLAY_AREA_TOP + 1
            etype = random.choice(diff.enemy_types)
            data = ENEMY_DATA[etype]
            self.enemies.append(EnemyUnit(
                x=x,
                y=float(row),
                enemy_type=etype,
                hp=data["base_hp"] * diff.enemy_hp_mult,
                speed=data["base_speed"] * diff.speed_multiplier,
                score_value=data["score_value"],
            ))

        if diff.has_boss:
            boss_index = ((wave_number // 5) - 1) % 3
            cycle      = ((wave_number // 5) - 1) // 3
            catalog    = BOSS_CATALOG[boss_index]
            self.boss  = BossUnit(
                x=PLAYER_START_X,
                y=float(PLAY_AREA_TOP),
                hp=catalog["base_hp"] + 5 * cycle,
                speed=0.3 * diff.speed_multiplier,
                score_value=catalog["score_value"],
                label=catalog["label"],
                mechanic=catalog["mechanic"],
            )

    # ── Session reset ──────────────────────────────────────────────────────────
    def reset(self) -> None:
        """Reinitialise session state, preserving high_score. (US2 T050)"""
        high = self.high_score
        self.player           = Player(x=PLAYER_START_X)
        self.enemies          = []
        self.boss             = None
        self.rounds           = []
        self.boss_rounds      = []
        self.tokens           = []
        self.wave_number      = 1
        self.tick             = 0
        self.transition_ticks = 0
        self.phase            = Phase.PLAYING
        self.high_score       = high
        self._spawn_wave(1)
