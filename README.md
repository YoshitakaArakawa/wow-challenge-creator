# WOW Challenge Creator

A [Claude Code](https://claude.ai/claude-code) powered toolkit for creating [Workout Wednesday](https://workout-wednesday.com/) Tableau challenges.

## What is Workout Wednesday?

Workout Wednesday (WOW) is a weekly Tableau skill challenge. Each week, a new visualization is published and participants try to recreate it as closely as possible. Difficulty ranges from beginner to advanced.

- Website: https://workout-wednesday.com/
- Tableau challenges: https://workout-wednesday.com/category/tableau/

## What This Repo Does

This repository provides Claude Code skills and scripts to streamline the WOW challenge authoring workflow:

1. **Brainstorm** - Generate and refine challenge ideas with duplicate checking
2. **Prototype** - Quick HTML mockups to visualize chart layouts before building in Tableau
3. **Create challenges** - Write bilingual (EN/JA) requirement documents with a consistent style
4. **Analyze workbooks** - Extract structure, calculated fields, LOD expressions, and dependencies from .twbx files
5. **Capture screenshots** - Grab PNGs from Tableau Public visualizations
6. **Look up Tableau features** - Search recent Tableau Desktop features for inspiration

## Getting Started

### Prerequisites

- [Claude Code](https://claude.ai/claude-code) CLI or IDE extension
- Node.js 18+
- (Optional) Python 3.x for Tableau feature cache updates

### Setup

```bash
git clone https://github.com/YoshitakaArakawa/wow-challenge-creator.git
cd wow-challenge-creator
```

Install dependencies for the analysis scripts:

```bash
cd .claude/skills/create-challenges/scripts/twbx && npm install
cd ../tableau-public && npm install
```

### Usage

Open the project in Claude Code and use the built-in skills:

- `/brainstorm` - Start ideation for a new challenge
- `/create-challenges` - Write requirement docs or analyze a workbook
- `/tableau-features` - Search Tableau Desktop features

The workflow and conventions are documented in [CLAUDE.md](CLAUDE.md).

## Project Structure

```
.claude/skills/
  brainstorm/          # Ideation and duplicate checking
  create-challenges/   # Requirement authoring + twbx/screenshot scripts
  tableau-features/    # Tableau Desktop feature lookup with cache
outputs/               # Generated challenge folders (gitignored)
```

## License

[MIT](LICENSE)
