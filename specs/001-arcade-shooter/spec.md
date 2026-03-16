# Feature Specification: Space Marine Arcade Shooter

**Feature Branch**: `001-arcade-shooter`
**Created**: 2026-03-15
**Status**: Draft
**Input**: User description: "Build a terminal-based Space Marine arcade shooter."

## User Scenarios & Testing *(mandatory)*

## User Story 1 - Player Movement & Firing (Priority: P1)

A player launches the game, sees the Space Marine at the bottom of the screen, and
can immediately move the warrior left and right and fire Bolter rounds upward.
No enemies are required — this story delivers a controllable player character that
responds to keyboard input, establishing the foundation all other stories build on.

**Why this priority**  
Without a responsive, controllable player character there is no game. Every other
story depends on movement and firing being functional.

**Independent Test**  
Launch the game, observe the Space Marine on screen, press left/right/fire keys,
confirm the character moves and rounds travel upward. This delivers a playable
interactive foundation even with no enemies present.

### Acceptance Scenarios

1. **Given** the game has started, **When** the player presses the left movement key,  
   **Then** the Space Marine moves one position to the left without leaving the play area.
2. **Given** the game has started, **When** the player presses the right movement key,  
   **Then** the Space Marine moves one position to the right without leaving the play area.
3. **Given** the game has started, **When** the player presses the fire key,  
   **Then** a Bolter round appears above the Space Marine and travels upward.
4. **Given** a Bolter round is travelling upward, **When** it reaches the top of the play area,  
   **Then** it disappears without error.
5. **Given** the game is running, **When** the player presses the quit key,  
   **Then** the game exits cleanly and restores the terminal to its prior state.

---

## User Story 2 - Enemy Wave Combat (Priority: P2)

Enemies spawn in formations and descend toward the player. The player destroys them
with Bolter fire before they reach the bottom. Once all enemies in a wave are
eliminated, the next wave begins.

This establishes the core combat loop of the arcade experience.

**Why this priority**  
A playable combat loop — fire at enemies, clear the wave, face the next — is the
minimum viable game experience.

**Independent Test**  
Launch the game and observe enemies spawn, descend, and be destroyed by Bolter
rounds. Confirm a new wave starts after the previous is cleared.

### Acceptance Scenarios

1. **Given** a wave begins, **When** enemies spawn,  
   **Then** they appear near the top of the play area in a recognisable formation and begin descending.
2. **Given** a Bolter round is in flight, **When** it strikes an enemy,  
   **Then** the enemy is removed from the field and the round disappears.
3. **Given** the player has not intercepted an enemy, **When** an enemy reaches the player's row,  
   **Then** the player loses one life and the enemy is removed.
4. **Given** all enemies in a wave are destroyed, **When** no enemies remain on screen,  
   **Then** the next wave begins after a brief transition.
5. **Given** the player has lost all lives, **When** the last life is lost,  
   **Then** the game enters the Game Over state and no further movement or firing input is accepted.

---

## User Story 3 - Escalating Difficulty & Boss Encounters (Priority: P3)

Each wave becomes progressively harder than the last. Enemies may move faster,
spawn in greater numbers, or require more hits to destroy.

Every fifth wave introduces a named boss enemy from Warhammer 40K lore with a
unique mechanic not present in standard enemies.

**Why this priority**  
Escalation and boss encounters create long-term engagement and replayability.

**Independent Test**  
Play through at least six waves and verify that wave 2 is noticeably harder than
wave 1 and that wave 5 spawns a named boss enemy with at least one unique behaviour.

### Acceptance Scenarios

1. **Given** two consecutive waves, **When** comparing difficulty parameters,  
   **Then** at least one of speed, spawn count, health, or formation density increases.
2. **Given** wave 5 begins, **When** enemies spawn,  
   **Then** a named boss enemy appears on screen (e.g., Hive Tyrant, Chaos Terminator, Ork Warboss).
3. **Given** a boss enemy is present, **When** the player fires Bolter rounds at it,  
   **Then** the boss requires more hits to destroy than any standard enemy.
4. **Given** a boss enemy is present, **When** observing its behaviour,  
   **Then** it exhibits at least one mechanic not seen in standard enemies.
5. **Given** a boss wave, **When** all standard enemies are destroyed but the boss remains,  
   **Then** the wave does not end until the boss is defeated.

---

## User Story 4 - Replayability & Score Tracking (Priority: P4)

Score, lives, wave counter, and session high score are displayed throughout play.

On game over the player sees their final score and wave reached, and can restart
instantly with a single keypress without exiting the terminal.

**Why this priority**  
These systems transform a single playthrough into a replayable arcade experience.

