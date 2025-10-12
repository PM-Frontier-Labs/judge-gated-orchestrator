# Complete Judge-Gated Orchestrator Package

**Version:** 1.0 (888 LOC)
**Generated:** 2025-10-12
**Purpose:** Autonomous AI execution protocol with quality gates

This single file contains the complete codebase, documentation, tests, and configuration for the judge-gated-orchestrator system.

---

## Table of Contents

1. [Overview](#overview)
2. [Core Documentation](#core-documentation)
3. [Code Implementation](#code-implementation)
4. [Tests](#tests)
5. [Configuration Files](#configuration-files)
6. [Project Structure](#project-structure)

---

## Overview

### What Is This?

A file-based protocol for autonomous AI execution with quality gates. Like Git tracks changes through `.git/`, this tracks autonomous work through `.repo/`.

**Key Innovation:** Judge blocks progression until quality gates pass. Agent iterates until approved, then advances automatically.

**Use Case:** Define 6-phase roadmap → Claude executes autonomously → Wake up to completed work with tests passing.

### Core Concepts

- **Phase**: Unit of work with defined scope and gates
- **Brief**: Instructions for the phase (what to build)
- **Gate**: Quality check (tests, docs, drift, lint, LLM review)
- **Judge**: Validates all gates and blocks progression
- **Controller**: Orchestrates review → approve → advance flow

### Architecture

```
Phase → Brief → Implementation → Review → Judge → Gates → Verdict
                                    ↓                       ↓
                                 Critique ←──────────── Issues
                                    ↓                       ↓
                                  Fix ──────────────→  Approved
                                                           ↓
                                                      Next Phase
```

---

## Core Documentation

### README.md

```markdown
# Gated Phase Protocol

**Autonomous AI execution with quality gates.**

## What Is This?

A protocol for autonomous execution—not a framework. Like Git tracks code through `.git/`, this tracks autonomous work through `.repo/`.

## Quick Start

```bash
git clone <repo>
cd judge-gated-orchestrator
pip install -r requirements.txt
./orient.sh
./tools/phasectl.py review P02-impl-feature
```

## Key Features

✅ Autonomous multi-phase execution
✅ Quality gates (tests, lint, docs, drift, LLM)
✅ Context-window proof (file-based state)
✅ Terminal-native (no servers)
✅ 888 LOC implementation

## Gates Enforced

| Gate | Check | Example |
|------|-------|---------|
| tests | Suite passes | pytest exit = 0 |
| lint | Static analysis | ruff check . = 0 |
| docs | Files updated | README.md modified |
| drift | Scope boundaries | Only src/mvp/** changes |
| llm_review | Semantic quality | Claude reviews code |

## Workflow

1. Read brief (.repo/briefs/P01.md)
2. Implement within scope
3. Run ./tools/phasectl.py review P01
4. Judge validates gates
5. If approved: advance to P02
6. If critique: fix → re-review

## Philosophy

This is a protocol, not a framework. You don't import it, you follow it.
```

---

### PROTOCOL.md

