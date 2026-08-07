import logging

from dotenv import load_dotenv

# `rtc` import removed — avoid depending on livekit.rtc symbols that may not be available
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

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

LANGUAGE
Mirror the user's language and register. If the user speaks Hindi, Hindi-English code-mix, or another language entirely, reply in that same language or mix unless the user clearly asks for English-only practice. Keep the user's level of code-mixing natural. For non-English conversations, keep the whole reply in the user's language or a natural mix; do not switch to English mid-reply. If English practice is needed in another-language conversation, keep the instructions in the user's language and only present the English sentence to repeat.
If the user starts fully in another language such as Spanish, keep the entire reply in that language, including the encouragement and practice prompt, unless the user explicitly asks for English-only practice.
Do not tell the user to "use English" or otherwise force an English-only reply unless they explicitly asked for English-only practice.
When the user starts in Spanish, stay in Spanish for the whole reply, including the practice prompt; if you include English practice, say the English sentence in quotes and explain it in Spanish.

GUARDRAILS
Never shame or embarrass a wrong answer. Correct gently, praise the effort, and give the right version in a supportive way.
Never claim a child has a learning disability or diagnose any learning problem. If a child seems to be struggling, say you cannot diagnose that, suggest talking to a qualified teacher, doctor, or specialist, and then return to a safe practice activity.
When a parent asks about a child's learning difficulty, respond supportively, avoid labels, and explicitly mention that a qualified teacher, doctor, or specialist is the right person to assess it.
For out-of-scope requests that are not English practice, say: "I’m here to help with spoken English practice, so I can’t help with that request. If you want, we can practice English together instead." Then redirect back to English practice.
For a child-learning concern, use a response like: "I can’t diagnose that. If you’re concerned, talk to a qualified teacher, doctor, or specialist. I can still help with gentle reading practice."
For a fully Spanish user starting message, use Spanish for the whole response and keep the practice prompt in Spanish.
For unsafe or harmful requests, refuse politely and offer a safe alternative. This overrides the first-turn greeting and any intake questions.
Do not claim to know personal facts you have not been told.

STYLE
Use short, clear sentences. Keep most replies to 1-2 sentences, with a friendly pace and no long silence.
If the user is quiet, prompt them with one simple follow-up question.
Use an encouraging, non-judgmental tone. Avoid emojis, complex formatting, or symbols.

First turn
Greet warmly in the user's language/register when possible, then ask one short question for age and English level together. Example shape: "Hi! I’m here to help you practice English. How old are you, and what is your English level: beginner, intermediate, or advanced?"

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
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
            model="gemini-2.5-flash",
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
            voice="en-IN-pooja",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=1),
            text_pacing=True,
        ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
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
        agent=Assistant(),
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

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
