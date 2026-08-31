"""Cross-platform frame rendering and MP4 encoding for hackathon demos."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1920, 1080
FPS = 24
BG = (13, 11, 18)
FG = (244, 234, 220)
AMBER = (232, 160, 74)
MUTED = (138, 122, 104)
GREEN = (125, 186, 106)
PANEL = (30, 22, 16)

_FONT_DB = None


def ffmpeg_exe() -> str:
    import shutil

    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as exc:
        raise RuntimeError("ffmpeg not found; pip install imageio-ffmpeg or add ffmpeg to PATH") from exc


def ffprobe_exe() -> str:
    import shutil

    found = shutil.which("ffprobe")
    if found:
        return found
    ffmpeg = Path(ffmpeg_exe())
    probe = ffmpeg.with_name("ffprobe.exe" if ffmpeg.suffix else "ffprobe")
    if probe.is_file():
        return str(probe)
    raise RuntimeError("ffprobe not found")


def git_stamp(root: Path) -> str:
    try:
        short = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if short and "fatal" not in short:
            return short
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return "dev"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def font(size: int, *, mono: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates: list[str] = []
    if sys.platform == "win32":
        windir = Path(r"C:\Windows\Fonts")
        if mono:
            candidates += [
                str(windir / "CascadiaMono.ttf"),
                str(windir / "consola.ttf"),
                str(windir / "lucon.ttf"),
            ]
        else:
            candidates += [
                str(windir / "segoeui.ttf"),
                str(windir / "arial.ttf"),
            ]
    elif sys.platform == "darwin":
        if mono:
            candidates += [
                "/System/Library/Fonts/Menlo.ttc",
                "/System/Library/Fonts/SFNSMono.ttf",
            ]
        else:
            candidates += [
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ]
    else:
        if mono:
            candidates += [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            ]
        else:
            candidates += [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def svg_font_db():
    global _FONT_DB
    if _FONT_DB is None:
        import svg2png_py

        _FONT_DB = svg2png_py.FontDatabase.system()
    return _FONT_DB


def svg_to_png(svg_text: str, *, width: int | None = None, height: int | None = None) -> Image.Image:
    import re

    import svg2png_py

    db = svg_font_db()
    kwargs: dict = {"bg_color": (20, 15, 10, 255)}
    if width and height:
        kwargs["bg_size"] = (width, height)
    try:
        png_bytes = svg2png_py.svg_to_png(svg_text, db, **kwargs)
        from io import BytesIO

        return Image.open(BytesIO(png_bytes)).convert("RGB")
    except RuntimeError:
        return _svg_fallback_png(svg_text)


def _svg_fallback_png(svg_text: str) -> Image.Image:
    import html as html_mod
    import re

    text = re.sub(r"<[^>]+>", " ", html_mod.unescape(svg_text))
    lines = [line.strip() for line in text.splitlines() if line.strip()][-32:]
    img = Image.new("RGB", (1280, 720), BG)
    draw = ImageDraw.Draw(img)
    draw.text((24, 24), "ANIMA TUI (fallback frame)", fill=AMBER, font=font(22, mono=True))
    y = 64
    body = font(16, mono=True)
    for line in lines:
        draw.text((24, y), line[:110], fill=FG, font=body)
        y += 22
    return img


def letterbox(image: Image.Image, caption: str = "", stamp: str = "") -> Image.Image:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), BG)
    src = image.copy()
    src.thumbnail((WIDTH - 80, HEIGHT - 140), Image.Resampling.LANCZOS)
    x = (WIDTH - src.width) // 2
    y = 70 + (HEIGHT - 140 - src.height) // 2
    canvas.paste(src, (x, y))
    draw = ImageDraw.Draw(canvas)
    title_font = font(28)
    cap_font = font(20)
    stamp_font = font(18)
    draw.rectangle((0, 0, WIDTH, 56), fill=PANEL)
    draw.text((40, 14), "ANIMA", fill=AMBER, font=title_font)
    draw.text((160, 18), "Sibyl is the self  ·  graphical CLI & plain REPL", fill=MUTED, font=stamp_font)
    if stamp:
        draw.text((WIDTH - 40 - draw.textlength(stamp, font=stamp_font), 18), stamp, fill=AMBER, font=stamp_font)
    if caption:
        draw.rectangle((0, HEIGHT - 56, WIDTH, HEIGHT), fill=PANEL)
        draw.text((40, HEIGHT - 40), caption, fill=FG, font=cap_font)
    return canvas


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def title_card(
    title: str,
    body: str,
    *,
    stamp: str = "",
    subtitle: str = "Anima  ·  local-first being  ·  MIT",
) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    title_font = font(72)
    body_font = font(36)
    sub_font = font(24)
    stamp_font = font(22)
    if stamp:
        draw.text((48, 36), stamp, fill=AMBER, font=stamp_font)
    draw.text((48, 260), title, fill=AMBER, font=title_font)
    y = 380
    for line in wrap(draw, body, body_font, WIDTH - 96):
        draw.text((48, y), line, fill=FG, font=body_font)
        y += 52
    draw.text((48, HEIGHT - 96), subtitle, fill=MUTED, font=sub_font)
    return img


def hold(frames: list[Image.Image], image: Image.Image, seconds: float) -> None:
    count = max(1, int(seconds * FPS))
    frames.extend([image] * count)


def crossfade(frames: list[Image.Image], a: Image.Image, b: Image.Image, seconds: float = 0.35) -> None:
    steps = max(2, int(seconds * FPS))
    for i in range(steps):
        alpha = i / (steps - 1)
        blended = Image.blend(a, b, alpha)
        frames.append(blended)


def encode_mp4(frames: list[Image.Image], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="anima-vid-") as tmp:
        tmp_path = Path(tmp)
        for i, frame in enumerate(frames):
            frame.save(tmp_path / f"f{i:05d}.png")
        cmd = [
            ffmpeg_exe(),
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(tmp_path / "f%05d.png"),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(dest),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def probe_duration(path: Path) -> float:
    try:
        out = subprocess.check_output(
            [ffprobe_exe(), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
            text=True,
        ).strip()
        return float(out)
    except (RuntimeError, subprocess.CalledProcessError, ValueError):
        proc = subprocess.run(
            [ffmpeg_exe(), "-i", str(path)],
            capture_output=True,
            text=True,
        )
        import re

        match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", proc.stderr or "")
        if not match:
            return 0.0
        hours, minutes, seconds = match.groups()
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def concat_videos(parts: list[Path], dest: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="anima-concat-") as tmp:
        listing = Path(tmp) / "list.txt"
        listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
        subprocess.run(
            [
                ffmpeg_exe(),
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(listing),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(dest),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