**Independent Test**  
Play a full session to game over. Confirm score increments on kills, lives decrement
on hits, wave counter advances, and restart begins a fresh session without relaunching.

### Acceptance Scenarios

1. **Given** gameplay is active, **When** the player destroys an enemy,  
   **Then** the score increases by a visible amount appropriate to the enemy type.
2. **Given** gameplay is active, **When** the player is hit by an enemy,  
   **Then** the lives counter decreases by one.
3. **Given** the game is running, **When** the player advances to a new wave,  
   **Then** the wave counter increments to the new wave number.
4. **Given** a session ends with a score higher than the current session best,  
   **When** the game-over screen appears,  
   **Then** the high score updates to reflect the new record.
5. **Given** the game-over screen is visible, **When** the player presses the restart key,  
   **Then** a new session begins immediately with score reset and lives restored.

---

# Edge Cases

- Terminal window is smaller than the minimum required play area — the game MUST
  display a clear message and exit gracefully.
- Player fires many rounds rapidly — all rounds MUST be tracked independently.
- Player is hit on the same frame the final enemy is destroyed — life loss still
  registers and the next wave begins normally.
- Restart is pressed immediately on game-over — a new session starts cleanly.
- Player holds movement keys continuously — the Space Marine stops at boundaries
  and does not wrap across the screen.
- Multiple enemies are destroyed simultaneously — wave completion triggers once.

# Requirements *(mandatory)*

## Start & Launch

**FR-001**: The game MUST launch with a single command requiring no installation or configuration.

**FR-002**: The game MUST display a start screen showing the game title, controls, and a start prompt.

---

## Player Controls

**FR-003**: The player MUST be able to move left and right within the play area.

**FR-004**: The player MUST be able to fire a Bolter round upward.

**FR-005**: Multiple Bolter rounds MUST be able to exist simultaneously.

**FR-006**: The player MUST be able to quit the game at any time and restore the terminal state.

---

## Enemy System

**FR-007**: Enemies MUST spawn in wave formations and descend toward the player.

**FR-008**: The game MUST include Tyranid Termagants, Chaos Space Marines, and Ork Boyz by wave 5.

**FR-009**: Enemy and boss names MUST use Warhammer 40K lore terminology.

**FR-010**: Bolter rounds hitting enemies MUST remove them or reduce their health.

**FR-011**: Enemies reaching the player's row MUST cause loss of one life.

---

## Wave & Difficulty Progression

**FR-012**: A new wave MUST begin automatically after the current wave is cleared.

**FR-013**: Each wave MUST increase difficulty via speed, spawn count, health, or formation density.

**FR-014**: Every fifth wave MUST spawn a boss enemy.

**FR-015**: Boss enemies MUST have at least one unique mechanic.

---

## Replayability Systems

**FR-016**: Score, wave number, lives, and session high score MUST be displayed.

**FR-017**: Destroying enemies MUST increase score.

**FR-018**: Each session begins with 3 lives.

**FR-019**: Losing all lives MUST trigger a Game Over screen displaying final score and wave.

**FR-020**: The player MUST be able to restart immediately from the Game Over screen.

---

## Robustness

**FR-021**: If the terminal window is too small, the game MUST show a clear error message and exit safely.

---

# Key Entities

**Space Marine (Player)**  
The player-controlled character with horizontal movement and remaining lives.

**Enemy**  
Hostile units descending toward the player with position, type, health, and speed.

**Boss Enemy**  
Special enemy appearing every five waves with elevated health and unique behaviour.

**Bolter Round**  
Projectile fired upward by the player.

**Wave**  
A set of enemies spawned together with increasing difficulty parameters.

**Game Session**  
Tracks score, session high score, wave number, remaining lives, and current state.

---

# Success Criteria *(mandatory)*

**SC-001**: A player can clone the repository and start gameplay with one command and no setup.

**SC-002**: The game runs on macOS with Python 3.8+ and no external dependencies.

**SC-003**: All three enemy types appear before wave 6.

**SC-004**: Each wave is visibly harder than the previous.

**SC-005**: Boss enemies appear every fifth wave.

**SC-006**: Score, wave, and lives remain visible and accurate throughout gameplay.

**SC-007**: A player can finish a session and start another without restarting the program.

**SC-008**: All player-facing terminology uses Warhammer 40K lore.

---

# Assumptions

- **Lives**: 3 lives per session.
- **Session high score** means the highest score achieved since program start.
- **Enemy return fire** is optional and may be limited to boss enemies.
- **Terminal size** minimum assumed: 80×24.
- **Wave transitions** may include a short pause or message between waves.
- **Controls visibility**: active controls MUST be shown on the start screen or UI.