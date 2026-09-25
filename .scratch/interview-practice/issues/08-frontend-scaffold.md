# 08 Frontend scaffold

Status: resolved
Blocked by: 01

Create `frontend/` with `create-next-app` (App Router, TypeScript, Tailwind, ESLint, no `src/` dir). Add `lib/api.ts`: typed fetch wrapper over `NEXT_PUBLIC_API_URL` with TypeScript types mirroring the backend schemas. Add a root layout with a nav (New interview, History). Every page file starts with `"use client"` per ADR-0001. Add `frontend/.env.example` with `NEXT_PUBLIC_API_URL=http://localhost:8000`.

Done when `npm run dev` shows the nav and `/health` is reachable via the api wrapper.

## Comments

- 2026-09-25: Done. `create-next-app` (Next 16.3.6, React 19.2, TypeScript, Tailwind v4, ESLint, App Router, no src dir). `lib/api.ts` typed client + `ApiError`; `app/layout.tsx` server layout with metadata; `app/nav.tsx` ("use client", `usePathname` active link) with `app/backend-status.tsx` health indicator; placeholder "use client" pages for `/`, `/history`, `/interviews/[id]`, `/interviews/[id]/evaluation` (dynamic id via `useParams`). `.env.example` + `.env.local` with `NEXT_PUBLIC_API_URL`; frontend `.gitignore` now keeps `.env.example`. `tsc`, `eslint`, `next build` all pass; dev servers smoke-tested with curl (pages render, CORS OK). No browser available on this machine for an in-page check (Playwright reports no Chrome installed).
- Note for later issues (from the bundled Next 16 docs): `"use client"` must be the first line; `params` are Promises in this version, so client pages use `useParams()`; `NEXT_PUBLIC_*` values are inlined at build time; Turbopack is the default; `window`/`localStorage` only inside `useEffect`.
