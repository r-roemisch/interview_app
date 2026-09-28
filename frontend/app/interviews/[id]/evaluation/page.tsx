"use client";

import { History, RotateCcw, RotateCw, Scale } from "lucide-react";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError, type Evaluation, type Interview, type Message, type StarBreakdown, type Verdict } from "@/lib/api";
import { DIFFICULTY_OPTIONS, SENIORITY_OPTIONS, STAR_PARTS, VERDICT_LABEL } from "@/lib/labels";
import { Button, ErrorBanner, LinkButton, Page, PersonaAvatar, Spinner, StarLetter } from "../../../ui";

const VERDICT_STYLE: Record<Verdict, string> = {
  strong_hire: "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-500/15 dark:text-emerald-300 dark:ring-emerald-500/30",
  hire: "bg-indigo-50 text-indigo-700 ring-indigo-200 dark:bg-indigo-500/15 dark:text-indigo-300 dark:ring-indigo-500/30",
  no_hire: "bg-red-50 text-red-700 ring-red-200 dark:bg-red-500/15 dark:text-red-300 dark:ring-red-500/30",
};

// Evaluation page: the Judge's score and verdict, improvement points, and the transcript
// with each STAR Breakdown under its Answer.
export default function EvaluationPage() {
  const { id } = useParams<{ id: string }>();
  const interviewId = Number(id);
  const router = useRouter();

  const [interview, setInterview] = useState<Interview | null>(null);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [state, setState] = useState<"loading" | "judging" | "missing" | "ready" | "error">("loading");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  // Bumping this counter re-runs the loading effect: the Retry button does it immediately,
  // and the polling effect below does it every 2 s while the Judge is still running.
  const [reloadKey, setReloadKey] = useState(0);
  const reload = () => setReloadKey((k) => k + 1);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const iv = await api.getInterview(interviewId);
      if (cancelled) return;
      setInterview(iv);
      setError(null);
      if (iv.status === "in_progress") {
        router.replace(`/interviews/${interviewId}`);
        return;
      }
      try {
        const ev = await api.getEvaluation(interviewId);
        if (cancelled) return;
        setEvaluation(ev);
        setState("ready");
      } catch (e) {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 404) setState("judging");
        else if (e instanceof ApiError && e.status === 409) setState("missing");
        else throw e;
      }
    };
    load().catch((e) => {
      if (cancelled) return;
      setState("error");
      setError(e instanceof ApiError ? e.message : "Could not load the evaluation.");
    });
    return () => {
      cancelled = true;
    };
  }, [interviewId, reloadKey, router]);

  useEffect(() => {
    if (state !== "judging") return;
    const timer = setTimeout(reload, 2000);
    return () => clearTimeout(timer);
  }, [state, reloadKey]);

  async function rerun() {
    setBusy(true);
    try {
      await api.rerunEvaluation(interviewId);
      setState("judging");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not re-run the evaluation.");
    } finally {
      setBusy(false);
    }
  }

  async function practiceAgain() {
    setBusy(true);
    try {
      const next = await api.practiceAgain(interviewId);
      router.push(`/interviews/${next.id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not start a new interview.");
      setBusy(false);
    }
  }

  if (state === "loading")
    return (
      <Page title="Evaluation">
        <Spinner label="Loading..." />
      </Page>
    );
  if (state === "error")
    return (
      <Page title="Evaluation">
        <ErrorBanner message={error ?? "Something went wrong."} onRetry={reload} />
      </Page>
    );
  if (!interview) return null;

  const chips = [
    SENIORITY_OPTIONS.find((o) => o.value === interview.seniority)?.label,
    `${DIFFICULTY_OPTIONS.find((o) => o.value === interview.difficulty)?.label} difficulty`,
    interview.industry,
    interview.ended_early ? "Ended early" : null,
  ].filter(Boolean) as string[];

  return (
    <Page
      title={interview.title}
      intro={
        <span className="flex flex-wrap gap-1.5">
          {chips.map((chip) => (
            <span key={chip} className="rounded-md bg-zinc-100 px-1.5 py-0.5 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
              {chip}
            </span>
          ))}
        </span>
      }
    >
      <div className="space-y-10">
        {error && <ErrorBanner message={error} />}

        {state === "judging" && (
          <div className="rounded-2xl border border-zinc-200 px-5 py-6 dark:border-zinc-800">
            <Spinner label="The judge is scoring your answers..." />
          </div>
        )}

        {state === "missing" && (
          <div className="space-y-3">
            <ErrorBanner message="The evaluation could not be produced. You can ask the judge to try again." />
            <Button onClick={rerun} disabled={busy}>
              <RotateCw className="h-4 w-4" />
              Re-run evaluation
            </Button>
          </div>
        )}

        {state === "ready" && evaluation && (
          <>
            <ScoreCard evaluation={evaluation} />

            <section>
              <h2 className="mb-3 text-lg font-semibold">Improve next time</h2>
              <ul className="space-y-2">
                {evaluation.improvement_points.map((p, i) => (
                  <li key={i} className="flex gap-3 rounded-xl border border-zinc-200 px-4 py-3 text-[15px] leading-relaxed dark:border-zinc-800">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-indigo-500" />
                    {p}
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <div className="mb-5 flex items-center gap-3">
                <PersonaAvatar name={interview.persona_name} />
                <div>
                  <h2 className="text-lg font-semibold">Transcript and STAR breakdown</h2>
                  <p className="text-sm text-zinc-500">
                    Questions asked by {interview.persona_name}, {interview.persona_title}
                  </p>
                </div>
              </div>
              <Transcript messages={interview.messages} breakdowns={evaluation.star_breakdowns} personaName={interview.persona_name} />
            </section>
          </>
        )}

        <footer className="flex flex-wrap items-center gap-3 border-t border-zinc-200 pt-6 dark:border-zinc-800">
          <Button onClick={practiceAgain} disabled={busy}>
            <RotateCcw className="h-4 w-4" />
            Practice this job again
          </Button>
          <LinkButton href="/history">
            <History className="h-4 w-4" />
            Back to history
          </LinkButton>
          {busy && <Spinner label="Starting a new interview..." />}
        </footer>
      </div>
    </Page>
  );
}

// The Evaluation comes from the Judge, never from the Persona (ADR-0002).
function ScoreCard({ evaluation }: { evaluation: Evaluation }) {
  return (
    <section className="grid gap-6 rounded-2xl border border-zinc-200 bg-zinc-50/60 p-6 sm:grid-cols-[auto_1fr] dark:border-zinc-800 dark:bg-zinc-900/40">
      <div className="flex items-center gap-4 sm:flex-col sm:items-start">
        <p className="leading-none">
          <span className="text-6xl font-semibold tracking-tight tabular-nums">{evaluation.overall_score}</span>
          <span className="ml-1 text-lg text-zinc-400">/100</span>
        </p>
        <span className={`rounded-full px-2.5 py-1 text-sm font-medium ring-1 ${VERDICT_STYLE[evaluation.verdict]}`}>
          {VERDICT_LABEL[evaluation.verdict]}
        </span>
      </div>
      <div>
        <p className="mb-2 flex items-center gap-1.5 text-sm font-medium text-zinc-500">
          <Scale className="h-4 w-4" />
          Judge
        </p>
        <p className="text-[15px] leading-relaxed">{evaluation.justification}</p>
      </div>
    </section>
  );
}

function Transcript({
  messages,
  breakdowns,
  personaName,
}: {
  messages: Message[];
  breakdowns: StarBreakdown[];
  personaName: string;
}) {
  const byPosition = new Map(breakdowns.map((b) => [b.position, b]));
  // Question number by message id, worked out before rendering.
  const questionNumber = new Map(messages.filter((m) => m.role === "question").map((m, i) => [m.id, i + 1]));
  return (
    <ol className="space-y-6">
      {messages.map((m) => {
        if (m.role === "closing") {
          return (
            <li key={m.id} className="rounded-xl border border-indigo-200 bg-indigo-50/60 px-4 py-3 text-[15px] leading-relaxed dark:border-indigo-500/30 dark:bg-indigo-500/10">
              <p className="mb-1 text-xs font-medium text-indigo-700 dark:text-indigo-300">Closing from {personaName}</p>
              {m.text}
            </li>
          );
        }
        if (m.role === "question") {
          return (
            <li key={m.id} className="flex gap-3">
              <span className="w-5 shrink-0 pt-0.5 text-right text-sm font-semibold tabular-nums text-indigo-600 dark:text-indigo-400">
                {questionNumber.get(m.id)}
              </span>
              <p className="whitespace-pre-wrap font-medium leading-relaxed">{m.text}</p>
            </li>
          );
        }
        const breakdown = byPosition.get(m.position);
        return (
          <li key={m.id} className="ml-8 overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
            <p className="whitespace-pre-wrap bg-zinc-100 px-4 py-3 text-[15px] leading-relaxed dark:bg-zinc-800/80">
              {m.text || <em className="text-zinc-500">(no answer given)</em>}
            </p>
            {breakdown && <StarRows breakdown={breakdown} />}
          </li>
        );
      })}
    </ol>
  );
}

function StarRows({ breakdown }: { breakdown: StarBreakdown }) {
  return (
    <ul className="divide-y divide-zinc-100 text-sm dark:divide-zinc-800">
      {STAR_PARTS.map((part) => {
        const r = breakdown[part.key];
        return (
          <li key={part.key} className="grid grid-cols-[auto_1fr] items-start gap-x-3 gap-y-1 px-4 py-2.5 sm:grid-cols-[auto_7rem_1fr]">
            <StarLetter letter={part.label[0]} />
            <span className="flex items-center gap-2 pt-1">
              <span className="font-medium sm:hidden">{part.label}</span>
              <RatingBar rating={r.rating} label={part.label} />
            </span>
            <span className="col-start-2 text-zinc-600 sm:col-start-3 sm:pt-0.5 dark:text-zinc-400">{r.comment}</span>
          </li>
        );
      })}
    </ul>
  );
}

function RatingBar({ rating, label }: { rating: number; label: string }) {
  return (
    <span className="flex gap-0.5" role="img" aria-label={`${label}: ${rating} out of 5`}>
      {Array.from({ length: 5 }, (_, i) => (
        <span key={i} className={`h-1.5 w-4 rounded-full ${i < rating ? "bg-indigo-600 dark:bg-indigo-400" : "bg-zinc-200 dark:bg-zinc-700"}`} />
      ))}
    </span>
  );
}
