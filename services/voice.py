"""Voice service for OpenAI Realtime API integration."""

import asyncio
import base64
import json
import os

import websockets
from dotenv import load_dotenv

from models.criteria import CriterionEvidence
from services.challenger import O1A_CRITERIA_DETAILS

load_dotenv()

OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime"
OPENAI_REALTIME_MODEL = "gpt-4o-realtime-preview-2024-12-17"


def build_system_prompt(criterion: CriterionEvidence, resume_text: str) -> str:
    """Build the system prompt for voice challenge session."""
    status = "MET" if criterion.met else "NOT MET"
    details = O1A_CRITERIA_DETAILS.get(criterion.name, {})
    regulatory_language = details.get("regulatory_language", criterion.description)

    return f"""You are a friendly O-1A visa advisor having a voice conversation. Keep responses SHORT and conversational (2-3 sentences max).

CRITERION: "{criterion.name}"
USCIS DEFINITION: "{regulatory_language}"

CURRENT STATUS: {status}
REASONING: {criterion.reasoning}

RESUME CONTEXT (first 1500 chars):
{resume_text[:1500]}

YOUR ROLE:
- Have a natural voice conversation about this O-1A criterion
- Explain what evidence would help in plain English
- Ask clarifying questions one at a time
- Be encouraging but honest about what qualifies
- When they share relevant evidence, acknowledge it and dig deeper for specifics
- Keep responses brief - this is a voice conversation, not a lecture

CONVERSATION STYLE:
- Warm, casual, like talking to a knowledgeable friend
- Use natural speech patterns (contractions, filler words are OK)
- Respond directly to what the user says
- Ask ONE follow-up question at a time"""


async def create_realtime_session(
    criterion: CriterionEvidence,
    resume_text: str,
    client_ws,
):
    """
    Create a bridge between the browser client and OpenAI Realtime API.

    Args:
        criterion: The O-1A criterion being challenged
        resume_text: Raw text from the parsed resume
        client_ws: The WebSocket connection to the browser client
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        await client_ws.send_json(
            {"type": "error", "message": "OpenAI API key not configured"}
        )
        return

    url = f"{OPENAI_REALTIME_URL}?model={OPENAI_REALTIME_MODEL}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "realtime=v1",
    }

    system_prompt = build_system_prompt(criterion, resume_text)

    try:
        async with websockets.connect(url, additional_headers=headers) as openai_ws:
            # Configure the session
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": system_prompt,
                    "voice": "alloy",
                    "output_audio_format": "pcm16",
                    "speed": 1.2,
                    "input_audio_format": "pcm16",
                    "input_audio_transcription": {"model": "whisper-1"},
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500,
                    },
                },
            }
            await openai_ws.send(json.dumps(session_config))

            # Notify client that session is ready
            await client_ws.send_json({"type": "session.ready"})

            # Create tasks for bidirectional communication
            async def forward_to_openai():
                """Forward messages from browser to OpenAI."""
                try:
                    async for message in client_ws.iter_json():
                        if message.get("type") == "audio":
                            # Forward audio data to OpenAI
                            audio_event = {
                                "type": "input_audio_buffer.append",
                                "audio": message.get("audio"),  # base64 encoded PCM16
                            }
                            await openai_ws.send(json.dumps(audio_event))
                        elif message.get("type") == "audio.commit":
                            # Commit the audio buffer
                            await openai_ws.send(
                                json.dumps({"type": "input_audio_buffer.commit"})
                            )
                        elif message.get("type") == "response.create":
                            # Request a response
                            await openai_ws.send(
                                json.dumps({"type": "response.create"})
                            )
                        elif message.get("type") == "response.cancel":
                            # Cancel current response (barge-in)
                            await openai_ws.send(
                                json.dumps({"type": "response.cancel"})
                            )
                        elif message.get("type") == "session.update":
                            # Update session settings (e.g., speed)
                            await openai_ws.send(
                                json.dumps(
                                    {
                                        "type": "session.update",
                                        "session": message.get("session", {}),
                                    }
                                )
                            )
                        elif message.get("type") == "close":
                            break
                except Exception as e:
                    print(f"Error forwarding to OpenAI: {e}")

            async def forward_to_client():
                """Forward messages from OpenAI to browser."""
                try:
                    async for message in openai_ws:
                        data = json.loads(message)
                        event_type = data.get("type", "")

                        # Forward relevant events to client
                        if event_type == "response.audio.delta":
                            # Audio chunk from assistant
                            await client_ws.send_json(
                                {
                                    "type": "audio.delta",
                                    "audio": data.get("delta", ""),
                                }
                            )
                        elif event_type == "response.audio.done":
                            await client_ws.send_json({"type": "audio.done"})
                        elif event_type == "response.audio_transcript.delta":
                            # Transcript of assistant's speech
                            await client_ws.send_json(
                                {
                                    "type": "transcript.delta",
                                    "role": "assistant",
                                    "delta": data.get("delta", ""),
                                }
                            )
                        elif event_type == "response.audio_transcript.done":
                            await client_ws.send_json(
                                {
                                    "type": "transcript.done",
                                    "role": "assistant",
                                    "transcript": data.get("transcript", ""),
                                }
                            )
                        elif (
                            event_type
                            == "conversation.item.input_audio_transcription.completed"
                        ):
                            # Transcript of user's speech
                            await client_ws.send_json(
                                {
                                    "type": "transcript.done",
                                    "role": "user",
                                    "transcript": data.get("transcript", ""),
                                }
                            )
                        elif event_type == "response.done":
                            await client_ws.send_json({"type": "response.done"})
                        elif event_type == "error":
                            error_message = data.get("error", {}).get(
                                "message", "Unknown error"
                            )
                            # Ignore benign cancellation error (happens during barge-in when no response is active)
                            if "no active response" not in error_message.lower():
                                await client_ws.send_json(
                                    {
                                        "type": "error",
                                        "message": error_message,
                                    }
                                )
                        elif event_type == "session.created":
                            await client_ws.send_json({"type": "session.created"})
                        elif event_type == "session.updated":
                            await client_ws.send_json({"type": "session.updated"})
                        elif event_type == "input_audio_buffer.speech_started":
                            await client_ws.send_json({"type": "speech.started"})
                        elif event_type == "input_audio_buffer.speech_stopped":
                            await client_ws.send_json({"type": "speech.stopped"})

                except Exception as e:
                    print(f"Error forwarding to client: {e}")

            # Run both tasks concurrently
            await asyncio.gather(
                forward_to_openai(),
                forward_to_client(),
                return_exceptions=True,
            )

    except websockets.exceptions.InvalidStatusCode as e:
        await client_ws.send_json(
            {
                "type": "error",
                "message": f"Failed to connect to OpenAI: {e}",
            }
        )
    except Exception as e:
        await client_ws.send_json(
            {
                "type": "error",
                "message": f"Voice session error: {str(e)}",
            }
        )
