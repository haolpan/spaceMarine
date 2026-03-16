"""
space_marine.py — curses renderer + entry point for Space Marine Arcade Shooter.
Imports game logic from game.py (zero curses). Do not put game logic here.
"""
import curses
import time
import sys

from game import (
    GameState, Phase,
    SCREEN_ROWS, SCREEN_COLS, PLAYER_ROW, PLAY_AREA_TOP,
    FRAME_DELAY, TRANSITION_TICKS,
    WeaponTier,
)

# FR-014: HUD weapon tier labels
WEAPON_TIER_LABELS = {
    WeaponTier.STANDARD:     "BOLTER",
    WeaponTier.TWIN_LINKED:  "TWIN-LNK",
    WeaponTier.STORM_BOLTER: "STORM",
}

FLAVOR_TEXT = [
    "For the Emperor!",
    "By the Omnissiah!",
    "Death to the Xenos!",
    "Hold the line, Battle-Brother!",
    "No mercy for the heretic!",
    "Suffer not the alien to live!",
]


def draw_start_screen(stdscr: "curses.window") -> None:
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    def center(row: int, text: str) -> None:
        col = max(0, (w - len(text)) // 2)
        try:
            stdscr.addstr(row, col, text)
        except curses.error:
            pass

    center(6,  "╔══════════════════════════════════════════════╗")
    center(7,  "║                                              ║")
    center(8,  "║          *** SPACE MARINE ***                ║")
    center(9,  "║   A Warhammer 40,000 Arcade Experience       ║")
    center(10, "║                                              ║")
    center(11, "║  Defend the Imperium against the enemies     ║")
    center(12, "║  of Mankind.                                 ║")
    center(13, "║                                              ║")
    center(14, "║  CONTROLS:                                   ║")
    center(15, "║    ←/→  or  A/D   Move Space Marine          ║")
    center(16, "║    SPACE           Fire Bolter               ║")
    center(17, "║    R / ENTER       Start                     ║")
    center(18, "║    Q               Quit                      ║")
    center(19, "║                                              ║")
    center(20, "║       Press ENTER or R to begin              ║")
    center(21, "║             For the Emperor!                 ║")
    center(22, "║                                              ║")
    center(23, "╚══════════════════════════════════════════════╝")
    stdscr.refresh()


def draw_game_over_screen(stdscr: "curses.window", gs: GameState) -> None:
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    def center(row: int, text: str) -> None:
        col = max(0, (w - len(text)) // 2)
        try:
            stdscr.addstr(row, col, text)
        except curses.error:
            pass

    center(6,  "╔══════════════════════════════════════════════╗")
    center(7,  "║                                              ║")
    center(8,  "║        *** BATTLE CONCLUDED ***              ║")
    center(9,  "║                                              ║")
    center(10, "║  The Space Marine has fallen in glorious     ║")
    center(11, "║  combat.                                     ║")
    center(12, "║                                              ║")
    center(13, f"║  FINAL SCORE:    {gs.player.score:05d}                     ║")
    center(14, f"║  WAVE REACHED:   {gs.wave_number:02d}                        ║")
    center(15, f"║  SESSION BEST:   {gs.high_score:05d}                     ║")
    center(16, "║                                              ║")
    center(17, "║      Press ENTER or R to fight again         ║")
    center(18, "║      Press Q to retreat                      ║")
    center(19, "║                                              ║")
    center(20, "╚══════════════════════════════════════════════╝")
    stdscr.refresh()


def draw_wave_transition(stdscr: "curses.window", gs: GameState) -> None:
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    def center(row: int, text: str) -> None:
        col = max(0, (w - len(text)) // 2)
        try:
            stdscr.addstr(row, col, text)
        except curses.error:
            pass

    center(h // 2 - 1, f"=== WAVE {gs.wave_number + 1} INCOMING ===")
    center(h // 2 + 1, "Prepare, Battle-Brother.")
    ticks_left = max(0, gs.transition_ticks)
    bar_len = max(0, ticks_left * 20 // TRANSITION_TICKS) if TRANSITION_TICKS > 0 else 0
    center(h // 2 + 3, f"[{'█' * bar_len}{' ' * (20 - bar_len)}]")
    stdscr.refresh()


def draw_hud(stdscr: "curses.window", gs: GameState) -> None:
    """Draw rows 0–2: title bar, HUD stats, separator."""
    h, w = stdscr.getmaxyx()
    border_inner = SCREEN_COLS - 2

    def safe_addstr(row: int, col: int, text: str) -> None:
        if 0 <= row < h and 0 <= col < w:
            try:
                stdscr.addstr(row, col, text[:max(0, w - col)])
            except curses.error:
                pass

    title = "SPACE MARINE"
    title_line = ("╔" + "═" * ((border_inner - len(title) - 2) // 2) +
                  f" {title} " +
                  "═" * ((border_inner - len(title) - 2 + 1) // 2) + "╗")
    safe_addstr(0, 0, title_line[:SCREEN_COLS])

    lives_str  = " ".join(["♥"] * max(0, gs.player.lives))
    tier_label = WEAPON_TIER_LABELS.get(gs.player.weapon_tier, "BOLTER")   # FR-014, SC-006
    hud = (f"  SCORE: {gs.player.score:05d}   HI: {gs.high_score:05d}"
           f"   WAVE: {gs.wave_number:02d}   {lives_str}   {tier_label}")
    safe_addstr(1, 0, "║" + hud.ljust(border_inner) + "║")
    safe_addstr(2, 0, "╠" + "═" * border_inner + "╣")


def draw_game(stdscr: "curses.window", gs: GameState) -> None:
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    def safe_addstr(row: int, col: int, text: str) -> None:
        if 0 <= row < h and 0 <= col < w:
            try:
                stdscr.addstr(row, col, text[:max(0, w - col)])
            except curses.error:
                pass

    border_inner = SCREEN_COLS - 2

    # ── HUD rows 0–2 ───────────────────────────────────────────────────────────
    draw_hud(stdscr, gs)

    # ── Rows 3–20: play area side borders ──────────────────────────────────────
    for row in range(PLAY_AREA_TOP, 21):
        safe_addstr(row, 0, "║")
        safe_addstr(row, SCREEN_COLS - 1, "║")

    # ── Row 21: separator ──────────────────────────────────────────────────────
    safe_addstr(21, 0, "╠" + "═" * border_inner + "╣")

    # ── Row 22: flavor text + controls hint ────────────────────────────────────
    flavor = FLAVOR_TEXT[(gs.tick // 60) % len(FLAVOR_TEXT)]
    status = f"[← → move  SPACE fire  Q quit]  {flavor}"
    safe_addstr(22, 0, "║" + status.ljust(border_inner) + "║")

    # ── Row 23: player ─────────────────────────────────────────────────────────
    safe_addstr(23, 0, "║")
    safe_addstr(PLAYER_ROW, gs.player.x - 1, "[℧]")  # FR-001, FR-002: 3-col Ultramarine symbol (℧ U+2127 Ultima mark); FR-003: collision anchor = player.x
    safe_addstr(23, SCREEN_COLS - 1, "║")

    # ── Bolter rounds ──────────────────────────────────────────────────────────
    for r in gs.rounds:
        if PLAY_AREA_TOP <= r.y < PLAYER_ROW:
            safe_addstr(r.y, r.x, "│")

    # ── Enemies ────────────────────────────────────────────────────────────────
    for e in gs.enemies:
        row = int(e.y)
        if PLAY_AREA_TOP <= row < PLAYER_ROW:
            safe_addstr(row, e.x, e.symbol)

    # ── Boss ───────────────────────────────────────────────────────────────────
    _BOSS_ART = {
        "Hive Tyrant":      "/\\  /\\",
        "Chaos Terminator": "><><>",
        "Ork Warboss":      "[|||]",
    }
    if gs.boss is not None:
        b = gs.boss
        row = int(b.y)
        if PLAY_AREA_TOP <= row < PLAYER_ROW:
            # FR-008, FR-009: decorative art row above HP bar (T014, T015)
            if row - 2 >= PLAY_AREA_TOP:
                art = _BOSS_ART.get(b.label, "*****")
                safe_addstr(row - 2, max(1, b.x - len(art) // 2), art)
            # HP bar on the row above (if space available)
            if row - 1 >= PLAY_AREA_TOP:
                hp_filled = max(0, b.hp)
                hp_bar = f"{b.label}  HP: {'█' * min(hp_filled, 20)}"
                safe_addstr(row - 1, max(1, b.x - len(hp_bar) // 2), hp_bar)
            safe_addstr(row, b.x - 1, b.symbol)

    # ── Boss projectiles ───────────────────────────────────────────────────────
    for bp in gs.boss_rounds:
        if PLAY_AREA_TOP <= bp.y < PLAYER_ROW:
            safe_addstr(bp.y, bp.x, "↓")

    # ── Power-up tokens ────────────────────────────────────────────────────────
    for token in gs.tokens:
        row = int(token.y)
        if PLAY_AREA_TOP <= row < PLAYER_ROW:
            safe_addstr(row, token.x, "*")

    stdscr.refresh()


def run_game(stdscr: "curses.window") -> None:
    # ── Terminal size check ────────────────────────────────────────────────────
    rows, cols = stdscr.getmaxyx()
    if rows < SCREEN_ROWS or cols < SCREEN_COLS:
        stdscr.erase()
        msg = "Terminal too small. Minimum 80x24 required. Press any key."
        try:
            stdscr.addstr(rows // 2, max(0, (cols - len(msg)) // 2), msg)
        except curses.error:
            pass
        stdscr.refresh()
        stdscr.nodelay(False)
        stdscr.getch()
        return

    curses.curs_set(0)
    stdscr.nodelay(True)

    gs = GameState()

    while gs.phase != Phase.QUIT:
        # ── Mid-game terminal size guard (T082) ────────────────────────────────
        rows, cols = stdscr.getmaxyx()
        if rows < SCREEN_ROWS or cols < SCREEN_COLS:
            stdscr.erase()
            msg = "Terminal too small — resize to 80×24 to continue."
            try:
                stdscr.addstr(0, 0, msg[:cols])
            except curses.error:
                pass
            stdscr.refresh()
            time.sleep(FRAME_DELAY)
            continue

        key = stdscr.getch()
        while key != curses.ERR:
            gs.handle_input(key)
            key = stdscr.getch()

        gs.update()

        if gs.phase == Phase.START:
            draw_start_screen(stdscr)
        elif gs.phase == Phase.PLAYING:
            draw_game(stdscr, gs)
        elif gs.phase == Phase.WAVE_TRANSITION:
            draw_wave_transition(stdscr, gs)
        elif gs.phase == Phase.GAME_OVER:
            draw_game_over_screen(stdscr, gs)

        time.sleep(FRAME_DELAY)


if __name__ == "__main__":
    curses.wrapper(run_game)
