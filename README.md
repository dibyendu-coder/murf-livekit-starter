# Voice Agent Starter — Powered by Murf Falcon

Build a production voice AI agent in 5 minutes. Powered by the fastest TTS on the market - swap the system prompt to build anything from customer support to language tutors.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Murf Falcon](https://img.shields.io/badge/TTS-Murf%20Falcon-6366F1)](https://murf.ai/api/docs/text-to-speech/streaming) [![LiveKit](https://img.shields.io/badge/Transport-LiveKit-002cf2)](https://docs.livekit.io) [![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/) [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)

---

## Why Murf Falcon

- **55ms model latency** - fastest production TTS
- **130ms time-to-first-audio** across 10+ global regions
- **$0.01/1000 characters** - up to 10x cheaper than alternatives
- **150+ voices** across 35+ languages
- **99.38% pronunciation accuracy**

---

## Architecture

```mermaid
flowchart LR
    A[🎙️ User speaks] -->|audio| B[Deepgram STT]
    B -->|text| C[LLM]
    C -->|response text| D[Murf Falcon TTS]
    D -->|audio| E[LiveKit]
    E -->|stream| F[🔊 User hears]

    style A fill:#444441,stroke:#888780,color:#fff
    style B fill:#185FA5,stroke:#85B7EB,color:#fff
    style C fill:#534AB7,stroke:#AFA9EC,color:#fff
    style D fill:#0F6E56,stroke:#5DCAA5,color:#fff
    style E fill:#D85A30,stroke:#F0997B,color:#fff
    style F fill:#444441,stroke:#888780,color:#fff
```

---

## Quickstart

### Prerequisites

- **Python** 3.10+
- **[uv](https://docs.astral.sh/uv/)** - fast Python package manager
  ```bash
  # macOS/Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **Node.js** 18+
- **pnpm** — fast Node package manager
  ```bash
  npm install -g pnpm
  ```
- A [LiveKit](https://cloud.livekit.io/) project (free tier available)

### Step 1: Clone the repo

```bash
git clone https://github.com/murf-ai/murf-livekit-starter.git
cd murf-livekit-starter
```

### Step 2: Set up environment variables

Create `.env.local` in both `backend/` and `frontend/` (copy from `.env.example` in each). You need:

| Variable                               | Where to get it                                        | Required |
| -------------------------------------- | ------------------------------------------------------ | -------- |
| `LIVEKIT_URL`                          | LiveKit Cloud dashboard                                | Yes      |
| `LIVEKIT_API_KEY`                      | LiveKit Cloud dashboard                                | Yes      |
| `LIVEKIT_API_SECRET`                   | LiveKit Cloud dashboard                                | Yes      |
| `MURF_API_KEY`                         | [murf.ai/api/dashboard](https://murf.ai/api/dashboard) | Yes      |
| `DEEPGRAM_API_KEY`                     | [deepgram.com](https://deepgram.com)                   | Yes      |
| `GOOGLE_API_KEY` (or `OPENAI_API_KEY`) | Depends on LLM choice                                  | Yes      |

### Step 3: Install backend dependencies

```bash
cd backend
uv sync
uv run python src/agent.py download-files
```

### Step 4: Install frontend dependencies

```bash
cd frontend
pnpm install
```

### Step 5: Run it

**Option A - All-in-one (from repo root):**

```bash
# macOS/Linux
chmod +x start_app.sh
./start_app.sh

# Windows (PowerShell)
.\start_app.ps1
```

**Option B - Separate terminals:**

```bash
# Terminal 1 — LiveKit Server
livekit-server --dev

# Terminal 2 — Backend agent
cd backend && uv run python src/agent.py dev

# Terminal 3 — Frontend
cd frontend && pnpm dev
```

Then open **http://localhost:3000** in your browser.

You should now see the voice agent UI. Click **Start talking**, allow microphone access, and speak — the agent will respond with Murf Falcon TTS. Ensure your backend and (if using Option B) LiveKit server are running.

---

## Deploy

Want to deploy this beyond localhost? You'll need to deploy **two services**: the backend agent and the frontend. Both must use the same LiveKit project.

> This is a two-service app — the backend agent and the frontend UI deploy separately. You'll need both running and connected to the same LiveKit project.

### Backend (Python agent) — Deploy to Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/tIVCF1?referralCode=cNjn2P&utm_medium=integration&utm_source=template&utm_campaign=generic)

Set these environment variables in Railway:

- `MURF_API_KEY`
- `DEEPGRAM_API_KEY`
- `GOOGLE_API_KEY` or `OPENAI_API_KEY`
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`

The backend runs as a long-lived Python process that connects to LiveKit as an agent. Railway handles this well.

### Frontend (Next.js) — Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/murf-ai/murf-livekit-starter&root-directory=frontend&env=LIVEKIT_URL,LIVEKIT_API_KEY,LIVEKIT_API_SECRET&project-name=murf-voice-agent&repository-name=murf-voice-agent)

Set these environment variables in Vercel:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `AGENT_NAME` (optional — for explicit agent dispatch)

The frontend is a standard Next.js app. Point it at the same LiveKit instance your backend agent is connected to.

### Connecting them

The frontend and backend don't call each other directly — they both connect to **LiveKit**, which handles the real-time audio transport.

1. Use the **same** `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` on both Railway and Vercel
2. Set `AGENT_NAME=my-agent` on Vercel — this matches the `agent_name="my-agent"` registered in `backend/src/agent.py`
3. Verify: Railway logs should show the agent connected to LiveKit. Open your Vercel URL, click **Start talking** — the agent should respond

If the agent doesn't connect, double-check that both services point to the same LiveKit project and that the backend is running (check Railway logs).

---

## Change the Use Case

The default system prompt makes this a **customer support agent**. You can change the agent’s behavior by editing the prompt.

**Where the prompt lives:** `backend/src/agent.py`- the `SYSTEM_PROMPT` constant (near the top of the file, after the imports). Change that string to change what your voice agent does.

### Example prompts (copy-paste)

**Customer Support (default):**

```
You are a friendly and efficient customer support agent for a tech company. Help users with account issues, billing questions, and product troubleshooting. Be concise, empathetic, and solution-oriented. If you don't know something, say so honestly and offer to escalate.
```

**Language Tutor:**

```
You are a patient and encouraging language tutor helping the user practice conversational Spanish. Speak primarily in Spanish but switch to English to explain grammar or vocabulary when needed. Correct mistakes gently and suggest better phrasing. Keep conversations natural and fun.
```

**AI Receptionist:**

```
You are a professional receptionist for a medical clinic. Help callers schedule appointments, answer questions about office hours and services, and take messages for doctors. Be warm but efficient. Ask for the caller's name and reason for calling upfront.
```

See the Configuration section below for voice, STT, and LLM options.

---

## Configuration

### Murf voice

Edit the `tts=murf.TTS(...)` call in `backend/src/agent.py`. Set the `voice` argument to any Murf voice ID. Examples:

- `Anisha` — Indian English (female, default in this starter)
- `Pooja` — Indian English (female)
- `Samar` — Indian English (male)
- `Amara` — US English (female)
- `Gordon` — US English (male)
- `Hazel` — UK English (female)
- `Bertie` — UK English (male)

Browse all voices: [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library).

### STT provider

STT is configured in `backend/src/agent.py` in the `AgentSession(stt=...)` call. The default is Deepgram (`deepgram.STT(model="nova-3")`). You can swap to another LiveKit-compatible STT plugin if needed.

### LLM (Gemini vs OpenAI)

- **Gemini (default):** Set `GOOGLE_API_KEY` and use `llm=google.LLM(model="gemini-3.5-flash-lite")` in `agent.py`.
- **OpenAI:** Set `OPENAI_API_KEY`, add the OpenAI plugin, and use the corresponding `llm=openai.LLM(...)` in `agent.py`.

### Audio format

Murf Falcon and LiveKit handle audio format internally. For advanced options, see [Murf API docs](https://murf.ai/api/docs) and [LiveKit docs](https://docs.livekit.io).

---

## Project Structure

```
murf-livekit-starter/
├── backend/                 # Python voice agent (LiveKit Agents + Murf Falcon)
│   ├── src/
│   │   └── agent.py         # Agent entrypoint, pipeline (STT/LLM/TTS), system prompt
│   ├── tests/               # Agent tests
│   ├── .env.example         # Backend env template
│   ├── pyproject.toml       # Python deps (uv)
│   └── railway.toml         # Railway deploy config
├── frontend/                # Next.js UI for voice sessions
│   ├── app/
│   │   ├── page.tsx         # Main page
│   │   └── api/token/       # LiveKit token endpoint (dev)
│   ├── components/          # UI (agents-ui, app config, theme)
│   ├── app-config.ts        # Branding, title, button text, accent
│   ├── .env.example         # Frontend env template
│   └── package.json         # Node deps (pnpm)
├── start_app.sh             # Start LiveKit + backend + frontend (macOS/Linux)
├── start_app.ps1            # Start LiveKit + backend + frontend (Windows)
├── README.md                # This file
```

For deeper documentation on each part, see:

- [Backend Documentation](./backend/README.md) — agent pipeline, voice/LLM/STT configuration, testing, deployment
- [Frontend Documentation](./frontend/README.md) — UI customization, visualizers, theming, component architecture

---

## Links

- [Murf API Docs](https://murf.ai/api/docs)
- [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library)
- [LiveKit Docs](https://docs.livekit.io)
- [Deepgram Docs](https://developers.deepgram.com)
- [Murf Falcon Benchmarks](https://murf.ai/falcon/benchmarks)
- [TTS Latency Benchmarker](https://github.com/sahilsgupta/tts-latency-benchmarker) — run your own p50/p95 tests across providers
- [Murf Discord](https://discord.gg/FbKAy96Sz7)
- [Murf Startup Incubator](https://murf.ai/api) — 50M free characters for startups

---

## License

MIT

---

## Day 5 — Learning & Literacy Tool

> **Challenge track**: 10 Days of Voice Agents — Learning & Literacy

### What problem does the tool solve?

Before Day 5, the voice tutor could explain concepts and correct free-form speech, but it had no structured exercise library. The learner could not request a specific grammar drill or vocabulary quiz and receive a real, curated question. There was also no programmatic way to evaluate a learner's answer — the LLM had to judge correctness entirely on its own, without an authoritative answer key.

Day 5 adds two function-calling tools that give the agent access to a local, curated exercise dataset. The agent now:

1. **Retrieves a real exercise** from the dataset instead of improvising one.
2. **Evaluates the learner's answer** against the stored correct answer using deterministic logic.

### Why is the tool necessary?

| Without tool | With tool |
|---|---|
| LLM composes exercises from memory — quality is inconsistent | Exercises come from a structured, reviewed dataset |
| Correctness is judged by the LLM — may be lenient or wrong | Correctness is determined by `evaluate_answer()` — deterministic |
| No anti-repeat logic — same question may be asked twice | `exclude_ids` prevents same exercise repeating in a session |
| Difficulty never changes programmatically | Adaptive difficulty: correct-streak of 3 raises level |

---

### Dataset

> **The current learning exercise dataset is locally curated for the Day-5 Learning & Literacy prototype.**
> It is NOT sourced from an external API.

| Field | Value |
|---|---|
| **Source** | `Local Learning Exercise Dataset` |
| **Data version** | `2026-08-10` |
| **File** | `backend/src/exercises.py` |
| **Count** | 35 exercises |
| **Levels** | `beginner` · `intermediate` · `advanced` |
| **Skills** | `grammar` · `vocabulary` · `sentence_formation` · `speaking` · `comprehension` |
| **Types** | `multiple_choice` · `fill_in_the_blank` · `sentence_correction` · `vocabulary` · `speaking_prompt` |

Each exercise contains:

```json
{
  "id": "grammar_001",
  "level": "beginner",
  "skill": "grammar",
  "topic": "present tense",
  "question": "She ___ to school every day.",
  "options": ["go", "goes", "going"],
  "correct_answer": "goes",
  "explanation": "We use 'goes' with 'she' in the simple present tense.",
  "difficulty": 1,
  "exercise_type": "fill_in_the_blank"
}
```

---

### Function: `get_next_exercise`

**File**: `backend/src/exercises.py`
**Agent tool name**: `get_next_exercise_tool`

**Description**:
Retrieves a suitable exercise from the local dataset based on the learner's level, skill, and optional topic. Respects `exclude_ids` to prevent repetition.

**Input parameters**:

| Parameter | Type | Required | Description |
|---|---|---|---|
| `level` | `str` | Yes | `"beginner"` / `"intermediate"` / `"advanced"` |
| `skill` | `str` | Yes | `"grammar"` / `"vocabulary"` / `"sentence_formation"` / `"speaking"` / `"comprehension"` |
| `topic` | `str or None` | No | Optional topic filter, e.g. `"present tense"` |
| `difficulty` | `int or None` | No | `1` / `2` / `3` |
| `exclude_ids` | `list[str] or None` | No | Exercise IDs to skip |

**Output structure**:

```json
{
  "success": true,
  "exercise": {
    "id": "grammar_001",
    "question": "She ___ to school every day.",
    "options": ["go", "goes", "going"],
    "level": "beginner",
    "skill": "grammar",
    "topic": "present tense",
    "difficulty": 1,
    "exercise_type": "fill_in_the_blank"
  },
  "source": "Local Learning Exercise Dataset",
  "data_version": "2026-08-10"
}
```

On failure: `{ "success": false, "error": "..." }`

---

### Function: `evaluate_answer`

**File**: `backend/src/exercises.py`
**Agent tool name**: `evaluate_answer_tool`

**Description**:
Evaluates the learner's answer against the stored correct answer for a given exercise. Uses normalised string matching (case-insensitive, punctuation-stripped). For `speaking_prompt` exercises, uses keyword-presence matching.

**Input parameters**:

| Parameter | Type | Required | Description |
|---|---|---|---|
| `exercise_id` | `str` | Yes | The `id` field from `get_next_exercise` output |
| `learner_answer` | `str` | Yes | The learner's verbatim spoken or typed answer |

**Output structure**:

```json
{
  "success": true,
  "correct": false,
  "score": 0,
  "feedback": "Good attempt! The correct answer is 'goes'.",
  "correct_answer": "goes",
  "explanation": "We use 'goes' with 'she' in the simple present tense.",
  "exercise_id": "grammar_001"
}
```

On failure: `{ "success": false, "error": "...", "exercise_id": "grammar_001" }`

---

### Tool-calling logic

The agent system prompt instructs Gemini to:

- **Call `get_next_exercise_tool`** whenever the learner asks for a practice question, exercise, or says they want to continue learning — including Hindi/code-mixed requests like `"Mujhe ek grammar question do"`.
- **NOT call** the tool for greetings, casual conversation, or non-learning requests.
- **Call `evaluate_answer_tool`** immediately after the learner answers an exercise, passing the `exercise_id` from the previous tool result and the learner's verbatim answer.
- **Never invent** an exercise or an evaluation result if the tool is available.

---

### Error handling

| Scenario | Agent response |
|---|---|
| `get_next_exercise` returns `success=false` | "I'm having a little trouble accessing the exercises right now. Let's try again in a moment." |
| `evaluate_answer` returns `success=false` | "I couldn't check that answer properly just now, so I don't want to give you misleading feedback. Let's try the question again." |
| Exercise ID not found | `success=false` with a short error string (no stack trace) |
| Empty/invalid learner answer | `success=false` with a short error string |

Technical errors, stack traces, and internal details are **never** exposed to the learner.

---

### Wrong-answer phrasing

The system prompt prohibits shaming language. Wrong answers receive supportive feedback:

- "Good attempt! The correct answer is X."
- "Almost! Let's look at that together."
- "Nice try! The correct form is X."
- "You're getting there! The answer is X."

---

### Adaptive difficulty

| State | Behaviour |
|---|---|
| 3 consecutive correct answers | Difficulty increases by 1 (max 3) |
| Incorrect answer | Streak resets; difficulty does NOT change on a single wrong answer |
| Unknown learner level | Defaults to `beginner` / difficulty 1 |

---

### Example conversation (Demo flow)

```
Learner: I am a beginner. Give me a grammar exercise.

  Agent calls: get_next_exercise_tool(level="beginner", skill="grammar")
  Tool returns: exercise grammar_001

Agent: Great! Here's a grammar question.
       She ___ to school every day.
       Which word fits the blank: A) go, B) goes, or C) going?

Learner: Goes.

  Agent calls: evaluate_answer_tool(exercise_id="grammar_001", learner_answer="Goes")
  Tool returns: correct=true

Agent: Excellent! That's exactly right. We use 'goes' with 'she'
       in the simple present tense. Would you like another one?

Learner: Mujhe ek aur question do.

  Agent calls: get_next_exercise_tool(level="beginner", skill="grammar",
               exclude_ids=["grammar_001"])
  Tool returns: a different exercise

Agent: Bilkul! Here's your next question...
```

---

### Testing performed

| Test | Type | Result |
|---|---|---|
| `get_next_exercise` returns valid exercise | Unit | Passed |
| `get_next_exercise` with `exclude_ids` returns different exercise | Unit | Passed |
| `evaluate_answer` correct answer → `correct=true` | Unit | Passed |
| `evaluate_answer` wrong answer → supportive feedback, no shaming | Unit | Passed |
| `evaluate_answer` unknown exercise ID → `success=false` gracefully | Unit | Passed |
| Case-insensitive + punctuation-stripped matching | Unit | Passed |
| All three levels have exercises | Smoke | Passed |
| All five skills have exercises | Smoke | Passed |
| Grammar exercise request triggers `get_next_exercise_tool` | LLM eval | Passed |
| Greeting does NOT trigger any tool | LLM eval | Passed |
| Hindi code-mixed request triggers `get_next_exercise_tool` | LLM eval | Passed |

---

### Known limitations

- The exercise dataset is small (35 exercises). With extensive use, the anti-repeat window (last 20) may exhaust a skill/level combination. The fallback relaxes filters to prevent deadlock.
- Speaking-prompt evaluation uses keyword-presence matching, not semantic evaluation. An LLM-based semantic evaluator could be added in a future day.
- Adaptive difficulty uses only the current session's streak; it does not persist across sessions. Integrating with `save_caller` / `lookup_caller` is a future enhancement.
- The dataset covers English exercises only; Hindi-medium exercises are not yet included.
