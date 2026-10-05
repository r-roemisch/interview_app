# 04 Daily Budget (backend)

Status: resolved

Guard 2. See spec section "Guard 2: Daily Budget". Vocabulary: Daily Budget in `CONTEXT.md`.

- `config.py` and `.env.example`: `DAILY_BUDGET`, default `2`.
- A small module (e.g. `budget.py`) that reads `data.usage_daily` from `GET https://openrouter.ai/api/v1/key` with `httpx` and the existing key, returning `None` when it cannot be read (logs a warning). A FastAPI dependency so tests can replace it; with `LLM_PROVIDER=fake` it is not called.
- `POST /interviews` and `POST /interviews/{id}/practice-again`: before any model call, 429 "Today's budget of $2.00 is used up ($2.13 spent). Try again tomorrow." when spending is at or over the budget.

Done when tests cover: at or over the budget → 429 and no model call, for both endpoints; under → starts; unreadable spending → starts; answering and ending an Interview never check the budget. Then one real read of the key's spending, noted in a comment.

## Comments

- 2026-10-05: Done. `budget.py`: `read_daily_spend` (httpx, `usage_daily`, None on any failure, logged), `FakeDailySpend`, dependency `get_daily_spend` (None with the fake provider). `DAILY_BUDGET` in `config.py` and `.env.example`. `_check_daily_budget` in the router, before any model call in `POST /interviews` and Practice again. `tests/test_daily_budget.py` (12 tests, including the reader with `httpx.MockTransport`). Real read of the key: $0.11 spent today.
