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
"""


class Assistant(Agent):
    def __init__(self, user_id: str) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        # Store the caller's user_id so tools can use it without being passed it
        # again by the LLM each time.
        self._user_id = user_id

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

    # Re-check participant identity right before lookup in case participant connected after room join
    if ctx.room.remote_participants:
        p = list(ctx.room.remote_participants.values())[0]
        if p.identity:
            user_id = p.identity

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
