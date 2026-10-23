"""Every outline in docs/PROMPTING.md must pass the gate and build with both builders."""
from __future__ import annotations

import contextlib
import io
import re
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_deck  # noqa: E402
import build_slides  # noqa: E402
import check_outline  # noqa: E402

GUIDE = ROOT / "docs" / "PROMPTING.md"


class PromptingGuideTests(unittest.TestCase):
    def blocks(self):
        return [yaml.safe_load(b) for b in re.findall(r"```yaml\n(.*?)```", GUIDE.read_text(), re.S)]

    def test_every_yaml_block_is_a_full_outline(self):
        blocks = self.blocks()
        self.assertGreaterEqual(len(blocks), 3)
        for b in blocks:
            self.assertIn("slides", b)

    def test_outlines_pass_gate_and_build(self):
        for n, outline in enumerate(self.blocks(), 1):
            with self.subTest(block=n):
                errors, _ = check_outline.check(outline, "both", f"block {n}")
                self.assertEqual(errors, [])
                with contextlib.redirect_stderr(io.StringIO()):
                    plan = build_slides.build_plan(outline, {})
                    self.assertTrue(plan["requests"])
                    with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
                        dest = Path(tmp) / "deck.pptx"
                        build_deck.build(outline, ROOT / "assets" / "template.pptx", dest)
                        prs = build_deck.Presentation(str(dest))
                    self.assertEqual(len(prs.slides), len(outline["slides"]))

    def test_prompt_layouts_exist(self):
        text = GUIDE.read_text()
        for name in re.findall(r"^\d+ ([a-z-]+)[: (]", text, re.M):
            self.assertIn(build_slides.LAYOUT_ALIASES.get(name, name).lower(), check_outline.KNOWN_LAYOUTS, name)

    def test_shipped_example_passes(self):
        outline = build_slides.load_outline(ROOT / "examples" / "outline.yaml")
        self.assertEqual(check_outline.check(outline, "both", "example")[0], [])


if __name__ == "__main__":
    unittest.main()
