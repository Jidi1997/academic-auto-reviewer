# Architecture & Workflow Deep Dive

This document explains the internal mechanisms of the **academic-auto-reviewer** ecosystem. It is intended for power users, developers, and researchers seeking absolute transparency on how their manuscripts undergo automated, zero-hallucination peer review.

---

## Core Philosophy: Multi-Agent Collaboration & Zero-Hallucination RAG

At the heart of this system is a multi-agent parallel workflow coordinated by the **Orchestrator**. It dispatches three specialized agents: the **Linguist** for textual polishing, the **Architect** for logical evaluation, and the **Auditor** for the most critical task—fact-checking.

Large Language Models (LLMs) are notorious for "hallucinating" academic citations and falsely confirming empirical claims. To solve this, our ecosystem enforces strict **Natural Language Inference (NLI)** constraints on the **Auditor** agent. The agent is completely restricted from drawing upon its internal training data or using live web-search. It evaluates claims **only** against exact textual excerpts fetched from your local Markdown database (pre-processed by *mark-lit-down*), ensuring a closed-loop validation process.

---

## Phase 1: Input Parsing & Command Execution

The entire process begins when the user triggers the workflow via the AI agent terminal:

```bash
/paper-review drafts/my_manuscript.md --voice third
```

Upon sensing this trigger, the `orchestrator` parses your arguments. If `--voice third` is detected, it applies a third-person narrative preference, which ensures stylistic alignment across all specialized agents.

---

## Phase 2: Pre-Processing Pipeline (`tools/`)

To maximize token usage and reduce "cognitive load" on the AI editor, the Orchestrator delegates a cleanup process to local python scripts.

### 1. `preprocess_manuscript.py`
This tool reads your draft and strips out elements irrelevant to rhetorical analysis:
- **References & Bibliography Block**
- **Figures, Images, and Captions**
- **Tables and Data Structures**

The output is a lightweight `_clean.md` file representing only the pure textual narrative. This file is then cleanly split into chapters (`ch01.md`, `ch02.md`) to drastically increase the LLM's resolution and attention span per section.

---

## Phase 3: Evidence Linking Workflow

Before the `auditor` ever sees the document, the ecosystem executes `batch_factcheck_prep.py`. This script represents the critical Retrieval-Augmented Generation (RAG) link.

1. **Extraction**: Uses Regex to find every APA/Author-Date standard citation in your clean draft.
2. **Bib Lookup**: Cross-references the citation with your local `.bib` file to find the `citekey`.
3. **Database Fetch**: Once the `citekey` is identified, it executes `read_literature.py` to extract the exact text from your **local Markdown database** (generated beforehand by *mark-lit-down*).
4. **JSON Construction**: The citations and their exact corresponding source-texts are compiled into a massive, heavily-constrained JSON file.

---

## Phase 4: Parallel Agent Dispatch

With preprocessing and JSON construction fully complete, the `orchestrator` launches three specialized agents in parallel execution spaces.

### The Linguistic Track (`linguist`)
Scans the split chapters sentence-by-sentence.
- Enforces strict grammatical rules (Oxford commas, CJK-Latin spacing, punctuation nesting).
- Banned from changing tone, meaning, or sentence structure.
- Outputs an actionable log indicating exact lines and old/new text.

### The Structural Track (`architect`)
Evaluates the logical macro-flow of the chapters.
- Flags logical gaps, redundancy, over-hedging, and weak transitions.
- Evaluates Macro-Structure constraints (e.g., *Is the hypothesis generated in the Intro accurately tested in the Methodology?*).
- Outputs a Structural Flow Log with actionable revisions.

### The Auditing Track (`auditor`)
Consumes the JSON context file generated in Phase 3.
- Reads your manuscript's claim side-by-side with the local evidence block.
- Classifies every citation as `SUPPORTED`, `CONTRADICTED`, `UNVERIFIABLE`, or `NEUTRAL`.
- Outputs a Markdown table cross-validating the integrity of your literature review.

---

## Phase 5: Result Compilation

Once all agents signal completion, the `orchestrator` gathers the logs and reports. Your original manuscript remains pristine and unmodified, but you are now armed with:

- `[Proofreading Log]`
- `[Structural Flow Log]`
- `[Fact-Check Validation Report]`

Every modification is transparent and actionable. You iterate exactly as you would with human editorial feedback from a top-tier journal.
