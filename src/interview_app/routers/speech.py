from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from interview_app.llm import LLMUnavailable
from interview_app.models import Interview, MessageRole
from interview_app.routers.interviews import load_interview
from interview_app.speech import SpeechClient, get_speech_client

router = APIRouter(tags=["voice"])

MAX_AUDIO_BYTES = 25 * 1024 * 1024
# The formats the audio model reads. Browsers record webm or mp4, which it does not, so the
# frontend converts every recording to WAV before sending it (ADR-0005).
AUDIO_FORMATS = {
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/wave": "wav",
    "audio/mpeg": "mp3",
}


def _looks_like(audio_format: str, audio: bytes) -> bool:
    """The file's first bytes must match the declared type, not just the header the browser sent."""
    if audio_format == "wav":
        return audio[:4] == b"RIFF" and audio[8:12] == b"WAVE"
    # MP3: an ID3 tag, or straight into an MPEG frame (11 sync bits set).
    return audio[:3] == b"ID3" or (len(audio) > 1 and audio[0] == 0xFF and audio[1] & 0xE0 == 0xE0)


@router.get("/interviews/{interview_id}/messages/{message_id}/speech")
def speak_message(
    message_id: int,
    interview: Interview = Depends(load_interview),
    speech: SpeechClient = Depends(get_speech_client),
) -> Response:
    """A Question or the Closing spoken in the Persona's voice. Generated on request, never stored."""
    message = next((m for m in interview.messages if m.id == message_id), None)
    # Only a Voice Interview is spoken: nothing else may cause a paid speech call (spec: C4).
    if not interview.voice_interview or message is None or message.role == MessageRole.ANSWER:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No interviewer message with this id")
    try:
        audio = speech.speak(message.text, interview.persona_voice)
    except LLMUnavailable as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"Speech is unavailable: {exc}") from exc
    return Response(content=audio, media_type="audio/wav")


class Transcription(BaseModel):
    text: str


@router.post("/transcriptions", response_model=Transcription)
def transcribe(file: UploadFile = File(...), speech: SpeechClient = Depends(get_speech_client)) -> Transcription:
    """A spoken Answer as text, for the candidate to check before sending. The audio is not kept."""
    # "audio/wav;codecs=1" -> "audio/wav"
    audio_format = AUDIO_FORMATS.get((file.content_type or "").split(";")[0].strip())
    if audio_format is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "This audio format is not supported.")
    audio = file.file.read(MAX_AUDIO_BYTES + 1)
    if len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "The recording is larger than 25 MB.")
    if not _looks_like(audio_format, audio):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "This audio format is not supported.")
    try:
        return Transcription(text=speech.transcribe(audio, audio_format))
    except LLMUnavailable as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"Transcription is unavailable: {exc}") from exc
