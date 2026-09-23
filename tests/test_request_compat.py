"""Jev System One request-shape compatibility (validation + prompt formatting)."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compat import description_text, instructions_text  # noqa: E402
from engine import _prompt  # noqa: E402
from server import (  # noqa: E402
    ChoiceQuestion,
    NoulCriteria,
    NoulQuestion,
    ScoreQuestion,
    SystemOneRequest,
    app,
)


ATT = Path(
    "/home/box/agent-data/agents/3b48e1df-ec2b-4243-a465-626dc1ce9668/attachments"
)


class InstructionsTextTests(unittest.TestCase):
    def test_string(self):
        self.assertEqual(instructions_text("  hello  "), "hello")

    def test_list(self):
        self.assertEqual(instructions_text(["Is it urgent?", "Be careful."]), "Is it urgent? Be careful.")

    def test_object_question_key(self):
        self.assertEqual(
            instructions_text({"question": "Is the reviewer dissatisfied?"}),
            "Is the reviewer dissatisfied?",
        )

    def test_object_task_key(self):
        self.assertIn("Rate likelihood", instructions_text({"task": "Rate likelihood"}))

    def test_none(self):
        self.assertEqual(instructions_text(None), "")


class DescriptionTextTests(unittest.TestCase):
    def test_string(self):
        self.assertEqual(description_text("yes"), "yes")

    def test_object(self):
        self.assertEqual(
            description_text({"meaning": "assembles furniture"}),
            '{"meaning": "assembles furniture"}',
        )

    def test_array(self):
        self.assertEqual(description_text(["a", "b"]), '["a", "b"]')

    def test_null(self):
        self.assertEqual(description_text(None), "")


class NoulCriteriaSchemaTests(unittest.TestCase):
    def test_string_true_false(self):
        c = NoulCriteria.model_validate({"true": "yes", "false": "no"})
        self.assertEqual(c.true, "yes")
        self.assertEqual(c.false, "no")

    def test_nested_object_and_array(self):
        c = NoulCriteria.model_validate(
            {
                "true": {"meaning": "The steps assemble furniture"},
                "false": ["Something else"],
            }
        )
        self.assertIsInstance(c.true, dict)
        self.assertIsInstance(c.false, list)

    def test_arrays_of_strings(self):
        c = NoulCriteria.model_validate({"true": ["a"], "false": ["b"]})
        self.assertEqual(c.true, ["a"])

    def test_null_values(self):
        c = NoulCriteria.model_validate({"true": None, "false": None})
        self.assertIsNone(c.true)

    def test_omitted(self):
        c = NoulCriteria.model_validate({})
        self.assertIsNone(c.true)


class QuestionSchemaTests(unittest.TestCase):
    def test_noul_omit_criteria(self):
        q = NoulQuestion.model_validate({"type": "noul", "instructions": "Urgent?"})
        self.assertIsNone(q.criteria)

    def test_noul_criteria_must_be_object_not_string(self):
        with self.assertRaises(ValidationError):
            NoulQuestion.model_validate(
                {"type": "noul", "instructions": "Urgent?", "criteria": "just a string"}
            )

    def test_noul_instructions_flexible(self):
        for instr in ["s", ["a", "b"], {"question": "q?"}, None]:
            NoulQuestion.model_validate({"type": "noul", "instructions": instr})

    def test_choice_nested_descriptions(self):
        ChoiceQuestion.model_validate(
            {
                "type": "choice",
                "instructions": ["Classify sentiment."],
                "criteria": {
                    "negative": {"label": "Negative", "description": "Complaints"},
                    "neutral": ["Factual"],
                    "positive": "Praise",
                    "other": None,
                },
            }
        )

    def test_choice_requires_criteria(self):
        with self.assertRaises(ValidationError):
            ChoiceQuestion.model_validate({"type": "choice", "instructions": "x"})

    def test_score_nested_levels(self):
        ScoreQuestion.model_validate(
            {
                "type": "score",
                "instructions": {"task": "Rate"},
                "criteria": [
                    {"level": "Vague", "detail": "none"},
                    ["Uncertain", "maybe"],
                    "Fully specific",
                ],
            }
        )

    def test_score_requires_nonempty_criteria(self):
        with self.assertRaises(ValidationError):
            ScoreQuestion.model_validate({"type": "score", "criteria": []})


    def test_noul_criteria_array_rejected(self):
        with self.assertRaises(ValidationError):
            NoulQuestion.model_validate(
                {"type": "noul", "instructions": "Urgent?", "criteria": ["a"]}
            )

    def test_noul_criteria_number_rejected(self):
        with self.assertRaises(ValidationError):
            NoulQuestion.model_validate(
                {"type": "noul", "instructions": "Urgent?", "criteria": 123}
            )

    def test_noul_criteria_null_ok(self):
        q = NoulQuestion.model_validate(
            {"type": "noul", "instructions": "Urgent?", "criteria": None}
        )
        self.assertIsNone(q.criteria)

    def test_choice_criteria_rejects_non_flexible_scalar(self):
        # bool/number are not in TypeSafe description anyOf
        with self.assertRaises(ValidationError):
            ChoiceQuestion.model_validate(
                {"type": "choice", "instructions": "x", "criteria": {"a": 1}}
            )



class SystemOneRequestTests(unittest.TestCase):
    def test_attached_baking_payload(self):
        body = json.loads((ATT / "fd39966c4bea0c5dfc10c52fae05b45a81a190b520c3657b0e1c6b077127eabc.json").read_text())
        SystemOneRequest.model_validate(body)

    def test_attached_headphones_payload(self):
        body = json.loads((ATT / "a09e4eaec6ddc6e34bad3da4e7d168c5302885748e60d29596492bd82295687d.json").read_text())
        SystemOneRequest.model_validate(body)

    def test_attached_cafe_payload(self):
        body = json.loads((ATT / "9e3aa78188e55f0d55c03fe39d0d46a4a553ade28b767ad6d5b566c409053ee6.json").read_text())
        SystemOneRequest.model_validate(body)

    def test_noul_criteria_string_rejected(self):
        with self.assertRaises(ValidationError):
            SystemOneRequest.model_validate(
                {
                    "model": "solar-mini4-jev",
                    "state": "x",
                    "questions": {
                        "q": {"type": "noul", "instructions": "y", "criteria": "bad"}
                    },
                }
            )


class PromptCompatTests(unittest.TestCase):
    def test_prompt_accepts_list_and_object_instructions(self):
        text = _prompt(
            "The cafe opens at 7.",
            {
                "a": {"type": "noul", "instructions": ["Is this a cafe?"]},
                "b": {"type": "noul", "instructions": {"question": "Food business?"}},
            },
        )
        self.assertIn("Is this a cafe?", text)
        self.assertIn("Food business?", text)

    def test_prompt_accepts_nested_noul_criteria(self):
        text = _prompt(
            [{"step": 1}],
            {
                "is_furniture_assembly": {
                    "type": "noul",
                    "instructions": ["Assemble furniture?"],
                    "criteria": {
                        "true": {"meaning": "Assembles furniture"},
                        "false": ["Not furniture"],
                    },
                }
            },
        )
        self.assertIn("Assembles furniture", text)
        self.assertIn("Not furniture", text)

    def test_prompt_choice_score_nested(self):
        text = _prompt(
            {"review": "bad"},
            {
                "sentiment": {
                    "type": "choice",
                    "instructions": ["Classify"],
                    "criteria": {
                        "negative": {"label": "Negative", "description": "Complaints"}
                    },
                },
                "score": {
                    "type": "score",
                    "instructions": {"task": "Rate"},
                    "criteria": [["Very unlikely", "Never"], "Maybe"],
                },
            },
        )
        self.assertIn("Complaints", text)
        self.assertIn("Very unlikely", text)


class ApiValidationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_missing_key_401(self):
        r = self.client.post(
            "/v1/systemone",
            json={
                "state": "x",
                "questions": {"q": {"type": "noul", "instructions": "y"}},
            },
        )
        self.assertEqual(r.status_code, 401)

    def test_noul_criteria_string_422(self):
        r = self.client.post(
            "/v1/systemone",
            headers={"X-Upstage-Api-Key": "test-key"},
            json={
                "state": "x",
                "questions": {
                    "q": {"type": "noul", "instructions": "y", "criteria": "bad"}
                },
            },
        )
        self.assertEqual(r.status_code, 422)

    @patch("server.system_one")
    def test_nested_shapes_reach_engine_200(self, mock_s1):
        mock_s1.return_value = {
            "model": "solar-mini4-jev/solar-mini4",
            "answers": {"is_furniture_assembly": {"type": "noul", "noul": 0.01}},
            "usage": {"input_tokens": 1, "output_tokens": 1},
            "latency_s": 0.01,
        }
        body = json.loads(
            (ATT / "fd39966c4bea0c5dfc10c52fae05b45a81a190b520c3657b0e1c6b077127eabc.json").read_text()
        )
        # only noul question to keep mock simple
        body["questions"] = {"is_furniture_assembly": body["questions"]["is_furniture_assembly"]}
        r = self.client.post(
            "/v1/systemone",
            headers={"X-Upstage-Api-Key": "test-key"},
            json=body,
        )
        self.assertEqual(r.status_code, 200, r.text)
        mock_s1.assert_called_once()
        _state, questions = mock_s1.call_args.args[:2]
        crit = questions["is_furniture_assembly"]["criteria"]
        self.assertIsInstance(crit["true"], dict)
        self.assertIsInstance(crit["false"], list)

    @patch("server.system_one")
    def test_headphones_payload_200(self, mock_s1):
        mock_s1.return_value = {
            "model": "m",
            "answers": {},
            "usage": {},
            "latency_s": 0.01,
        }
        body = json.loads(
            (ATT / "a09e4eaec6ddc6e34bad3da4e7d168c5302885748e60d29596492bd82295687d.json").read_text()
        )
        mock_s1.return_value["answers"] = {
            k: {"type": q["type"], **({"noul": 0.9} if q["type"] == "noul" else {})}
            for k, q in body["questions"].items()
        }
        r = self.client.post(
            "/v1/systemone",
            headers={"Authorization": "Bearer test-key"},
            json=body,
        )
        self.assertEqual(r.status_code, 200, r.text)


if __name__ == "__main__":
    unittest.main()
