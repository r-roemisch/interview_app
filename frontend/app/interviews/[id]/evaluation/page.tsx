"use client";

import { History, RotateCcw, RotateCw, Scale, Scale3d } from "lucide-react";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError, type Evaluation, type Interview, type Judge, type Message, type StarBreakdown, type Verdict } from "@/lib/api";
import {
  confidenceLevel,
  DIFFICULTY_OPTIONS,
  JEV_EXPLANATION,
  JUDGE_LABEL,
  SENIORITY_OPTIONS,
  STAR_PARTS,
  VERDICT_LABEL,
} from "@/lib/labels";
import { Button, cardClass, ErrorBanner, LinkButton, Page, PersonaAvatar, Spinner, StarLetter } from "../../../ui";

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
  // The other Judge's Evaluation, once it has been run for the comparison.
  const [other, setOther] = useState<Evaluation | null>(null);
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
        const all = await api.listEvaluations(interviewId);
        if (cancelled) return;
        setEvaluation(ev);
        setOther(all.find((e) => e.judge !== iv.judge) ?? null);
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
    // Only Rude is worth a chip: Friendly is the default (spec: rude-interviewer).
    interview.demeanor === "rude" ? "Rude interviewer" : null,
    interview.industry,
    interview.ended_early ? "Ended early" : null,
  ].filter(Boolean) as string[];

  return (
    <Page
      title={interview.title}
      intro={
        <span className="flex flex-wrap gap-1.5">
          {chips.map((chip) => (
            <span key={chip} className="rounded-md bg-white/70 px-1.5 py-0.5 text-xs text-zinc-600 ring-1 ring-zinc-200/70 dark:bg-zinc-800 dark:text-zinc-400 dark:ring-zinc-700/70">
              {chip}
            </span>
          ))}
        </span>
      }
    >
      <div className="space-y-10">
        {error && <ErrorBanner message={error} />}

        {state === "judging" && (
          <div className={`rounded-2xl px-5 py-6 ${cardClass}`}>
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

            {other ? (
              <Comparison chosen={evaluation} other={other} />
            ) : (
              <RunOtherJudge interviewId={interviewId} judge={evaluation.judge === "llm" ? "jev" : "llm"} onDone={setOther} />
            )}

            <section>
              <h2 className="mb-3 text-lg font-semibold">Improve next time</h2>
              <ul className="space-y-2">
                {evaluation.improvement_points.map((p, i) => (
                  <li key={i} className={`flex gap-3 rounded-xl px-4 py-3 text-[15px] leading-relaxed ${cardClass}`}>
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-indigo-500" />
                    {p}
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <div className="mb-5 flex items-center gap-3">
                <PersonaAvatar name={interview.persona_name} interviewId={interview.id} portrait={interview.portrait} />
                <div>
                  <h2 className="text-lg font-semibold">Transcript and STAR breakdown</h2>
                  <p className="text-sm text-zinc-600 dark:text-zinc-400">
                    Questions asked by {interview.persona_name}, {interview.persona_title}
                  </p>
                </div>
              </div>
              <Transcript messages={interview.messages} breakdowns={evaluation.star_breakdowns} personaName={interview.persona_name} />
            </section>
          </>
        )}

        <footer className="flex flex-wrap items-center gap-3 border-t border-zinc-200/70 pt-6 dark:border-zinc-800/70">
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

// The Evaluation comes from a Judge, never from the Persona (ADR-0002, ADR-0003).
function ScoreCard({ evaluation }: { evaluation: Evaluation }) {
  const isJev = evaluation.judge === "jev";
  return (
    <section className={`grid gap-6 rounded-2xl p-6 sm:grid-cols-[auto_1fr] ${cardClass}`}>
      <div className="flex items-center gap-4 sm:flex-col sm:items-start">
        <p className="leading-none">
          <span className="text-6xl font-semibold tracking-tight tabular-nums">{evaluation.overall_score}</span>
          <span className="ml-1 text-lg text-zinc-400">/100</span>
          {evaluation.overall_confidence != null && <Confidence value={evaluation.overall_confidence} />}
        </p>
        <span className="flex items-center gap-1.5">
          <span className={`rounded-full px-2.5 py-1 text-sm font-medium ring-1 ${VERDICT_STYLE[evaluation.verdict]}`}>
            {VERDICT_LABEL[evaluation.verdict]}
          </span>
          {evaluation.verdict_confidence != null && <Confidence value={evaluation.verdict_confidence} />}
        </span>
      </div>
      <div>
        <p className="mb-2 flex items-center gap-1.5 text-sm font-medium text-zinc-600 dark:text-zinc-400">
          <Scale className="h-4 w-4" />
          {JUDGE_LABEL[evaluation.judge]} Judge
        </p>
        {isJev ? (
          <>
            <p className="text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
              <span className="font-medium text-zinc-900 dark:text-zinc-100">How the JEV Judge works. </span>
              {JEV_EXPLANATION}
            </p>
            <p className="mt-3 flex flex-wrap gap-3 text-xs text-zinc-600 dark:text-zinc-400">
              {(["high", "medium", "low"] as const).map((level) => (
                <span key={level} className="flex items-center gap-1.5">
                  <span className={`h-2 w-2 rounded-full ${CONFIDENCE_DOT[level]}`} />
                  {level} confidence
                </span>
              ))}
            </p>
          </>
        ) : (
          <p className="text-[15px] leading-relaxed">{evaluation.justification}</p>
        )}
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
          <li key={m.id} className={`ml-8 overflow-hidden rounded-xl ${cardClass}`}>
            <p className="whitespace-pre-wrap bg-zinc-50 px-4 py-3 text-[15px] leading-relaxed dark:bg-zinc-800/60">
              {m.text || <em className="text-zinc-600 dark:text-zinc-400">(no answer given)</em>}
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
              {r.confidence != null && <Confidence value={r.confidence} />}
            </span>
            {r.comment && <span className="col-start-2 text-zinc-600 sm:col-start-3 sm:pt-0.5 dark:text-zinc-400">{r.comment}</span>}
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

const CONFIDENCE_DOT = { high: "bg-emerald-500", medium: "bg-amber-400", low: "bg-red-500" };

// A coloured dot for JEV's confidence in one decision; the legend is in the ScoreCard.
function Confidence({ value }: { value: number }) {
  const level = confidenceLevel(value);
  return (
    <span
      role="img"
      aria-label={`${level} confidence`}
      title={`JEV confidence: ${level} (${value.toFixed(2)})`}
      className={`ml-1.5 inline-block h-2 w-2 shrink-0 rounded-full align-middle ${CONFIDENCE_DOT[level]}`}
    />
  );
}

// Button that runs the Judge that was not chosen. It waits for the result (the LLM Judge can
// take a while) and shows any error next to the button, which then works as a retry.
function RunOtherJudge({ interviewId, judge, onDone }: { interviewId: number; judge: Judge; onDone: (e: Evaluation) => void }) {
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setRunning(true);
    setError(null);
    try {
      onDone(await api.runJudge(interviewId, judge));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The Judge could not run.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <Button variant="secondary" onClick={run} disabled={running}>
        <Scale3d className="h-4 w-4" />
        Run {JUDGE_LABEL[judge]} Judge to compare
      </Button>
      {running && <Spinner label={`The ${JUDGE_LABEL[judge]} Judge is scoring the same answers...`} />}
      {error && <span className="text-sm text-red-600 dark:text-red-400">{error}</span>}
    </div>
  );
}

// Both Judges side by side on the same transcript: scores, verdicts, and STAR ratings per Answer.
function Comparison({ chosen, other }: { chosen: Evaluation; other: Evaluation }) {
  const cols = [chosen, other];
  const stars = (b: StarBreakdown) => STAR_PARTS.map((p) => `${p.label[0]}${b[p.key].rating}`).join(" ");
  return (
    <section>
      <h2 className="mb-3 text-lg font-semibold">Judges compared</h2>
      <div className={`overflow-x-auto rounded-xl ${cardClass}`}>
        <table className="w-full text-sm">
          <thead className="bg-zinc-50 text-left text-zinc-600 dark:text-zinc-400 dark:bg-zinc-900/60">
            <tr>
              <th className="px-4 py-2 font-medium" />
              {cols.map((e, i) => (
                <th key={e.judge} className="px-4 py-2 font-medium">
                  {JUDGE_LABEL[e.judge]} Judge{i === 0 && " (chosen)"}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100 tabular-nums dark:divide-zinc-800">
            <tr>
              <td className="px-4 py-2 text-zinc-600 dark:text-zinc-400">Overall score</td>
              {cols.map((e) => (
                <td key={e.judge} className="px-4 py-2 text-base font-semibold">{e.overall_score}</td>
              ))}
            </tr>
            <tr>
              <td className="px-4 py-2 text-zinc-600 dark:text-zinc-400">Verdict</td>
              {cols.map((e) => (
                <td key={e.judge} className="px-4 py-2">{VERDICT_LABEL[e.verdict]}</td>
              ))}
            </tr>
            {chosen.star_breakdowns.map((b, i) => (
              <tr key={b.position}>
                <td className="px-4 py-2 text-zinc-600 dark:text-zinc-400">Answer {i + 1}</td>
                {cols.map((e) => (
                  <td key={e.judge} className="px-4 py-2 font-mono text-xs">
                    {e.star_breakdowns[i] ? stars(e.star_breakdowns[i]) : "-"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
