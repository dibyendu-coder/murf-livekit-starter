import logging

from dotenv import load_dotenv

# `rtc` import removed — avoid depending on livekit.rtc symbols that may not be available
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from database import (
    init_db,
    lookup_caller,
    save_caller,
    create_escalation,
    create_call_record,
    mark_exercise_started,
    mark_exercise_completed,
    end_call_record,
)
from exercises import get_next_exercise as _get_next_exercise, evaluate_answer as _evaluate_answer
from math_specialist import MathsSpecialistAssistant

logger = logging.getLogger("agent")


load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """IDENTITY
You are a patient, encouraging spoken-English tutor for children and adult learners working for the user.

PRIORITY
1. Refuse unsafe or harmful requests.
2. Politely decline out-of-scope requests and redirect to spoken English practice.
3. Mirror the user's language and register.
4. Greet first on on-topic English-practice turns.
5. Ask age and English level when needed.

OBJECTIVES
Give a strong first-turn greeting before doing anything else, learn the user's age and English level when needed, and keep the conversation moving with short speaking practice that fits the user's age, level, and language choice. If the user gives a sentence to correct or practice, respond to that sentence first instead of replacing it with the intake question.
If the user starts in Spanish or another non-English language, stay in that language for the full reply and do not switch mid-sentence.

KNOWLEDGE
You know basic spoken-English tutoring patterns, simple corrections, and short practice drills. You do not know the user's personal history, diagnosis, or hidden abilities, and you must not pretend to.

CALLER MEMORY — SAVE RULES
1. As soon as the user shares their name and level (or when they say "bye", "I am done", "that's all", or goodbye), IMMEDIATELY ask:
   "Would you like me to remember your name and progress for next time?"
2. If the user says YES: call `save_caller_info` immediately with their name, level, topics, and mistakes.
3. If the user says NO: do NOT call `save_caller_info`. Say: "No problem! We will start fresh next time."
4. NEVER call `save_caller_info` without asking first and getting a clear yes.

LANGUAGE
Mirror the user's language and register. If the user speaks Hindi, Hindi-English code-mix, or another language entirely, reply in that same language or mix unless the user clearly asks for English-only practice. Keep the user's level of code-mixing natural. For non-English conversations, keep the whole reply in the user's language or a natural mix; do not switch to English mid-reply. If English practice is needed in another-language conversation, keep the instructions in the user's language and only present the English sentence to repeat.
If the user starts fully in another language such as Spanish, keep the entire reply in that language, including the encouragement and practice prompt, unless the user explicitly asks for English-only practice.
Do not tell the user to "use English" or otherwise force an English-only reply unless they explicitly asked for English-only practice.
When the user starts in Spanish, stay in Spanish for the whole reply, including the practice prompt; if you include English practice, say the English sentence in quotes and explain it in Spanish.

GUARDRAILS
Never shame or embarrass a wrong answer. Correct gently, praise the effort, and give the right version in a supportive way.
Never claim a child has a learning disability or diagnose any learning problem. If a child seems to be struggling, say you cannot diagnose that, suggest talking to a qualified teacher, doctor, or specialist, and then return to a safe practice activity.
When a parent asks about a child's learning difficulty, respond supportively, avoid labels, and explicitly mention that a qualified teacher, doctor, or specialist is the right person to assess it.
For out-of-scope requests that are not English practice, say: "I'm here to help with spoken English practice, so I can't help with that request. If you want, we can practice English together instead." Then redirect back to English practice.
For a child-learning concern, use a response like: "I can't diagnose that. If you're concerned, talk to a qualified teacher, doctor, or specialist. I can still help with gentle reading practice."
For a fully Spanish user starting message, use Spanish for the whole response and keep the practice prompt in Spanish.
For unsafe or harmful requests, refuse politely and offer a safe alternative. This overrides the first-turn greeting and any intake questions.
Do not claim to know personal facts you have not been told.

STYLE
Use short, clear sentences. Keep most replies to 1-2 sentences, with a friendly pace and no long silence.
If the user is quiet, prompt them with one simple follow-up question.
Use an encouraging, non-judgmental tone. Avoid emojis, complex formatting, or symbols.

First turn
Look up the caller first. If returning: "Welcome back, {name}! Last time we worked on {topics}. Ready to continue?" If new: greet warmly in the user's language/register when possible, ask for their name, then ask one short question for age and English level together.

Behavior rules
- For children under 13: use very simple vocabulary, short sentences, gentle praise, and fun repetition exercises. Provide phonetic hints and short, playful prompts like "Repeat after me: I like apples."
- For adult learners: use natural conversational language, correct common mistakes gently, and offer optional expanded explanations and examples when asked.
- Encourage the user to speak and repeat sentences. Offer short role-play prompts and ask the user to respond.
- When correcting, show a concise corrected sentence and a one-line explanation unless the user asks for more.
- Provide practice exercises such as repeat-after-me, minimal pairs, and short Q&A.
- If the user provides only one of age or level, ask only for the missing detail.
- If the user gives a sentence to practice, a correction request, or an obvious language-learning attempt, correct or respond to that content first, then continue the tutoring flow.
- Once you have both age and level, briefly acknowledge them and immediately begin a short speaking practice question.
- If you cannot answer a question, be honest and offer a simpler practice exercise instead.
- Always ask a follow-up question to continue the spoken practice.

LEARNING EXERCISES — FUNCTION TOOLS (DAY 5)
You have two structured-exercise tools. Use them precisely as described.

get_next_exercise_tool:
Call this tool whenever the learner:
  - Asks for a practice question or exercise
  - Says they want to practice English grammar, vocabulary, speaking, or comprehension
  - Asks for another question or wants to continue
  - Uses code-mixed language to ask for a question (e.g. "Mujhe ek grammar question do")
Do NOT call this tool for greetings, casual conversation, or requests unrelated to learning.
Do NOT invent or compose an exercise yourself when this tool is available.
Always pass the learner's known level and skill. If level is unknown, default to "beginner".

evaluate_answer_tool:
Call this tool immediately after the learner answers an exercise that was retrieved by
get_next_exercise_tool. Pass the exercise_id from the previous get_next_exercise_tool result
and the learner's verbatim answer.
Do NOT claim whether the answer is correct or incorrect without calling this tool first.
Do NOT invent an evaluation result if the tool fails.

WRONG ANSWER VOICE PHRASING (MANDATORY):
After evaluate_answer_tool returns correct=false, use only supportive, encouraging language.
NEVER say: "Wrong", "That's wrong", "Bad answer", "You failed", "You don't understand".
INSTEAD say things like:
  "Good attempt! The correct answer is X."
  "Almost! Let's look at that together."
  "Nice try! The correct form is X."
  "You're getting there! The answer is X."
Then offer a brief explanation (from the tool's 'explanation' field) and ask if they want another question.

For multiple-choice questions, read the options aloud clearly, e.g.:
  "Which word fits the blank: A) go, B) goes, or C) going?"

TOOL FAILURE HANDLING:
If get_next_exercise_tool returns success=false, say:
  "I'm having a little trouble accessing the exercises right now. Let's try again in a moment."
If evaluate_answer_tool returns success=false, say:
  "I couldn't check that answer properly just now, so I don't want to give you misleading feedback. Let's try the question again."
Never expose technical errors, stack traces, or internal details to the learner.

HUMAN ESCALATION — FUNCTION TOOL (DAY 7)

You have one escalation tool: create_escalation_tool.
Use it ONLY in the two situations below. Use your understanding of meaning — not just keywords.

ESCALATION CONDITION 1 — Learner is clearly upset, frustrated, or overwhelmed:
  Examples: "I'm frustrated", "I don't understand this anymore", "This is too hard",
            "I give up", "I can't do this", "I am getting frustrated"

ESCALATION CONDITION 2 — Learner explicitly asks for a teacher or human:
  Examples: "I want to talk to a teacher", "Can I speak to a human?",
            "Connect me to my teacher", "I need a human to explain this",
            "Can a teacher help me?"

DO NOT ESCALATE — these are NORMAL tutoring interactions:
  - Getting an answer wrong
  - "Give me another question"
  - "Explain that again"
  - "I don't know the answer"
  - "Can you repeat the question?"
  - Any single wrong answer or momentary confusion

PERMISSION FLOW (MANDATORY — always ask first):

  If CONDITION 1 (frustrated learner):
    Say: "I understand. I can create a request for a teacher to help you. I would share
    a short summary of what you're struggling with and what we've already tried.
    Would you like me to send that request?"

  If CONDITION 2 (explicit teacher request):
    Say: "Sure. I can create a request for a teacher. I would share a short summary of
    what you need help with. Is that okay?"

  Wait for the learner's response.

  If learner says YES → call create_escalation_tool immediately.
  If learner says NO  → say exactly: "That's completely fine. We won't send a request.
    We can continue practicing here." — do NOT create a request, do NOT pressure again.

AFTER SUCCESSFUL TOOL CALL:
  Say: "Your teacher-help request has been created. Your reference ID is [insert the
  reference_id from the tool result]. A teacher can review the request and follow up
  using your preferred method."

IF TOOL FAILS (success=false in the result):
  Say: "I'm sorry, I couldn't create the teacher-help request right now. You can
  continue practicing here, or try again later."
  Do NOT claim the request was created. Do NOT give a fake reference ID.

INFORMATION TO INCLUDE when calling create_escalation_tool:
  - learner_name: the learner's name if known, otherwise null
  - reason: brief reason ("Learner frustrated" or "Learner requested teacher")
  - what_happened: one or two sentences describing the situation
  - agent_actions_taken: a short list of things the agent already tried this session
  - urgency: "normal" unless the learner is very distressed, in which case "high"
  - language: the learner's language or mix (e.g. "Hindi + English")
  - preferred_follow_up: ask the learner how they prefer to be contacted, or use null
  - topic: the topic being studied if known, otherwise null

NEVER include in the tool call:
  - Passwords, OTPs, PINs, API keys, authentication tokens
  - The full conversation transcript
  - Any sensitive personal information not needed by the teacher

HANDOFF TOOL — MATHS PRACTICE SPECIALIST (DAY 9)
You have a specialist handoff tool: `handoff_to_maths_specialist`.
Call this tool IMMEDIATELY when the learner's request requires maths learning, solving, understanding, or maths practice (e.g. arithmetic, fractions, percentages, algebra, basic geometry).

DO NOT use this tool for:
  - English learning, grammar exercises, vocabulary, speaking practice, or comprehension
  - Normal conversation or general tutoring requests already supported

MANDATORY HANDOFF ANNOUNCEMENT:
When the learner asks a maths question, YOU MUST SPEAK THIS EXACT ANNOUNCEMENT FIRST in your response before or as you execute `handoff_to_maths_specialist`:
"I'll connect you to our Maths Practice Specialist, who can help you with this."
Do not omit this announcement sentence under any circumstances!
"""




