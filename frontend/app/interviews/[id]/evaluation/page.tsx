"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError, type Evaluation, type Interview, type Message, type StarBreakdown, type StarRating } from "@/lib/api";
import { VERDICT_LABEL } from "@/lib/labels";
import { Button, ErrorBanner, LinkButton, Spinner } from "../../../ui";

// Evaluation page: score, verdict, transcript with STAR breakdowns inline, improvement points.
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

  if (state === "loading") return <Spinner label="Loading..." />;
  if (state === "error") return <ErrorBanner message={error ?? "Something went wrong."} onRetry={reload} />;
  if (!interview) return null;

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold">Evaluation: {interview.title}</h1>
        <p className="text-sm text-zinc-500">
          {interview.seniority} level · {interview.difficulty} difficulty
          {interview.ended_early ? " · ended early" : ""}
        </p>
      </header>

      {error && <ErrorBanner message={error} />}

      {state === "judging" && <Spinner label="The judge is reviewing your answers..." />}

      {state === "missing" && (
        <div className="space-y-3">
          <ErrorBanner message="The evaluation could not be produced. You can ask the judge to try again." />
          <Button onClick={rerun} disabled={busy}>
            Re-run evaluation
          </Button>
        </div>
      )}

      {state === "ready" && evaluation && (
        <>
          <section className="grid gap-4 rounded-lg border border-zinc-200 p-5 sm:grid-cols-[auto_1fr] dark:border-zinc-800">
            <div className="text-center">
              <div className="text-5xl font-semibold">{evaluation.overall_score}</div>
              <div className="text-xs text-zinc-500">out of 100</div>
              <div className="mt-2 text-sm font-medium">{VERDICT_LABEL[evaluation.verdict]}</div>
            </div>
            <p className="text-sm leading-relaxed">{evaluation.justification}</p>
          </section>

          <section className="space-y-4">
            <h2 className="text-lg font-semibold">Transcript and STAR breakdown</h2>
            <Transcript messages={interview.messages} breakdowns={evaluation.star_breakdowns} />
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-semibold">Improvement points</h2>
            <ol className="list-decimal space-y-1 pl-5 text-sm">
              {evaluation.improvement_points.map((p, i) => (
                <li key={i}>{p}</li>
              ))}
            </ol>
          </section>
        </>
      )}

      <footer className="flex flex-wrap gap-3">
        <Button onClick={practiceAgain} disabled={busy}>
          Practice this job again
        </Button>
        <LinkButton href="/history">Back to history</LinkButton>
        {busy && <Spinner label="Starting a new interview..." />}
      </footer>
    </div>
  );
}

function Transcript({ messages, breakdowns }: { messages: Message[]; breakdowns: StarBreakdown[] }) {
  const byPosition = new Map(breakdowns.map((b) => [b.position, b]));
  return (
    <ol className="space-y-4">
      {messages.map((m) => {
        if (m.role === "closing") {
          return (
            <li key={m.id} className="rounded-md bg-amber-50 px-4 py-2 text-sm dark:bg-amber-950">
              {m.text}
            </li>
          );
        }
        if (m.role === "question") {
          return (
            <li key={m.id} className="text-sm font-medium">
              {m.text}
            </li>
          );
        }
        const breakdown = byPosition.get(m.position);
        return (
          <li key={m.id} className="rounded-md border border-zinc-200 dark:border-zinc-800">
            <p className="whitespace-pre-wrap px-4 py-3 text-sm">
              {m.text || <em className="opacity-60">(no answer given)</em>}
            </p>
            {breakdown && <StarTable breakdown={breakdown} />}
          </li>
        );
      })}
    </ol>
  );
}

function StarTable({ breakdown }: { breakdown: StarBreakdown }) {
  const rows: [string, StarRating][] = [
    ["Situation", breakdown.situation],
    ["Task", breakdown.task],
    ["Action", breakdown.action],
    ["Result", breakdown.result],
  ];
  return (
    <table className="w-full border-t border-zinc-200 text-sm dark:border-zinc-800">
      <tbody>
        {rows.map(([name, r]) => (
          <tr key={name} className="border-b border-zinc-100 last:border-0 dark:border-zinc-800">
            <th className="w-24 px-4 py-2 text-left font-medium">{name}</th>
            <td className="w-16 px-2 py-2 tabular-nums" aria-label={`${r.rating} out of 5`}>
              {"★".repeat(r.rating)}
              <span className="text-zinc-300 dark:text-zinc-600">{"★".repeat(5 - r.rating)}</span>
            </td>
            <td className="px-2 py-2 text-zinc-600 dark:text-zinc-400">{r.comment}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
