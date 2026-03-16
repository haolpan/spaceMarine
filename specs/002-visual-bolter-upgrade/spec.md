# Feature Specification: Visual Fidelity & Bolter Upgrade System

**Feature Branch**: `002-visual-bolter-upgrade`
**Created**: 2026-03-15
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Faction-Accurate Character Silhouettes (Priority: P1)

A player launching the game immediately recognises each entity by its visual
shape alone, without needing to read a label. The Space Marine they control
looks like an Ultramarine — armoured silhouette with chapter iconography across
2–3 character rows. Tyranid Termagants look insectoid. Chaos Space Marines look
spiked and corrupted. Ork Boyz look hunched and brutish. Bosses gain a more
imposing multi-row form.

**Why this priority**: Visual identity is the fastest immersion improvement.
It is independently demonstrable from the first second of play, before any
combat occurs, and requires no gameplay mechanic changes.

**Independent Test**: Launch the game → player character reads as an armoured
Space Marine → each of the three enemy types is visually distinct from the
others and from the player → no label reading required to tell them apart.

**Acceptance Scenarios**:

1. **Given** the game is in PLAYING phase, **When** the player character is rendered, **Then** it occupies 3 columns and at least 2 rows and resembles an armoured warrior holding a weapon.
2. **Given** a Tyranid Termagant is on screen, **When** the player looks at it, **Then** its symbol reads as insectoid or alien.
3. **Given** a Chaos Space Marine is on screen, **When** the player looks at it, **Then** its symbol reads as spiked or chaotically armoured.
4. **Given** an Ork Boy is on screen, **When** the player looks at it, **Then** its symbol reads as hulking and brutish.
5. **Given** a boss enemy is on screen, **When** the player looks at it, **Then** it renders across at least 3 columns and 2 rows, visually more imposing than standard enemies.

---

### User Story 2 — Bolter Upgrade Power-Up System (Priority: P2)

When the player destroys an enemy, there is a small chance a power-up token
drops from the kill site and falls toward the player. Collecting it by moving
under it upgrades the Bolter to the next tier. Tiers: **Standard** (single
round) → **Twin-Linked** (two parallel rounds) → **Storm Bolter** (three rounds
fanning outward). The HUD shows the active tier at all times. Dying resets the
weapon to Standard.

**Why this priority**: Adds a reward loop and tactical depth on top of the
existing combat, requiring P1 visuals to land well. Independently testable
without changing enemies or bosses.

**Independent Test**: Play until a power-up drops → walk under it → HUD tier
label changes → firing produces additional rounds → lose a life → tier resets
to Standard.

**Acceptance Scenarios**:

1. **Given** an enemy is killed and the random drop triggers, **When** the token spawns, **Then** it appears at the enemy's last position and falls downward.
2. **Given** a token is falling and reaches the player row at the player's column, **When** contact occurs, **Then** weapon tier advances by one step.
3. **Given** the player is at Storm Bolter tier and another token is collected, **When** contact occurs, **Then** tier remains at Storm Bolter (cap reached).
4. **Given** the player has Twin-Linked or Storm Bolter tier and loses a life, **When** the life is deducted, **Then** tier immediately reverts to Standard.
5. **Given** any weapon tier is active and the player fires, **When** rounds spawn, **Then** Standard = 1 round at x; Twin-Linked = 2 rounds at x−1 and x+1; Storm Bolter = 3 rounds with outer two drifting diagonally outward each tick.

---

### Edge Cases

- Power-up token and a Bolter round occupy the same cell — they do not interact; only the player collects tokens.
- Multiple tokens falling simultaneously — each is tracked and collected independently.
- Token falls past the player row without collection — token is removed from game state.
- Player dies while a token is mid-fall — token disappears with the combat state reset.
- Storm Bolter diagonal rounds reach the play-area boundary — rounds are removed normally when y < PLAY_AREA_TOP.

## Requirements *(mandatory)*

### Functional Requirements

**Visual — Player Character**

- **FR-001**: The Space Marine character MUST render across a minimum of 2 rows and 3 columns, forming a recognisable armoured silhouette with a weapon shape.
- **FR-002**: The character design MUST reference Ultramarine chapter iconography (inverted Omega / Ultima mark on the body).
- **FR-003**: The player's collision and movement logic MUST remain based on a single anchor x-position (centre column); visual rows above the player row are cosmetic only.

