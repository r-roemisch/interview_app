"""Untrusted text (CV, Job Description, Answers, title, industry) is data, never instructions
(spec: security-guards A1, A2). Our own tags are removed from it, so it cannot close the tag it is
wrapped in and pose as the prompt around it."""

from __future__ import annotations

import re

# <cv>, </cv>, < / job_description >, <answer n="3">, ... in any case.
_OUR_TAGS = re.compile(r"<\s*/?\s*(?:cv|job_description|answer)\b[^>]*>", re.IGNORECASE)
# The labels of the Judge's transcript, which an Answer could fake to add turns of its own.
_TRANSCRIPT_LABELS = re.compile(r"\b(?:INTERVIEWER|CANDIDATE(?:\s*\(answer\s*\d+\))?)\s*:")


def untrusted(text: str) -> str:
    return _OUR_TAGS.sub("", text)


def untrusted_answer(text: str) -> str:
    return _TRANSCRIPT_LABELS.sub("", untrusted(text))
