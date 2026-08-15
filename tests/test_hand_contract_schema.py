import json
from pathlib import Path


SCHEMA = Path(__file__).parents[1] / "docs" / "hand_observation_contract.json"


def test_hand_observation_schema_is_valid_json_and_has_evidence_boundary():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    assert schema["$schema"].startswith("https://json-schema.org/")
    assert schema["title"] == "Human Pathology Platform Hand Observation Run"
    assert "evidence_contract" in schema["required"]
    evidence = schema["properties"]["evidence_contract"]["properties"]
    assert evidence["medical_conclusions"]["maxItems"] == 0
    assert schema["properties"]["source"]["const"] == "own_cohort"
