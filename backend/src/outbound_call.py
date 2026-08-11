"""
outbound_call.py — Day 6: Outbound SIP Calling via LiveKit SIP Trunk

Makes a REAL outbound call using your LiveKit SIP Trunk.
When the learner answers, the existing agent.py takes over completely —
no STT, LLM, TTS, or exercise logic is duplicated here.

Flow:
    1. Create a LiveKit room (unique per call)
    2. Dispatch the existing 'my-agent' to the room
    3. Create a SIP participant (LiveKit dials out via your trunk)
    4. Linphone / phone rings on the learner's device
    5. Learner answers → joins the LiveKit room
    6. Existing agent.py handles EVERYTHING:
           Deepgram STT  →  Gemini LLM
           get_next_exercise()  /  evaluate_answer()   (exercises.py)
           Murf Falcon TTS
    7. Monitor until call ends — log status changes
    8. Clean up the room

Required env vars in backend/.env.local:
    LIVEKIT_URL              — already set  (wss://...)
    LIVEKIT_API_KEY          — already set
    LIVEKIT_API_SECRET       — already set
    LIVEKIT_SIP_TRUNK_ID     — ← NEW: your outbound SIP trunk ID (e.g. ST_xxxx)
    AGENT_NAME               — optional, default "my-agent"
    SIP_CALL_TIMEOUT         — optional, default 60 seconds

Usage:
    uv run python src/outbound_call.py alice@sip.linphone.org
    uv run python src/outbound_call.py +91XXXXXXXXXX
    uv run python src/outbound_call.py sip:alice@example.com

From Python:
    from outbound_call import make_outbound_call
    make_outbound_call("alice@sip.linphone.org")
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# ── load environment ──────────────────────────────────────────────────────────
# This file lives in backend/src/  — .env.local is one level up in backend/
_BACKEND_DIR = Path(__file__).parent.parent   # backend/src/ → backend/
load_dotenv(_BACKEND_DIR / ".env.local")

# ── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("outbound")

# ── read environment (NEVER log credential values) ────────────────────────────
LIVEKIT_URL        = os.environ.get("LIVEKIT_URL", "")
LIVEKIT_API_KEY    = os.environ.get("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "")
SIP_TRUNK_ID       = os.environ.get("LIVEKIT_SIP_TRUNK_ID", "")
AGENT_NAME         = os.environ.get("AGENT_NAME", "my-agent")
SIP_CALL_TIMEOUT   = int(os.environ.get("SIP_CALL_TIMEOUT", "60"))

# ── how often to poll LiveKit for participant status (seconds) ────────────────
_POLL_INTERVAL = 2.0


# ─────────────────────────────────────────────────────────────────────────────
# Structured log helpers  (never log credential values)
# ─────────────────────────────────────────────────────────────────────────────

def _log_call(msg: str) -> None:
    logger.info("[CALL] %s", msg)

def _log_ai(msg: str) -> None:
    logger.info("[AI] %s", msg)

def _log_err(msg: str) -> None:
    logger.error("[ERROR] %s", msg)


# ─────────────────────────────────────────────────────────────────────────────
# Config validation
# ─────────────────────────────────────────────────────────────────────────────

def _validate_config() -> None:
    """
    Check all required environment variables.
    Exits with a clear error — never prints credential values.
    """
    required = {
        "LIVEKIT_URL":           LIVEKIT_URL,
        "LIVEKIT_API_KEY":       LIVEKIT_API_KEY,
        "LIVEKIT_API_SECRET":    LIVEKIT_API_SECRET,
        "LIVEKIT_SIP_TRUNK_ID":  SIP_TRUNK_ID,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        for k in missing:
            _log_err(f"{k} is not set in backend/.env.local")
        print(
            "\nAdd the missing values to backend/.env.local:\n"
            "  LIVEKIT_SIP_TRUNK_ID=ST_xxxxxxxxxxxxxxxxxxxx\n"
            "\nAll other required keys (LIVEKIT_URL, LIVEKIT_API_KEY,\n"
            "LIVEKIT_API_SECRET) should already be present.\n",
            file=sys.stderr,
        )
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Destination normalisation
# ─────────────────────────────────────────────────────────────────────────────

def _normalise_destination(destination: str) -> str:
    """
    Normalise destination for LiveKit SIP Trunk API.

    LiveKit expects a phone number or SIP username (e.g. "dibyendu" or "+91XXXXXXXXXX"),
    not a full SIP URI like "sip:dibyendu@sip.linphone.org", because the domain is
    configured directly on the Outbound Trunk.

    Examples:
        "dibyendu@sip.linphone.org" → "dibyendu"
        "sip:dibyendu@sip.linphone.org" → "dibyendu"
        "dibyendu"                 → "dibyendu"
        "+91XXXXXXXXXX"            → "+91XXXXXXXXXX"
    """
    dest = destination.strip()
    if dest.startswith("sip:") or dest.startswith("sips:"):
        dest = dest.split(":", 1)[1]
    if "@" in dest:
        dest = dest.split("@", 1)[0]
    return dest


# ─────────────────────────────────────────────────────────────────────────────
# Async outbound call implementation
# ─────────────────────────────────────────────────────────────────────────────

async def _run_call(destination: str) -> None:
    """
    Core async implementation.  Called by make_outbound_call().

    Steps:
        1  Create a dedicated LiveKit room for this call.
        2  Dispatch the existing 'my-agent' (agent.py) to the room.
        3  Create a SIP participant — LiveKit dials out via the trunk.
        4  Poll participant state until ACTIVE (answered) or gone.
        5  Wait until the participant disconnects (call ended by either side).
        6  Delete the room.
    """
    try:
        from livekit import api  # already installed via livekit-agents
    except ImportError:
        _log_err(
            "livekit package not found — run:  uv run python src/agent.py  "
            "to ensure the venv is active, then retry."
        )
        sys.exit(1)

    destination_uri = _normalise_destination(destination)

    # Unique room name — keeps calls isolated from one another
    room_name            = f"outbound-{uuid.uuid4().hex[:10]}"
    participant_identity = destination_uri if destination_uri else f"sip-learner-{uuid.uuid4().hex[:6]}"

    _log_call(f"Initiating outbound call to {destination}")
    _log_call(f"Room: {room_name}  |  SIP URI: {destination_uri}")

    async with api.LiveKitAPI(
        url        = LIVEKIT_URL,
        api_key    = LIVEKIT_API_KEY,
        api_secret = LIVEKIT_API_SECRET,
    ) as lk:

        # ── Step 1: Create the room ───────────────────────────────────────────
        try:
            await lk.room.create_room(
                api.CreateRoomRequest(name=room_name)
            )
            _log_call(f"Room created: {room_name}")
        except Exception as exc:
            _log_err(f"Failed to create room: {exc}")
            return

        try:
            # ── Step 2: Dispatch the existing agent to this room ──────────────
            # The agent registered as AGENT_NAME ("my-agent") in agent.py will
            # connect to this room and run the full AI conversation pipeline.
            try:
                await lk.agent_dispatch.create_dispatch(
                    api.CreateAgentDispatchRequest(
                        agent_name = AGENT_NAME,
                        room       = room_name,
                    )
                )
                _log_ai(f"Agent '{AGENT_NAME}' dispatched to room {room_name}")
            except Exception as exc:
                # Non-fatal: the agent may auto-dispatch based on its config.
                # Log and continue — the call can still proceed.
                _log_call(
                    f"Agent dispatch returned: {exc}  "
                    f"(agent may auto-dispatch — continuing)"
                )

            # ── Step 3: Create SIP participant (outbound call) ────────────────
            _log_call("CALLING")
            try:
                sip_info = await lk.sip.create_sip_participant(
                    api.CreateSIPParticipantRequest(
                        sip_trunk_id         = SIP_TRUNK_ID,
                        sip_call_to          = destination_uri,
                        room_name            = room_name,
                        participant_identity = participant_identity,
                        participant_name     = "Learner",
                        play_ringtone        = True,   # plays ringtone in room while waiting
                        wait_until_answered  = False,  # don't block — we poll below
                    )
                )
                _log_call(f"RINGING — SIP participant created: {participant_identity}")
            except Exception as exc:
                _log_err(f"Failed to create SIP participant: {exc}")
                _log_call("FAILED")
                return

            # ── Step 4 & 5: Monitor call status ──────────────────────────────
            deadline  = time.monotonic() + SIP_CALL_TIMEOUT
            connected = False
            last_log  = ""

            _log_call("Waiting for learner to answer…")

            while True:
                await asyncio.sleep(_POLL_INTERVAL)

                # Check for timeout
                if not connected and time.monotonic() > deadline:
                    _log_call("NO_ANSWER — call timed out")
                    break

                # Poll participants in the room
                try:
                    resp = await lk.room.list_participants(
                        api.ListParticipantsRequest(room=room_name)
                    )
                except Exception as exc:
                    _log_err(f"Status poll error: {exc}")
                    continue

                # Find our SIP participant
                sip_p = next(
                    (p for p in resp.participants
                     if p.identity == participant_identity),
                    None,
                )

                if sip_p is None:
                    if connected:
                        _log_call("COMPLETED — learner disconnected")
                    else:
                        _log_call("NO_ANSWER — SIP participant left before answering")
                    break

                # Map numeric state to name and log transitions
                state_map = {0: "JOINING", 1: "JOINED", 2: "ACTIVE", 3: "DISCONNECTED"}
                state_name = state_map.get(sip_p.state, f"STATE_{sip_p.state}")

                if state_name != last_log:
                    last_log = state_name

                    if sip_p.state == 0:    # JOINING
                        _log_call("RINGING")
                    elif sip_p.state == 1:  # JOINED
                        _log_call("RINGING — joined room, waiting for media")
                    elif sip_p.state == 2:  # ACTIVE
                        if not connected:
                            connected = True
                            _log_call("CONNECTED")
                            _log_ai("Voice session started")
                            _log_ai(
                                f"Existing agent '{AGENT_NAME}' is handling "
                                "STT -> Gemini -> exercises -> Murf TTS"
                            )
                    elif sip_p.state == 3:  # DISCONNECTED
                        if connected:
                            _log_call("COMPLETED — call ended")
                        else:
                            _log_call("FAILED — disconnected before answering")
                        break

        finally:
            # ── Step 6: Clean up the room ─────────────────────────────────────
            _log_call("Cleaning up room…")
            try:
                await lk.room.delete_room(
                    api.DeleteRoomRequest(room=room_name)
                )
            except Exception:
                pass  # Room may already be gone
            _log_call("Cleanup complete")


# ─────────────────────────────────────────────────────────────────────────────
# Public entry-point
# ─────────────────────────────────────────────────────────────────────────────

def make_outbound_call(destination: str) -> None:
    """
    Make a real outbound SIP call via your LiveKit SIP Trunk.

    The existing AI agent (agent.py) handles the full conversation once the
    learner answers — no AI logic is duplicated in this file.

    Args:
        destination: Where to call.  Accepted formats:
            "alice@sip.linphone.org"   — SIP URI
            "+91XXXXXXXXXX"            — E.164 phone number (PSTN via trunk)
            "sip:alice@example.com"    — explicit SIP URI

    Example:
        make_outbound_call("alice@sip.linphone.org")
        make_outbound_call("+919876543210")
    """
    _validate_config()
    try:
        asyncio.run(_run_call(destination))
    except KeyboardInterrupt:
        _log_call("Interrupted by user — call terminated")


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry-point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "\nUsage:\n"
            "  uv run python src/outbound_call.py <destination>\n\n"
            "Examples:\n"
            "  uv run python src/outbound_call.py alice@sip.linphone.org\n"
            "  uv run python src/outbound_call.py +91XXXXXXXXXX\n"
            "  uv run python src/outbound_call.py sip:alice@sip.linphone.org\n\n"
            "Required in backend/.env.local:\n"
            "  LIVEKIT_SIP_TRUNK_ID=ST_xxxxxxxxxxxxxxxxxxxx\n"
            "  (LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET already set)\n",
            file=sys.stderr,
        )
        sys.exit(1)

    make_outbound_call(sys.argv[1])
