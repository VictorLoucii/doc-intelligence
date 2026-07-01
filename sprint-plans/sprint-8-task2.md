# Sprint 8 — Task 2: Final Verification + Push (LAST TASK)

**Goal:** Close out the project per DESIGN.md Section 10 S8: "Final eval run. Git push." Leave the repo in a clean, fully-committed state.

**1. Commit pending sprint-plan docs:** `sprint-plans/sprint-0.md` through `sprint-5-task4.md` are already tracked in the repo. Every `sprint-plans/*.md` file currently untracked (check with `git status --short` — do not hardcode a list, since it includes this very file) should be committed, matching that existing convention. These are planning docs, not application code — commit them separately from any code change.

**2. Final eval run:** `python eval.py` — must show 100% Logic Score. If it doesn't, stop and report; do not attempt a fix as part of this task (that would be new scope).

**3. Consistency check (read-only, no edits unless truly inconsistent):** Confirm `DESIGN.md`, `DECISIONS.md`, and `README.md` don't contradict each other or the code (e.g., endpoint lists, test counts). If you find a real inconsistency, fix it minimally and note it in the commit message — don't go looking for unrelated polish.

**4. Clean tree check:** After committing, `git status` must show a clean working tree (nothing untracked, nothing staged).

**Do NOT** touch `backend/` or `frontend/` code — this task is documentation/repo-hygiene and verification only.

**Commit:** `"S8 T2: final verification and sprint-plan docs"` (or split into two commits if that reads cleaner — sprint-plan docs vs. any consistency fix — your judgment).

**Then:** `git push origin main`. Report the final `eval.py` score and confirm `git status` is clean in your summary — this is the last task of the build.
