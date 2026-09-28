from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from interview_app.llm import LLMUnavailable
from interview_app.models import Interview, MessageRole
from interview_app.routers.interviews import load_interview
from interview_app.speech import SpeechClient, get_speech_client

router = APIRouter(tags=["voice"])

MAX_AUDIO_BYTES = 25 * 1024 * 1024
# Formats MediaRecorder produces in the browsers we support, and the file extension the
# transcription model reads the format from.
AUDIO_EXTENSIONS = {
    "audio/webm": "webm",
    "audio/ogg": "ogg",
    "audio/mp4": "m4a",
    "audio/x-m4a": "m4a",
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
}


@router.get("/interviews/{interview_id}/messages/{message_id}/speech")
def speak_message(
    message_id: int,
    interview: Interview = Depends(load_interview),
    speech: SpeechClient = Depends(get_speech_client),
) -> Response:
    """A Question or the Closing spoken in the Persona's voice. Generated on request, never stored."""
    message = next((m for m in interview.messages if m.id == message_id), None)
    if message is None or message.role == MessageRole.ANSWER:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No interviewer message with this id")
    try:
        audio = speech.speak(message.text, interview.persona_voice)
    except LLMUnavailable as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"Speech is unavailable: {exc}") from exc
    return Response(content=audio, media_type="audio/mpeg")


class Transcription(BaseModel):
    text: str


@router.post("/transcriptions", response_model=Transcription)
def transcribe(file: UploadFile = File(...), speech: SpeechClient = Depends(get_speech_client)) -> Transcription:
    """A spoken Answer as text, for the candidate to check before sending. The audio is not kept."""
    # "audio/webm;codecs=opus" -> "audio/webm"
    content_type = (file.content_type or "").split(";")[0].strip()
    extension = AUDIO_EXTENSIONS.get(content_type)
    if extension is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "This audio format is not supported.")
    audio = file.file.read(MAX_AUDIO_BYTES + 1)
    if len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "The recording is larger than 25 MB.")
    try:
        return Transcription(text=speech.transcribe(audio, f"answer.{extension}", content_type))
    except LLMUnavailable as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"Transcription is unavailable: {exc}") from exc
