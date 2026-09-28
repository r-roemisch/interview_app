# A JEV Judge alongside the LLM Judge, with Improvement Points from a fixed Checklist

The user picks a Judge per Interview: the LLM Judge (ADR-0002) or the JEV Judge, TypeSafe's typed-decision model reached through OpenRouter. JEV cannot write text, so a JEV Evaluation has STAR ratings, an Overall Score and a Verdict, each with a confidence, but no comments or justification. Its three Improvement Points come from a fixed Checklist of yes/no checks, each with pre-written wording: the app takes the three checks JEV was least sure were met. We accept a Judge that cannot explain itself because it is fast, very cheap and not biased by persuasive wording, and because comparing it with the LLM Judge on the same transcript is the point of the feature. Having an LLM write the missing text from JEV's scores was rejected: it would bring back the cost and bias JEV is meant to avoid.

## Consequences

- An Interview holds at most one Evaluation per Judge. The status and the History score follow the chosen Judge; the other Judge can be run afterwards for a side-by-side comparison.
- Overall Scores are only comparable between Interviews judged by the same Judge, so History shows which Judge produced each score.
- JEV is called through the TypeSafe SDK, not the `openai` SDK, so the app has two model clients.
- No automatic escalation from JEV to the LLM Judge: thresholds would need calibration data the project does not have. JEV's confidence is shown to the user instead.
