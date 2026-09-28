# 03 Run the other Judge (backend)

Status: resolved
Blocked by: 02

Endpoints to run the Judge that was not chosen and to list both Evaluations for the comparison. See spec "Evaluation page" and "API".

- `GET /interviews/{id}/evaluations`: all Evaluations of the Interview (0-2), each with its `judge`.
- `POST /interviews/{id}/evaluations/{judge}`: runs that Judge synchronously and returns 201 with the Evaluation.
  - 409 if the Interview has not ended, or if `judge` is the chosen Judge (that one uses "Re-run evaluation").
  - Running it again replaces the earlier Evaluation from that Judge.
  - On failure: 503 with a message, no Evaluation stored for that Judge, and the Interview's status is not touched.
- The Interview's status and History score depend only on the chosen Judge's Evaluation.

Done when tests cover: a second Evaluation is created and listed; status and History score are unchanged by it; 409 for the chosen Judge and for an Interview still In Progress; failure returns 503 and leaves status and any existing Evaluations unchanged; running it twice keeps one Evaluation per Judge.

## Comments

- 2026-09-29: Done. `GET /interviews/{id}/evaluations` returns `interview.evaluations`. `POST /interviews/{id}/evaluations/{judge}` calls `services.judge.run_other_judge`, which reuses `evaluate` and `replace_evaluation` from issue 02 and commits only on success. 409 while In Progress and for the chosen Judge; 503 on failure with nothing changed. It also works while the chosen Judge's Evaluation is missing (the status stays Evaluation Missing). 5 tests added to `tests/test_jev_judge.py`; 87 passed.
