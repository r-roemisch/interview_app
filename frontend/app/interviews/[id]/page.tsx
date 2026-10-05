"use client";

import {
  ArrowUp,
  ChevronDown,
  ClipboardCheck,
  Flag,
  Loader2,
  Mic,
  RotateCw,
  ShieldAlert,
  Square,
  Volume2,
  VolumeX,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError, speechUrl, type Interview, type Message } from "@/lib/api";
import { DIFFICULTY_OPTIONS, OFF_TOPIC_REMINDERS, SENIORITY_OPTIONS, STAR_PARTS } from "@/lib/labels";
import { toWav } from "@/lib/wav";
import { Button, cardClass, ErrorBanner, glassClass, Page, PersonaAvatar, Spinner, StarLetter } from "../../ui";

type EvaluationState = "polling" | "ready" | "missing";

// Plays one interviewer message, stopping whatever was playing. Any failure (network, 503,
// the browser blocking autoplay) is silent: the text is on screen and the replay button retries.
function play(audioRef: React.RefObject<HTMLAudioElement | null>, url: string) {
  audioRef.current?.pause();
  audioRef.current = new Audio(url);
  audioRef.current.play().catch(() => {});
}

// Interview page: the chat with the interviewer, plus a side panel with the Persona, the Job,
// the Question tracker and a STAR reminder. Also handles resuming an in-progress Interview
// and the hand-off to the Evaluation after the Closing.
export default function InterviewPage() {
  const { id } = useParams<{ id: string }>();
  const interviewId = Number(id);
  const router = useRouter();

  const [interview, setInterview] = useState<Interview | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  // The Answer being sent. Shown in the transcript until the reply arrives; on failure it
  // goes back into the Answer box, so nothing typed is lost.
  const [pending, setPending] = useState<string | null>(null);
  const [ending, setEnding] = useState(false);
  // The off-topic reminder after the last Answer sent (1 or 2), from the app, not the interviewer.
  // Never stored: a reload or the next accepted Answer clears it.
  const [reminder, setReminder] = useState<number | null>(null);
  // What failed last, so Retry repeats the right action.
  const [failed, setFailed] = useState<{ message: string; action?: "send" | "end" } | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationState>("polling");
  const [detailsOpen, setDetailsOpen] = useState(false);
  // Voice Interview: the audio playing now, which interviewer messages were already spoken
  // (null until the first load), and a mute switch that is not saved.
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const spokenRef = useRef<Set<number> | null>(null);
  const [muted, setMuted] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  // Bumping this counter re-runs the loading effect (used by the Retry button).
  const [reloadKey, setReloadKey] = useState(0);
  const reload = () => setReloadKey((k) => k + 1);

  useEffect(() => {
    let cancelled = false;
    api
      .getInterview(interviewId)
      .then((iv) => {
        if (cancelled) return;
        setInterview(iv);
        setLoadError(null);
      })
      .catch((e) => {
        if (cancelled) return;
        setLoadError(
          e instanceof ApiError && e.status === 404 ? "This interview does not exist." : "Could not load the interview.",
        );
      });
    return () => {
      cancelled = true;
    };
  }, [interviewId, reloadKey]);

  // Once the Interview has ended, poll for the Evaluation every 2 s until it exists or the Judge
  // failed (409). Any other failure, e.g. the backend restarting, is just tried again.
  // `evaluation` is a dependency so that "Re-run evaluation" starts polling again.
  const ended = interview !== null && interview.status !== "in_progress";
  useEffect(() => {
    if (!ended || evaluation !== "polling") return;
    let cancelled = false;
    const check = async () => {
      try {
        await api.getEvaluation(interviewId);
        if (!cancelled) setEvaluation("ready");
      } catch (e) {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 409) setEvaluation("missing");
        else timer = setTimeout(check, 2000);
      }
    };
    let timer = setTimeout(check, 500);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [ended, evaluation, interviewId]);

  // Speak each new Question and the Closing once, as it arrives.
  useEffect(() => {
    if (!interview?.voice_interview) return;
    const interviewerMessages = interview.messages.filter((m) => m.role !== "answer");
    if (spokenRef.current === null) {
      // First load: a fresh Interview speaks its first Question; a resumed one stays quiet.
      const fresh = !interview.messages.some((m) => m.role === "answer");
      spokenRef.current = new Set(fresh ? [] : interviewerMessages.map((m) => m.id));
    }
    const spoken = spokenRef.current;
    const unspoken = interviewerMessages.filter((m) => !spoken.has(m.id));
    unspoken.forEach((m) => spoken.add(m.id));
    const latest = unspoken.at(-1);
    if (latest && !muted) play(audioRef, speechUrl(interview.id, latest.id));
  }, [interview, muted]);

  // While the Portrait is being made, ask every 2 s whether it is ready. Only the Portrait state is
  // taken from the answer, so a slow poll can never overwrite a newer transcript.
  const portraitPending = interview?.portrait === "pending";
  useEffect(() => {
    if (!portraitPending) return;
    const timer = setInterval(() => {
      api
        .getInterview(interviewId)
        .then((iv) => setInterview((current) => current && { ...current, portrait: iv.portrait }))
        .catch(() => {}); // try again on the next tick
    }, 2000);
    return () => clearInterval(timer);
  }, [portraitPending, interviewId]);

  // Stop speaking when leaving the page.
  useEffect(() => () => audioRef.current?.pause(), []);

  function toggleMute() {
    if (!muted) audioRef.current?.pause();
    setMuted(!muted);
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [interview?.messages.length, pending, ending]);

  const busy = pending !== null || ending;

  async function send() {
    if (!interview || busy) return;
    const text = draft;
    setFailed(null);
    setPending(text);
    setDraft("");
    try {
      const updated = await api.submitAnswer(interview.id, text);
      setInterview(updated);
      const offTopic = updated.status === "in_progress" && updated.off_topic_count > interview.off_topic_count;
      setReminder(offTopic ? updated.off_topic_count : null);
      // The Answer was not kept: leave it in the box, so a wrongly blocked one can be edited and sent again.
      if (offTopic) setDraft(text);
    } catch (e) {
      setDraft(text);
      setFailed({ message: e instanceof ApiError ? e.message : "Could not send the answer.", action: "send" });
    } finally {
      setPending(null);
    }
  }

  async function endEarly({ confirmed = false } = {}) {
    if (!interview || busy) return;
    if (!confirmed && !window.confirm("End the interview now and get evaluated on the answers so far?")) return;
    setFailed(null);
    setEnding(true);
    try {
      setInterview(await api.endInterview(interview.id));
    } catch (e) {
      setFailed({ message: e instanceof ApiError ? e.message : "Could not end the interview.", action: "end" });
    } finally {
      setEnding(false);
    }
  }

  async function rerun() {
    if (!interview) return;
    setFailed(null);
    try {
      setInterview(await api.rerunEvaluation(interview.id));
      setEvaluation("polling");
    } catch (e) {
      setFailed({ message: e instanceof ApiError ? e.message : "Could not re-run the evaluation." });
    }
  }

  if (loadError)
    return (
      <Page title="Interview">
        <ErrorBanner message={loadError} onRetry={reload} />
      </Page>
    );
  if (!interview)
    return (
      <Page title="Interview">
        <Spinner label="Loading interview..." />
      </Page>
    );

  const answered = interview.messages.filter((m) => m.role === "answer").length + (pending !== null ? 1 : 0);
  const panel = (
    <Panel
      interview={interview}
      answered={answered}
      onEnd={() => endEarly()}
      endDisabled={busy || answered === 0}
      muted={muted}
      onToggleMute={toggleMute}
    />
  );

  return (
    <div className="flex h-full">
      {/* The interviewer sits on the left, like the other person in a video call (spec: portrait). */}
      <aside className={`hidden w-80 shrink-0 overflow-y-auto border-r border-zinc-200/70 p-5 lg:block dark:border-zinc-800/70 ${glassClass}`}>
        {panel}
      </aside>
      <section className="flex min-w-0 flex-1 flex-col">
        {/* Below lg the side panel folds into this strip; tapping it shows the full panel. */}
        <div className={`border-b border-zinc-200/70 px-4 py-2 lg:hidden dark:border-zinc-800/70 ${glassClass}`}>
          <button
            onClick={() => setDetailsOpen((o) => !o)}
            aria-expanded={detailsOpen}
            className="flex w-full items-center gap-3 text-left text-sm"
          >
            <PersonaAvatar name={interview.persona_name} size="sm" interviewId={interview.id} portrait={interview.portrait} />
            <span className="flex-1">
              <QuestionTracker interview={interview} answered={answered} compact />
            </span>
            <span className="sr-only">Interview details</span>
            <ChevronDown className={`h-4 w-4 text-zinc-400 transition-transform ${detailsOpen ? "rotate-180" : ""}`} />
          </button>
          {detailsOpen && <div className="pt-4 pb-2">{panel}</div>}
        </div>

        <div className="flex-1 overflow-y-auto">
          <ol className="mx-auto max-w-2xl space-y-6 px-4 py-8">
            {interview.messages.map((m) => (
              <Entry
                key={m.id}
                message={m}
                messages={interview.messages}
                personaName={interview.persona_name}
                onPlay={interview.voice_interview ? () => play(audioRef, speechUrl(interview.id, m.id)) : undefined}
              />
            ))}
            {reminder !== null && pending === null && (
              <li className="flex items-start gap-2 rounded-xl border border-amber-200/70 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-300">
                <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
                {OFF_TOPIC_REMINDERS[reminder - 1]}
              </li>
            )}
            {pending !== null && <AnswerBlock text={pending} dim />}
            {busy && (
              <li className="rounded-xl border border-dashed border-zinc-300 bg-white/50 px-4 py-4 dark:border-zinc-700 dark:bg-zinc-900/40">
                <ThinkingDots name={interview.persona_name} />
              </li>
            )}
          </ol>
          <div ref={bottomRef} />
        </div>

        <div className="mx-auto w-full max-w-2xl space-y-3 px-4 pb-4">
          {failed && (
            <ErrorBanner
              message={failed.message}
              onRetry={failed.action === "send" ? send : failed.action === "end" ? () => endEarly({ confirmed: true }) : undefined}
            />
          )}
          {interview.status === "in_progress" ? (
            <Composer
              draft={draft}
              setDraft={setDraft}
              onSend={send}
              busy={busy}
              personaName={interview.persona_name}
              // A transcription is added to whatever is already in the Answer box.
              onTranscript={interview.voice_interview ? (text) => setDraft((d) => (d.trim() ? `${d.trimEnd()} ${text}` : text)) : undefined}
              // Otherwise the mic records the interviewer's voice too.
              onRecordingStart={() => audioRef.current?.pause()}
            />
          ) : (
            <JudgingFooter
              state={evaluation}
              onOpen={() => router.push(`/interviews/${interview.id}/evaluation`)}
              onRerun={rerun}
            />
          )}
        </div>
      </section>

    </div>
  );
}

