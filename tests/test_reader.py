"""The static reader can be hosted in a subdirectory without exposing solutions in questions."""
import importlib.util
import json
from pathlib import Path
import re

import pytest

READER = Path(__file__).resolve().parents[1] / "reader"
spec = importlib.util.spec_from_file_location("reader_build", READER / "build.py")
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


@pytest.fixture
def edition(tmp_path):
    source = tmp_path / "edition"
    source.mkdir()
    (source / "diagram.png").write_bytes(b"diagram")
    records = [{
        "day": day, "question": 'A < B & "C". Find the area.', "image": "diagram.png",
        "unit": "cm", "target_kind": "area", "answer": {"float": 40, "display": "40 cm²"},
        "difficulty": {"depth": (day - 1) % 3 + 1, "label": ("Easy", "Medium", "Hard")[(day - 1) % 3]},
        "solution_steps": ["The secret derivation."], "hints": ["First nudge.", "Second nudge.", "Final nudge."],
    } for day in range(1, 15)]
    manifest = source / "editor.json"
    manifest.write_text(json.dumps({"sessions": records}))
    return manifest


def test_static_pages_escape_text_and_keep_help_in_separate_files(edition, tmp_path):
    output = reader.build(edition, tmp_path / "site")
    for day in range(1, 15):
        html = (output / reader.page_name(day)).read_text()
        assert "A &lt; B &amp; &quot;C&quot;" in html
        assert "40 cm²" not in html
        assert "secret derivation" not in html
        assert "First nudge" not in html
        assert 'href="/static/css/style.css"' in html
        assert "{{" not in html
        label = ("Easy", "Medium", "Hard")[(day - 1) % 3]
        assert f'Estimated difficulty: {label}</p>' in html
        for archive_label in ("Easy", "Medium", "Hard"):
            assert f'· {archive_label} (estimated)</span>' in html
        for url in re.findall(r'(?:href|src)="([^"]+)"', html):
            if not url.startswith("/"):
                assert (output / url.split("?")[0]).is_file(), url
        help_path = re.search(r'data-help="([^"]+)"', html)[1]
        assert json.loads((output / help_path / "check.json").read_text()) == 40
        assert json.loads((output / help_path / "hint-1.json").read_text()) == "First nudge."
        assert html.count('class="archive-difficulty"') == 14
        assert ('rel="prev"' in html) == (day > 1)
        assert ('rel="next"' in html) == (day < 14)
        if day < 14:
            assert f'href="{reader.page_name(day + 1)}" rel="next"' in html
    assert not (output / "host-style.css").exists()
    assert not (output / "editor.json").exists()


def test_rebuilds_are_stable_and_changed_content_has_new_identity(edition, tmp_path):
    output = reader.build(edition, tmp_path / "site")
    original = (output / "index.html").read_bytes()
    reader.build(edition, output)
    assert (output / "index.html").read_bytes() == original
    identity = (output / ".geomake-build").read_text()
    manifest = json.loads(edition.read_text())
    manifest["sessions"][0]["question"] += " A new given."
    edition.write_text(json.dumps(manifest))
    reader.build(edition, output)
    assert (output / ".geomake-build").read_text() != identity


def test_failed_build_preserves_previous_output_and_unrelated_files(edition, tmp_path):
    output = reader.build(edition, tmp_path / "site")
    original = (output / "index.html").read_bytes()
    (edition.parent / "diagram.png").unlink()
    with pytest.raises(FileNotFoundError):
        reader.build(edition, output)
    assert (output / "index.html").read_bytes() == original
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "mine.txt").write_text("Keep this.")
    with pytest.raises(ValueError, match="empty output"):
        reader.build(edition, notes)
    assert (notes / "mine.txt").read_text() == "Keep this."


def test_adding_labels_keeps_the_identity_used_for_existing_saved_answers(edition):
    import hashlib

    manifest = json.loads(edition.read_text())
    manifest["sessions"][0]["warmup"] = {"difficulty": {"depth": 1, "label": "Easy"}}
    identity = reader.edition_identity(manifest)
    for puzzle in manifest["sessions"]:
        puzzle["difficulty"].pop("label")
        if puzzle.get("warmup"):
            puzzle["warmup"]["difficulty"].pop("label")
    original_hash = hashlib.sha256(json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    assert identity == original_hash == reader.edition_identity(manifest)
