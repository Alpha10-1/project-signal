# Project Signal — Responsible-Use Note

This note covers privacy, fairness, security, transparency, human oversight,
and limitations for the Task 1 pipeline and the two apps submitted for
Tasks 2 and 3. It's written for whoever has to decide whether, and how, this
could move from prototype to something people actually rely on.

## Privacy

**`project_signal_cleaned.xlsx` contains full, unredacted PII.** This was a
deliberate decision for Task 1, not an oversight — see the report §1.5 and
§5. The raw sheets carry operator full names, personal emails, mobile
numbers, badge IDs, and certificate numbers exactly as supplied, and the
cleaned copy doesn't strip any of it. The reasoning: several of the
cross-record contradictions flagged in Task 1 (e.g. a badge scanned under an
ID belonging to someone else) can only be checked by a reviewer if the
identity fields are still there. Stripping them at cleaning time would have
hidden the evidence, not protected anyone.

The consequence is that **this file needs to be handled like the personal
data it contains** — access-controlled, not emailed around, not attached to
a public deck. It should not be treated as safe to distribute just because
it says "cleaned."

**The two apps do not carry this risk.** Both `project_signal_triage.html`
and `project_signal_assistant.html` embed a separately-built extract that
excludes direct identifiers entirely — no names, emails, phone numbers,
badge IDs, or certificate numbers appear in either file. The assistant
retains only pseudonymous `Operator_ID` / `Employee_ID` / `Reporter_ID` /
`Observed_Person_ID` values, and is instructed to refuse any request that
asks it to reconstruct or guess a real identity from those IDs (see its
system prompt, rule 5). This was checked directly, not assumed — neither
HTML file contains any of the direct-identifier field names or values
present in the raw workbook.

**The assistant calls an external API to generate answers.** Only the
de-identified extract described above is sent as part of that call — the
full-PII cleaned workbook is never transmitted anywhere by either app. This
matters for the "Reveal 5: Data leakage" scenario in the brief: the design
already avoids sending raw personal data to an external AI service, which is
the failure mode that scenario describes.

## Fairness

The Task 1 report (§5.2) flags `Home_Zone` and `Contractor_Group` as proxy
variables: each of the 8 operators has a fixed, unique pairing of the two,
so either field alone can re-identify a specific person even without a
name attached. Neither field is included in either app's dataset, for the
same reason direct identifiers were excluded — a filter or ranking "by zone"
would functionally be a ranking by person, not an anonymous operational
metric.

More broadly, any tool built on top of this data that ranks, scores, or
flags people or shifts should be treated with the same caution the brief's
own bonus scenario raises: a shift that's flagged more often isn't
necessarily performing worse — it may be running older equipment or harder
work. Neither app in this submission currently does person- or shift-level
scoring, but if this were extended toward the "ethical allocation"
direction, that conflation is the first thing to test for before trusting
any output.

`Training_Records.Medical_Fitness_Code` (report §5.3) is flagged in the
source data's own dictionary as a restricted fitness code. It's retained in
the cleaned workbook (tagged in a `_Sensitive_Fields` column) but is not
used by either app. It should not be joined against performance, safety, or
allocation data without a specific authorised purpose and access controls —
this is a field that needs a hard gate before any downstream use, not an
opt-in checkbox added later.

## Security

- Neither app has a backend. Both are static, self-contained HTML/JS files
  that run entirely in the browser — there's no server-side data store to
  secure or misconfigure.
- The triage app's review decisions (status, reviewer, notes) are stored
  client-side only. They don't sync between machines or users. This is a
  reasonable limitation for a prototype but means the "who reviewed what"
  trail is not currently tamper-evident or centrally auditable — see
  Limitations below.
- The assistant depends on a live call to `api.anthropic.com`. If this were
  deployed beyond a demo, that call would need to go through whatever
  logging, rate-limiting, and access-control layer the organisation
  normally puts in front of an external API — none of that exists in this
  prototype.

## Transparency

- Every exception the triage app shows traces back to a documented code
  (`DUP`, `MISSING`, `OUTLIER`, etc.) with a plain-language description —
  nothing is a black-box flag. The full code list and counts are in the
  Task 1 report §2 and Appendix A.
- The assistant is instructed to cite the specific record IDs behind every
  factual claim, and the app independently re-checks each cited ID against
  the real dataset before displaying the answer — this was tested directly
  (see `TESTING.md` §3, test 6), including a case where the underlying
  model produced a citation that didn't exist and the verification step
  caught it. The verification is what makes "evidence-grounded" a testable
  claim rather than a description.
- Where the assistant can't support an answer with evidence, it's
  instructed to say so rather than fill the gap with general knowledge —
  also confirmed in testing.

## Human oversight

- The assistant routes two categories of request to a human review queue
  rather than answering directly: anything asking it to identify, rank, or
  make an employment/discipline decision about a specific individual, and
  anything asking for PII that isn't in the de-identified dataset. Both
  were tested and confirmed working (`TESTING.md` §3, tests 4–5).
- The triage app's review workflow (Open → Reviewed, with reviewer and
  note fields) exists so a human explicitly clears each flag rather than
  the pipeline silently deciding what's safe to ignore — matching the
  Task 1 report's stated principle (§1.5) that no exception is auto-resolved.
- Several items in the Task 1 report (§6) are explicitly left as open
  questions for a human decision-owner rather than resolved by the
  pipeline — e.g. the `MNT.Priority="Urgent"` mapping, the unmapped
  equipment code `TRK099`, and the named allegation in `SAF0027`. None of
  these were silently defaulted.

## Limitations

- The full-PII cleaned workbook (`project_signal_cleaned.xlsx`) needs
  access controls before wider distribution — see Privacy above. This
  submission does not include a redacted/masked variant, because Task 1
  treats redaction as a purpose-and-governance decision that belongs with
  whoever owns the downstream use case, not something a cleaning script
  should decide silently. If this moved toward production, a masked export
  path would need to be built and the decision of who gets which version
  formally owned by someone.
- Triage app review state is local to one browser/machine (see Security).
- The assistant has no offline fallback — without API access it loads but
  cannot answer questions.
- No automated regression test suite exists yet; all testing was manual and
  is recorded in `TESTING.md`. The pipeline's parsing/normalisation
  functions are pure functions and would be the easiest place to start if
  this were to continue past prototype stage.
- Both apps were built and tested against the exact 414-record dataset
  supplied. Behaviour on a larger or structurally different dataset (new
  equipment, new sheet, different date formats) is unverified.
- If a real HR record were ever joined to this data (per the brief's
  Reveal 1 scenario), everything in this note about proxy variables and
  fairness would need re-evaluating before that join happened, not after —
  age, medical restrictions, disciplinary records, and absence history are
  exactly the kind of fields that turn an operational dataset into one
  capable of individual-level consequence.
