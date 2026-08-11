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
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation, openai
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from database import init_db, lookup_caller, save_caller
from exercises import get_next_exercise as _get_next_exercise, evaluate_answer as _evaluate_answer

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
"""


class Assistant(Agent):
    def __init__(self, user_id: str = "default_user") -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        # Store the caller's user_id so tools can use it without being passed it
        # again by the LLM each time.
        self._user_id = user_id

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


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    # Initialise the caller database once at startup (idempotent).
    init_db()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Connect before attaching the session to the room. Starting the session
    # first can leave the audio/transcription pipeline without a connected room,
    # which means user turns never reach the LLM reliably.
    await ctx.connect()

    # Resolve user identity safely from remote participants
    user_id = ctx.room.name
    if ctx.room.remote_participants:
        p = list(ctx.room.remote_participants.values())[0]
        if p.identity:
            user_id = p.identity
    logger.info("Caller identity resolved: %s", user_id)

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
            voice="Anisha",
            style="Conversational",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=1),
            text_pacing=True,
        ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        # Keep the pause after speech short.
        min_endpointing_delay=0.3,
        max_endpointing_delay=1.5,
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(user_id=user_id),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                # Use default BVC noise cancellation for all participants. Avoid
                # importing `rtc.ParticipantKind` to stay compatible with
                # different livekit package layouts.
                noise_cancellation=lambda params: noise_cancellation.BVC(),
            ),
        ),
    )

    # Wait until a remote participant (learner / SIP call) has actually joined the room
    # before resolving identity and generating the greeting.
    participant = await ctx.wait_for_participant()
    if participant and participant.identity:
        user_id = participant.identity
    logger.info("Caller identity resolved: %s", user_id)

    # Look up the caller in Python — do NOT rely on the LLM calling a tool here
    # because a tool-call round-trip on the very first turn can stall speech output.
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

    # A system prompt alone does not produce speech when the caller joins.
    # generate_reply with a concrete instruction triggers immediate speech.
    await session.generate_reply(instructions=greeting_instructions)


if __name__ == "__main__":
    cli.run_app(server)