**Visual — Enemies**

- **FR-004**: Each of the three enemy types MUST use a symbol or glyph that visually differs from the other two and from the player.
- **FR-005**: Termagant symbol MUST suggest an insectoid or multi-limbed shape.
- **FR-006**: Chaos Space Marine symbol MUST suggest spiked or chaotic armour.
- **FR-007**: Ork Boy symbol MUST suggest a hunched, brutish silhouette.

**Visual — Bosses**

- **FR-008**: Boss enemies MUST render at minimum 3 columns wide and 2 rows tall.
- **FR-009**: The additional boss visual row MUST appear above the existing boss label/HP-bar row; existing label logic is unchanged.

**Bolter Upgrade System**

- **FR-010**: On any enemy death, the game MUST evaluate a 15% random chance to spawn a power-up token at the enemy's last position.
- **FR-011**: A spawned token MUST descend at a rate of 1 row per 2 ticks (half the speed of a standard Termagant).
- **FR-012**: A token is collected when it reaches the player row AND its column equals the player's current x-position.
- **FR-013**: On collection, weapon tier MUST advance by exactly one step; collecting at Storm Bolter has no effect.
- **FR-014**: The HUD MUST display the current weapon tier with a short label: `BOLTER`, `TWIN-LNK`, or `STORM`.
- **FR-015**: On any life loss, weapon tier MUST immediately revert to Standard.
- **FR-016**: Firing at Standard tier MUST spawn one BolterRound at player x.
- **FR-017**: Firing at Twin-Linked tier MUST spawn two BolterRound instances at player x−1 and player x+1.
- **FR-018**: Firing at Storm Bolter tier MUST spawn three rounds: one straight at player x, and two that drift ±1 column per tick as they travel upward.
- **FR-019**: Power-up tokens MUST NOT be destroyed by Bolter rounds.
- **FR-020**: Tokens that descend past the player row MUST be removed from game state.

### Key Entities

- **PowerUpToken**: Collectible object with position (x, y:float) and descent speed. Spawned on enemy death by probability check. Removed on collection or on passing player row.
- **WeaponTier**: Ordered three-level value (Standard → Twin-Linked → Storm Bolter). Owned by Player. Resets to Standard on life loss.
- **DiagonalBolterRound**: A BolterRound variant that additionally shifts ±1 column per tick as it travels upward. Used for the outer two rounds of Storm Bolter fire.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every enemy type is correctly identified by visual appearance alone within 10 seconds of wave start, without reading any label.
- **SC-002**: The player character is recognised as an armoured Space Marine by a first-time observer within 5 seconds.
- **SC-003**: A power-up token appears at least once during a standard 3-wave session (statistically near-certain at 15% per kill with 8+ enemies per wave).
- **SC-004**: Weapon tier upgrade is visible within one fire action of collecting a token — more rounds appear immediately.
- **SC-005**: Weapon tier reverts to Standard within one tick of a life being lost — no residual spread rounds fire after the life deduction.
- **SC-006**: HUD weapon tier label is readable at all times during PLAYING phase and updates the same frame as a tier change.
- **SC-007**: No layout corruption, overlap, or visual artefact is introduced to the existing HUD, border, or play-area by the new multi-row art.

## Assumptions

- Terminal font is monospaced UTF-8; multi-byte characters that render as double-width cells are avoided.
- The 80×24 minimum terminal constraint remains in force. Multi-row character art fits within existing play-area boundaries.
- The 15% drop probability is a fixed starting point; balance tuning is out of scope.
- Diagonal BolterRound x-drift uses integer increments per tick, consistent with existing collision model.
- Boss visual enhancement (FR-008, FR-009) is rendering-only; HP, mechanics, and collision are unchanged.

## Out of Scope

- Sound or flash effects on power-up collection.
- Power-up types other than Bolter tier advance (no shields, no extra lives).
- Persistent weapon tier across waves or sessions.
- Enemy behaviour or AI changes.
- Boss mechanic changes.
