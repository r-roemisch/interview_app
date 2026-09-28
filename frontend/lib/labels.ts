import type { Difficulty, InterviewStatus, Judge, Seniority, Verdict } from "./api";

export const STATUS_LABEL: Record<InterviewStatus, string> = {
  in_progress: "In progress",
  judging: "Judging",
  completed: "Completed",
  evaluation_missing: "Evaluation missing",
};

export const VERDICT_LABEL: Record<Verdict, string> = {
  strong_hire: "Strong hire",
  hire: "Hire",
  no_hire: "No hire",
};

export const SENIORITY_OPTIONS: { value: Seniority; label: string }[] = [
  { value: "junior", label: "Junior" },
  { value: "mid", label: "Mid" },
  { value: "senior", label: "Senior" },
];

export const DIFFICULTY_OPTIONS: { value: Difficulty; label: string; hint: string }[] = [
  { value: "easy", label: "Easy", hint: "Common questions, no follow-ups" },
  { value: "normal", label: "Normal", hint: "Standard questions, one follow-up when vague" },
  { value: "hard", label: "Hard", hint: "Probing follow-ups, expects metrics and trade-offs" },
];

export const JUDGE_OPTIONS: { value: Judge; label: string; hint: string }[] = [
  { value: "llm", label: "LLM Judge", hint: "Written feedback on every answer" },
  { value: "jev", label: "JEV Judge", hint: "Fast ratings with confidence, no written feedback" },
];

export const MODE_OPTIONS: { value: "written" | "voice"; label: string; hint: string }[] = [
  { value: "written", label: "Written interview", hint: "Read the questions and type your answers" },
  { value: "voice", label: "Voice interview", hint: "The interviewer speaks and you answer out loud" },
];

export const JUDGE_LABEL: Record<Judge, string> = { llm: "LLM", jev: "JEV" };

// Shown on Setup and on a JEV Evaluation (spec: judge-choice).
export const JEV_EXPLANATION =
  "The JEV Judge is a model that doesn't write text. It picks answers from fixed scales: a 1-5 rating for " +
  "each part of every STAR answer, an overall score and a verdict, and it says how confident it is in each " +
  "one. It doesn't explain its ratings. Your Improvement Points come from a fixed checklist of good interview " +
  "habits: the three habits JEV was least sure you showed. For written feedback, choose the LLM Judge or run " +
  "it afterwards to compare.";

// Display-only buckets for JEV's confidence (spec: judge-choice, Evaluation page).
export function confidenceLevel(confidence: number): "high" | "medium" | "low" {
  if (confidence >= 0.85) return "high";
  if (confidence < 0.6) return "low";
  return "medium";
}

export const STAR_PARTS = [
  { key: "situation", label: "Situation", hint: "Where and when. Keep it short." },
  { key: "task", label: "Task", hint: "What you were responsible for." },
  { key: "action", label: "Action", hint: "What you did, not the team." },
  { key: "result", label: "Result", hint: "What changed, with a number." },
] as const;

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}
