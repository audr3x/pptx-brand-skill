import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from outline_rules import prepare  # noqa: E402


def warnings_for(slides):
    _, errors, warnings = prepare({"slides": slides}, "both")
    return errors, warnings


class OutlineRulesTest(unittest.TestCase):
    def test_body_and_bullets_together_warns(self):
        errors, warnings = warnings_for([{"layout": "content", "title": "T", "body": "Context", "bullets": ["A"]}])
        self.assertEqual(errors, [])
        self.assertTrue(any("both bullets and body" in w for w in warnings))

    def test_items_and_right_together_warns(self):
        errors, warnings = warnings_for(
            [{"layout": "two-column", "title": "T", "items": [{"title": "A"}], "right": [{"title": "B"}]}]
        )
        self.assertTrue(any("both items and right" in w for w in warnings))

    def test_todo_left_in_warns(self):
        _, warnings = warnings_for([{"layout": "content", "title": "Next steps", "bullets": ["TODO owner"]}])
        self.assertTrue(any("TODO" in w for w in warnings))

    def test_bool_is_an_error_not_a_crash(self):
        errors, _ = warnings_for([{"layout": "content", "title": True}])
        self.assertTrue(errors)

    def test_unknown_field_is_an_error(self):
        errors, _ = warnings_for([{"layout": "content", "title": "T", "colour": "red"}])
        self.assertTrue(any("colour" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
