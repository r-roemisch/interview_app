# Interview Practice

A single-user web app where a candidate rehearses a behavioral job interview with an LLM-driven interviewer and receives a structured evaluation at the end.

## Language

### Setup

**Job**:
The position the candidate is practicing for. Only the title is required; industry, Seniority and Job Description are optional.
_Avoid_: Position, role, vacancy

**Job Description**:
Free text pasted from a real job posting. Optional; when present it is used to infer Recommended Settings and to ground questions.
_Avoid_: Posting, JD

**Seniority**:
The level of the Job (junior, mid, senior). Belongs to the Job, never to the candidate. Chosen by the user; a Recommended Setting may suggest it but never sets it silently.
_Avoid_: Level, experience level

**Recommended Settings**:
Values for Job fields suggested by the app from a pasted Job Description. The user may accept or override any of them before the Interview starts.
_Avoid_: Auto-fill, defaults

**Difficulty**:
How demanding the interviewer's questions and follow-ups are. Easy: common, direct questions, no follow-ups. Normal: standard questions, one follow-up when an Answer is vague. Hard: situational, probing questions with follow-ups that challenge specifics and expect metrics and trade-offs.
_Avoid_: Mode, level, rude

### Interview

**Interview**:
One practice session: a live, turn-based conversation between the interviewer and the candidate for a given Job and Difficulty, capped at ten interviewer Questions, ending in an Evaluation. An Interview is In Progress, Completed, or Evaluation Missing.
_Avoid_: Session, conversation, chat

**In Progress**:
An Interview that still accepts Answers. It can be resumed from History.
_Avoid_: Active, open, running

**Completed**:
An Interview that no longer accepts Answers and has an Evaluation.
_Avoid_: Finished, done, closed

**Evaluation Missing**:
An Interview that no longer accepts Answers but whose Evaluation could not be produced. The user can re-run the Judge.
_Avoid_: Failed, errored, pending

**Question**:
One message from the interviewer to the candidate. Follow-up questions are Questions too and count toward the cap.
_Avoid_: Prompt, turn

**Answer**:
The candidate's plain-text reply to one Question.
_Avoid_: Response, message

**Closing**:
The interviewer's final message after the last Answer or an early end, referencing what was discussed. It is not a Question and does not count toward the cap.
_Avoid_: Goodbye, wrap-up, summary

### Outcome

**Evaluation**:
The judgment produced once, after the Interview ends: a STAR Breakdown per Answer, an Overall Score, and a Recommendation. Produced by the Judge, not the interviewer.
_Avoid_: Feedback, report, results

**Overall Score**:
A single 0-100 number the Judge assigns to the whole Interview, using the STAR Breakdowns and fit to the Job as evidence, with a one-paragraph justification. Comparable across Interviews in History.
_Avoid_: Grade, total, rating

**Judge**:
The evaluator that scores the Interview. A separate prompt from the interviewer so the interviewer's style does not bias the score.
_Avoid_: LLM-as-a-judge, grader, jev

**STAR Breakdown**:
Assessment of one Answer against Situation, Task, Action and Result, each rated 1-5 with a one-line comment.
_Avoid_: STAR score, rubric

**Recommendation**:
The Verdict plus concrete Improvement Points.
_Avoid_: Advice, summary

**Verdict**:
The hiring decision a real interviewer would give: strong hire, hire, or no hire.
_Avoid_: Outcome, decision, result

**Improvement Points**:
A short list of specific things the candidate should do better next time.
_Avoid_: Tips, suggestions

### History

**History**:
The list of all past Interviews, completed or in progress. A completed Interview opens its Evaluation; an in-progress one can be resumed.
_Avoid_: Archive, log, past sessions
