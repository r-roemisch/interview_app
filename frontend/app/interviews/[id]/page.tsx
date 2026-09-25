"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError, type Interview, type Message } from "@/lib/api";
import { Button, ErrorBanner, inputClass, Spinner } from "../../ui";

type EvaluationState = "polling" | "ready" | "missing";

// Interview page: the chat with the interviewer. Also handles resuming an in-progress Interview
// and the hand-off to the Evaluation after the Closing.
export default function InterviewPage() {
  const { id } = useParams<{ id: string }>();
  const interviewId = Number(id);
  const router = useRouter();

  const [interview, setInterview] = useState<Interview | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  // Polling starts as soon as the Interview has ended (see the effect below).
  const [evaluation, setEvaluation] = useState<EvaluationState>("polling");
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

  // Once the Interview has ended, poll for the Evaluation every 2 s until it exists or the Judge failed.
  const ended = interview !== null && interview.status !== "in_progress";
  useEffect(() => {
    if (!ended) return;
    let cancelled = false;
    const check = async () => {
      try {
        await api.getEvaluation(interviewId);
        if (!cancelled) setEvaluation("ready");
      } catch (e) {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 409) setEvaluation("missing");
        else if (e instanceof ApiError && e.status === 404) timer = setTimeout(check, 2000);
        else setEvaluation("missing");
      }
    };
    let timer = setTimeout(check, 500);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [ended, interviewId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [interview?.messages.length]);

  async function send() {
    if (!interview) return;
    setSendError(null);
    setSending(true);
    try {
      const updated = await api.submitAnswer(interview.id, draft);
      setInterview(updated);
      setDraft(""); // only cleared on success, so a failed send keeps the typed text
    } catch (e) {
      setSendError(e instanceof ApiError ? e.message : "Could not send the answer.");
    } finally {
      setSending(false);
    }
  }

  async function endEarly() {
    if (!interview || !window.confirm("End the interview now and get evaluated on the answers so far?")) return;
    setSendError(null);
    setSending(true);
    try {
      setInterview(await api.endInterview(interview.id));
    } catch (e) {
      setSendError(e instanceof ApiError ? e.message : "Could not end the interview.");
    } finally {
      setSending(false);
    }
  }

  async function rerun() {
    if (!interview) return;
    try {
      setInterview(await api.rerunEvaluation(interview.id));
      setEvaluation("polling");
    } catch (e) {
      setSendError(e instanceof ApiError ? e.message : "Could not re-run the evaluation.");
    }
  }

  if (loadError) return <ErrorBanner message={loadError} onRetry={reload} />;
  if (!interview) return <Spinner label="Loading interview..." />;

  const answered = interview.messages.filter((m) => m.role === "answer").length;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">{interview.title}</h1>
          <p className="text-sm text-zinc-500">
            {interview.seniority} level · {interview.difficulty} difficulty
            {interview.industry ? ` · ${interview.industry}` : ""}
          </p>
        </div>
        <span className="text-sm text-zinc-500">
          Question {Math.min(interview.question_count, interview.question_cap)} of {interview.question_cap}
        </span>
      </header>

      <ol className="space-y-3">
        {interview.messages.map((m) => (
          <ChatBubble key={m.id} message={m} />
        ))}
        <div ref={bottomRef} />
      </ol>

      {sendError && <ErrorBanner message={sendError} onRetry={interview.status === "in_progress" ? send : undefined} />}

      {interview.status === "in_progress" ? (
        <div className="space-y-3">
          <textarea
            className={`${inputClass} min-h-28`}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Type your answer. Situation, Task, Action, Result."
            disabled={sending}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) void send();
            }}
          />
          <div className="flex items-center gap-3">
            <Button onClick={send} disabled={sending}>
              Send
            </Button>
            <Button variant="secondary" onClick={endEarly} disabled={sending || answered === 0}>
              End interview
            </Button>
            {sending && <Spinner label="The interviewer is thinking..." />}
            <span className="ml-auto text-xs text-zinc-400">Ctrl+Enter to send</span>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-3">
          {evaluation === "missing" ? (
            <Button onClick={rerun}>Re-run evaluation</Button>
          ) : (
            <Button onClick={() => router.push(`/interviews/${interview.id}/evaluation`)} disabled={evaluation !== "ready"}>
              See evaluation
            </Button>
          )}
          {evaluation === "polling" && <Spinner label="The judge is reviewing your answers..." />}
          {evaluation === "missing" && (
            <span className="text-sm text-red-700 dark:text-red-400">The evaluation could not be produced.</span>
          )}
        </div>
      )}
    </div>
  );
}

function ChatBubble({ message }: { message: Message }) {
  const mine = message.role === "answer";
  const style = mine
    ? "ml-auto bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
    : message.role === "closing"
      ? "bg-amber-50 dark:bg-amber-950"
      : "bg-zinc-100 dark:bg-zinc-800";
  return (
    <li className={`max-w-[85%] whitespace-pre-wrap rounded-lg px-4 py-2 text-sm ${style}`}>
      {message.text || <em className="opacity-60">(no answer given)</em>}
    </li>
  );
}
