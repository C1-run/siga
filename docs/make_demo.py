"""Render docs/demo.gif from live CLI output.

    python docs/make_demo.py            # needs Pillow and ffmpeg

Every frame is the real stdout of `siga audit` on the bundled synthetic CSV, so the
demo cannot drift from the output the release actually prints.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "demo.gif"
DEMO_ARGV = ["audit", "siga-audit/examples/trades_sample.csv", "--cost", "30", "--cluster-days"]
COMMAND = "$ siga " + " ".join(DEMO_ARGV)

WIDTH, HEIGHT = 1104, 480
BG = (13, 17, 23)
TITLEBAR = (22, 27, 34)
PRIMARY = (201, 209, 217)
MUTED = (139, 148, 158)
GREEN = (63, 185, 80)
RED = (248, 81, 73)
AMBER = (217, 130, 36)
MARGIN_X, MARGIN_TOP, LINE_H = 20, 58, 24
FPS = 20

_FONT_CANDIDATES = (
    "/System/Library/Fonts/SFNSMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
)


def capture_output() -> list[str]:
    proc = subprocess.run(
        [sys.executable, "-m", "siga_briefing.cli", *DEMO_ARGV],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(f"siga audit failed ({proc.returncode}):\n{proc.stderr}")
    return proc.stdout.rstrip("\n").splitlines()


def pick_font(size: int):
    from PIL import ImageFont

    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default(size)


def fit_font(lines: list[str]):
    """Largest monospace size at which the widest line still fits the canvas."""
    from PIL import Image, ImageDraw

    draw = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    for size in range(20, 9, -1):
        font = pick_font(size)
        if all(draw.textlength(line, font=font) <= WIDTH - 2 * MARGIN_X for line in lines):
            return font
    raise SystemExit("output lines are too wide for the canvas")


def color_for(line: str) -> tuple[int, int, int]:
    text = line.strip()
    if text.startswith("$"):
        return PRIMARY
    if text.startswith(("=", "note:")):
        return MUTED
    if text.startswith("OOS ("):
        return GREEN
    if text.startswith("VERDICT:"):
        return RED if text.endswith("FAIL") else GREEN
    if text.startswith("- "):
        return RED if "negative" in text else MUTED
    return PRIMARY


def draw_frame(draw, font, visible: list[str], cursor: str | None) -> None:
    for i, line in enumerate(visible):
        if not line.strip():
            continue
        draw.text((MARGIN_X, MARGIN_TOP + i * LINE_H), line, font=font, fill=color_for(line))
    if cursor is not None:
        x = MARGIN_X + draw.textlength(cursor, font=font)
        y = MARGIN_TOP
        draw.rectangle((x + 2, y, x + 12, y + LINE_H - 7), fill=PRIMARY)


def render_frame(visible: list[str], cursor: str | None, font):
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, WIDTH, 34), fill=TITLEBAR)
    for i, dot in enumerate((RED, AMBER, GREEN)):
        x = 22 + i * 26
        draw.ellipse((x, 12, x + 14, 26), fill=dot)
    title = "siga — audit"
    title_font = pick_font(16)
    draw.text(
        ((WIDTH - draw.textlength(title, font=title_font)) / 2, 9),
        title,
        font=title_font,
        fill=MUTED,
    )
    draw_frame(draw, font, visible, cursor)
    return img


def assemble(frames_dir: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise SystemExit("ffmpeg not found — needed to encode the gif")
    vf = (
        "split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]"
        "paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle"
    )
    subprocess.run(
        [
            ffmpeg, "-y", "-loglevel", "error",
            "-framerate", str(FPS), "-i", str(frames_dir / "frame_%03d.png"),
            "-vf", vf, "-loop", "0", str(OUT),
        ],
        check=True,
    )


def main() -> int:
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("Pillow not found — pip install pillow first")

    screen = [COMMAND, ""] + capture_output()
    font = fit_font(screen)

    # type the command, reveal the output line by line, then hold on the verdict
    frames: list[tuple[list[str], str | None]] = []
    for i in range(6, len(COMMAND) + 1, max(1, len(COMMAND) // 10)):
        frames.append(([COMMAND[:i]], COMMAND[:i]))
    frames.append(([COMMAND], None))
    for n in range(2, len(screen) + 1):
        frames.append((screen[:n], None))
    frames += [(screen, None)] * 8

    frames_dir = Path(tempfile.mkdtemp(prefix="siga-demo-"))
    try:
        for i, (visible, cursor) in enumerate(frames):
            render_frame(visible, cursor, font).save(frames_dir / f"frame_{i:03d}.png")
        assemble(frames_dir)
    finally:
        shutil.rmtree(frames_dir, ignore_errors=True)

    probe = Image.open(OUT)
    print(
        f"wrote {OUT} — {probe.size[0]}x{probe.size[1]}, "
        f"{probe.n_frames} frames, {OUT.stat().st_size / 1024:.0f} KiB"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
