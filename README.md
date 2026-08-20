# Project Signal — AI Junior Analyst Submission

Fictional mining-operations dataset: cleaned, reconciled, and turned into two
working applications. This README covers what's in the repo and how to run
each piece.

## Contents

| Path | What it is |
|---|---|
| `project_signal_raw.xlsx` | **Untouched source data**, exactly as supplied. Not modified anywhere in this repo. |
| `project_signal_cleaned.xlsx` | Output of the cleaning pipeline: raw sheets, cleaned sheets, `Exception_Log`, `Duplicates_Removed`, `Run_Info`, `Sheet_Record_Counts`, plus `README` and `Data_Quality_Summary` cover tabs. |
| `Project_Signal_Task1_Data_Quality_Report.docx` | Task 1 write-up: methodology, findings by issue type, cross-record contradictions, PII/proxy-variable inventory, open items, appendices. |
| `scripts/common.py` | Shared date parser and equipment-name normaliser. |
| `scripts/clean_project_signal.py` | Task 1 pipeline — one cleaning function per dataset, produces `project_signal_cleaned.xlsx`. |
| `scripts/finalize_workbook.py` | Applies formatting and adds the `README`/`Data_Quality_Summary` cover tabs to the cleaned workbook. |
| `scripts/project_signal_triage.html` | **Task 2 submission** — data-quality triage app. |
| `scripts/project_signal_assistant.html` | **Task 3 submission** — evidence-grounded assistant. |

Task 2 and Task 3 each offered a choice of two deliverables. This submission
uses the triage app and the assistant — see [Why these two](#why-these-two)
below for the reasoning.

## How to run

### Task 1 — regenerate the cleaned workbook

Requires Python 3 with `pandas`, `numpy`, and `openpyxl`.

```bash
cd scripts
pip install pandas numpy openpyxl
python3 clean_project_signal.py ../project_signal_raw.xlsx ../project_signal_cleaned.xlsx
python3 finalize_workbook.py ../project_signal_cleaned.xlsx
```

The first command runs the exception-detection and cleaning rules and writes
the raw/cleaned/exception sheets. The second applies formatting and adds the
cover sheets. `project_signal_cleaned.xlsx` in this repo is the already-built
output — you only need to re-run this if you change the source data or the
cleaning rules.

### Task 2 — data-quality triage app

No install needed. Open `scripts/project_signal_triage.html` directly in a
browser (double-click, or `open scripts/project_signal_triage.html`). It's a
static, self-contained page with the exception data embedded, so it works
offline with no server.

What it does: shows every one of the 117 flagged records from
`Exception_Log`, filterable by issue type and sheet, with the detail behind
each flag. Reviewers can annotate/clear flags and export the filtered set as
CSV.

### Task 3 — evidence-grounded assistant

Also a static, self-contained HTML file — open
`scripts/project_signal_assistant.html` directly in a browser.

What it does: answers questions about the cleaned dataset (e.g. "which
assets had unusually high downtime?"), cites the specific record IDs behind
every claim, and independently re-verifies each citation against the actual
data before showing an answer. If it can't support an answer with evidence,
it says so rather than guessing. Requests that need identity data not
present in the cleaned dataset are routed to the human review queue rather
than answered.

> **Note:** this app calls the Claude API to generate answers, then checks
> the response against the source records before displaying it — the
> verification step is local and doesn't depend on the model being correct.
> If you're running this outside an environment with API access configured,
> the chat interface will load but won't return answers.

## Why these two

The brief offered a choice for Task 2 (triage app **or** operational
dashboard) and Task 3 (evidence-grounded assistant **or** ethical allocation
prototype). Earlier drafts built all four; this submission keeps two to
match the brief's scope and to keep the testing/documentation surface
honest.

- **Triage app over dashboard**: the Task 2 candidate brief specifically
  asks for a scorecard, missing-value/duplicate/outlier detection,
  invalid-date detection, and a downloadable exception file. The triage app
  is built directly on the pipeline's own `Exception_Log` and covers each of
  those points; the dashboard is closer to an operational-performance view
  than a data-quality one.
- **Assistant over allocation prototype**: the Task 3 candidate brief's
  example questions ("which assets had unusually high downtime," "show the
  records supporting the answer") are answered close to verbatim by the
  assistant, which also implements the citation-verification and
  human-review-escalation behaviour the brief calls "governance and
  human-review controls."

## Other deliverables in this submission package

Alongside this repo:

- Data-quality report (`Project_Signal_Task1_Data_Quality_Report.docx`)
- Testing evidence
- Responsible-use note
- AI usage log
- Executive summary (one-pager)
- Personal reflection

See the individual files for each of these.

## A note on the data

The source workbook's own cover sheet states the dataset is intentionally
messy and should not be treated as a real operational record. All names,
IDs, and figures in this repo are fictional.
