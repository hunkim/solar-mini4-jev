"""Unit tests for _heuristic_overrides structural guards (no API)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import _heuristic_overrides  # noqa: E402


class HeuristicOverrideTests(unittest.TestCase):
    def test_noul_absurd_action_on_mild_state(self):
        self.skipTest("patch2 not kept")

    def test_score_low_when_alternative_still_works(self):
        self.skipTest("patch1 not kept")

    def test_noul_time_window_safety_boost(self):
        state = (
            "Patrol reports slab fracture lines above the north bowl; "
            "35cm storm snow on weak layer; lifts open in 90 minutes."
        )
        questions = {
            "yes": {
                "type": "noul",
                "instructions": "Should avalanche control close the north bowl before opening?",
            }
        }
        answers = {"yes": {"type": "noul", "noul": 0.25}}
        _heuristic_overrides(state, questions, answers)
        self.assertGreaterEqual(answers["yes"]["noul"], 0.8)

        # Mild + time must NOT boost
        state2 = "Gift shop printer jam; next show in 40 minutes; dome systems nominal."
        questions2 = {
            "yes": {
                "type": "noul",
                "instructions": "Should staff evacuate the dome for a fire emergency now?",
            }
        }
        answers2 = {"yes": {"type": "noul", "noul": 0.2}}
        _heuristic_overrides(state2, questions2, answers2)
        self.assertLessEqual(answers2["yes"]["noul"], 0.35)


if __name__ == "__main__":
    unittest.main()
