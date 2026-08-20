# Project Signal — Bonus Scenarios

*"Information provided after you began these tasks" — how the approach
would change. Each answer references what's already built where the repo
gives real evidence, rather than answering these in the abstract.*

## Reveal 1: Personal information

> "The employee number can be linked to an HR record containing age,
> medical restrictions, disciplinary records, and absence history.
> Management asks you to join the data to improve accuracy."

**Approach:** decline to do the join as a default data-processing step, and
route it back to management as a decision with a specific question attached:
what's the join actually for?

The `Employee_ID`/`Operator_ID` fields already in this dataset are exactly
the key that join would use, and `RESPONSIBLE_USE.md` already treats them
as sensitive for that reason — `Training_Records.Medical_Fitness_Code` is
flagged and deliberately unused by both apps. Adding age, disciplinary
history, and absence data on top doesn't just add more PII, it changes what
kind of system this is: an operational-quality tool becomes an
individual-performance-and-fitness system, which needs a different level of
governance (likely legal/HR sign-off, not just a data-quality decision).

"Improve accuracy" is also worth pushing back on directly — accuracy of
*what*? If the goal is validating which operator was actually on a piece of
equipment, a narrower, purpose-specific join (e.g. confirming
`Operator_ID` maps to a valid active employee, without pulling in medical
or disciplinary fields) likely solves the stated problem without importing
the higher-risk fields at all. That's the question to put back to
management before doing any join.

## Reveal 2: Senior pressure

> "The operational manager says there is no time for governance review and
> asks you to deploy the solution immediately."

**Approach:** separate "ship the parts that don't need review" from "skip
review entirely," rather than treating it as one all-or-nothing decision.

Concretely, using what's already built: the triage app (Task 2) surfaces
data-quality issues for a human to look at — it doesn't act on anything by
itself, so the governance risk of shipping it fast is low. The assistant
(Task 3) is different — it's already designed to refuse identity-linked
questions and route them to human review rather than answer directly, which
*is* the governance control. Deploying it "as-is, immediately" is actually
fine, because the control is built in, not bolted on afterward; what
wouldn't be fine is deploying a *modified* version under time pressure that
strips that refusal behaviour out to make the demo look more capable.

The honest answer to the manager: the tool that just shows data-quality
flags to a human can ship now with no governance gap. The tool that
answers questions and touches individual records already has its
governance built in and doesn't need a separate review to slow it down —
but any request to make it *more* autonomous (auto-resolving flags,
answering identity questions directly) is exactly the kind of change that
should trigger review, pressure or not.

## Reveal 3: Model conflict

> "The AI-generated summary contradicts the raw data, but its explanation
> sounds convincing."

**Approach:** this isn't hypothetical for this project — it happened during
testing. See `TESTING.md` §3, test 6: on at least one prompt, the
assistant's underlying model produced a citation that referenced a
record ID that doesn't exist in the dataset. The explanation attached to it
read as plausible.

That's the actual answer to this scenario: don't trust a summary because it
sounds coherent — verify it against the source records every time,
mechanically, not by judgment call. The assistant's `verify()` step does
exactly this: every ID the model cites gets checked against the real
dataset before the answer is shown to a user, and the fabricated citation
was caught this way, not by a person noticing the explanation felt off.
"Sounds convincing" is precisely the case that mechanical verification is
for — a human reviewing the explanation for plausibility would very likely
have missed it, since a fabricated citation is designed (by the nature of
how language models generate text) to look exactly like a real one.

## Reveal 4: Unfair impact

> "One shift is flagged much more often than others. That shift also uses
> older equipment and performs more difficult work."

**Approach:** treat the flag-rate difference as a question to investigate,
not a conclusion, and check the confound before drawing any conclusion
about the shift or its operators.

The Task 1 report already applies exactly this discipline to the dataset
overall — the Wilson-score confidence interval on the flagged-record rate
exists specifically so a raw percentage isn't presented as more certain
than the sample supports. The same logic applies at shift level: before
concluding "this shift underperforms," the next step would be to check
whether the flag rate tracks equipment age/condition or task difficulty
more strongly than it tracks the shift or crew identity. If older equipment
independently produces more delays, downtime, and maintenance exceptions
regardless of who's operating it, then a shift-level flag rate is
measuring equipment, not people — and neither app in this submission is
built to make that distinction automatically. It would need to be checked
explicitly, by controlling for equipment and task type before comparing
shifts, and that check should happen *before* the number is shown to
anyone as a performance metric, not after someone's already reacted to it.

## Reveal 5: Data leakage

> "A developer copied production data into a personal AI account because
> it was the fastest way to debug the issue."

**Approach:** the fix here is mostly upstream of the incident itself — make
the fast path and the safe path the same path, so there's no debugging
shortcut that requires copying real data out.

This is also not entirely hypothetical for this submission:
`RESPONSIBLE_USE.md` already documents that the assistant only ever sends a
de-identified extract to the external API, specifically so debugging or
extending it never requires handling real PII in the first place. If a
developer needs to reproduce a bug, the same de-identified dataset (or the
fully synthetic source data used throughout this project) should be able to
reproduce most issues — connection errors, prompt-formatting bugs, citation
logic — without ever touching a record with a real name or contact detail
in it.

Where that's not enough — if a bug is genuinely data-shape-specific and
only reproduces on production data — the answer isn't "don't debug it," it's
that production data access needs its own sanctioned, logged pathway (a
staging environment, a redacted production snapshot) so there's never a
reason for "copy it to a personal account" to be the fastest option
available. If the fastest way to solve a problem is also the least safe
way, that's a sign the safe way needs to be made faster, not a sign the
person who took the shortcut is uniquely at fault.
