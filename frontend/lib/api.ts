// Typed client for the FastAPI backend. Types mirror src/interview_app/schemas.py.
// Every page is a client component (ADR-0001), so all calls happen in the browser.

export type Seniority = "junior" | "mid" | "senior";
export type Difficulty = "easy" | "normal" | "hard";
export type Demeanor = "friendly" | "rude";
export type Judge = "llm" | "jev";
export type InterviewStatus = "in_progress" | "judging" | "completed" | "evaluation_missing";
export type MessageRole = "question" | "answer" | "closing";
export type Verdict = "strong_hire" | "hire" | "no_hire";
// "none": no Portrait was asked for at Setup (or the Interview is older than Portraits).
export type PortraitState = "none" | "pending" | "ready" | "failed";

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
  demeanor: Demeanor;
  judge: Judge;
  persona_name: string;
  persona_title: string;
  persona_voice: string;
  voice_interview: boolean;
  portrait: PortraitState;
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
  demeanor: Demeanor;
  cv?: string | null;
  judge: Judge;
  voice_interview: boolean;
  portrait: boolean;
}

export interface HistoryRow {
  id: number;
  title: string;
  created_at: string;
  status: InterviewStatus;
  judge: Judge;
  overall_score: number | null;
}

export interface StarRating {
  rating: number;
  comment: string | null; // null from the JEV Judge
  confidence?: number | null; // JEV Judge only, 0-1
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
  judge: Judge;
  overall_score: number;
  justification: string | null; // null from the JEV Judge
  verdict: Verdict;
  improvement_points: string[];
  star_breakdowns: StarBreakdown[];
  overall_confidence: number | null;
  verdict_confidence: number | null;
  checklist: { check: string; probability: number }[] | null;
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
      // A file upload (FormData) must not get a JSON Content-Type: the browser sets its own.
      headers: init.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...(init.headers ?? {}) },
    });
  } catch {
    throw new ApiError(0, "Cannot reach the backend. Is it running?");
  }
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
      // FastAPI's own validation errors (422) are a list, e.g.
      // [{ loc: ["body", "cv"], msg: "String should have at most 20000 characters" }]
      else if (Array.isArray(body.detail))
        detail = (body.detail as { loc?: unknown[]; msg?: string }[])
          .map((d) => `${d.loc?.at(-1) ?? "input"}: ${d.msg}`)
          .join("; ");
    } catch {
      // non-JSON error body: keep statusText
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

/** WAV of an interviewer message in the Persona's voice; used directly as an <audio> source. */
export const speechUrl = (interviewId: number, messageId: number) =>
  `${API_URL}/interviews/${interviewId}/messages/${messageId}/speech`;

/** The Persona's Portrait (PNG) once its state is "ready"; used directly as an <img> source. */
export const portraitUrl = (interviewId: number) => `${API_URL}/interviews/${interviewId}/portrait`;

const json = (body: unknown): RequestInit => ({ method: "POST", body: JSON.stringify(body) });

export const api = {
  health: () => request<{ status: string }>("/health"),

  recommendSettings: (job_description: string) =>
    request<RecommendedSettings>("/recommend-settings", json({ job_description })),

  latestCv: () => request<{ cv: string | null }>("/cv/latest"),
  extractText: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ text: string }>("/extract-text", { method: "POST", body: form });
  },

  // A recorded Answer as text. The backend reads the format from the Blob's type (audio/wav, see lib/wav.ts).
  transcribe: (audio: Blob) => {
    const form = new FormData();
    form.append("file", audio, "answer");
    return request<{ text: string }>("/transcriptions", { method: "POST", body: form });
  },

  createInterview: (body: InterviewCreate) => request<Interview>("/interviews", json(body)),
  getInterview: (id: number) => request<Interview>(`/interviews/${id}`),
  submitAnswer: (id: number, text: string) =>
    request<Interview>(`/interviews/${id}/answers`, json({ text })),
  endInterview: (id: number) => request<Interview>(`/interviews/${id}/end`, { method: "POST" }),

  getEvaluation: (id: number) => request<Evaluation>(`/interviews/${id}/evaluation`),
  listEvaluations: (id: number) => request<Evaluation[]>(`/interviews/${id}/evaluations`),
  runJudge: (id: number, judge: Judge) =>
    request<Evaluation>(`/interviews/${id}/evaluations/${judge}`, { method: "POST" }),
  rerunEvaluation: (id: number) =>
    request<Interview>(`/interviews/${id}/evaluation/rerun`, { method: "POST" }),

  listInterviews: () => request<HistoryRow[]>("/interviews"),
  deleteInterview: (id: number) => request<void>(`/interviews/${id}`, { method: "DELETE" }),
  practiceAgain: (id: number) =>
    request<Interview>(`/interviews/${id}/practice-again`, { method: "POST" }),
};
