import type { Demeanor, Difficulty, InterviewerModel, InterviewStatus, Judge, PromptStyle, Seniority, Verdict } from "./api";

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

export const DEMEANOR_OPTIONS: { value: Demeanor; label: string; hint: string }[] = [
  { value: "friendly", label: "Friendly", hint: "Patient and polite" },
  { value: "rude", label: "Rude", hint: "Impatient, sceptical, curt" },
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

// Setup choices for trying out models and prompts (spec: interviewer-experiments).
export const INTERVIEWER_MODEL_OPTIONS: { value: InterviewerModel; label: string; hint: string }[] = [
  { value: "openai/gpt-4.1-mini", label: "GPT-4.1 Mini", hint: "Baseline: the model used so far, no built-in reasoning" },
  { value: "openai/gpt-5-nano", label: "GPT-5 Nano", hint: "Cheapest, but slow: it reasons before every reply" },
  { value: "anthropic/claude-sonnet-5.5", label: "Claude Sonnet 5.5", hint: "Best, and the most expensive" },
  { value: "google/gemma-4-31b-it", label: "Gemma 4 31B", hint: "Open model you could run yourself" },
];

export const PROMPT_STYLE_OPTIONS: { value: PromptStyle; label: string; hint: string }[] = [
  { value: "zero_shot", label: "Zero-shot", hint: "The interviewer gets only its rules." },
  { value: "one_shot", label: "One-shot", hint: "The interviewer also gets one example exchange." },
  { value: "few_shot", label: "Few-shot", hint: "The interviewer also gets three example exchanges." },
  { value: "chain_of_thought", label: "Chain-of-thought", hint: "The interviewer thinks about your last answer before asking." },
  { value: "plan_ahead", label: "Plan-ahead", hint: "The interviewer plans the topics of the interview first, then follows the plan." },
  {
    value: "self_check",
    label: "Self-check",
    hint: "The interviewer drafts each question, checks it against its rules, then asks the corrected one.",
  },
];

// After the first and second Off-topic Answer; the third ends the Interview (CONTEXT.md: Off-topic Answer).
export const OFF_TOPIC_REMINDERS = [
  "Let's stay with the interview. Please answer the question.",
  "Last reminder: one more answer like that ends the interview.",
];

// "GPT-4.1 Mini · Few-shot", for History rows.
export function experimentLabel(model: InterviewerModel, style: PromptStyle): string {
  const modelLabel = INTERVIEWER_MODEL_OPTIONS.find((o) => o.value === model)?.label ?? model;
  const styleLabel = PROMPT_STYLE_OPTIONS.find((o) => o.value === style)?.label ?? style;
  return `${modelLabel} · ${styleLabel}`;
}

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
