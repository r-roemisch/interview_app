# 08 Frontend scaffold

Status: ready-for-agent
Blocked by: 01

Create `frontend/` with `create-next-app` (App Router, TypeScript, Tailwind, ESLint, no `src/` dir). Add `lib/api.ts`: typed fetch wrapper over `NEXT_PUBLIC_API_URL` with TypeScript types mirroring the backend schemas. Add a root layout with a nav (New interview, History). Every page file starts with `"use client"` per ADR-0001. Add `frontend/.env.example` with `NEXT_PUBLIC_API_URL=http://localhost:8000`.

Done when `npm run dev` shows the nav and `/health` is reachable via the api wrapper.
