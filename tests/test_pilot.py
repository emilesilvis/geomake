"""A usable, stable edition, with progressive disclosure and no overwritten notes."""

import json
import math
import re

import pytest

from geomake import pilot


@pytest.fixture(scope="module")
def edition(tmp_path_factory):
    out = tmp_path_factory.mktemp("edition")
    manifest = pilot.generate_pilot(7, str(out))
    return out, manifest


def test_edition_is_complete_and_the_deliberate_pair_has_the_same_size(edition):
    out, manifest = edition
    assert len(manifest["sessions"]) == 14
    assert json.loads((out / "editor.json").read_text()) == manifest
    sessions = manifest["sessions"]
    assert sessions[1]["params"]["a"] == sessions[2]["params"]["a"]
    assert sessions[1]["answer"]["exact"] == sessions[2]["answer"]["exact"]
    assert "14 days of geometry" in (out / "START_HERE.md").read_text()
    assert "| 14 |" in (out / "FEEDBACK.md").read_text()
    for day in range(1, 15):
        slug = f"day-{day:02d}"
        question = (out / f"{slug}.md").read_text()
        record = sessions[day - 1]
        assert record["question"] in question
        assert f'Estimated difficulty: {record["difficulty"]["label"]}' in question
        if record["warmup"]:
            warmup = (out / "warmups" / f"{slug}.md").read_text()
            assert f'Estimated difficulty: {record["warmup"]["difficulty"]["label"]}' in warmup
        assert record["answer"]["display"] not in question
        assert record["insight"] not in question
        assert record["hints"][0] not in question
        for level, hint in enumerate(record["hints"], 1):
            text = (out / "hints" / f"{slug}-{level}.md").read_text()
            assert hint in text
            for later in record["hints"][level:]:
                assert later not in text


def test_every_puzzle_help_and_navigation_link_resolves(edition):
    out, _ = edition
    for page in out.rglob("*.md"):
        for target in re.findall(r"\]\(([^)]+)\)", page.read_text()):
            assert (page.parent / target).is_file(), f"broken link in {page}: {target}"


def test_edition_can_be_reconstructed_from_its_recorded_seeds(edition):
    _, manifest = edition
    for record in manifest["sessions"]:
        for item in (record, record["warmup"]):
            if item:
                rebuilt = pilot.build(item["recipe"], item["seed"]).to_record()
                assert rebuilt["params"] == item["params"]
                assert rebuilt["answer"] == item["answer"]
                assert rebuilt["question"] == item["question"]


@pytest.mark.parametrize("seed", [0, 7, 42])
def test_continuation_climbs_from_day_seven_and_references_earlier_ideas(seed):
    from geomake.ladder import score

    puzzles = [pilot.build(s.recipe, seed) for s in pilot.SESSIONS]
    assert len({p.recipe for p in puzzles}) == 14
    scores = [score(p) for p in puzzles[6:]]
    assert all(a < b for a, b in zip(scores, scores[1:]))
    for day, session in enumerate(pilot.SESSIONS[7:], 8):
        assert session.builds_on
        assert all(1 <= prior < day for prior in session.builds_on)


def test_original_seed_seven_puzzles_keep_their_published_seeds_and_answers(edition):
    _, manifest = edition
    original = [
        (3534216998, 40), (2009308712, 16 - 4 * math.pi),
        (2009308712, 16 - 4 * math.pi),
        (1787171501, -98 + 49 * math.pi),
        (4134286627, -100 + 50 * math.pi),
        (2176975175, 49 * math.pi), (1322470501, 25),
    ]
    for record, (seed, answer) in zip(manifest["sessions"][:7], original):
        assert record["seed"] == seed
        assert record["answer"]["float"] == pytest.approx(answer)


def test_refuses_to_overwrite_a_players_notes(edition):
    out, _ = edition
    feedback = out / "FEEDBACK.md"
    feedback.write_text("Dad: the leaf clicked after hint 1.\n")
    with pytest.raises(ValueError, match="not empty"):
        pilot.generate_pilot(8, str(out))
    assert feedback.read_text() == "Dad: the leaf clicked after hint 1.\n"


def test_failed_verification_does_not_export_an_edition(tmp_path, monkeypatch):
    from geomake.verify import VerifyResult

    monkeypatch.setattr(pilot, "verify", lambda *a, **kw: VerifyResult(False, [("area", False, "bad")]))
    out = tmp_path / "failed-edition"
    with pytest.raises(RuntimeError, match="verification failed"):
        pilot.generate_pilot(7, str(out))
    assert not out.exists()
