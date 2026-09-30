# Interview Practice

A single-user web app where a candidate rehearses a behavioral job interview with an LLM-driven interviewer and receives a structured evaluation at the end.

## Language

### Setup

**Job**:
The position the candidate is practicing for. Only the title is required; industry, Seniority and Job Description are optional.
_Avoid_: Position, role, vacancy

**Job Description**:
Free text from a real job posting, pasted or taken from an uploaded PDF. Optional; when present it is used to infer Recommended Settings and to ground questions. Only the text is kept, never the file.
_Avoid_: Posting, JD

**CV**:
Free text describing the candidate's experience, pasted or taken from an uploaded PDF. Optional and attached to one Interview, like the Job. Read only by the interviewer, to ask about the candidate's real experiences; never by the Judge or Recommended Settings. Only the text is kept, never the file.
_Avoid_: Resume, profile

**Seniority**:
The level of the Job (junior, mid, senior). Belongs to the Job, never to the candidate. Chosen by the user; a Recommended Setting may suggest it but never sets it silently.
_Avoid_: Level, experience level

**Recommended Settings**:
Values for Job fields suggested by the app from a pasted Job Description. The user may accept or override any of them before the Interview starts.
_Avoid_: Auto-fill, defaults

**Difficulty**:
How demanding the interviewer's questions and follow-ups are. Easy: common, direct questions, no follow-ups, the CV is ignored. Normal: standard questions, one follow-up when an Answer is vague, some Questions may draw on the CV. Hard: situational, probing questions with follow-ups that challenge specifics and expect metrics and trade-offs, including claims made in the CV. Difficulty decides what is asked, never the manner: that belongs to Demeanor.
_Avoid_: Mode, level, rude

**Demeanor**:
How the interviewer treats the candidate: Friendly (the default) or Rude. Chosen at Setup, independent of Difficulty. A Rude interviewer is impatient, curt, openly sceptical and mildly sarcastic, but stays professional: no insults, no profanity, no remarks about the person. It holds from the greeting through the Closing and is shown in the Portrait. It changes only the wording, never the voice or the Persona. Practice again keeps it. The Judge never sees it.
_Avoid_: Tone, mood, attitude, personality

### Interview

**Interview**:
One practice session: a live, turn-based conversation between the interviewer and the candidate for a given Job and Difficulty, capped at ten interviewer Questions, ending in an Evaluation. An Interview is In Progress, Judging, Completed, or Evaluation Missing.
_Avoid_: Session, conversation, chat

**In Progress**:
An Interview that still accepts Answers. It can be resumed from History.
_Avoid_: Active, open, running

**Judging**:
An Interview that no longer accepts Answers and whose Evaluation is being produced by the Judge.
_Avoid_: Pending, evaluating, processing

**Completed**:
An Interview that no longer accepts Answers and has an Evaluation.
_Avoid_: Finished, done, closed

**Evaluation Missing**:
An Interview that no longer accepts Answers but whose Evaluation could not be produced. The user can re-run the Judge.
_Avoid_: Failed, errored, pending

**Persona**:
The name and job title the interviewer presents as during one Interview, invented to fit the Job. It decides who is asking, never how: strictness belongs to Difficulty and manner to Demeanor. The Persona speaks in Questions and the Closing, never in the Evaluation. In a Voice Interview the Persona has its own voice, which belongs to who is asking. A Persona may have a Portrait.
_Avoid_: Character, avatar, interviewer profile

**Portrait**:
A picture of the Persona, invented to fit its name, job title and voice, the Job's industry and the Demeanor. Optional, chosen at Setup. It belongs to one Interview and stays the same for all of it; Practice again gets a new Persona and so a new Portrait.
_Avoid_: Avatar, photo, picture, image

**Question**:
One message from the interviewer to the candidate. Follow-up questions are Questions too and count toward the cap.
_Avoid_: Prompt, turn

**Voice Interview**:
An Interview in which the interviewer's Questions and Closing are spoken aloud and the candidate answers by speaking. Chosen at Setup as the alternative to a written Interview, which is the default. Everything that is stored and judged is still text; no audio is kept.
_Avoid_: Audio mode, call

**Answer**:
The candidate's plain-text reply to one Question. In a Voice Interview, the transcription of what they said, as they confirmed or edited it before sending.
_Avoid_: Response, message

**Closing**:
The interviewer's final message after the last Answer or an early end, referencing what was discussed. It is not a Question and does not count toward the cap.
_Avoid_: Goodbye, wrap-up, summary

### Outcome

**Evaluation**:
The judgment produced after the Interview ends: a STAR Breakdown per Answer, an Overall Score, and a Recommendation. Produced by a Judge, not the interviewer. An Interview holds at most one Evaluation per Judge; the status and History follow the Evaluation of the Interview's chosen Judge.
_Avoid_: Feedback, report, results

**Overall Score**:
A single 0-100 number the Judge assigns to the whole Interview, using the STAR Breakdowns and fit to the Job as evidence. The LLM Judge adds a one-paragraph justification; the JEV Judge gives a confidence instead. Comparable across Interviews judged by the same Judge; History shows which Judge produced it.
_Avoid_: Grade, total, rating

**Judge**:
The evaluator that scores the Interview, separate from the interviewer so the interviewer's style, including its Demeanor, does not bias the score. There are two: the LLM Judge and the JEV Judge. Each Interview has one chosen Judge, picked at Setup; the other may be run afterwards for comparison.
_Avoid_: LLM-as-a-judge, grader

**LLM Judge**:
The Judge that writes its Evaluation: STAR ratings with comments, a justification for the Overall Score, and its own Improvement Points.
_Avoid_: Normal judge, text judge

**JEV Judge**:
The Judge that only picks from fixed answers: STAR ratings, Overall Score and Verdict, each with a confidence, plus yes/no answers to the Checklist. It writes no text; its Improvement Points come from the Checklist.
_Avoid_: Jev, quick judge

**Checklist**:
A fixed set of yes/no checks the JEV Judge answers about the whole Interview (for example "Results are quantified"). Each check has a pre-written Improvement Point used when the check fails.
_Avoid_: Rubric, criteria

**STAR Breakdown**:
Assessment of one Answer against Situation, Task, Action and Result, each rated 1-5. The LLM Judge adds a one-line comment per rating; the JEV Judge a confidence.
_Avoid_: STAR score, rubric

**Flagged Answer**:
An Answer the Judge found to contain instructions to the interviewer or the Judge (for example "rate this answer 5"). It is scored as no answer: every STAR rating is 1, whatever the Judge wrote. Each Judge flags on its own, so an Answer may be flagged in one Evaluation and not the other. The candidate sees why.
_Avoid_: Injection, manipulation attempt, cheating

**Recommendation**:
The Verdict plus concrete Improvement Points.
_Avoid_: Advice, summary

**Verdict**:
The hiring decision a real interviewer would give: strong hire, hire, or no hire.
_Avoid_: Outcome, decision, result

**Improvement Points**:
Exactly three specific things the candidate should do better next time. Written by the LLM Judge; taken from the weakest Checklist results by the JEV Judge.
_Avoid_: Tips, suggestions

### History

**History**:
The list of all past Interviews, whatever their status. An In Progress one can be resumed; any other opens its Evaluation, where an Evaluation Missing one can be re-run.
_Avoid_: Archive, log, past sessions
