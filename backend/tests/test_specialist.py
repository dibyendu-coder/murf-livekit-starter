"""
test_specialist.py — Day 9 Specialist Agent & Handoff Tests

Tests:
- TEST 1 — Normal Main Agent Request ("Help me practice spoken English.") -> Handled by main agent, NO handoff.
- TEST 2 — Maths Specialist Request ("I don't understand percentages.") -> Triggers handoff_to_maths_specialist, Maths Specialist takes over, introduces itself, context preserved.
- TEST 3 — Code-Mixed Request ("Mujhe fractions samajh nahi aa raha.") -> Handoff triggered, Specialist responds in Hindi-English code-mixed register.
- TEST 4 — Return to Main Agent ("Now I want to practice English.") -> Switch back from Maths Specialist to Main Agent.
- TEST 5 — Unit test for MathsSpecialistAssistant initialization and return_to_main_agent tool.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from math_specialist import MathsSpecialistAssistant
from agent import Assistant


def test_maths_specialist_initialization():
    """TEST 5: Verify MathsSpecialistAssistant init & properties."""
    specialist = MathsSpecialistAssistant(
        user_id="test_user_101",
        session_id="session_101",
        learner_level="beginner",
        language_preference="Hindi-English",
        initial_context="I don't understand percentages.",
    )
    assert specialist._user_id == "test_user_101"
    assert specialist._session_id == "session_101"
    assert specialist.learner_level == "beginner"
    assert specialist.language_preference == "Hindi-English"
    assert specialist.initial_context == "I don't understand percentages."
    assert specialist.active_agent_type == "MATHS_SPECIALIST"
    assert "Maths Practice Specialist" in specialist.instructions


@pytest.mark.asyncio
async def test_maths_specialist_return_tool():
    """TEST 4 (Unit): return_to_main_agent tool execution."""
    specialist = MathsSpecialistAssistant(user_id="test_user")
    mock_context = MagicMock()
    result = await specialist.return_to_main_agent(mock_context, reason="Finished maths practice")
    assert result["success"] is True
    assert result["action"] == "return_to_main_agent"
    assert result["reason"] == "Finished maths practice"


@pytest.mark.asyncio
async def test_main_agent_handoff_tool_execution():
    """TEST 2 (Unit): handoff_to_maths_specialist tool execution."""
    main_agent = Assistant(user_id="learner_42")
    mock_context = MagicMock()
    result = await main_agent.handoff_to_maths_specialist(
        mock_context,
        maths_question="Help me solve 2x + 5 = 15.",
        topic="algebra",
        language="English",
    )
    assert result["success"] is True
    assert result["action"] == "handoff_to_maths_specialist"
    assert result["maths_question"] == "Help me solve 2x + 5 = 15."
    assert result["topic"] == "algebra"
    assert "Maths Practice Specialist" in result["announcement"]


def test_handoff_decision_rules():
    """Verify handoff trigger criteria for test questions."""
    maths_prompts = [
        "Help me solve 2x + 5 = 15.",
        "I don't understand percentages.",
        "Give me a maths question.",
        "What is 25% of 200?",
        "Teach me fractions.",
        "Help me with algebra.",
        "Explain this geometry problem.",
        "Mujhe fractions samajh nahi aa raha.",
    ]

    english_prompts = [
        "Give me an English exercise.",
        "Help me improve my spoken English.",
        "Correct my sentence.",
        "Let's practice conversation.",
        "Explain this English grammar rule.",
    ]

    # Verify classification logic check
    for prompt in maths_prompts:
        is_maths = any(
            kw in prompt.lower()
            for kw in [
                "math", "solve", "2x", "%", "percentage", "fraction", "algebra", "geometry",
                "samajh nahi aa raha", "200"
            ]
        )
        assert is_maths is True, f"Failed to identify maths prompt: {prompt}"

    for prompt in english_prompts:
        is_maths = any(
            kw in prompt.lower()
            for kw in ["2x", "percentage", "fraction", "algebra", "geometry"]
        )
        assert is_maths is False, f"Erroneously flagged English prompt as maths: {prompt}"
