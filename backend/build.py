"""Export the current answer catalog for the Worker, outside the public reader."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("reader_build", ROOT.parent / "reader/build.py")
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def build(edition: Path, output: Path):
    manifest = json.loads(edition.read_text(encoding="utf-8"))
    puzzles = manifest["sessions"]
    if not puzzles or [p["day"] for p in puzzles] != list(range(1, len(puzzles)+1)):
        raise ValueError("An edition must have consecutive days starting at 1.")
    catalog = {
        "edition": reader.edition_identity(manifest),
        "puzzles": [{
            "id": reader.puzzle_identity(puzzle),
            "answer": puzzle["answer"].get("degrees", puzzle["answer"]["float"]),
        } for puzzle in puzzles],
    }
    content = json.dumps(catalog, indent=2, allow_nan=False) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edition", type=Path, default=ROOT.parent / "out/daily-pilot/editor.json")
    parser.add_argument("--out", type=Path, default=ROOT / ".generated/puzzles.json")
    args = parser.parse_args()
    print(build(args.edition, args.out))
