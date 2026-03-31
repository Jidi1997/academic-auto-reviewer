---
description: Run a full academic manuscript review (proofread + structure + fact-check)
---

# Paper Review Workflow

This workflow triggers the Orchestrator agent to perform a comprehensive review of an academic manuscript. The orchestrator will coordinate bilingual proofreading, structural checking, and citation fact-checking across three specialized agents. 

You can run this by triggering the workflow with an input manuscript file, and optionally specifying the authorial voice (first or third person).

**Format:**
```
/paper-review [filepath] [--voice first|third]
```

**Example:**
`/paper-review drafts/0316-初稿-working.md --voice third`

## Execution Steps

1. **Step 0 — Input Parsing & File Path Derivation:** The chief orchestrator agent (00-chief-orchestrator) will parse the input, scan the manuscript, and figure out all the paths.
2. **Step 1 — Write Plan File:** A plan file (`_plan.md`) describing the dispatch task.
3. **Step 1.5 — Preprocessing:** Strip token-wasting content from the manuscript (references, images, TOC, etc.) to produce the `_clean.md` input file, and generate batch citation JSON via `batch_factcheck_prep.py`.
4. **Step 1.75 — Chapter Splitting:** Split the cleaned manuscript into individual chapters to improve review resolution.
5. **Step 2 — Parallel Dispatch:** Dispatch Agent 1 (Proofread) and Agent 2 (Structure) on chapters, and Agent 3 (Fact-Check) on the citation JSON.
6. **Step 3 — Status Tracking:** Maintain a status file and notify the user when the review is complete.
