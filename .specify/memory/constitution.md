<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 → 2.0.0 (MAJOR — all five principles replaced with project-specific rules)

Bump rationale:
  v1.0.0 contained generic software-engineering placeholders. The project is now
  fully defined as a Python curses arcade game. All five principles were redefined;
  this is backward-incompatible with any in-flight work written against v1.0.0.

Modified principles (old → new):
  I.   Feature-First Development           → I.   Zero-Dependency Portability
  II.  Test-Driven Development             → II.  Warhammer 40K Authenticity
  III. Clean Architecture                  → III. Minimal Footprint
  IV.  Observability                       → IV.  Escalating Difficulty
  V.   Simplicity (YAGNI)                  → V.   Replayability

Added sections:
  - Explicit Out-of-Scope (codifies the project's stated exclusions)

Removed / renamed sections:
  - "Technology & Stack Constraints" retitled and now fully resolved (no TODO)
  - Development Workflow simplified to match a solo arcade game project

Templates requiring updates:
  ✅ .specify/templates/plan-template.md — Constitution Check gates now derive from
     the 5 new principles; no structural change to the template needed (gates are
     generated at plan time from this file)
  ✅ .specify/templates/spec-template.md — User Scenarios and Success Criteria sections
     remain mandatory and are consistent with the new principles
  ✅ .specify/templates/tasks-template.md — Observability task type from v1.0.0 no
     longer mandated; testable-core-logic note added to task notes section
  ✅ .specify/templates/constitution-template.md — source template unchanged (generic)

Resolved TODOs from v1.0.0:
  - TODO(TECH_STACK): Resolved — Python 3, stdlib curses, macOS terminal.
  - TODO(RATIFICATION_DATE): Confirmed 2026-03-15.

Deferred TODOs:
  - None.
-->

# Space Marine Constitution

## Core Principles

### I. Zero-Dependency Portability

The game MUST run with a single command (`python space_marine.py` or equivalent)
on any Mac that has Python 3 installed.

Only Python's **standard library** is permitted — `pip install` is prohibited.
The `curses` module MUST be the sole rendering and input mechanism.

Any feature that requires a third-party dependency is out-of-scope and MUST
be rejected or redesigned using stdlib alternatives.

The launch command MUST require:

- no installation step
- no environment variables
- no command-line arguments
- no configuration files
- no pre-run scripts

**Rationale**: The zero-setup promise is the primary UX guarantee. A single
broken import makes the game unrunnable for the target audience.

### II. Warhammer 40K Authenticity

All enemy designations, weapon names, faction labels, and in-game flavor text
MUST use lore-accurate Warhammer 40,000 terminology.

Generic sci-fi substitutes (e.g., "alien", "laser gun") are prohibited in
player-facing text.

Mandatory enemy roster (MUST appear by wave 5 at the latest):

- Tyranid Termagants
- Chaos Space Marines
- Ork Boyz

Boss enemies introduced at wave milestones MUST also be named from established
Warhammer 40K lore, such as:

- Hive Tyrant
- Chaos Terminator
- Ork Warboss

**Rationale**: The Warhammer 40K theme is the product differentiator. Lore
accuracy distinguishes this project from a generic arcade clone.

### III. Minimal Footprint

The game MUST remain extremely small and easy to inspect.

Runtime source code SHOULD remain within **1–3 Python files**.

Adding files beyond this range SHOULD only occur when it improves:

- testability
- readability
- maintainability

Splitting modules purely for stylistic organisation without practical benefit
is discouraged.

Launch MUST require exactly one command with no build step, compilation, or
pre-run tooling.

**Rationale**: Instant playability is a core pillar. Excessive file sprawl
increases cognitive overhead and undermines the "clone and play" experience.

### IV. Escalating Difficulty

Each successive wave MUST be harder than the previous one.

Difficulty MUST increase along at least one measurable axis:

- enemy movement speed
- enemy spawn count
- enemy health multiplier
- formation density
- enemy fire rate

A wave MUST NOT reduce all difficulty parameters relative to the previous wave.

Boss enemies MUST appear at defined milestones (recommended: every 5 waves).

Each boss MUST introduce at least one mechanic not present in standard enemies,
for example:

- increased health pool
- erratic or non-linear movement
- multi-phase behaviour
- splitting into smaller enemies on death

**Rationale**: Escalation is the core engagement loop. A flat difficulty curve
kills replayability after the first run.

### V. Replayability

Every playable build MUST include the following systems:

**Score Display**
- The current score MUST be visible during gameplay.

**High Score**
- The highest score achieved in the current session MUST be displayed.
- Persistence across process restarts SHOULD be implemented using a file
  (e.g., JSON) but is not mandatory.

**Wave Counter**
- The current wave MUST be visible on screen at all times.

**Lives System**
- The player MUST start with a finite number of lives (minimum: 3).

**Game Over Screen**
- Losing all lives MUST display:
  - final score
  - wave reached
  - restart prompt

**Instant Restart**
- The player MUST be able to restart immediately after game-over with a
  single keypress without exiting the terminal.

**Rationale**: One-run arcade games are quickly forgotten. These systems
create the return loop that makes the game worth replaying.

## User Experience Expectations

The game SHOULD include a minimal start screen that shows:

- game title
- control instructions
- start key

Controls MUST be simple and discoverable.

Key bindings SHOULD remain stable and minimal (e.g., movement + fire + quit).

Rendering SHOULD work within a typical terminal window without requiring
manual resizing or non-default terminal configuration.

The game SHOULD avoid visible flicker when updating frames where practical.

## Technology & Stack

**Language**
- Python 3 (minimum 3.8)

**Rendering & Input**
- Python stdlib `curses` only

**Persistence**
- stdlib `json` or `pickle` for optional high score storage

**Testing**
- `unittest` from Python's standard library for core game logic

The curses rendering layer is excluded from automated test requirements.

The **game logic layer MUST be separated from the curses rendering layer**
so that core mechanics (state, scoring, wave progression, collision detection)
can be unit tested without requiring a terminal.

## Platform Support

Primary platform:

- macOS terminal

Secondary platform (best effort):

- Linux terminal

Windows support is **not guaranteed**. Users may run the game through
compatibility environments such as:

- WSL (Windows Subsystem for Linux)
- Git Bash environments that provide curses support

## Explicit Out-of-Scope

The following are permanently out-of-scope and MUST NOT be implemented:

- Multiplayer (local or networked)
- Sound or audio output
- Mouse input
- Graphical rendering outside terminal character cells
- External dependencies outside Python's standard library
- Required terminal resizing or non-default terminal configuration

Proposals touching any of the above MUST be rejected during spec review.

## Development Workflow

1. **Spec first**: No implementation begins without an approved `spec.md`
   (`/speckit.specify` → `/speckit.clarify` → review).
2. **Plan before coding**: Run `/speckit.plan` to produce `plan.md` and verify
   the Constitution Check passes all five Core Principles.
3. **Tasks before execution**: Run `/speckit.tasks` to produce `tasks.md` before
   writing code.
4. **Play-test gate**: Before marking a wave or feature complete, manually play
   through it in the terminal and confirm it is fun and functional.
5. **No regressions**: New waves or enemies MUST NOT break previously passing waves.
   All earlier gameplay MUST remain intact after each merge.
6. **Out-of-scope guard**: Any feature touching the Explicit Out-of-Scope list MUST
   be rejected at spec review, not at implementation time.

## Governance

This constitution supersedes all other documented practices in this repository.
Where a conflict exists between this document and any other guide, this document wins.

**Amendment procedure**:

1. Open a PR that modifies `.specify/memory/constitution.md`.
2. Increment `CONSTITUTION_VERSION` according to the versioning policy below.
3. Run `/speckit.constitution` to propagate changes to dependent templates.
4. PR description MUST include: motivation, principles affected, and migration notes
   for any in-flight feature specs.
5. PR requires at least one approving review before merge.

**Versioning policy**:

- **MAJOR** (X.0.0): Backward-incompatible removal or redefinition of a principle.
- **MINOR** (X.Y.0): New principle or section added; materially expanded guidance.
- **PATCH** (X.Y.Z): Clarifications, wording improvements, typo fixes.

**Compliance review**: Every PR and design review MUST confirm adherence to the five
Core Principles. Use `.specify/memory/constitution.md` as the authoritative reference.

**Version**: 2.0.0 | **Ratified**: 2026-03-15 | **Last Amended**: 2026-03-15
