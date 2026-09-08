"""Export a pilot as plain files for emilesilvis.com's apps/ directory."""
from __future__ import annotations

import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
ASSETS = ("styles.css", "theme.js", "app.js", "answer.js", "progress.js", "leaderboard.js")


def page_name(day: int) -> str:
    return "index.html" if day == 1 else f"day-{day:02d}.html"


def puzzle_link(day: int, label: str, *, rel: str = "", current: bool = False) -> str:
    # Only Puzzle 1 is available before JavaScript restores completion.
    attributes = f'href="{page_name(day)}"' if day == 1 else 'role="link" aria-disabled="true"'
    attributes += f' data-puzzle-day="{day}" data-href="{page_name(day)}"'
    if rel:
        attributes += f' rel="{rel}"'
    if current:
        attributes += ' aria-current="page"'
    return f'<a {attributes}>{escape(label)}</a>'


def edition_identity(manifest: dict) -> str:
    # Labels are annotations, not changes to a puzzle. Ignore them in the
    # existing content hash to preserve saved answers for already published weeks.
    content = json.loads(json.dumps(manifest))
    for puzzle in content["sessions"]:
        for item in (puzzle, puzzle.get("warmup")):
            if item:
                item.get("difficulty", {}).pop("label", None)
    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def puzzle_identity(puzzle: dict) -> str:
    """A solve survives appended days and editorial changes to the same question."""
    content = {key: puzzle.get(key) for key in ("recipe", "seed", "question", "target_kind", "unit")}
    content["answer"] = puzzle["answer"].get("exact", puzzle["answer"]["float"])
    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def previous_editions(manifest: dict) -> list[dict]:
    """Only an identical published prefix can recover that edition's browser progress."""
    if manifest.get("version") != "three-week-ladder-v1":
        return []
    editions = []
    for version, total in (("first-week-v1", 7), ("two-week-ladder-v1", 14)):
        if len(manifest["sessions"]) > total:
            previous = {**manifest, "version": version, "sessions": manifest["sessions"][:total]}
            editions.append({"edition": edition_identity(previous), "total": total})
    return editions


def build(edition: Path, output: Path, api_url: str = "") -> Path:
    edition, output = edition.resolve(), output.resolve()
    api_url = api_url.rstrip("/")
    if api_url:
        api = urlsplit(api_url)
        local = api.hostname in {"localhost", "127.0.0.1", "::1"}
        if not api.hostname or api.username or api.password or api.query or api.fragment or api.path or (api.scheme != "https" and not (api.scheme == "http" and local)):
            raise ValueError("The API URL must be an HTTPS origin (or HTTP localhost for development).")
    if ROOT.is_relative_to(output) or edition.is_relative_to(output):
        raise ValueError("The output must not contain the reader source or edition.")
    if output.exists() and any(output.iterdir()) and not (output / ".geomake-build").is_file():
        raise ValueError("Choose an empty output folder; this one is not a generated reader.")
    manifest = json.loads(edition.read_text(encoding="utf-8"))
    puzzles = manifest["sessions"]
    if not puzzles or [p["day"] for p in puzzles] != list(range(1, len(puzzles) + 1)):
        raise ValueError("An edition must have consecutive days starting at 1.")
    for puzzle in puzzles:
        if puzzle.get("difficulty", {}).get("label") not in {"Easy", "Medium", "Hard"}:
            raise ValueError("Each puzzle needs an estimated difficulty label; export it with the current generator.")
    edition_id = edition_identity(manifest)
    asset_id = hashlib.sha256(b"".join((ROOT / name).read_bytes() for name in ASSETS)).hexdigest()[:12]
    template = (ROOT / "template.html").read_text(encoding="utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="geomake-build-", dir=output.parent) as temporary:
        staged = Path(temporary) / "site"
        staged.mkdir()
        (staged / "images").mkdir()
        for name in ASSETS:
            content = (ROOT / name).read_text(encoding="utf-8")
            if name == "app.js":
                for module in ("answer.js", "progress.js", "leaderboard.js"):
                    content = content.replace(f"'./{module}'", f"'./{module}?v={asset_id}'")
            (staged / name).write_text(content, encoding="utf-8")
        for puzzle in puzzles:
            day = puzzle["day"]
            image = (edition.parent / puzzle["image"]).resolve()
            if not image.is_relative_to(edition.parent):
                raise ValueError("Puzzle images must be inside the edition folder.")
            image_path = f"images/day-{day:02d}{image.suffix}"
            shutil.copyfile(image, staged / image_path)
            help_path = f"data/{edition_id}/day-{day:02d}"
            help_dir = staged / help_path
            help_dir.mkdir(parents=True)
            payloads = {
                **{f"hint-{level}": hint for level, hint in enumerate(puzzle["hints"], 1)},
            }
            if not api_url:
                payloads["check"] = puzzle["answer"]["float"]
            for name, value in payloads.items():
                (help_dir / f"{name}.json").write_text(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
            unit = puzzle["unit"]
            if puzzle["target_kind"] == "area":
                unit += "²"
            fields = {key: escape(str(value), quote=True) for key, value in {
                "day": day, "total": len(puzzles), "edition": edition_id, "assets": asset_id,
                "question": puzzle["question"], "image": image_path,
                "alt": puzzle["question"], "help": help_path,
                "unit": unit, "hint_count": len(puzzle["hints"]),
                "difficulty": puzzle["difficulty"]["label"],
                "api": api_url, "previous_editions": json.dumps(previous_editions(manifest)),
            }.items()}
            fields["previous"] = puzzle_link(day - 1, "← Previous", rel="prev") if day > 1 else '<span></span>'
            fields["next"] = puzzle_link(day + 1, "Next →", rel="next") if day < len(puzzles) else '<span></span>'
            fields["puzzle_hidden"] = ' hidden' if day > 1 or api_url else ''
            fields["lock_hidden"] = ' hidden' if day == 1 or api_url else ''
            fields["leaderboard_hidden"] = '' if api_url else ' hidden'
            fields["progress"] = f"Enter the correct answer to unlock Puzzle {day + 1}." if day < len(puzzles) else "Solve this puzzle to complete the set."
            fields["archive"] = "".join(
                '<li>' + puzzle_link(item["day"], f'Puzzle {item["day"]}', current=item["day"] == day)
                + f' <span class="archive-difficulty">· {escape(item["difficulty"]["label"])} (estimated)</span>'
                + f'<span class="puzzle-state" data-state-day="{item["day"]}">{" · Locked" if item["day"] > 1 else ""}</span></li>'
                for item in puzzles
            )
            html = re.sub(r"\{\{(\w+)\}\}", lambda match: fields[match[1]], template)
            (staged / page_name(day)).write_text(html, encoding="utf-8")
        (staged / ".geomake-build").write_text(edition_id + "\n", encoding="utf-8")
        if output.exists():
            shutil.rmtree(output)
        staged.rename(output)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edition", type=Path, default=ROOT.parent / "out/daily-pilot/editor.json")
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    parser.add_argument("--api-url", default="", help="Cloudflare Worker origin; omit for the standalone reader")
    args = parser.parse_args()
    print(build(args.edition, args.out, args.api_url))