class Assistant(Agent):
    def __init__(self, user_id: str = "default_user", session_id: str | None = None) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        # Store the caller's user_id and session_id so tools can use them
        self._user_id = user_id
        self._session_id = session_id or user_id

        # ── Day-5: session-level exercise memory ──────────────────────────
        # Track which exercises have been used this session to prevent repeats.
        self._used_exercise_ids: list[str] = []
        # Track the last exercise so evaluate_answer_tool can reference it.
        self._current_exercise_id: str | None = None
        # Adaptive difficulty state (1=easy, 2=medium, 3=hard).
        self._current_difficulty: int = 1
        # Consecutive correct answers — used to gently raise difficulty.
        self._correct_streak: int = 0

    # ------------------------------------------------------------------
    # Tool: look up a caller in the database
    # ------------------------------------------------------------------

    @function_tool
    async def lookup_caller_info(
        self,
        context: RunContext,
        user_id: str,
    ) -> dict:
        """Look up a caller's saved profile from the database.

        Call this at the very start of every session, before greeting the user.
        Use the caller's user_id (provided in the session start instructions).

        Args:
            user_id: The unique identifier for the caller.

        Returns:
            A dictionary with the caller's profile, or an empty dict if the
            caller is not found in the database (i.e. a new caller).
        """
        logger.info("Looking up caller: user_id=%s", user_id)
        record = lookup_caller(user_id)
        if record is None:
            logger.info("Caller not found — new caller.")
            return {}
        logger.info(
            "Returning caller found: name=%s, level=%s",
            record.get("name"),
            record.get("current_level"),
        )
        return record

    # ------------------------------------------------------------------
    # Tool: save what the agent learned this session
    # ------------------------------------------------------------------

    @function_tool
    async def save_caller_info(
        self,
        context: RunContext,
        user_id: str,
        name: str,
        language_preference: str | None = None,
        current_level: str | None = None,
        topics_covered: list[str] | None = None,
        mistakes: list[str] | None = None,
    ) -> str:
        """Save or update a caller's profile in the database.

        IMPORTANT: Only call this tool after the caller has explicitly said
        "yes" when asked whether they want their progress remembered.
        Never call this without prior consent.

        Args:
            user_id: The unique identifier for the caller.
            name: The caller's name.
            language_preference: Language or mix the caller prefers (e.g. "Hindi-English").
            current_level: The caller's English level (e.g. "beginner", "intermediate", "advanced").
            topics_covered: List of topics practised in this session.
            mistakes: List of recurring mistakes the caller makes.

        Returns:
            A confirmation message string.
        """
        target_user_id = self._user_id if self._user_id and self._user_id != "default_user" else user_id
        logger.info(
            "Saving caller info: user_id=%s, name=%s, level=%s",
            target_user_id,
            name,
            current_level,
        )
        record = {
            "user_id": target_user_id,
            "name": name,
            "language_preference": language_preference,
            "current_level": current_level,
            "topics_covered": topics_covered or [],
            "mistakes": mistakes or [],
        }
        save_caller(record)
        return f"Progress saved for {name}. I'll remember this for next time!"

    # ------------------------------------------------------------------
    # Tool: retrieve the next learning exercise (Day 5)
    # ------------------------------------------------------------------

    @function_tool
    async def get_next_exercise_tool(
        self,
        context: RunContext,
        level: str,
        skill: str,
        topic: str | None = None,
    ) -> dict:
        """Use this tool whenever the learner asks for a practice question, wants to
        practice English, asks for another exercise, wants to continue learning, or
        needs an exercise based on their current level, skill, or topic.
        Do NOT invent an exercise when this tool is available.
        Do NOT call this for greetings, casual conversation, or non-learning requests.

        Valid levels  : "beginner", "intermediate", "advanced"
        Valid skills  : "grammar", "vocabulary", "sentence_formation", "speaking",
                        "comprehension"

        Args:
            level: The learner's English level.
            skill: The skill to practise (grammar / vocabulary / sentence_formation /
                   speaking / comprehension).
            topic: Optional topic within the skill (e.g. "present tense"). Leave
                   None if not specified by the learner.

        Returns:
            A dict with 'success', 'exercise' (id, question, options, level, skill,
            topic, difficulty, exercise_type), 'source', and 'data_version'.
            If success is False, contains 'error' with a short reason.
        """
        logger.info(
            "get_next_exercise_tool called: level=%s skill=%s topic=%s difficulty=%s",
            level,
            skill,
            topic,
            self._current_difficulty,
        )

        result = _get_next_exercise(
            level=level,
            skill=skill,
            topic=topic,
            difficulty=self._current_difficulty if self._current_difficulty > 1 else None,
            exclude_ids=list(self._used_exercise_ids),
        )

        if result.get("success") and result.get("exercise"):
            exercise_id = result["exercise"]["id"]
            self._current_exercise_id = exercise_id
            # Add to used set; keep the rolling window to 20 to avoid deadlock
            # on small datasets.
            self._used_exercise_ids.append(exercise_id)
            if len(self._used_exercise_ids) > 20:
                self._used_exercise_ids.pop(0)
            logger.info("Exercise retrieved: id=%s", exercise_id)
            # Track exercise started for call analytics (Day 8)
            if self._session_id:
                mark_exercise_started(self._session_id)

        return result

    # ------------------------------------------------------------------
    # Tool: evaluate the learner's answer (Day 5)
    # ------------------------------------------------------------------

    @function_tool
    async def evaluate_answer_tool(
        self,
        context: RunContext,
        exercise_id: str,
        learner_answer: str,
    ) -> dict:
        """Use this tool after the learner answers an exercise retrieved by
        get_next_exercise_tool. Evaluate the learner's response using the exercise
        context. Do NOT make unsupported claims about whether the answer is correct
        when this evaluation tool is available.

        Args:
            exercise_id:    The 'id' field from the exercise returned by
                            get_next_exercise_tool.
            learner_answer: The learner's spoken or typed response, verbatim.

        Returns:
            A dict with 'success', 'correct' (bool), 'score' (0 or 1), 'feedback'
            (ready-to-speak supportive string), 'correct_answer', 'explanation',
            and 'exercise_id'.
            If success is False, contains 'error' with a short reason.
        """
        logger.info(
            "evaluate_answer_tool called: exercise_id=%s learner_answer=%r",
            exercise_id,
            learner_answer,
        )

        result = _evaluate_answer(exercise_id=exercise_id, learner_answer=learner_answer)

        if result.get("success"):
            # Track exercise completed and feedback given for call analytics (Day 8)
            if self._session_id:
                mark_exercise_completed(self._session_id)

            # Adaptive difficulty — adjust gently, never aggressively
            if result["correct"]:
                self._correct_streak += 1
                # Raise difficulty only after 3 consecutive correct answers
                if self._correct_streak >= 3 and self._current_difficulty < 3:
                    self._current_difficulty += 1
                    self._correct_streak = 0
                    logger.info(
                        "Difficulty raised to %d after streak", self._current_difficulty
                    )
            else:
                self._correct_streak = 0
                # Lower difficulty only after struggling (do not drop on a single miss)
                # The agent is trusted to detect when the learner is genuinely struggling
                # across multiple turns; a single wrong answer does not change difficulty.

        return result

    # ------------------------------------------------------------------
    # Tool: create a human-help escalation request (Day 7)
    # ------------------------------------------------------------------

    @function_tool
    async def create_escalation_tool(
        self,
        context: RunContext,
        learner_name: str | None,
        reason: str,
        what_happened: str,
        agent_actions_taken: list[str] | None,
        urgency: str,
        language: str | None,
        preferred_follow_up: str | None,
        topic: str | None,
    ) -> dict:
        """Create a human-help escalation request for a teacher to review.

        ONLY call this tool after:
          1. Detecting the learner is frustrated OR explicitly asking for a teacher.
          2. Asking the learner's permission and receiving a clear YES.

        Never call this tool without the learner's explicit consent.
        Never include passwords, OTPs, PINs, API keys, or full transcripts.

        Args:
            learner_name:         Learner's first name if known, otherwise None.
            reason:               Brief reason (e.g. "Learner frustrated" or
                                  "Learner requested teacher").
            what_happened:        One or two sentences describing the situation.
            agent_actions_taken:  List of things the agent already tried
                                  (e.g. ["3 grammar exercises", "repeated explanation"]).
                                  Pass an empty list if nothing specific was attempted.
            urgency:              "normal" or "high".
            language:             Learner's language or mix (e.g. "Hindi + English").
            preferred_follow_up:  How the teacher should follow up (e.g. "voice call"),
                                  or None if not asked.
            topic:                The learning topic if known (e.g. "grammar"), or None.

        Returns:
            {"success": True, "reference_id": "HELP-XXXX"} on success.
            {"success": False, "error": "<short reason>"}   on failure.
        """
        # Build a concise human-readable summary for the teacher
        actions_str = ""
        if agent_actions_taken:
            actions_str = "\n\nThe agent already attempted:\n" + "\n".join(
                f"- {a}" for a in agent_actions_taken
            )

        summary_lines = [
            f"Learner needs help{f' with {topic}' if topic else ''}.",
            f"{what_happened.strip()}{actions_str}",
        ]
        if language:
            summary_lines.append(f"\nLanguage: {language}")
        if preferred_follow_up:
            summary_lines.append(f"Follow-up: {preferred_follow_up}")

        summary = "\n".join(summary_lines)

        logger.info(
            "create_escalation_tool called: learner_id=%s reason=%r urgency=%s",
            self._user_id,
            reason,
            urgency,
        )

        try:
            result = create_escalation(
                learner_id=self._user_id,
                reason=reason,
                summary=summary,
                learner_name=learner_name,
                topic=topic,
                agent_actions=agent_actions_taken or [],
                urgency=urgency or "normal",
                language=language,
                preferred_follow_up=preferred_follow_up,
            )
            if result.get("success"):
                logger.info(
                    "Escalation created successfully: reference_id=%s",
                    result.get("reference_id"),
                )
            else:
                logger.error(
                    "create_escalation returned failure: %s", result.get("error")
                )
            return result
        except Exception as exc:  # noqa: BLE001
            # Log the full technical error for the developer but never expose it
            # to the learner — the agent's system prompt handles the user-facing message.
            logger.error(
                "create_escalation_tool unexpected error: %s", exc, exc_info=True
            )
            return {"success": False, "error": "Unexpected error creating escalation."}

    # ------------------------------------------------------------------
    # Tool: hand off to Maths Practice Specialist (Day 9)
    # ------------------------------------------------------------------

    @function_tool
    async def handoff_to_maths_specialist(
        self,
        context: RunContext,
        maths_question: str,
        topic: str | None = None,
        language: str | None = None,
    ) -> dict:
        """Transfer the learner to the Maths Practice Specialist when the learner asks for help
        solving, understanding, practicing, or learning a mathematics topic. Do not use this
        tool for English learning, spoken-English practice, normal conversation, or requests
        that the main Learning & Literacy agent can already handle.

        Args:
            maths_question: The learner's current maths question or request verbatim.
            topic:          Specific maths topic if identified (e.g. "percentages", "fractions", "algebra").
            language:       Learner's preferred language or mix (e.g. "Hindi-English").

        Returns:
            A dictionary with status and transferred context.
        """
        logger.info(
            "handoff_to_maths_specialist called: user_id=%s topic=%s question=%r",
            self._user_id,
            topic,
            maths_question,
        )

        try:
            specialist_instructions = (
                "ACT AS THE MATHS PRACTICE SPECIALIST AGENT NOW.\n"
                f"The learner was just transferred to you with the question: '{maths_question}'.\n"
                f"Topic: {topic or 'Mathematics'}.\n"
                "Respond IMMEDIATELY as the Maths Practice Specialist:\n"
                "1. Introduce yourself briefly: 'Hi! I'm your Maths Practice Specialist. I understand you'd like help with...'\n"
                "2. Acknowledge the learner's exact question so they know context was transferred without repeating.\n"
                "3. Provide a clear, step-by-step explanation or hint, and encourage them to attempt the next step.\n"
                "4. LANGUAGE RULE: Default to English. Only reply in Hindi or Hindi-English code-mix if the learner explicitly asked in Hindi/code-mix."
            )


            # Perform agent update on session if session is available in context
            session = getattr(context, "session", None)
            if session:
                specialist_agent = MathsSpecialistAssistant(
                    user_id=self._user_id,
                    session_id=self._session_id,
                    initial_context=maths_question,
                    language_preference=language,
                )
                session.update_agent(specialist_agent)

            return {
                "success": True,
                "action": "handoff_to_maths_specialist",
                "maths_question": maths_question,
                "topic": topic,
                "language": language or "English",
                "learner_id": self._user_id,
                "instructions_for_specialist": specialist_instructions,
            }

        except Exception as exc:  # noqa: BLE001
            logger.error("handoff_to_maths_specialist error: %s", exc, exc_info=True)
            return {
                "success": False,
                "error": "I couldn't connect you to the Maths Practice Specialist right now, but I can still try to help with the basics.",
            }




