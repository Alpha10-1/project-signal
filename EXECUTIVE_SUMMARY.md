# Project Signal — Executive Summary

*For a non-technical manager. One page.*

## What this is

Nine operational logs from the mine (equipment, delays, shift performance,
safety, training, maintenance, environmental readings, access control, and
operator activity) were checked for data quality, cleaned, and turned into
two working tools: one that helps a reviewer triage data problems, and one
that answers plain-language questions about the operation with evidence
attached to every answer.

## Can we trust the data?

**Not as-is, but yes once it's been through the cleaning process included
here.** About 1 in 4 records (105 of 414) had at least one issue — mostly
minor and fixable: missing approval sign-offs, inconsistent spelling of
equipment names, dates recorded in different formats. All of that has been
resolved.

A smaller number of issues are more serious and are flagged for a person to
decide on, not something a script should quietly fix:

- **6 records genuinely contradict each other** — for example, a delay's
  stated duration doesn't match its own start/end time, or a safety
  observation shows a closing date earlier than the date it was opened.
- **One access-badge scan is logged under someone else's ID.**
- **One safety report names an individual alongside an unproven
  allegation** — this has been set aside for the normal safety-review
  process rather than processed automatically.

None of these were deleted or silently corrected. They're listed, with
exact record numbers, so whoever owns each source system can make the call.

## What was built

1. **A triage tool** — shows every data-quality issue found, filterable and
   searchable, with a button to export a working list for review.
2. **An assistant** — answers questions like "which equipment had unusually
   high downtime?" and shows exactly which records back up the answer. If
   it can't find enough evidence to answer safely, it says so instead of
   guessing. Questions that would require identifying or judging a specific
   person are routed to a person to answer, not the assistant.

## What needs a decision before this goes further

- The full cleaned dataset still contains real names, emails, and phone
  numbers — that copy needs to be treated as personal data (access
  controlled), not shared broadly. The two tools above don't have this
  problem; they only see anonymised IDs.
- A few open questions need a business owner's sign-off (listed in the full
  data-quality report) — none were guessed at or defaulted silently.
- This is a working prototype, not a production system. It hasn't been
  tested against a live data feed or a larger dataset, and it has no
  automated safeguards beyond what a person can currently review manually.

## Bottom line

The underlying data is usable and the messiness is now well understood and
documented — but a handful of specific records need a human decision before
anyone acts on them, and the personal-data handling needs a policy decision
before this moves beyond a prototype.