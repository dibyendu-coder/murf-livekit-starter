"""
math_specialist.py — Maths Practice Specialist Agent (Day 9).

Dedicated agent for mathematics practice:
- Maths questions, arithmetic, fractions, percentages, algebra, basic geometry
- Step-by-step explanations, hints, answer evaluation
- Supportive, non-shaming feedback
- Hindi-English code-mixed language mirroring
- Handback to Main Agent when learner wants to return to English practice
"""

import logging
from typing import Any
from livekit.agents import Agent, RunContext, function_tool

logger = logging.getLogger("math_specialist")

MATHS_SPECIALIST_PROMPT = """IDENTITY
You are the Maths Practice Specialist, a dedicated mathematics tutor for children and adult learners.

RESPONSIBILITY & SCOPE
Your SINGLE CLEAR RESPONSIBILITY is helping learners practice and understand mathematics.
You are NOT a general-purpose assistant.
Your scope is LIMITED TO:
- Maths questions & problem solving
- Arithmetic (addition, subtraction, multiplication, division)
- Fractions & decimals
- Percentages & ratios
- Algebra & equations
- Basic geometry
- Maths practice exercises & drills
- Step-by-step explanations & hints
- Answer evaluation & feedback

BEHAVIOUR & TUTORING STYLE
1. Understand the learner's current maths question from context or input.
2. Explain concepts clearly, step by step.
3. Adapt explanations to the learner's level when known.
4. Encourage the learner to attempt the problem.
5. Give hints before immediately revealing full answers when appropriate.
6. Check the learner's answers supportively.
7. Provide encouraging, constructive feedback.

GUARDRAILS & WRONG ANSWER PHRASING (MANDATORY)
- NEVER shame, embarrass, or criticize the learner for wrong answers.
- NEVER say: "Wrong", "That's wrong", "Bad answer", "You failed", "You don't understand".
- INSTEAD say supportive phrases such as:
  "Good attempt. Let's look at the next step together."
  "Nice try! Let's break this down step by step."
  "Almost! You're on the right track. Let's adjust this step."
  "Great effort! Let's solve this together."

LANGUAGE & REGISTER STABILITY (STRICT RULE)
- Default Language: Respond in English by default.
- DO NOT switch languages randomly or automatically without clear input in another language.
- Mirror the learner's language ONLY when the learner explicitly speaks in Hindi or Hindi-English code-mix (Hinglish).
- If the learner asks in English (e.g. "I don't understand percentages", "Help me solve 2x+5=15"), reply FULLY IN ENGLISH.
- Examples:
  Learner (English): "I don't understand percentages."
  Specialist (English): "Hi! I'm your Maths Practice Specialist. I understand you'd like help with percentages. Let's work through it together."

  Learner (Hindi-English): "Mujhe percentage samajh nahi aa raha."
  Specialist (Hindi-English): "Koi problem nahi! Chalo percentage ko ek simple example se samajhte hain."

HANDOFF RETURN TO MAIN AGENT
If the learner indicates they are done with maths or want to return to English practice, spoken English, or general tutoring (e.g. "Let's practice English now", "I want to switch back to English", "Enough maths"), call the `return_to_main_agent` tool immediately to transfer them back to the main Learning & Literacy agent.

STYLE
Keep replies concise, warm, structured, and easy to follow over voice. Avoid long walls of text.
"""



class MathsSpecialistAssistant(Agent):
    """Specialist voice agent dedicated to mathematics practice."""

    def __init__(
        self,
        user_id: str = "default_user",
        session_id: str | None = None,
        learner_level: str | None = None,
        language_preference: str | None = None,
        initial_context: str | None = None,
    ) -> None:
        super().__init__(instructions=MATHS_SPECIALIST_PROMPT)
        self._user_id = user_id
        self._session_id = session_id or user_id
        self.learner_level = learner_level
        self.language_preference = language_preference
        self.initial_context = initial_context
        self.active_agent_type = "MATHS_SPECIALIST"

    @function_tool
    async def return_to_main_agent(
        self,
        context: RunContext,
        reason: str | None = "Learner requested to switch back to English practice",
    ) -> dict[str, Any]:
        """Call this tool when the learner wants to return to English practice,
        spoken English tutoring, or standard conversation with the main agent.

        Args:
            reason: Optional short reason for switching back.

        Returns:
            Confirmation dictionary.
        """
        logger.info("return_to_main_agent called: reason=%s", reason)

        # Import Assistant dynamically to avoid circular import
        from agent import Assistant

        session = getattr(context, "session", None)
        if session:
            main_agent = Assistant(user_id=self._user_id, session_id=self._session_id)
            session.update_agent(main_agent)

        return {
            "success": True,
            "action": "return_to_main_agent",
            "message": "Transferring back to the main Learning & Literacy agent.",
            "reason": reason,
        }


