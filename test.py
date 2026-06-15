#!/usr/bin/env python3
"""
cava_grid.py

Shows a live grid of cava-style spectrum visualizers in your terminal,
one per PulseAudio/PipeWire source (including monitor sources for sinks).

Requires:
  - cava (installed and on PATH)
  - python3 (curses is in stdlib)
  - pactl (pulseaudio-utils / pipewire-pulse)

Usage:
  python3 cava_grid.py
"""

import curses
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

BARS_PER_CELL = 16   # number of cava bars rendered per cell
FRAMERATE = 30


def get_sources():
    """Return list of (name, description) for all pactl sources."""
    out = subprocess.run(
        ["pactl", "list", "sources"], capture_output=True, text=True, check=True
    ).stdout

    sources = []
    name = None
    desc = None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("Name:"):
            name = line.split("Name:", 1)[1].strip()
        elif line.startswith("Description:"):
            desc = line.split("Description:", 1)[1].strip()
            if name:
                sources.append((name, desc or name))
                name = None
                desc = None
    return sources


class CavaWorker:
    """Spawns a cava process for one source and keeps reading bar values."""

    def __init__(self, source_name, bars=BARS_PER_CELL, framerate=FRAMERATE):
        self.source_name = source_name
        self.bars = bars
        self.framerate = framerate
        self.values = [0] * bars
        self.lock = threading.Lock()
        self._stop = threading.Event()
        self._proc = None
        self._thread = None
        self._cfg_path = None

    def _write_config(self):
        fd, path = tempfile.mkstemp(prefix="cava_", suffix=".conf")
        cfg = f"""
[general]
bars = {self.bars}
framerate = {self.framerate}

[input]
method = pulse
source = {self.source_name}

[output]
method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = 100
bar_delimiter = 32
frame_delimiter = 10
"""
        with os.fdopen(fd, "w") as f:
            f.write(cfg)
        self._cfg_path = path
        return path

    def start(self):
        cfg_path = self._write_config()
        self._proc = subprocess.Popen(
            ["cava", "-p", cfg_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        for line in self._proc.stdout:
            if self._stop.is_set():
                break
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            try:
                vals = [int(p) for p in parts]
            except ValueError:
                continue
            if len(vals) == self.bars:
                with self.lock:
                    self.values = vals

    def get_values(self):
        with self.lock:
            return list(self.values)

    def stop(self):
        self._stop.set()
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        if self._cfg_path and os.path.exists(self._cfg_path):
            os.unlink(self._cfg_path)


BAR_CHARS = " ▁▂▃▄▅▆▇█"


def render_bar(value, height):
    """Render a single vertical bar as a list of chars from bottom to top,
    given value 0-100 and the cell's pixel height (in rows * 8 levels)."""
    levels = height * 8
    filled = int((value / 100.0) * levels)
    filled = max(0, min(filled, levels))
    rows = []
    for r in range(height):
        # row 0 is top, row height-1 is bottom
        row_from_bottom = height - 1 - r
        cell_levels = filled - row_from_bottom * 8
        if cell_levels <= 0:
            rows.append(" ")
        elif cell_levels >= 8:
            rows.append(BAR_CHARS[8])
        else:
            rows.append(BAR_CHARS[cell_levels])
    return rows  # top to bottom


def short_name(desc, max_len):
    if len(desc) <= max_len:
        return desc
    return desc[: max_len - 1] + "…"


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)

    sources = get_sources()
    if not sources:
        stdscr.addstr(0, 0, "No PulseAudio sources found.")
        stdscr.refresh()
        time.sleep(2)
        return

    workers = []
    for name, desc in sources:
        w = CavaWorker(name)
        w.start()
        workers.append((w, desc, name))

    try:
        while True:
            ch = stdscr.getch()
            if ch in (ord("q"), ord("Q"), 27):
                break

            stdscr.erase()
            max_y, max_x = stdscr.getmaxyx()
            n = len(workers)

            # auto grid: choose cols/rows close to square, biased to wider
            cols = max(1, int(n ** 0.5 + 0.5))
            rows = max(1, (n + cols - 1) // cols)

            cell_w = max_x // cols
            cell_h = max_y // rows

            for idx, (worker, desc, sname) in enumerate(workers):
                r = idx // cols
                c = idx % cols
                x0 = c * cell_w
                y0 = r * cell_h

                if cell_h < 3 or cell_w < 4:
                    continue

                # title line
                title = short_name(desc, cell_w - 1)
                try:
                    stdscr.addstr(y0, x0, title, curses.color_pair(1) | curses.A_BOLD)
                except curses.error:
                    pass

                bar_area_h = cell_h - 1
                if bar_area_h < 1:
                    continue

                vals = worker.get_values()
                n_bars = len(vals)
                avail_w = cell_w - 1
                bar_w = max(1, avail_w // n_bars)

                cols_rendered = [render_bar(v, bar_area_h) for v in vals]

                for row in range(bar_area_h):
                    line_chars = []
                    for v_idx, col_chars in enumerate(cols_rendered):
                        ch_char = col_chars[row]
                        line_chars.append(ch_char * bar_w)
                    line = "".join(line_chars)[:avail_w]
                    try:
                        stdscr.addstr(
                            y0 + 1 + row, x0, line, curses.color_pair(2)
                        )
                    except curses.error:
                        pass

            footer = "q: quit  |  sources auto-detected from pactl"
            try:
                stdscr.addstr(max_y - 1, 0, footer[: max_x - 1], curses.A_DIM)
            except curses.error:
                pass

            stdscr.refresh()
            time.sleep(1.0 / FRAMERATE)
    finally:
        for worker, _, _ in workers:
            worker.stop()


if __name__ == "__main__":
    if shutil.which("cava") is None:
        print("Error: 'cava' not found on PATH. Install it first.")
        sys.exit(1)
    if shutil.which("pactl") is None:
        print("Error: 'pactl' not found on PATH.")
        sys.exit(1)

    curses.wrapper(main)
