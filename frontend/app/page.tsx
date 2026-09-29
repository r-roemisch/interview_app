"use client";

import { FileUp, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, type Difficulty, type Judge, type Seniority } from "@/lib/api";
import { DIFFICULTY_OPTIONS, JEV_EXPLANATION, JUDGE_OPTIONS, MODE_OPTIONS, SENIORITY_OPTIONS } from "@/lib/labels";
import { Button, cardClass, ErrorBanner, Field, inputClass, Page, Spinner } from "./ui";

// Setup page: describe the Job, pick Difficulty and Judge, start an Interview.
export default function SetupPage() {
  const router = useRouter();

  // One piece of state per form field. Seniority and Difficulty have the defaults from the spec.
  const [title, setTitle] = useState("");
  const [industry, setIndustry] = useState("");
  const [seniority, setSeniority] = useState<Seniority>("mid");
  const [jobDescription, setJobDescription] = useState("");
  const [difficulty, setDifficulty] = useState<Difficulty>("normal");
  const [cv, setCv] = useState("");
  const [judge, setJudge] = useState<Judge>("llm");
  const [mode, setMode] = useState<"written" | "voice">("written");

  const [recommending, setRecommending] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Pre-fill the CV from the last Interview that had one. Runs once, after the first render.
  useEffect(() => {
    api
      .latestCv()
      .then((r) => setCv((current) => current || r.cv || ""))
      .catch(() => {}); // no CV to pre-fill is fine
  }, []);

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
        cv: cv.trim() || null,
        judge,
        voice_interview: mode === "voice",
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
        <section className={`space-y-3 rounded-2xl p-5 ${cardClass}`}>
          <Field label="Job description" hint="Optional. Paste a real posting and the app suggests the fields below.">
            <textarea
              className={`${inputClass} min-h-36`}
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              maxLength={20000}
              placeholder="Paste the job posting here"
            />
          </Field>
          <div className="flex items-center gap-3">
            <Button type="button" variant="secondary" onClick={recommend} disabled={busy || !jobDescription.trim()}>
              <Sparkles className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              Recommend settings
            </Button>
            <PdfUpload onText={setJobDescription} onError={setError} disabled={busy} />
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
              <div className="grid grid-cols-3 gap-1 rounded-lg bg-zinc-200/60 p-1 dark:bg-zinc-900/60">
                {SENIORITY_OPTIONS.map((o) => (
                  <label
                    key={o.value}
                    className={`cursor-pointer rounded-md px-3 py-1.5 text-center text-sm has-focus-visible:outline-2 has-focus-visible:outline-indigo-500 ${
                      seniority === o.value
                        ? "bg-white font-medium shadow-sm dark:bg-zinc-800"
                        : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100"
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

          <ChoiceCards legend="Interview" name="mode" options={MODE_OPTIONS} value={mode} onChange={setMode} />

          <ChoiceCards legend="Difficulty" name="difficulty" options={DIFFICULTY_OPTIONS} value={difficulty} onChange={setDifficulty} />

          <div>
            <ChoiceCards legend="Judge" name="judge" options={JUDGE_OPTIONS} value={judge} onChange={setJudge} />
            {judge === "jev" && (
              <p className="mt-2 rounded-lg bg-white/70 p-3 text-xs leading-relaxed text-zinc-600 ring-1 ring-zinc-200/70 dark:bg-zinc-900/60 dark:text-zinc-400 dark:ring-zinc-800/70">
                <span className="font-medium text-zinc-900 dark:text-zinc-100">How the JEV Judge works. </span>
                {JEV_EXPLANATION}
              </p>
            )}
          </div>

          <Field label="Your CV" hint="Optional. On Normal and Hard the interviewer asks about your experience. Only the interviewer reads it.">
            <textarea
              className={`${inputClass} min-h-28`}
              value={cv}
              onChange={(e) => setCv(e.target.value)}
              maxLength={20000}
              placeholder="Paste your CV here"
            />
          </Field>
          <PdfUpload onText={setCv} onError={setError} disabled={busy} />
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

// "Upload PDF" button: sends the file to the backend and hands back the extracted text.
// The <label> wraps a hidden file input, so clicking the label opens the file picker.
function PdfUpload({
  onText,
  onError,
  disabled,
}: {
  onText: (text: string) => void;
  onError: (message: string | null) => void;
  disabled: boolean;
}) {
  const [uploading, setUploading] = useState(false);

  async function upload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = ""; // lets the same file be picked again
    if (!file) return;
    onError(null);
    setUploading(true);
    try {
      onText((await api.extractText(file)).text);
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Could not read the PDF.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <label
      className={`inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-zinc-200 bg-white px-3.5 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 has-focus-visible:outline-2 has-focus-visible:outline-indigo-500 dark:border-zinc-800 dark:bg-zinc-900/60 dark:text-zinc-200 dark:hover:bg-zinc-800 ${
        disabled || uploading ? "pointer-events-none opacity-50" : ""
      }`}
    >
      <input type="file" accept="application/pdf,.pdf" onChange={upload} disabled={disabled || uploading} className="sr-only" />
      <FileUp className="h-4 w-4" />
      {uploading ? "Reading PDF..." : "Upload PDF"}
    </label>
  );
}

// A row of selectable cards (radio buttons in disguise), used for Difficulty and Judge.
// Generic over T so each use keeps its own value type ("easy" | ... or "llm" | "jev").
function ChoiceCards<T extends string>({
  legend,
  name,
  options,
  value,
  onChange,
}: {
  legend: string;
  name: string;
  options: { value: T; label: string; hint: string }[];
  value: T;
  onChange: (value: T) => void;
}) {
  return (
    <fieldset>
      <legend className="mb-1.5 text-sm font-medium">{legend}</legend>
      <div className={`grid gap-2 ${options.length === 3 ? "sm:grid-cols-3" : "sm:grid-cols-2"}`}>
        {options.map((o) => (
          <label
            key={o.value}
            className={`cursor-pointer rounded-xl border p-3.5 text-sm transition-colors has-focus-visible:outline-2 has-focus-visible:outline-indigo-500 ${
              value === o.value
                ? "border-indigo-500 bg-indigo-50 shadow-sm ring-1 ring-indigo-500 dark:bg-indigo-500/15"
                : "border-zinc-200/70 bg-white shadow-sm hover:border-zinc-300 dark:border-zinc-800/70 dark:bg-zinc-900/60 dark:hover:border-zinc-700"
            }`}
          >
            <input type="radio" name={name} value={o.value} checked={value === o.value} onChange={() => onChange(o.value)} className="sr-only" />
            <span className="font-medium">{o.label}</span>
            <span className="mt-1 block text-xs leading-relaxed text-zinc-600 dark:text-zinc-400">{o.hint}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
