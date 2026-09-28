"use client";

import { Sparkles } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, type Difficulty, type Seniority } from "@/lib/api";
import { DIFFICULTY_OPTIONS, SENIORITY_OPTIONS } from "@/lib/labels";
import { Button, ErrorBanner, Field, inputClass, Page, Spinner } from "./ui";

// Setup page: describe the Job, pick Difficulty, start an Interview.
export default function SetupPage() {
  const router = useRouter();

  // One piece of state per form field. Seniority and Difficulty have the defaults from the spec.
  const [title, setTitle] = useState("");
  const [industry, setIndustry] = useState("");
  const [seniority, setSeniority] = useState<Seniority>("mid");
  const [jobDescription, setJobDescription] = useState("");
  const [difficulty, setDifficulty] = useState<Difficulty>("normal");

  const [recommending, setRecommending] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function recommend() {
    setError(null);
    setRecommending(true);
    try {
      const rec = await api.recommendSettings(jobDescription);
      // Fill the fields; the user can still edit each one before starting (Recommended Settings).
      setTitle(rec.title);
      setIndustry(rec.industry ?? "");
      setSeniority(rec.seniority);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not get recommendations.");
    } finally {
      setRecommending(false);
    }
  }

  async function start(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setStarting(true);
    try {
      const interview = await api.createInterview({
        title: title.trim(),
        industry: industry.trim() || null,
        seniority,
        job_description: jobDescription.trim() || null,
        difficulty,
      });
      router.push(`/interviews/${interview.id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not start the interview.");
      setStarting(false);
    }
  }

  const busy = recommending || starting;

  return (
    <Page title="New interview" intro="Describe the job you are practising for. Only the title is required.">
      <form onSubmit={start} className="space-y-8">
        <section className="space-y-3 rounded-2xl border border-zinc-200 bg-zinc-50/60 p-5 dark:border-zinc-800 dark:bg-zinc-900/40">
          <Field label="Job description" hint="Optional. Paste a real posting and the app suggests the fields below.">
            <textarea
              className={`${inputClass} min-h-36`}
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job posting here"
            />
          </Field>
          <div className="flex items-center gap-3">
            <Button type="button" variant="secondary" onClick={recommend} disabled={busy || !jobDescription.trim()}>
              <Sparkles className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              Recommend settings
            </Button>
            {recommending && <Spinner label="Reading the posting..." />}
          </div>
        </section>

        <div className="space-y-5">
          <Field label="Job title">
            <input className={inputClass} value={title} onChange={(e) => setTitle(e.target.value)} required placeholder="e.g. Backend Engineer" />
          </Field>

          <div className="grid gap-5 sm:grid-cols-2">
            <Field label="Industry" hint="Optional">
              <input className={inputClass} value={industry} onChange={(e) => setIndustry(e.target.value)} placeholder="e.g. Fintech" />
            </Field>
            <fieldset>
              <legend className="mb-1.5 text-sm font-medium">Seniority of the role</legend>
              <div className="grid grid-cols-3 gap-1 rounded-lg bg-zinc-100 p-1 dark:bg-zinc-900">
                {SENIORITY_OPTIONS.map((o) => (
                  <label
                    key={o.value}
                    className={`cursor-pointer rounded-md px-3 py-1.5 text-center text-sm has-focus-visible:outline-2 has-focus-visible:outline-indigo-500 ${
                      seniority === o.value
                        ? "bg-white font-medium shadow-sm dark:bg-zinc-800"
                        : "text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
                    }`}
                  >
                    <input
                      type="radio"
                      name="seniority"
                      value={o.value}
                      checked={seniority === o.value}
                      onChange={() => setSeniority(o.value)}
                      className="sr-only"
                    />
                    {o.label}
                  </label>
                ))}
              </div>
            </fieldset>
          </div>

          <fieldset>
            <legend className="mb-1.5 text-sm font-medium">Difficulty</legend>
            <div className="grid gap-2 sm:grid-cols-3">
              {DIFFICULTY_OPTIONS.map((o) => (
                <label
                  key={o.value}
                  className={`cursor-pointer rounded-xl border p-3.5 text-sm transition-colors has-focus-visible:outline-2 has-focus-visible:outline-indigo-500 ${
                    difficulty === o.value
                      ? "border-indigo-500 bg-indigo-50/60 ring-1 ring-indigo-500 dark:bg-indigo-500/10"
                      : "border-zinc-200 hover:border-zinc-300 dark:border-zinc-800 dark:hover:border-zinc-700"
                  }`}
                >
                  <input
                    type="radio"
                    name="difficulty"
                    value={o.value}
                    checked={difficulty === o.value}
                    onChange={() => setDifficulty(o.value)}
                    className="sr-only"
                  />
                  <span className="font-medium">{o.label}</span>
                  <span className="mt-1 block text-xs leading-relaxed text-zinc-500">{o.hint}</span>
                </label>
              ))}
            </div>
          </fieldset>
        </div>

        {error && <ErrorBanner message={error} />}

        <div className="flex items-center gap-3">
          <Button type="submit" disabled={busy || !title.trim()} className="px-5">
            Start interview
          </Button>
          {starting && <Spinner label="Preparing your interviewer and the first question..." />}
        </div>
      </form>
    </Page>
  );
}
