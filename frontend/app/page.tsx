"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, type Difficulty, type Seniority } from "@/lib/api";
import { DIFFICULTY_OPTIONS, SENIORITY_OPTIONS } from "@/lib/labels";
import { Button, ErrorBanner, Field, inputClass, Spinner } from "./ui";

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
    <form onSubmit={start} className="space-y-6">
      <h1 className="text-2xl font-semibold">New interview</h1>

      <Field label="Job description" hint="Optional. Paste a real posting and let the app suggest the fields below.">
        <textarea
          className={`${inputClass} min-h-40`}
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Paste the job posting here..."
        />
      </Field>
      <div className="flex items-center gap-3">
        <Button type="button" variant="secondary" onClick={recommend} disabled={busy || !jobDescription.trim()}>
          Recommend settings
        </Button>
        {recommending && <Spinner label="Reading the posting..." />}
      </div>

      <Field label="Job title">
        <input className={inputClass} value={title} onChange={(e) => setTitle(e.target.value)} required placeholder="e.g. Backend Engineer" />
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Industry" hint="Optional">
          <input className={inputClass} value={industry} onChange={(e) => setIndustry(e.target.value)} placeholder="e.g. Fintech" />
        </Field>
        <Field label="Seniority of the role">
          <select className={inputClass} value={seniority} onChange={(e) => setSeniority(e.target.value as Seniority)}>
            {SENIORITY_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </Field>
      </div>

      <fieldset>
        <legend className="mb-2 text-sm font-medium">Difficulty</legend>
        <div className="grid gap-2 sm:grid-cols-3">
          {DIFFICULTY_OPTIONS.map((o) => (
            <label
              key={o.value}
              className={`cursor-pointer rounded-md border p-3 text-sm ${
                difficulty === o.value ? "border-zinc-900 dark:border-zinc-100" : "border-zinc-300 dark:border-zinc-700"
              }`}
            >
              <input
                type="radio"
                name="difficulty"
                value={o.value}
                checked={difficulty === o.value}
                onChange={() => setDifficulty(o.value)}
                className="mr-2"
              />
              <span className="font-medium">{o.label}</span>
              <span className="mt-1 block text-xs text-zinc-500">{o.hint}</span>
            </label>
          ))}
        </div>
      </fieldset>

      {error && <ErrorBanner message={error} />}

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={busy || !title.trim()}>
          Start interview
        </Button>
        {starting && <Spinner label="The interviewer is preparing the first question..." />}
      </div>
    </form>
  );
}
