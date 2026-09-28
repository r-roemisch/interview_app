import type { Difficulty, InterviewStatus, Seniority, Verdict } from "./api";

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

export const STAR_PARTS = [
  { key: "situation", label: "Situation", hint: "Where and when. Keep it short." },
  { key: "task", label: "Task", hint: "What you were responsible for." },
  { key: "action", label: "Action", hint: "What you did, not the team." },
  { key: "result", label: "Result", hint: "What changed, with a number." },
] as const;

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}
