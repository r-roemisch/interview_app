# 10 Interview page

Status: ready-for-agent
Blocked by: 04, 05, 08

Page `/interviews/[id]`: loads the Interview, renders the transcript as a chat (interviewer left, candidate right), a counter "Question n of 10", a textarea + Send, and an "End interview" button enabled after the first Answer. On Send: post the Answer, append the returned Question or Closing. On a Closing: hide the input, show "See evaluation" disabled, poll `/interviews/[id]/evaluation` every 2 s; enable the button on 200, turn it into "Re-run evaluation" on 409 (which calls rerun and resumes polling). On 503 from Send: keep the typed text, show an error and a Retry button. Works for resumed In Progress Interviews.

Done when a full 10-question run and an early-end run both reach the Evaluation page.
