# Speech goes through the backend and OpenRouter, not the browser's speech APIs

In a Voice Interview, the browser records the Answer and sends it to FastAPI, which asks OpenRouter to transcribe it. Questions and the Closing are turned into speech the same way. The browser's built-in Web Speech API and `speechSynthesis` would be free, but speech recognition does not work in Firefox and sends audio to Google, and the built-in voices sound robotic on most systems. Going through OpenRouter keeps every model call behind the same key, error handling and fake provider (ADR-0001: secrets and model calls live in FastAPI only), works in every browser and gives each Persona a natural voice, at the cost of a few cents per Interview, about 1-2 s before each Question is spoken, and two more models on the OpenRouter allow-list.

## Consequences

- No live text while speaking: the Answer is transcribed after recording stops, then edited and sent by the candidate.
- No audio is stored; speech is generated on request and transcriptions become ordinary text Answers.
- Which models do the speaking and transcribing: ADR-0005.
