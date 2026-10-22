import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_outline import check  # noqa: E402
from outline_rules import prepare  # noqa: E402
from provenance import unsourced_dates, unsourced_figures, unsourced_names  # noqa: E402
from readback import readback  # noqa: E402


def build(outline: dict, tmp: Path) -> tuple[Path, Path]:
    src = tmp / "outline.yaml"
    src.write_text(yaml.safe_dump(outline, sort_keys=False))
    deck = tmp / "deck.pptx"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_deck.py"), str(src), "-o", str(deck)],
                   check=True, capture_output=True)
    return src, deck


class ColonBulletTest(unittest.TestCase):
    def test_unquoted_colon_bullet_is_kept_as_text(self):
        outline = yaml.safe_load("slides:\n- layout: content\n  title: Risks\n  bullets:\n  - Risk: Brazil on old ERP\n")
        outline, errors, warnings = prepare(outline, "pptx")
        self.assertEqual(errors, [])
        self.assertEqual(outline["slides"][0]["bullets"], ["Risk: Brazil on old ERP"])
        self.assertTrue(any("unquoted colon" in w for w in warnings))


class ReadbackTest(unittest.TestCase):
    def test_complete_deck_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, deck = build({"slides": [{"layout": "cover", "title": "Plan", "date": "May 2027"},
                                          {"layout": "content", "title": "Goals", "bullets": ["One", "Two"]}]}, Path(tmp))
            missing, _, checked = readback(src, deck)
        self.assertEqual(missing, [])
        self.assertEqual(checked, 5)

    def test_bullets_past_the_limit_are_reported(self):
        bullets = [f"Point {n}" for n in range(1, 9)]
        with tempfile.TemporaryDirectory() as tmp:
            src, deck = build({"slides": [{"layout": "content", "title": "Too many", "bullets": bullets}]}, Path(tmp))
            missing, _, _ = readback(src, deck)
        self.assertEqual(len(missing), 2)
        self.assertIn("Point 8", missing[-1])

    def test_cli_exits_1_on_drops(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, deck = build({"slides": [{"layout": "content", "title": "T", "bullets": [str(n) for n in range(8)]}]}, Path(tmp))
            rc = subprocess.run([sys.executable, str(ROOT / "scripts" / "readback.py"), str(src), str(deck)],
                                capture_output=True).returncode
        self.assertEqual(rc, 1)


class ChunkTest(unittest.TestCase):
    def test_rebuild_with_fewer_chunks_removes_stale_ones(self):
        import build_slides as bs

        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "fills.json"
            bs.write_request_chunks(dest, [{"n": i} for i in range(90)], size=40, meta={})
            bs.write_request_chunks(dest, [{"n": i} for i in range(30)], size=40, meta={})
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ["fills-01.json", "fills.json"])


class ProvenanceTest(unittest.TestCase):
    def test_invented_month_year_is_flagged(self):
        self.assertEqual(unsourced_dates("Kickoff October 2026", "Kickoff next quarter"), ["October 2026"])

    def test_date_parts_from_the_source_pass(self):
        self.assertEqual(unsourced_dates("Go-live March 2027", "go-live is March 3, 2027"), [])
        self.assertEqual(unsourced_dates("Status for Q3 FY27", "Q3 FY27 status"), [])

    def test_words_that_look_like_months_are_not_dates(self):
        self.assertEqual(unsourced_dates("Dates may slip. Marketing and Decision log", ""), [])

    def test_quarter_not_in_source_is_flagged(self):
        self.assertEqual(unsourced_dates("Q4 plan", "plan for next quarter"), ["Q4"])

    def test_figures(self):
        self.assertEqual(unsourced_figures("Budget $380k, down -12%, 2026", "budget 380k, 12% lower"), [])
        self.assertEqual(unsourced_figures("Saves 40% of time", "saves time"), [40.0])

    def test_names(self):
        self.assertEqual(unsourced_names(["Owner is Priya", "Status: Green"], "priya owns it"), [])
        self.assertEqual(unsourced_names(["Owner is Marcus"], "owner TBD"), ["Marcus"])

    def test_check_outline_prompt_warning(self):
        outline = {"slides": [{"layout": "cover", "title": "Payroll", "date": "November 2026"}]}
        errors, warnings = check(outline, "pptx", "o", source="Payroll kickoff deck, no date yet")
        self.assertEqual(errors, [])
        self.assertTrue(any("November 2026" in w and "TODO" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()
