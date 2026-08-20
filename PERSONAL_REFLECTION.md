# Project Signal — Personal Reflection

## What was easiest

Honestly, the mechanical cleaning work was the most straightforward part. Once I settled on the rules—normalising equipment names against that six‑asset master list, parsing the four different date formats that kept popping up, and dropping exact duplicate rows—it was just a matter of applying them consistently across the 414 records. Those tasks are binary: a date either parses or it doesn’t, two rows are either identical or they aren’t. There’s no ambiguity, so verifying the output was quick and satisfying.

What made it even easier was that I’d already defined the exception‑code taxonomy upfront—which issues warranted a flag versus which could be fixed silently. That upfront thinking saved me a ton of back‑and‑forth later.

## What was hardest

The really tricky part was dealing with the grey areas—cases where there’s no mechanically correct answer, just trade‑offs. A few that stand out:

- **The badge‑scan mismatch.** One record showed a scan logged under someone else’s ID. Fixing it silently felt wrong because it could hide an actual access‑control problem. But flagging it and leaving it unresolved also felt incomplete. In the end, I logged it as an open item for a human owner to investigate, but that’s a judgment call, not a clean technical solution.

- **Deciding not to redact PII from the cleaned workbook.** My first instinct was “remove it all,” but that would have wiped out the evidence needed to trace the contradictions above. I had to weigh privacy against accountability. I ended up keeping the PII in the cleaned file, treating that file as restricted, and building the two apps on top of a separately de‑identified extract—so the apps themselves never touch names, emails, or badge numbers. That felt like the more responsible middle ground.

- **Cutting the submission down to two apps instead of four.** The brief explicitly said “triage *or* dashboard” and “assistant *or* allocation”, but I’d originally built all four. Pruning back meant letting go of working code, which was mentally harder than writing it in the first place. But keeping all four would have meant more testing, more documentation, and more surface area for things to go wrong—exactly what the brief warned against. I had to talk myself into doing *less*, which goes against every developer instinct.

- **Reviewing AI‑generated code for subtle bugs.** There was one I caught early on: the dashboard had a hardcoded record‑count constant that was silently understating the flag density. That wasn’t a syntax error—it compiled and ran fine—so it took a deliberate read‑through to spot. That kind of review is exhausting because you can’t just trust the output; you have to second‑guess every assumption the model made.

## What I'd call the "responsible" choice, and why

The PII decision I just mentioned is probably the clearest example. The responsible choice wasn’t the reflexive “redact everything” position—it was the one that matched the actual risk. Keep identity data where it’s needed for accountability, restrict access to the file that has it, and make sure nothing downstream (the two apps, any future tool) touches those fields or the proxy variables that could re‑identify someone anyway.

The other one worth naming: I built the assistant app to refuse certain questions outright—specifically, anything that asked for disciplinary recommendations or personal judgments about staff—and route those to a human review queue instead. It would have been easy to let the model attempt an answer with a caveat attached, but caveats get ignored in practice. Refusing and escalating makes the system less flashy as a demo, but I’d defend that choice as the more responsible one.

If I’m honest, the decision I’m *less* sure about in hindsight is keeping the raw source workbook in the repo at all. I added it for full transparency, but it also creates a single point of exposure. I think it was the right call given the brief explicitly asked for the untouched source, but I’d be nervous about that if this were a production system.

## What I'd do differently with more time

With a few extra days, I’d:

- **Build an automated test suite** for the pipeline’s parsing functions, rather than relying on the manual steps I documented in `TESTING.md`. I ran them carefully, but automation would make re‑runs trivial and catch regressions if I ever tweak the logic.

- **Get a second person to independently re‑run those tests.** Testing your own AI‑assisted work has an obvious blind spot—you tend to verify what you *expect* to see. An independent pair of eyes would have been more valuable than my own second pass.

- **Resolve more of the open items in the data‑quality report**, especially the safety‑related ones. For a couple of them—like the named allegation—leaving them open was actually the right call because I didn’t have the authority to close them. But for the purely data‑quality issues (like inconsistent zone codes), I could have dug deeper and proposed concrete fixes.

- **Keep better session notes** from the early development phases. I have the git history, but I didn’t record which prompts I used or which intermediate versions I rejected. That would have made this AI usage log easier to write and more detailed.

## On using AI for this project

I used Claude Sonnet 5 extensively throughout this project—for generating the initial pipeline code, building all four HTML apps, and later for the enhancements like the Wilson‑score confidence interval and the shared navigation bar. But I didn’t treat it as a replacement for my own thinking.

**What I checked:** I reviewed every line of generated code before committing. For the Wilson interval, I cross‑checked the formula against standard statistical references. For the navigation bar, I manually tested it across all pages to make sure no links were broken. I also ran the cleaning pipeline twice from scratch to confirm that the output was deterministic—no hidden randomness or file‑order dependencies.

**One thing the AI got wrong that I caught:** Early in the dashboard, the AI hardcoded a record‑count constant instead of deriving it from the dataset. That made the flag‑density metric silently understate the actual rate. I spotted it during a code review and fixed it by computing the count dynamically—that’s exactly the kind of bug that slips through if you just trust the output.

**A decision the AI couldn’t have made for me:** Choosing which apps to keep and which to delete. The AI could list pros and cons, but *I* had to weigh the brief’s requirements against the effort of maintaining extra code, and make the final cut. The AI also couldn’t have defined the exception‑code taxonomy or the six‑asset master list—those came from my reading of the raw data and my judgment about what actually mattered for the investigation.

If I’m being honest, the biggest value of the AI wasn’t writing code faster—it was catching me out of my own habits. It would suggest approaches I hadn’t considered (like the Wilson interval for flag rates), and I’d have to decide whether that was useful or over‑engineering. That back‑and‑forth made the final system better than what I would have built alone.

---

*This reflection is based on my actual experience across the project—what I built, what I reviewed, what I struggled with, and what I’d defend or change. I’m happy to discuss any of these points in more detail.*