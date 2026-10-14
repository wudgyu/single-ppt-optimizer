# PPT Single-Slide Optimizer

This repository contains the MVP for an agent that optimizes a single slide from an existing presentation. The system parses source material, plans content and layout, generates an editable PPTX, renders previews, and runs automated quality checks.

## Repository Layout

| Path | Purpose |
|---|---|
| `apps/web` | Next.js frontend for task creation, progress, preview, and delivery. |
| `apps/api` | FastAPI service and orchestration for parsing, planning, generation, QA, and task state. |
| `apps/pptx-generator` | Node.js and PptxGenJS service that turns validated slide plans into editable PPTX files. |
| `packages/contracts` | Shared JSON contracts used by the API, generator, frontend, and tests. |
| `templates` | Versioned presentation themes and design tokens. |
| `scripts` | Local development and maintenance scripts. |
| `storage` | Runtime file storage for task inputs, parsed data, renders, and deliverables. This directory is not tracked in Git. |

## Getting Started

The repository is currently in its initial scaffold stage. Module-specific setup commands will be added as each workspace is initialized.
