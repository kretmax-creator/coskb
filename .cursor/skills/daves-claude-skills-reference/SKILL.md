---
name: daves-claude-skills-reference
description: Reference guide for 37 Claude Code skills across architecture, content processing, diagramming, vault health, scoring, reporting, meetings, and knowledge. Use when the user asks for ADR, impact analysis, PDF extraction, document processing, diagram generation, meeting notes, summarization, NFR capture, cost analysis, or similar workflows from the Daves-Claude-Code-Skills catalog.
---

# Daves Claude Code Skills Reference

Reference catalog for workflows from [Daves-Claude-Code-Skills](https://github.com/DavidROliverBA/Daves-Claude-Code-Skills). Apply equivalent workflows when the user requests these tasks.

## When to Use

Apply this reference when the user asks for:

- **Architecture**: ADR, impact analysis, scenario comparison, NFR capture/review, architecture reports, cost analysis, dependency graphs
- **Content**: PDF/PPTX/DOCX extraction, YouTube analysis, web capture, article summarization, book notes
- **Diagramming**: C4 diagrams, architecture diagrams, diagram review
- **Vault/Knowledge base**: Quality reports, broken links, orphan detection, auto-tagging, auto-summary, link checking
- **Scoring**: Document scoring, executive summaries
- **Reporting**: Weekly summaries, project status reports
- **Meetings**: Meeting notes, voice transcripts, email capture
- **Knowledge**: Summarization, find related content, find decisions, timelines

## Quick Reference by Category

| Category | Key Skills | Typical Output |
|----------|------------|----------------|
| **Architecture** | ADR, impact analysis, NFR capture | Decision records, impact matrices, measurable requirements |
| **Content** | PDF extract, weblink, article | Structured markdown, summaries, key quotes |
| **Diagramming** | Diagram, C4 diagram | Mermaid, PlantUML, C4 views |
| **Vault Health** | Quality report, broken links, auto-tag | Metrics, link reports, tagged notes |
| **Scoring** | Score document, exec summary | Rubric scores, CEO/CTO summaries |
| **Reporting** | Weekly summary, project report | Activity reports, status with risks |
| **Meetings** | Meeting notes, email capture | Structured notes, action items |
| **Knowledge** | Summarize, find related, timeline | Summaries, related content, Gantt/timelines |

## Workflow Patterns

1. **Single-pass**: ADR, NFR capture, weblink, diagram — one coherent pass
2. **Fan-out**: Impact analysis, quality report — split work across dimensions, then synthesize
3. **Batch**: Auto-tag, auto-summary, link checker — process many items with consistent rules
4. **Triage + deep**: Video digest — quick relevance scoring, then deep processing of top items

## Instructions

1. **Identify the match**: Map the user's request to the closest skill in the catalog (see [reference.md](reference.md))
2. **Apply the workflow**: Follow the pattern and output format for that skill
3. **Adapt for Cursor**: Use available tools (read, write, search, terminal) — no Claude agent teams; apply patterns sequentially or suggest batching when appropriate

## Full Catalog

For the complete 37-skill catalog with commands, agent counts, and model guidance, see [reference.md](reference.md).

## Source

Adapted from [Daves-Claude-Code-Skills](https://github.com/DavidROliverBA/Daves-Claude-Code-Skills) — [skills-reference.md](https://github.com/DavidROliverBA/Daves-Claude-Code-Skills/blob/main/docs/skills-reference.md).