server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    # Initialise the caller database once at startup (idempotent).
    init_db()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    await ctx.connect()

    # Resolve user identity safely from remote participants
    user_id = ctx.room.name
    if ctx.room.remote_participants:
        p = list(ctx.room.remote_participants.values())[0]
        if p.identity:
            user_id = p.identity
    logger.info("Caller identity resolved: %s", user_id)

    # Call Analytics (Day 8): session_id and call_type identification
    session_id = ctx.room.name
    call_type = "sip" if ("sip" in session_id.lower() or "sip" in user_id.lower()) else "browser"
    create_call_record(session_id=session_id, learner_id=user_id, call_type=call_type)

    def _on_shutdown():
        end_call_record(session_id)

    ctx.add_shutdown_callback(_on_shutdown)

    try:
        session = AgentSession(
            stt=deepgram.STT(model="nova-3"),
            llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
            tts=murf.TTS(
                voice="Anisha",
                style="Conversational",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=1),
                text_pacing=True,
            ),
            turn_detection=MultilingualModel(),
            min_endpointing_delay=0.3,
            max_endpointing_delay=1.5,
            preemptive_generation=True,
        )

        await session.start(
            agent=Assistant(user_id=user_id, session_id=session_id),
            room=ctx.room,
            room_options=room_io.RoomOptions(
                audio_input=room_io.AudioInputOptions(
                    noise_cancellation=lambda params: noise_cancellation.BVC(),
                ),
            ),
        )

        participant = await ctx.wait_for_participant()
        if participant and participant.identity:
            user_id = participant.identity
        logger.info("Caller identity resolved: %s", user_id)

        caller_record = lookup_caller(user_id)

        if caller_record:
            name   = caller_record["name"]
            level  = caller_record.get("current_level") or "unknown level"
            topics = caller_record.get("topics_covered") or []
            topics_str = ", ".join(topics) if topics else "various topics"
            greeting_instructions = (
                f"This is a returning caller. Their name is {name}, their current English level "
                f"is {level}, and last time they practised: {topics_str}. "
                f"Greet {name} warmly by name, briefly mention their level and last topics, "
                "and ask if they would like to continue from where they left off. "
                "Speak immediately — do not call any tools before greeting."
            )
        else:
            greeting_instructions = (
                "This is a new caller. Give a warm, friendly greeting, introduce yourself "
                "as their English practice tutor, ask for their name, and then ask for "
                "their age and English level (beginner, intermediate, or advanced). "
                "Speak immediately — do not call any tools before greeting."
            )

        await session.generate_reply(instructions=greeting_instructions)
    finally:
        end_call_record(session_id)


if __name__ == "__main__":
    cli.run_app(server)
