from pathlib import Path

from support_router.config import load_company_config
from support_router.domain import EmailRequest
from support_router.questions import build_questions
from support_router.state import build_state


CONFIG = Path(__file__).parents[1] / "config" / "teams.json"


def test_team_config_maps_directly_to_choice_criteria_and_suitability_context():
    config = load_company_config(CONFIG)
    questions = build_questions(config)
    assert questions["winning_team"]["criteria"] == config.jev_choice_criteria
    assert questions["has_suitable_team"]["instructions"]["teams"] == config.jev_choice_criteria


def test_state_contains_only_ordinary_email_data():
    request = EmailRequest("msg-1", "a@example.com", "Subject", "Body")
    state = build_state(request)
    assert state == {
        "email": {
            "message_id": "msg-1",
            "from": "a@example.com",
            "subject": "Subject",
            "body_text": "Body",
        }
    }
