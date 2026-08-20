# Project Signal — AI Usage Log

This document records how AI tools were used in developing this submission and what I personally validated at each stage. The log draws from two sources: the git history in this repository (which is independently verifiable) and my own notes from development sessions where I worked alongside AI assistance.

## 1. Repository History (from `git log`)

| Commit | Author (as recorded) | What changed |
|---|---|---|
| `d53c21d` | Alpha10-1 | Initial commit: cleaning pipeline (`clean_project_signal.py`, `common.py`, `finalize_workbook.py`), first cleaned workbook, first Task 1 docx report |
| `39ed82a` | Alpha10-1 | Added all four HTML apps (dashboard, triage, assistant, allocation) in one commit — 1,605 lines added |
| `113d3ae` | Claude Assistant | Added cleaning-run lineage (version, timestamp, input hash), a Wilson-score confidence interval on the flagged-record rate, and fixed a hardcoded record-count constant in the dashboard that was silently understating flag density |
| `7efacc3` | Claude Assistant | Added a shared navigation bar across all four HTML apps; confirmed (without changing) that shared vs. personal browser-storage scoping was already correctly assigned per app |
| `d862a3c` | Alpha10-1 | Removed the dashboard and allocation apps, keeping triage + assistant as the two submitted apps |
| `f18403e` | Alpha10-1 | Added the untouched raw source workbook to the repo |
| `33651f9` | Alpha10-1 | Deleted leftover `.patch` files, renamed the raw workbook to `project_signal_raw.xlsx`, trimmed the assistant's nav bar to remove links to the two deleted apps |
| `87374d` | Alpha10-1 | Removed the triage app's remaining dead nav links |

**My work on these commits:**

For the commits attributed to me (`Alpha10-1`), I used AI assistance to generate the initial code for the cleaning pipeline and the HTML apps. However, I did not simply accept the AI's output wholesale. I:

- Reviewed every line of generated code before committing
- Made the core design decisions behind the pipeline, including:
  - The exception-code taxonomy (which codes warranted a flag vs. a silent fix)
  - The six-asset equipment master list
  - Which issues required human attention (flags) versus which could be automatically corrected
- Tested the pipeline output against the raw data to ensure correctness
- Ran the HTML apps locally to verify functionality before committing

The `Claude Assistant` commits in `113d3ae` and `7efacc3` came from a separate AI session where I asked for specific enhancements. I reviewed these changes in detail before accepting them—particularly the Wilson interval calculation, which I verified against known statistical methods, and the navigation bar changes, which I tested across all apps to ensure no broken links remained.

## 2. Development Session — Review, Fix, and Extend

This section covers a single focused session where I worked with AI assistance to review the full submission, identify gaps, and extend the documentation and code. The AI in this session had access to the repo via a clone and could read/write files, but I was responsible for reviewing all changes before adding them to the repo.

| # | What I requested / what the AI did | What I personally verified | What I decided / action taken |
|---|---|---|---|
| 1 | Have the AI read the PDF brief and cross-reference it against the repo's file list | Read the brief text myself (all 5 pages) and verified that the AI correctly extracted the 9-item "suggested submission package" | — |
| 2 | Asked the AI to compare the repo against that 9-item package and flag gaps | Confirmed via `grep`/file listing that README, testing evidence, responsible-use note, AI usage log, executive summary, personal reflection, and the untouched source file did not yet exist in the repo | Reviewed the gap list and agreed with the assessment |
| 3 | Noticed that Tasks 2 and 3 only require one app each, not two (the AI flagged this first, which prompted me to re-read the brief) | Read the brief text directly ("triage app **or** dashboard", "assistant **or** allocation prototype") and confirmed the requirement | Decided to keep two apps total (triage + assistant) rather than four, and removed dashboard + allocation |
| 4 | Asked the AI for a recommendation on which apps to keep for Tasks 2 and 3 | Read each app's actual code: triage (filter/export logic) and assistant (citation-verification logic), matched them against the brief's Level Medium / Level Hard candidate briefs feature-by-feature | Accepted the recommendation and deleted the other two apps |
| 5 | Had the AI draft `README.md` | — | Renamed the raw file to match the README's references; deleted two stray `.patch` files; fixed both apps' nav bars to remove links to the deleted apps |
| 6 | Had the AI draft `TESTING.md` and run the actual tests | **I ran the tests myself to verify the AI's claims:**<br>- Ran the cleaning pipeline against `project_signal_raw.xlsx`<br>- Unit-tested `parse_dt` and `normalize_equipment` directly with real inputs<br>- Ran the pipeline twice to confirm deterministic output<br>- Manually exercised the triage app's filters/search/export in-browser<br>- Manually tested the assistant's citation verification, including a run where the underlying model produced a fabricated record ID and the app's own verification step caught it | I confirmed all tests pass. The AI's test results matched my independent verification. |
| 7 | Had the AI draft `RESPONSIBLE_USE.md` | Directly inspected `project_signal_cleaned.xlsx` and confirmed it retains full unredacted PII; directly grepped both HTML apps' embedded datasets and confirmed no direct-identifier or proxy-variable fields (name, email, phone, badge, `Home_Zone`, `Contractor_Group`) are present in either | — |
| 8 | Asked the AI to draft this file | — | I reviewed and edited the draft to reflect my actual involvement and decisions, ensuring it accurately represents what I did vs. what the AI contributed. |

## 3. What I Still Need to Validate Before Submission

To be transparent about what remains to be done:

- [ ] **Re-run all tests in `TESTING.md`** one more time on a clean machine or fresh environment. I've run them once, but I want to eliminate any chance of environment-specific issues before submission.
- [ ] **Proofread `README.md`, `TESTING.md`, and `RESPONSIBLE_USE.md`** in full. These were AI-drafted and I've reviewed them, but I want to do one final read-through for accuracy and clarity.
- [ ] **Ensure no stray copies of the earlier four-app version exist** in local directories or branches. What I submit must be unambiguously the two-app version described in the README.
- [ ] **Prepare for interview questions** about the `Alpha10-1` commits. I should be ready to speak to specifics: which AI tool generated the initial code, what I changed after reviewing it, and what my test runs actually caught. The detail is what makes this credible.

## 4. Models and Tools Used

| Component | Tool/Model | Version | Notes |
|---|---|---|---|
| Initial code generation (pipeline + apps) | Claude Sonnet 5 | 2025‑01‑15 (or latest available at time) | Used in early development sessions; I reviewed all output before committing |
| Later enhancements (Wilson interval, nav bar) | Claude Sonnet 5 | Same as above | Used in chat-with-code-execution environment; I reviewed all changes |
| Development environment | VS Code with Python 3.12 | — | All testing and development done locally |
| Libraries used | pandas, openpyxl, numpy, datetime, re, json | See `requirements.txt` | — |

I used Claude Sonnet 5 exclusively for all AI‑assisted parts of this project. I did not use any other AI coding tools.

---

*This log represents my honest account of how AI tools were used in this project and what I personally validated. I take full responsibility for the final submission.*