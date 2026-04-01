<div align="center">
 
<img src="docs/Image_clean_autoreview.png" width="600" alt="academic-auto-reviewer cover"/>
 
# 📚 academic-auto-reviewer
 
<p align="center">
  <img src="https://img.shields.io/badge/Framework-Antigravity-purple.svg?style=for-the-badge&logo=google" alt="Framework"/>
  <img src="https://img.shields.io/badge/Language-Python-blue?style=for-the-badge&logo=python&logoColor=white" alt="Language"/>
  <img src="https://img.shields.io/badge/Concept-Agentic%20RAG-orange?style=for-the-badge&logo=probot&logoColor=white" alt="Concept"/>
  <img src="https://img.shields.io/badge/Supports-EN%20|%20中文-brightgreen?style=for-the-badge" alt="Bilingual"/>
</p>

*基于本地代理化 RAG 架构、立足证据且引用可追溯的学术论文审阅管线。*

[English](README.md) | **[中文]**

</div>

`academic-auto-reviewer` 是一款专为研究者设计的任务编排管线。通过告别传统的单次对话式 LLM 交互（其往往存在引用幻觉和严重的证实偏差），本系统利用多个专业化 AI 代理，根据本地验证的文献数据库，对学术初稿进行严谨的实证审计、结构评议和事实核查。

---

## 循证审阅管线 (Evidence-Based Pipeline)

文中的每一项事实陈述都将根据您的本地文献库进行验证，而非依赖模型的预训练记忆。这确保了审阅过程的真实性与引用的可追溯性。

在执行实证核查前，您需要使用配套引擎构建本地数据库：
👉 **[mark-lit-down (知识库构建引擎)](https://github.com/Jidi1997/mark-lit-down)**

*(如果您仅需要语言润色和结构分析，可以跳过文献事实核查步骤。)*

---

## 工作流特性

本项目运行于 **Antigravity** 代理环境，在保持学术严谨性的同时，自动化处理繁琐的论文审阅任务。
- **双语支持：** 能够完美处理并审阅 **英文** 和 **中文** 学术稿件。
- **输入处理：** 系统接收标准 `.md` (Markdown) 格式的学术初稿。
- **输出结果：** 系统不会直接修改您的原生文档，而是生成四份专业、可操作的 Markdown 报告，提供结构化的反馈建议。

```mermaid
graph LR
    Input(["📄 Markdown 稿件"]) --> orchestrator{"🧠 orchestrator"}
    orchestrator -->|"语言习惯"| linguist["🖋️ linguist"]
    orchestrator -->|"逻辑结构"| architect["🏗️ architect"]
    orchestrator -->|"证据核查"| auditor["🔍 auditor"]
    linguist & architect & auditor --> Output(["📑 审阅报告集"])
```

> **不是 Markdown 格式？**
> 如果您的初稿是其他格式（如 Word 或 LaTeX），请在运行工作流前使用 [`pandoc`](https://pandoc.org/) 进行快速转换：
> ```bash
> # Word (.docx) 转 Markdown
> pandoc my_manuscript.docx -o my_manuscript.md
> 
> # LaTeX (.tex) 转 Markdown
> pandoc my_manuscript.tex -o my_manuscript.md
> ```

---

## 系统架构与代理职能

整个审阅管线由中心调度器 (Orchestrator) 协调，并分发给多个并行的分析轨道。

### orchestrator : 管线调度器
核心协调引擎。负责解析稿件、去除格式噪声、分发引用数据，并监督各代理的并行执行。

### linguist : 语言与风格代理
精通双语的专家代理，专注于语言准确性。在不改变原意的前提下，强制执行排版一致性和学术语法规范（如中英文混排空格、标点规则等）。

### architect : 结构连贯性代理
评估论证流和宏观逻辑。识别摘要、引言、方法论及结论部分存在的逻辑断层或冗余表达。

### auditor : NLI 事实核查代理
利用 [自然语言推理 (NLI)](https://en.wikipedia.org/wiki/Textual_entailment) 技术验证实证陈述。所有陈述必须严谨地通过本地数据库检索到的原文内容进行交叉验证。

### planner : 任务拆解核心
赋予工作流制定、拆解、跟踪和完成复杂任务的能力。通过强制生成 `_plan.md` 和 `_status.md` 文件，将任务进度映射到本地文件系统，确保过程透明可控。
*(核心方法论参考自 [othmanadi/planning-with-files](https://github.com/othmanadi/planning-with-files) 框架)*

---

## 安装与执行

1. **部署框架**：克隆并将此 `.agent` 目录放置在您的论文写作工作区的根目录下。
2. **配置数据库路径**：确保您的本地 Markdown 数据库已在代理的 RAG 技能中正确索引（详见 `.agent/skills/auditor/SKILL.md` 中的路径引用）。
3. **开始执行**：在 IDE 或代理终端中触发审阅。

```bash
/paper-review drafts/my_manuscript.md --voice third
```

*关于语称 (`--voice`)：您可以根据论文的叙述人称调整润色风格。可选值为 `first` (如 "We examine...")、`second` (如 "You can see...") 或 `third` (如 "This study examines...")，以确保全文色调统一。*

> **如需深入了解管线运行机制，请阅读 [工作流指南 (英文版)](docs/WORKFLOW_GUIDE.md)。**

---

## 输出报告 (Output Reports)

审阅完成后，您的原始初稿将保持不变。系统会生成以下三份报告：
- `[Proofreading Log]` — 语言修改建议与排版一致性核查明细。
- `[Structural Flow Log]` — 论证连贯性分析及各章节衔接评估。
- `[Fact-Check Validation Report]` — 基于本地数据库的事实核查结果。

---

## 许可与贡献

本项目基于 [MIT 许可协议](LICENSE) 发布。版权所有 &copy; 2026 Jidi Cao。

本系统采用高度模块化设计。鼓励研究人员将新的专业代理（例如方法论验证器或数据可视化顾问）集成到 `.agent/skills/` 目录中，并更新 `orchestrator` 的调度协议。