function Panel({
  interview,
  answered,
  onEnd,
  endDisabled,
  muted,
  onToggleMute,
}: {
  interview: Interview;
  answered: number;
  onEnd: () => void;
  endDisabled: boolean;
  muted: boolean;
  onToggleMute: () => void;
}) {
  const seniority = SENIORITY_OPTIONS.find((o) => o.value === interview.seniority)?.label;
  const difficulty = DIFFICULTY_OPTIONS.find((o) => o.value === interview.difficulty)?.label;
  return (
    <div className="space-y-7">
      <div>
        <PersonaAvatar name={interview.persona_name} size="panel" interviewId={interview.id} portrait={interview.portrait} />
        <p className="mt-3 font-semibold">{interview.persona_name}</p>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">{interview.persona_title}</p>
      </div>

      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
        <dt className="text-zinc-600 dark:text-zinc-400">Job</dt>
        <dd className="font-medium">{interview.title}</dd>
        {interview.industry && (
          <>
            <dt className="text-zinc-600 dark:text-zinc-400">Industry</dt>
            <dd>{interview.industry}</dd>
          </>
        )}
        <dt className="text-zinc-600 dark:text-zinc-400">Seniority</dt>
        <dd>{seniority}</dd>
        <dt className="text-zinc-600 dark:text-zinc-400">Difficulty</dt>
        <dd>{interview.demeanor === "rude" ? `${difficulty} · Rude` : difficulty}</dd>
      </dl>

      <QuestionTracker interview={interview} answered={answered} />

      <div>
        <p className="mb-2 text-sm font-medium">A strong answer covers</p>
        <ul className="space-y-2">
          {STAR_PARTS.map((part) => (
            <li key={part.key} className="flex gap-3 text-sm">
              <StarLetter letter={part.label[0]} />
              <span>
                <span className="font-medium">{part.label}</span>
                <span className="block text-zinc-600 dark:text-zinc-400">{part.hint}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>

      {interview.voice_interview && (
        <Button variant="secondary" onClick={onToggleMute} aria-pressed={muted} className="w-full">
          {muted ? <VolumeX className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5" />}
          {muted ? "Unmute interviewer" : "Mute interviewer"}
        </Button>
      )}

      {interview.status === "in_progress" && (
        <Button variant="secondary" onClick={onEnd} disabled={endDisabled} className="w-full">
          <Flag className="h-3.5 w-3.5" />
          End interview
        </Button>
      )}
    </div>
  );
}

// One segment per Question: answered ones filled, the open Question outlined, the rest empty.
function QuestionTracker({ interview, answered, compact = false }: { interview: Interview; answered: number; compact?: boolean }) {
  const cap = interview.question_cap;
  const open = interview.status === "in_progress";
  const summary = open
    ? `Question ${Math.min(answered + 1, cap)} of ${cap}`
    : interview.ended_early
      ? `Ended after ${answered}`
      : `${answered} of ${cap} answered`;
  return (
    <div>
      {!compact && (
        <p className="mb-2 flex justify-between text-sm">
          <span className="font-medium">Questions</span>
          <span className="tabular-nums text-zinc-600 dark:text-zinc-400">{summary}</span>
        </p>
      )}
      <div className="flex gap-1" role="img" aria-label={summary}>
        {Array.from({ length: cap }, (_, i) => (
          <span
            key={i}
            className={`h-1.5 flex-1 rounded-full ${
              i < answered
                ? "bg-indigo-600 dark:bg-indigo-400"
                : open && i === answered
                  ? "bg-indigo-200 ring-1 ring-indigo-500 dark:bg-indigo-500/30"
                  : "bg-zinc-200 dark:bg-zinc-800"
            }`}
          />
        ))}
      </div>
    </div>
  );
}

// Each Question is numbered, since the Interview really is a sequence of up to ten.
// In a Voice Interview, interviewer messages get a replay button (`onPlay`).
function Entry({
  message,
  messages,
  personaName,
  onPlay,
}: {
  message: Message;
  messages: Message[];
  personaName: string;
  onPlay?: () => void;
}) {
  if (message.role === "answer") return <AnswerBlock text={message.text} />;
  const replay = onPlay && (
    <button
      onClick={onPlay}
      aria-label="Play this message again"
      className="shrink-0 rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-indigo-600 focus-visible:outline-2 focus-visible:outline-indigo-500 dark:hover:bg-zinc-800"
    >
      <Volume2 className="h-4 w-4" />
    </button>
  );
  if (message.role === "closing") {
    return (
      <li className="flex gap-2 rounded-xl border border-indigo-200 bg-indigo-50/60 px-4 py-3 text-[15px] leading-relaxed dark:border-indigo-500/30 dark:bg-indigo-500/10">
        <div className="flex-1">
          <p className="mb-1 text-xs font-medium text-indigo-700 dark:text-indigo-300">Closing from {personaName}</p>
          {message.text}
        </div>
        {replay}
      </li>
    );
  }
  const number = messages.filter((m) => m.role === "question" && m.position <= message.position).length;
  return (
    <li className="flex gap-3">
      <span className="w-5 shrink-0 pt-1 text-right text-sm font-semibold tabular-nums text-indigo-600 dark:text-indigo-400">
        {number}
      </span>
      <p className="flex-1 whitespace-pre-wrap text-[17px] font-medium leading-relaxed">{message.text}</p>
      {replay}
    </li>
  );
}

function AnswerBlock({ text, dim = false }: { text: string; dim?: boolean }) {
  return (
    <li
      className={`ml-8 whitespace-pre-wrap rounded-xl px-4 py-3 text-[15px] leading-relaxed ${cardClass} ${dim ? "opacity-60" : ""}`}
    >
      {text || <em className="text-zinc-600 dark:text-zinc-400">(no answer given)</em>}
    </li>
  );
}

function ThinkingDots({ name }: { name: string }) {
  return (
    <span className="inline-flex items-center gap-1" role="status" aria-label={`${name} is thinking`}>
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          className="h-1.5 w-1.5 rounded-full bg-zinc-400 motion-safe:animate-bounce"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </span>
  );
}

function Composer({
  draft,
  setDraft,
  onSend,
  busy,
  personaName,
  onTranscript,
  onRecordingStart,
}: {
  draft: string;
  setDraft: (s: string) => void;
  onSend: () => void;
  busy: boolean;
  personaName: string;
  onTranscript?: (text: string) => void; // set in a Voice Interview: shows the mic button
  onRecordingStart: () => void;
}) {
  const recorder = useRecorder(onTranscript ?? (() => {}), onRecordingStart);
  // No sending mid-recording: the transcription would land in the next Answer's box.
  const sendBlocked = busy || recorder.state !== "idle";
  const hint = busy
    ? `${personaName} is reading your answer.`
    : recorder.state === "recording"
      ? `Recording ${formatSeconds(recorder.seconds)}. Click the square to stop.`
      : recorder.state === "transcribing"
        ? "Turning your recording into text..."
        : (recorder.error ?? "Ctrl+Enter to send");
  return (
    <div className="space-y-2">
      <div className="flex items-end gap-2 rounded-2xl border border-zinc-200 bg-white p-2 shadow-sm focus-within:border-indigo-400 focus-within:ring-4 focus-within:ring-indigo-500/10 dark:border-zinc-800 dark:bg-zinc-900/60">
        <textarea
          aria-label="Your answer"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              if (!sendBlocked) onSend();
            }
          }}
          disabled={busy}
          maxLength={10000}
          rows={2}
          placeholder="Describe the situation, what you did, and the result."
          className="max-h-48 min-h-12 flex-1 resize-none bg-transparent px-2 py-1.5 text-[15px] leading-relaxed outline-none field-sizing-content placeholder:text-zinc-400 disabled:opacity-50 dark:placeholder:text-zinc-500"
        />
        {onTranscript && (
          <button
            aria-label={recorder.state === "recording" ? "Stop recording" : "Start recording"}
            onClick={recorder.state === "recording" ? recorder.stop : recorder.start}
            disabled={busy || recorder.state === "transcribing"}
            className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-500 disabled:cursor-not-allowed disabled:opacity-50 ${
              recorder.state === "recording"
                ? "bg-red-600 text-white hover:bg-red-500"
                : "border border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
            }`}
          >
            {recorder.state === "recording" ? (
              <Square className="h-3.5 w-3.5 fill-current" />
            ) : recorder.state === "transcribing" ? (
              <Loader2 className="h-4 w-4 motion-safe:animate-spin" />
            ) : (
              <Mic className="h-4 w-4" />
            )}
          </button>
        )}
        {/* Enabled even when empty: an empty Answer is still an Answer (spec). */}
        <button
          aria-label="Send answer"
          onClick={onSend}
          disabled={sendBlocked}
          className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white hover:bg-indigo-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-500 disabled:cursor-not-allowed disabled:bg-zinc-200 disabled:text-zinc-400 dark:disabled:bg-zinc-800 dark:disabled:text-zinc-600"
        >
          <ArrowUp className="h-4 w-4" />
        </button>
      </div>
      <p className={`px-2 text-xs ${recorder.error && !busy && recorder.state === "idle" ? "text-red-600 dark:text-red-400" : "text-zinc-600 dark:text-zinc-400"}`}>{hint}</p>
    </div>
  );
}

function JudgingFooter({
  state,
  onOpen,
  onRerun,
}: {
  state: EvaluationState;
  onOpen: () => void;
  onRerun: () => void;
}) {
  return (
    <div className={`flex flex-wrap items-center gap-3 rounded-2xl px-4 py-3 ${cardClass}`}>
      <span className="flex-1 text-sm text-zinc-600 dark:text-zinc-400">
        {state === "polling" && <Spinner label="Interview finished. The judge is scoring your answers." />}
        {state === "ready" && "Interview finished. Your evaluation is ready."}
        {state === "missing" && <span className="text-red-700 dark:text-red-400">The evaluation could not be produced.</span>}
      </span>
      {state === "missing" ? (
        <Button onClick={onRerun}>
          <RotateCw className="h-4 w-4" />
          Re-run evaluation
        </Button>
      ) : (
        <Button onClick={onOpen} disabled={state !== "ready"}>
          <ClipboardCheck className="h-4 w-4" />
          See evaluation
        </Button>
      )}
    </div>
  );
}

const MAX_RECORDING_SECONDS = 5 * 60;

function formatSeconds(total: number): string {
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}

// Voice Interview: record an Answer in the browser, then have the backend transcribe it.
// The text goes into the Answer box for the candidate to check; nothing is sent automatically.
function useRecorder(onTranscript: (text: string) => void, onStart: () => void) {
  const [state, setState] = useState<"idle" | "recording" | "transcribing">("idle");
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);

  async function start() {
    setError(null);
    let stream: MediaStream;
    try {
      // The browser asks for microphone permission the first time. http://localhost counts as a
      // secure origin, so this works without HTTPS.
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError("No microphone access. Allow it in the browser, or type your answer.");
      return;
    }
    // Chrome and Firefox record webm, older Safari only mp4: use the first one this browser supports.
    const mimeType = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"].find((t) => MediaRecorder.isTypeSupported(t));
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    const chunks: Blob[] = [];
    recorder.ondataavailable = (e) => chunks.push(e.data);
    // Runs after stop(): release the mic, then convert the recording to WAV and send it for transcription.
    recorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop()); // also turns off the browser's recording indicator
      recorderRef.current = null;
      setState("transcribing");
      try {
        const { text } = await api.transcribe(await toWav(new Blob(chunks, { type: recorder.mimeType })));
        if (text) onTranscript(text);
      } catch (e) {
        setError(e instanceof ApiError ? e.message : "Could not transcribe the recording. Record again or type.");
      } finally {
        setState("idle");
      }
    };
    onStart();
    recorder.start();
    recorderRef.current = recorder;
    setSeconds(0);
    setState("recording");
  }

  function stop() {
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
  }

  // Count the seconds while recording, and stop by itself at the limit.
  useEffect(() => {
    if (state !== "recording") return;
    let elapsed = 0;
    const timer = setInterval(() => {
      elapsed += 1;
      setSeconds(elapsed);
      if (elapsed >= MAX_RECORDING_SECONDS && recorderRef.current?.state === "recording") recorderRef.current.stop();
    }, 1000);
    return () => clearInterval(timer);
  }, [state]);

  // Leaving the page mid-recording: drop the recording and release the mic.
  useEffect(
    () => () => {
      const recorder = recorderRef.current;
      if (recorder?.state === "recording") {
        recorder.onstop = null;
        recorder.stop();
        recorder.stream.getTracks().forEach((t) => t.stop());
      }
    },
    [],
  );

  return { state, seconds, error, start, stop };
}
