# Daves Claude Code Skills — Full Reference

Quick-reference for all 37 skills across 8 categories. Source: [Daves-Claude-Code-Skills](https://github.com/DavidROliverBA/Daves-Claude-Code-Skills).

---

## Architecture (8 skills)

| Skill | Command | Agents | Model | Description |
|-------|---------|--------|-------|-------------|
| ADR | `/adr` | — | Sonnet | Create Architecture Decision Records with context, rationale, and consequences |
| Impact Analysis | `/impact-analysis` | 4 | Sonnet | Analyse cascading change impact across technical, organisational, financial, and risk dimensions |
| Scenario Compare | `/scenario-compare` | 3 | Sonnet | Compare architectural scenarios with cost, timeline, complexity, and risk analysis |
| NFR Capture | `/nfr-capture` | — | Sonnet | Capture non-functional requirements with measurable acceptance criteria (ISO 25010) |
| NFR Review | `/nfr-review` | 3 | Sonnet | Review NFRs for completeness, measurability, and feasibility |
| Architecture Report | `/architecture-report` | 5 | Sonnet | Generate comprehensive architecture reports for governance and audit |
| Cost Analysis | `/cost-analysis` | 3 | Sonnet | Analyse infrastructure, licensing, and operational costs; identify savings |
| Dependency Graph | `/dependency-graph` | — | Sonnet | Visualise system dependencies with colour-coded criticality in Mermaid |

## Content Processing (8 skills)

| Skill | Command | Agents | Model | Description |
|-------|---------|--------|-------|-------------|
| PDF Extract | `/pdf-extract` | — | Sonnet | Extract structured content from PDFs with optional docling support for native table recognition |
| PPTX Extract | `/pptx-extract` | — | Sonnet | Convert PowerPoint slides to Markdown with docling/python-pptx dual extraction |
| YouTube Analyze | `/youtube-analyze` | — | Sonnet | Analyse videos via transcripts with timestamped summaries and key takeaways |
| Video Digest | `/video-digest` | N | Sonnet | Batch-triage videos by relevance (Haiku), then deeply process the best (Sonnet) |
| Weblink | `/weblink` | — | Haiku | Quick web page capture with AI-generated summary |
| Article | `/article` | — | Haiku | Quick article capture with summary, key quotes, and relevance scoring |
| Book Notes | `/book-notes` | 3 | Sonnet | Create book notes with parallel extraction and optional knowledge compounding |
| Document Extract | `/document-extract` | — | Sonnet | Extract from any format (PDF, DOCX, HTML, CSV) with auto-detection |

## Diagramming (3 skills)

| Skill | Command | Agents | Model | Description |
|-------|---------|--------|-------|-------------|
| Diagram | `/diagram` | — | Sonnet | Generate architecture diagrams (C4, system landscape, data flow, AWS) |
| C4 Diagram | `/c4-diagram` | — | Sonnet | Specialised C4 diagram generation: Mermaid C4, flowchart LR, or PlantUML |
| Diagram Review | `/diagram-review` | 4 | Sonnet | Analyse existing diagrams for readability and architecture quality |

## Vault Health (6 skills)

| Skill | Command | Agents | Model | Description |
|-------|---------|--------|-------|-------------|
| Quality Report | `/quality-report` | 5 | Sonnet | Comprehensive quality metrics with Flesch readability, link density, freshness thresholds |
| Broken Links | `/broken-links` | 3 | Sonnet | Find broken wiki-links, heading anchors, and missing attachment references |
| Orphan Finder | `/orphan-finder` | 4 | Sonnet | Detect disconnected notes and suggest meaningful connections |
| Auto-Tag | `/auto-tag` | N | Haiku | Batch auto-tag notes using type-based rules and keyword-to-tag mapping |
| Auto-Summary | `/auto-summary` | N | Haiku | Batch-generate one-line summary fields with type-specific patterns |
| Link Checker | `/link-checker` | N | Haiku | Validate external URLs with curl-based checking and status tracking |

## Scoring (2 skills)

| Skill | Command | Agents | Model | Description |
|-------|---------|--------|-------|-------------|
| Score Document | `/score-document` | 4 | Sonnet | Score documents against customisable rubrics with optional SQLite persistence |
| Exec Summary | `/exec-summary` | — | Sonnet | Generate executive summaries tailored to CEO, CTO, board, or PM audiences |

## Reporting (2 skills)

| Skill | Command | Agents | Model | Description |
|-------|---------|--------|-------|-------------|
| Weekly Summary | `/weekly-summary` | 5 | Sonnet | Generate weekly activity reports from daily notes, tasks, meetings, projects |
| Project Report | `/project-report` | 4 | Sonnet | Generate RAG project status reports with tasks, risks, and timeline assessment |

## Meetings (3 skills)

| Skill | Command | Agents | Model | Description |
|-------|---------|--------|-------|-------------|
| Meeting Notes | `/meeting-notes` | 3 | Sonnet | Create structured meeting notes with decision and action item extraction |
| Voice Meeting | `/voice-meeting` | — | Sonnet | Process voice transcripts with speech-to-text correction into structured notes |
| Email Capture | `/email-capture` | — | Haiku | Capture important emails as structured vault notes with action item extraction |

## Knowledge (5 skills)

| Skill | Command | Agents | Model | Description |
|-------|---------|--------|-------|-------------|
| Summarize | `/summarize` | — | Sonnet | Summarise notes with configurable depth (one-liner, paragraph, page) and audience |
| Find Related | `/find-related` | — | Sonnet | Discover related content via tag overlap, backlinks, keywords, temporal proximity |
| Find Decisions | `/find-decisions` | — | Sonnet | Extract and catalogue formal and informal decisions across a date range |
| Timeline | `/timeline` | — | Sonnet | Generate visual timelines (Mermaid Gantt, table, or list) from vault events |
| Skill Creator | `/skill-creator` | — | Sonnet | Generate new Claude Code skill files with agent team boilerplate |

---

## Agent Team Patterns (Claude)

| Pattern | Skills | Agents | Sub-Agent Model | Typical Speedup |
|---------|--------|--------|-----------------|-----------------|
| Fan-Out/Fan-In | 13 | 3-5 (fixed) | Sonnet or Haiku | 3-4× |
| Batch Processing | 3 | N (scales) | Haiku | 4-9× |
| Triage + Selective | 1 | N + selective | Haiku → Sonnet | 2-3× time, 60-80% cost saving |
| No agents | 20 | 0 | — | 1× |

---

## Model Cost Guide (Claude API)

| Model | Input | Output | Ideal For |
|-------|-------|--------|-----------|
| Haiku | $1.00/MTok | $5.00/MTok | Batch work, quick captures, triage |
| Sonnet | $3.00/MTok | $15.00/MTok | Analysis, synthesis, most skill work |
| Opus | $15.00/MTok | $75.00/MTok | Deep architectural reasoning |

**Cost optimisation tips**: Use Haiku for batch; triage with Haiku then deep-process subset with Sonnet; limit fan-out to 3-5 agents.
