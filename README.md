<div align="center">

<img src="docs/Image_clean_autoreview.png" width="600" alt="academic-auto-reviewer cover"/>

# academic-auto-reviewer

*A local workflow for reviewing academic manuscripts: language, argument structure, and citation checks against your own literature base.*

**[English]** | [中文](README_zh.md)

</div>

`academic-auto-reviewer` is a manuscript review workflow for researchers who want a structured, local-first review before submission. It reviews a near-final draft, generates separate reports for language and structure, and can optionally audit citation-grounded claims against a local literature database.

## What It Does

- Reviews near-final academic drafts across language, argument structure, and citation use
- Generates separate reports from specialist agents for targeted revision
- Provides side-by-side checks and professional revision suggestions instead of opaque edits
- Uses a local literature database for grounded citation auditing
- Supports English and Chinese manuscripts

## Who It's For

This project is designed for:

- Researchers preparing a near-final draft for submission
- Users who prefer local, inspectable workflows
- Authors working in Markdown directly or converting from Word or LaTeX for AI-assisted review

Markdown is the current working format for the review pipeline because it is easy to inspect, split, and process with AI agents. If your manuscript is in another format, converting it with `pandoc` is usually a low-friction step.

## Input and Output

| Input | Output |
|---|---|
| `my_manuscript.md` | `*_report_linguist.md` |
|  | `*_report_architect.md` |
|  | `*_report_auditor.md` |

The original manuscript is left unchanged.

For citation audit / fact check, the workflow additionally depends on a prepared local literature database in Markdown format. This database can be built with [mark-lit-down](https://github.com/Jidi1997/mark-lit-down).

## Quickstart

1. Prepare your manuscript in Markdown, or convert from Word / LaTeX with `pandoc`
2. Optionally prepare a local literature database for citation auditing
3. Run the review workflow in a supported agent runtime

Example:

```bash
/paper-review drafts/my_manuscript.md --voice third
```

Useful conversions:

```bash
pandoc my_manuscript.docx -o my_manuscript.md
pandoc my_manuscript.tex -o my_manuscript.md
```

## Workflow Overview

```mermaid
graph LR
    Input["Manuscript"] --> orchestrator{"Academic Review Orchestrator"}
    orchestrator -->|"Task Dispatch"| linguist["linguist"]
    orchestrator -->|"Task Dispatch"| architect["architect"]
    orchestrator -->|"Task Dispatch"| auditor["auditor"]
    linguist --> Output["Review Reports"]
    architect --> Output
    auditor --> Output
```

The workflow includes three review tracks:

- `linguist`: language and style issues
- `architect`: structure and argument flow
- `auditor`: citation-grounded claim checking

The orchestrator coordinates preprocessing, task dispatch, and report collection across the three specialist agents.

## Citation Audit Judgments

The `auditor` does not just flag issues. It distinguishes among three judgment types and returns evidence-grounded revision guidance:

- `entailment`: the cited source supports the claim
- `contradiction`: the claim misstates, reverses, or over-extends the cited source
- `neutral`: the available evidence is insufficient to verify the claim

## Current Scope

- Input format: Markdown manuscripts used as the working review format
- Typical source formats: Markdown, Word, and LaTeX via conversion
- Review language: English and Chinese
- Citation audit backend: local literature database
- Current packaged runtime: [Antigravity](https://github.com/google/antigravity)
- Workflow design: modular and portable to other agent runtimes

## Why This Project

Many AI tools help researchers read papers, summarize sources, or answer questions. `academic-auto-reviewer` focuses on a different stage: reviewing your own manuscript before submission.

Its goal is to make draft review more systematic by separating three tasks that are often mixed together:

- language cleanup
- structural diagnosis
- evidence-grounded citation auditing

Rather than promising perfect verification, the workflow is designed to make claims easier to inspect, challenge, and revise using local evidence.

## Documentation

- [Workflow Guide](docs/WORKFLOW_GUIDE.md)
- [Chinese Workflow Guide](docs/WORKFLOW_GUIDE_zh.md)

## FAQ

### Do I need Antigravity?

No in principle. The workflow design is general. This release is currently packaged for Antigravity.

### Do I need a local literature database?

Only for citation auditing. Language and structure review can run without it.

### Does it modify my manuscript?

No. The workflow generates review reports and leaves the original manuscript unchanged.

### Can I use Word or LaTeX?

Yes. The current working format is Markdown, but converting from Word or LaTeX with `pandoc` is usually straightforward.

## License

Released under the [MIT License](LICENSE). Copyright &copy; 2026 Jidi Cao.

## Credits

- The planning logic draws on ideas from [planning-with-files](https://github.com/othmanadi/planning-with-files).
- The local literature workflow is designed to work well with [mark-lit-down](https://github.com/Jidi1997/mark-lit-down).
