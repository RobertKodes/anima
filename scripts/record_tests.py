"""Every test is recorded as a video. This renderer turns pytest output into MP4 files."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1280, 720
FG = (244, 234, 220)
BG = (20, 15, 10)
AMBER = (232, 160, 74)
GREEN = (125, 186, 106)
RED = (212, 106, 106)
MUTED = (138, 122, 104)
FPS = 8
MAX_LINES = 22


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/Library/Fonts/SF-Mono-Regular.otf",
        "/System/Library/Fonts/Supplemental/Andale Mono.ttf",
    ):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def wrap(line: str, width: int = 108) -> list[str]:
    if len(line) <= width:
        return [line]
    parts = []
    rest = line
    while rest:
        parts.append(rest[:width])
        rest = rest[width:]
    return parts


def color_for(line: str) -> tuple[int, int, int]:
    if "PASSED" in line or "ok" == line.strip().lower():
        return GREEN
    if "FAILED" in line or "ERROR" in line:
        return RED
    if line.startswith("=") or line.startswith("TEST "):
        return AMBER
    return FG


def frames_for(title: str, lines: list[str]) -> list[Image.Image]:
    header = font(22)
    body = font(16)
    visible: list[str] = []
    images: list[Image.Image] = []
    intro = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(intro)
    draw.text((40, 30), "ANIMA  ·  test recording", fill=AMBER, font=header)
    draw.text((40, 70), title, fill=FG, font=body)
    images.extend([intro] * 6)
    for raw in lines:
        for piece in wrap(raw.rstrip()):
            visible.append(piece)
            visible = visible[-MAX_LINES:]
            frame = Image.new("RGB", (WIDTH, HEIGHT), BG)
            draw = ImageDraw.Draw(frame)
            draw.rectangle((0, 0, WIDTH, 56), fill=(30, 22, 16))
            draw.text((40, 16), title, fill=AMBER, font=header)
            y = 80
            for item in visible:
                draw.text((40, y), item, fill=color_for(item), font=body)
                y += 26
            images.append(frame)
    hold = images[-1] if images else intro
    images.extend([hold] * 10)
    return images


def encode_mp4(images: list[Image.Image], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for i, image in enumerate(images):
            image.save(tmp_path / f"f{i:05d}.png")
        cmd = [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(tmp_path / "f%05d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(dest),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_pytest(nodeid: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", nodeid, "-vv", "--tb=short", "-o", "addopts="],
        capture_output=True,
        text=True,
    )
    output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode, output


def catalog(recordings: Path) -> None:
    rows = sorted(recordings.glob("*.mp4"))
    lines = ["# Test recordings\n", "Every automated test is rendered to an MP4 after the run.\n"]
    for row in rows:
        lines.append(f"- `{row.name}` ({row.stat().st_size} bytes)")
    (recordings / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("recordings"))
    parser.add_argument("tests", nargs="*", default=["tests"])
    args = parser.parse_args()
    collect = subprocess.run(
        [sys.executable, "-m", "pytest", *args.tests, "--collect-only", "-q", "-o", "addopts="],
        capture_output=True,
        text=True,
        check=False,
    )
    nodeids = []
    for line in collect.stdout.splitlines():
        if line.startswith("tests/") and "::" in line:
            nodeids.append(line.strip())
    if not nodeids:
        print(collect.stdout)
        print(collect.stderr)
        print("No tests collected.")
        return 1
    failed = 0
    args.out.mkdir(parents=True, exist_ok=True)
    for nodeid in nodeids:
        print(f"recording {nodeid}")
        code, output = run_pytest(nodeid)
        title = "ANIMA TEST  " + nodeid
        images = frames_for(title, output.splitlines() or ["(no output)"])
        slug = nodeid.replace("/", "_").replace("::", "__").replace(".py", "")
        dest = args.out / f"{slug}.mp4"
        encode_mp4(images, dest)
        if code != 0:
            failed += 1
            print(f"  FAILED -> {dest}")
        else:
            print(f"  passed -> {dest}")
    catalog(args.out)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
