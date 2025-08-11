# matrix_rain.py
import os, sys, time, random, shutil, threading
from contextlib import contextmanager

try:
    # Nice Windows ANSI enablement + no-op elsewhere
    import colorama
    colorama.init()
except Exception:
    pass

# Katakana subset typical of the movie + ascii + digits
KATAKANA = list("ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ")
ASCII    = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
DIGITS   = list("0123456789")
GLYPHS   = KATAKANA + ASCII + DIGITS

# ANSI colors (green variants)
GREEN_DIM = "\x1b[38;5;22m"
GREEN     = "\x1b[38;5;46m"
GREEN_BRIGHT = "\x1b[92m"
RESET     = "\x1b[0m"

class MatrixRain:
    """
    Threaded Matrix-style 'digital rain' animation.
    - Bright head, dim tail
    - Random glyphs
    - Adapts to terminal width x height
    - Stops cleanly
    """
    def __init__(self, fps: int = 30, density: float = 0.25, min_tail=6, max_tail=22, enabled=True):
        self.fps = fps
        self.density = density
        self.min_tail = min_tail
        self.max_tail = max_tail
        self.enabled = enabled and self._isatty()
        self._stop = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._cols = []
        self._width = 0
        self._height = 0

    def _isatty(self):
        return sys.stdout.isatty() and os.environ.get("TERM", "") != "dumb"

    def _resize(self):
        size = shutil.get_terminal_size(fallback=(100, 28))
        self._width, self._height = size.columns, max(10, size.lines - 1)

        # Initialize column states: for each column, a list of y positions forming a streak
        self._cols = []
        for x in range(self._width):
            if random.random() < self.density:
                length = random.randint(self.min_tail, self.max_tail)
                start_y = random.randint(-self._height, 0)
                self._cols.append({"x": x, "y": start_y, "len": length})
            else:
                self._cols.append(None)

    def start(self):
        if not self.enabled:
            return
        self._resize()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        if not self.enabled:
            return
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        # Reset colors and move cursor to next line
        try:
            sys.stdout.write(RESET + "\n")
            sys.stdout.flush()
        except Exception:
            pass

    def _run(self):
        # Hide cursor
        sys.stdout.write("\x1b[?25l")
        sys.stdout.flush()
        try:
            last_size = shutil.get_terminal_size()
            frame_time = 1.0 / max(5, min(60, self.fps))
            while not self._stop.is_set():
                size = shutil.get_terminal_size(fallback=last_size)
                if size != last_size:
                    last_size = size
                    self._resize()

                # Draw frame
                buf = []
                # Clear with subtle fade (draw over everything)
                buf.append("\x1b[H")  # home cursor
                for row in range(self._height):
                    line_chars = []
                    for x in range(self._width):
                        streak = self._cols[x]
                        ch = " "
                        if streak:
                            head_y = streak["y"]
                            tail_len = streak["len"]
                            tail_start = head_y - tail_len
                            if tail_start <= row <= head_y:
                                # within tail
                                pos_in_tail = row - tail_start
                                # Head is bright, near-head green, tail dim
                                if row == head_y:
                                    color = GREEN_BRIGHT
                                elif pos_in_tail > tail_len * 0.8:
                                    color = GREEN
                                else:
                                    color = GREEN_DIM
                                ch = random.choice(GLYPHS)
                                line_chars.append(color + ch + RESET)
                                continue
                        line_chars.append(" ")
                    buf.append("".join(line_chars))

                # Advance streaks
                for x, streak in enumerate(self._cols):
                    if streak:
                        streak["y"] += 1
                        # recycle when off-screen
                        if streak["y"] - streak["len"] > self._height:
                            if random.random() < self.density:
                                # restart different length
                                self._cols[x] = {
                                    "x": x,
                                    "y": random.randint(-self._height // 2, 0),
                                    "len": random.randint(self.min_tail, self.max_tail),
                                }
                            else:
                                self._cols[x] = None
                    else:
                        # chance to start a new streak
                        if random.random() < self.density * 0.05:
                            self._cols[x] = {
                                "x": x,
                                "y": random.randint(-self._height // 2, 0),
                                "len": random.randint(self.min_tail, self.max_tail),
                            }

                sys.stdout.write("\n".join(buf))
                sys.stdout.flush()
                time.sleep(frame_time)
        except Exception:
            # Fail silently—never interrupt the work.
            pass
        finally:
            # Show cursor again
            try:
                sys.stdout.write("\x1b[?25h" + RESET)
                sys.stdout.flush()
            except Exception:
                pass

@contextmanager
def matrix_rain(enabled=True):
    rain = MatrixRain(enabled=enabled)
    try:
        rain.start()
        yield
    finally:
        rain.stop()
