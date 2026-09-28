// Typed client for the FastAPI backend. Types mirror src/interview_app/schemas.py.
// Every page is a client component (ADR-0001), so all calls happen in the browser.

export type Seniority = "junior" | "mid" | "senior";
export type Difficulty = "easy" | "normal" | "hard";
export type InterviewStatus = "in_progress" | "judging" | "completed" | "evaluation_missing";
export type MessageRole = "question" | "answer" | "closing";
export type Verdict = "strong_hire" | "hire" | "no_hire";

export interface Message {
  id: number;
  role: MessageRole;
  text: string;
  position: number;
}

export interface Interview {
  id: number;
  title: string;
  industry: string | null;
  seniority: Seniority;
  job_description: string | null;
  difficulty: Difficulty;
  persona_name: string;
  persona_title: string;
  status: InterviewStatus;
  ended_early: boolean;
  created_at: string;
  question_count: number;
  question_cap: number;
  messages: Message[];
}

export interface InterviewCreate {
  title: string;
  industry?: string | null;
  seniority: Seniority;
  job_description?: string | null;
  difficulty: Difficulty;
}

export interface HistoryRow {
  id: number;
  title: string;
  created_at: string;
  status: InterviewStatus;
  overall_score: number | null;
}

export interface StarRating {
  rating: number;
  comment: string;
}

export interface StarBreakdown {
  position: number;
  situation: StarRating;
  task: StarRating;
  action: StarRating;
  result: StarRating;
}

export interface Evaluation {
  interview_id: number;
  overall_score: number;
  justification: string;
  verdict: Verdict;
  improvement_points: string[];
  star_breakdowns: StarBreakdown[];
  created_at: string;
}

export interface RecommendedSettings {
  title: string;
  industry: string | null;
  seniority: Seniority;
}

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Thrown for any non-2xx response. `status` lets pages react to 404/409/503 specifically. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
    });
  } catch {
    throw new ApiError(0, "Cannot reach the backend. Is it running?");
  }
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // non-JSON error body: keep statusText
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

const json = (body: unknown): RequestInit => ({ method: "POST", body: JSON.stringify(body) });

export const api = {
  health: () => request<{ status: string }>("/health"),

  recommendSettings: (job_description: string) =>
    request<RecommendedSettings>("/recommend-settings", json({ job_description })),

  createInterview: (body: InterviewCreate) => request<Interview>("/interviews", json(body)),
  getInterview: (id: number) => request<Interview>(`/interviews/${id}`),
  submitAnswer: (id: number, text: string) =>
    request<Interview>(`/interviews/${id}/answers`, json({ text })),
  endInterview: (id: number) => request<Interview>(`/interviews/${id}/end`, { method: "POST" }),

  getEvaluation: (id: number) => request<Evaluation>(`/interviews/${id}/evaluation`),
  rerunEvaluation: (id: number) =>
    request<Interview>(`/interviews/${id}/evaluation/rerun`, { method: "POST" }),

  listInterviews: () => request<HistoryRow[]>("/interviews"),
  deleteInterview: (id: number) => request<void>(`/interviews/${id}`, { method: "DELETE" }),
  practiceAgain: (id: number) =>
    request<Interview>(`/interviews/${id}/practice-again`, { method: "POST" }),
};
