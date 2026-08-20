# Project Signal — AI Usage Log

This document records how AI tools were used in developing this submission and what I personally validated at each stage. The log draws from two sources: the git history in this repository (which is independently verifiable) and my own notes from development sessions where I worked alongside AI assistance.

## 1. Repository History (from `git log`)

| Commit | Author (as recorded) | What changed |
|---|---|---|
| `d53c21d` | Alpha10-1 | Initial commit: cleaning pipeline (`clean_project_signal.py`, `common.py`, `finalize_workbook.py`), first cleaned workbook, first Task 1 docx report |
| `39ed82a` | Alpha10-1 | Added all four HTML apps (dashboard, triage, assistant, allocation) in one commit — 1,605 lines added |
| `113d3ae` | Claude Assistant | Added cleaning-run lineage (version, timestamp, input hash) and a Wilson-score confidence interval on the flagged-record rate. Also fixed a hardcoded record-count constant in the dashboard that was silently understating flag density — the candidate reports having independently caught this issue before this commit and requested the fix; the AI implemented it. |
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

## 3. Development Session — Free-Tier Backend Swap (Assistant)

A separate, later session, after everything above was already in place: I
asked whether a free API existed so the assistant app could be evaluated by
a reviewer without anyone incurring an API cost. The AI recommended
Google's Gemini API (free tier, no card required) and I asked it to make
the swap.

| # | What I requested / what the AI did | What I personally verified | What I decided / action taken |
|---|---|---|---|
| 1 | Asked for free API alternatives to a paid model API | Reviewed the AI's comparison (Gemini, Groq, OpenRouter) and the trade-offs it raised (rate limits, request/response format differences, free-tier data-use terms) | Chose Gemini for context size and answer quality |
| 2 | Had the AI rewrite the assistant's backend call from Claude's API to Gemini's, including an in-page field for a user-supplied API key | Ran the app myself after the change | Found it returned a 404 — the model ID the AI used (`gemini-2.5-flash`) had been retired for new users in the time since the AI's training data. Reported this back with the console error. |
| 3 | Asked the AI to fix the 404 | Re-ran the app | AI corrected the model ID to the current free-tier model. Also independently caught and fixed an unrelated bug it noticed: the shared nav bar's "current page" link pointed at its own filename, which browsers block when running the file directly from disk — I hadn't noticed this one myself, it showed up as a console warning the AI explained |
| 4 | Asked a real aggregation question ("which truck lost the most time to delays") to test it | Read the actual response — it was garbled, mid-calculation text, not a real answer | Reported the exact broken output back to the AI rather than assuming it was a one-off glitch |
| 5 | Asked the AI to diagnose and fix the garbled-answer issue | Re-tested the same question | AI identified the root cause (the model's internal reasoning tokens were exhausting the output budget before finishing the JSON) and added token-budget and truncation-detection changes | 
| 6 | Re-tested after that fix | Got a `400 Bad Request` this time, different failure | Reported the new error text verbatim | AI identified this as a separate, unrelated API contract issue (a deprecated parameter name for the newer model generation) and fixed it |
| 7 | Re-tested again | Same garbled-answer symptom as #4 recurred on the multi-truck comparison question specifically | Reported this immediately rather than treating the earlier fix as sufficient | AI widened the token budget further and changed the reasoning-effort setting; I re-tested and confirmed the fix held |
| 8 | Asked the AI to update this log, `README.md`, `RESPONSIBLE_USE.md`, and `TESTING.md` to reflect the backend swap accurately | Read every changed section myself | Accepted the drafts after confirming they matched what actually happened in this session, including keeping the *un*successful intermediate attempts visible in `TESTING.md` rather than only recording the final working state |

**Why I'm keeping the failed intermediate attempts in this log and in
`TESTING.md`, not just the final fix:** a submission that only shows things
working can't be told apart from one where the failures were never
disclosed. The 404, the two separate 400/truncation bugs, and the fact that
the first truncation fix didn't fully hold are all real parts of how this
integration got built, and I think that's more credible than a log that
only shows a clean path to success.

## 4. What I Still Need to Validate Before Submission

To be transparent about what remains to be done:

- [ ] **Re-run all tests in `TESTING.md`** one more time on a clean machine or fresh environment. I've run them once, but I want to eliminate any chance of environment-specific issues before submission.
- [ ] **Proofread `README.md`, `TESTING.md`, and `RESPONSIBLE_USE.md`** in full. These were AI-drafted and I've reviewed them, but I want to do one final read-through for accuracy and clarity.
- [ ] **Ensure no stray copies of the earlier four-app version exist** in local directories or branches. What I submit must be unambiguously the two-app version described in the README.
- [ ] **Prepare for interview questions** about the `Alpha10-1` commits. I should be ready to speak to specifics: which AI tool generated the initial code, what I changed after reviewing it, and what my test runs actually caught. The detail is what makes this credible.
- [ ] **Re-test the Gemini backend swap with a fresh, never-used API key** on a machine that hasn't already hit any free-tier rate limits, to confirm the fixes in `TESTING.md` §3a hold outside my own development session.

## 5. Models and Tools Used

| Component | Tool/Model | Version | Notes |
|---|---|---|---|
| Initial code generation (pipeline + apps) | Claude Sonnet 5 | 2025‑01‑15 (or latest available at time) | Used in early development sessions; I reviewed all output before committing |
| Later enhancements (Wilson interval, nav bar) | Claude Sonnet 5 | Same as above | Used in chat-with-code-execution environment; I reviewed all changes |
| Backend swap (Claude API → free Gemini API) in the assistant app | Claude Sonnet 5 | Same as above | The coding assistant used to make this change; the assistant *app itself* now calls Google's Gemini API (`gemini-3.6-flash`) at runtime as its own separate AI backend — see §3 above and `TESTING.md` §3a |
| Development environment | VS Code with Python 3.12 | — | All testing and development done locally |
| Libraries used | pandas, openpyxl, numpy, datetime, re, json | See `requirements.txt` | — |

I used Claude Sonnet 5 exclusively as my coding assistant for all AI‑assisted
parts of this project. Note the distinction: Claude Sonnet 5 is the tool I
worked with to build and fix this repo; Google's Gemini API is what the
submitted assistant app itself calls at runtime to answer a reviewer's
questions. These are two different things — one is how the software was
built, the other is what the shipped software runs on.

---

*This log represents my honest account of how AI tools were used in this project and what I personally validated. I take full responsibility for the final submission.*