# Next.js is a client-only UI; FastAPI is the only backend

The app has a Python backend by requirement and is built by a frontend beginner. Next.js (App Router, TypeScript, Tailwind) is used because it is the framework the author wants to learn and employers ask about, but every page is a client component, and no server components, server actions, route handlers or Next.js API routes are used. All data access and all LLM calls go through the FastAPI JSON API. This keeps exactly one place where logic lives and avoids the server/client split that is the main source of confusion in Next.js. Vite + React was the alternative and would have been simpler, but would not have taught the target stack.

## Consequences

- The Next.js dev server is the only role Node.js plays.
- Anything that needs a secret (the OpenRouter key) must live in FastAPI, never in the frontend.
- Streaming, if added later, is a FastAPI concern first.
