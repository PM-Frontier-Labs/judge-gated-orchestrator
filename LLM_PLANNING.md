# LLM Planning Guide - Judge-Gated Protocol

**READ THIS WHEN:** Helping a human plan a multi-phase roadmap
**DON'T READ WHEN:** Executing work within an already-planned project (read PROTOCOL.md instead)

**Purpose:** This guide teaches you how to create effective `plan.yaml` files and phase briefs for autonomous execution.

---

## Quick Start

You're helping a human break their project into phases with quality gates. Here's the flow:

1. **Understand their goal** - What are they building?
2. **Propose phases** - Break work into 1-3 day increments
3. **Define scope** - What files can change in each phase?
4. **Choose gates** - What quality checks make sense?
5. **Write plan.yaml** - Formalize the roadmap
6. **Write briefs** - Detailed instructions for each phase
7. **Initialize** - Create CURRENT.json for phase 1
8. **Handoff** - Tell them to point you at PROTOCOL.md for execution

**After planning is done, you'll switch modes and read PROTOCOL.md for execution.**

---

## Phase Design Principles

### Size: 1-3 Days of Work

**Good phases:**
- ✅ Single feature or module
- ✅ Clear deliverable
- ✅ Independently testable
- ✅ 100-300 lines of code typically

**Bad phases:**
- ❌ "Implement entire backend" (too broad)
- ❌ "Add semicolon to line 42" (too narrow)
- ❌ Multiple unrelated features
- ❌ Work spanning 1+ weeks

### Testability: Every Phase Must Be Verifiable

**Each phase should:**
- Have tests that prove it works
- Create artifacts that can be checked
- Produce docs that can be reviewed

**If you can't test it, split it:**
- "Design auth system" → Not testable (too vague)
- "Implement JWT login endpoint" → Testable ✅

### Scope: Clear Boundaries

**Good scope patterns:**
```yaml
# Focused on one module
include: ["src/auth/**", "tests/auth/**", "docs/auth.md"]

# Multiple related files
include: ["migrations/001_*.sql", "src/models/user.py"]

# Wildcard for new features
include: ["src/features/payments/**"]
```

**Bad scope patterns:**
```yaml
# Too broad
include: ["src/**"]  # Everything!

# Too vague
include: ["*.py"]  # Which Python files?

# No tests
include: ["src/auth/**"]  # Where are tests?
```

### Dependencies: Sequential Phases

**Phases run sequentially, so order matters:**

```yaml
phases:
  - id: P01-database-schema
    # Must come first

  - id: P02-api-endpoints
    # Depends on P01 being done

  - id: P03-frontend
    # Depends on P02 being done
```

**Can't parallelize** - If human needs parallel work, they should use separate branches.

---

## plan.yaml Schema

### Complete Template

```yaml
plan:
  # Required fields
  id: PROJECT-ID                           # Uppercase, hyphens (e.g., MY-API)
  summary: "What you're building"          # 1 sentence

  # Optional configuration
  base_branch: "main"                      # Branch to diff against (default: "main")
  test_command: "pytest tests/ -v"         # How to run tests (default: "pytest tests/ -v")
  lint_command: "ruff check ."             # How to run linter (default: "ruff check .")

  # LLM review configuration (optional)
  llm_review_config:
    model: "claude-sonnet-4-20250514"      # Model to use
    max_tokens: 2000                       # Response length
    temperature: 0                         # Randomness (0 = deterministic)
    timeout_seconds: 60                    # API timeout
    budget_usd: null                       # Cost limit (null = unlimited)
    fail_on_transport_error: false         # Block on API errors?
    include_extensions: [".py"]            # File types to review
    exclude_patterns: []                   # Skip patterns

  # Protocol integrity (rarely modified)
  protocol_lock:
    protected_globs:
      - "tools/**"
      - ".repo/plan.yaml"
      - ".repo/protocol_manifest.json"
    allow_in_phases:
      - "P00-protocol-maintenance"

  # Runtime learning (collective intelligence)
  # No configuration needed here; learning is handled at runtime and stored under .repo/

  # Phase definitions
  phases:
    - id: P01-phase-name                   # Must be unique
      description: "What this accomplishes" # 1 sentence, actionable

      # Scope: What files can change
      scope:
        include: ["src/module/**", "tests/module/**"]  # Glob patterns
        exclude: ["src/**/legacy/**"]                  # Optional exclusions

      # Artifacts: Files that must exist after phase
      artifacts:
        must_exist: ["src/module/file.py", "tests/test_file.py"]

      # Gates: Quality checks
      gates:
        tests:
          must_pass: true                  # Required
          test_scope: "scope"              # "scope" | "all" (default: "all")
          quarantine: []                   # Optional: skip specific tests

        lint:
          must_pass: true                  # Optional gate

        docs:
          must_update: ["docs/module.md"]  # Files that must change

        drift:
          allowed_out_of_scope_changes: 0  # How many files can be out of scope

        llm_review:
          enabled: false                   # Optional LLM code review

      # Drift rules: Absolute restrictions
      drift_rules:
        forbid_changes: ["requirements.txt", "package.json"]  # Never touch these
```

### Field Reference

**plan.id** - Project identifier (uppercase, hyphens)

**plan.summary** - One sentence describing the project

**plan.base_branch** - Branch for git diffs (default: "main")

**plan.test_command** - Command to run tests
- Python: `"pytest tests/ -v"`
- Node: `"npm test"`
- Rust: `"cargo test"`
- Go: `"go test ./..."`

**plan.lint_command** - Command to run linter
- Python: `"ruff check ."` or `"flake8 ."`
- Node: `"eslint ."` or `"npm run lint"`
- Rust: `"cargo clippy"`

**phases[].id** - Unique phase identifier (e.g., P01-setup, P02-feature)

**phases[].scope.include** - Glob patterns for allowed files
- Use `**` for recursive: `"src/**/*.py"` matches nested files
- Multiple patterns: `["src/auth/**", "tests/auth/**"]`

**phases[].scope.exclude** - Patterns to exclude from include
- Example: `["src/**/test_*.py"]` excludes test files from src

**phases[].gates.tests.test_scope**
- `"scope"` - Run only tests matching scope.include (fast, focused)
- `"all"` - Run entire test suite (comprehensive)

**phases[].gates.tests.quarantine** - Skip specific tests
```yaml
quarantine:
  - path: "tests/test_flaky.py::test_timeout"
    reason: "External API timeout, tracked in issue #123"
```

**phases[].drift_rules.forbid_changes** - Files requiring dedicated phases
- Dependencies: `["requirements.txt", "package.json", "Cargo.toml"]`
- CI: `[".github/**", ".circleci/**"]`
- Migrations: `["migrations/**"]` (if you want separate migration phases)

---

## Gate Selection Guide

### When to Use Each Gate

#### tests: { must_pass: true }
**Always use** - Every phase should have tests

**test_scope: "scope"** when:
- Large codebase (100+ tests)
- Isolated module work
- Fast feedback loop desired
- Legacy tests exist elsewhere

**test_scope: "all"** when:
- Small codebase (<50 tests)
- Integration phase
- Breaking changes possible
- Final validation before release

**quarantine** when:
- Flaky external API tests
- Deliberately breaking tests (fixing next phase)
- Legacy tests unrelated to work
- Infrastructure not yet built

#### lint: { must_pass: true }
**Use when:**
- Team has style standards
- Want consistent code formatting
- Linter already configured

**Skip when:**
- Exploratory/prototype phase
- No linter configured yet
- Would slow down too much

#### docs: { must_update: ["file.md"] }
**Use when:**
- Public API changes
- New features need documentation
- Architecture decisions made

**Specify section anchors:**
```yaml
docs:
  must_update: ["docs/api.md#authentication"]
```

**Skip when:**
- Internal refactoring
- Bug fixes with no API changes
- Docs will be batch-updated later

#### drift: { allowed_out_of_scope_changes: N }
**Start with 0** - Be strict by default

**Allow 1-2 when:**
- Small config tweaks expected
- README updates likely
- Minor refactors of nearby code

**Allow 5+ when:**
- Exploratory refactor phase
- Touch files discovered during work

**Skip entirely** (omit gate) when:
- No scope defined
- Prototyping phase

#### llm_review: { enabled: true }
**Enable for:**
- Security-critical code (auth, encryption)
- Complex algorithms
- Public APIs
- Money/payment handling
- Untrusted input processing

**Skip for:**
- Boilerplate code
- Configuration files
- Test files
- Simple CRUD operations
- Cost-sensitive projects

---

## Scope Patterns Cookbook

### Common Patterns

#### Pattern: New Feature Module
```yaml
scope:
  include:
    - "src/features/payments/**"
    - "tests/features/payments/**"
    - "docs/features/payments.md"
```

#### Pattern: Database Schema
```yaml
scope:
  include:
    - "migrations/001_*.sql"
    - "src/models/user.py"
    - "tests/models/test_user.py"
```

#### Pattern: API Endpoints
```yaml
scope:
  include:
    - "src/api/routes/auth.py"
    - "tests/api/test_auth.py"
    - "docs/api.md#authentication"
```

#### Pattern: Refactoring
```yaml
scope:
  include:
    - "src/legacy/module/**"
    - "src/new/module/**"
    - "tests/module/**"
  exclude:
    - "src/legacy/module/deprecated/**"
```

#### Pattern: Configuration
```yaml
scope:
  include:
    - "config/**"
    - ".env.example"
    - "docs/configuration.md"
```

#### Pattern: Integration Tests
```yaml
scope:
  include:
    - "tests/integration/**"
gates:
  tests:
    test_scope: "all"  # Run everything for integration
```

### Anti-Patterns to Avoid

#### ❌ Too Broad
```yaml
# BAD - Everything can change
scope:
  include: ["**"]
```

#### ❌ No Tests
```yaml
# BAD - Where are the tests?
scope:
  include: ["src/auth/**"]
```

#### ❌ Vague Wildcards
```yaml
# BAD - Which files exactly?
scope:
  include: ["*.py", "*.js"]
```

#### ❌ Cross-Module
```yaml
# BAD - Too many unrelated things
scope:
  include: ["src/auth/**", "src/payments/**", "src/notifications/**"]
```

#### ❌ Incorrect Globstar
```yaml
# BAD - Single * doesn't match nested paths
scope:
  include: ["src/*/auth.py"]  # Won't match src/module/submodule/auth.py
# GOOD - Use ** for recursive
  include: ["src/**/auth.py"]
```

---

## Phase Templates

### Template 1: Setup/Scaffold Phase

**Use when:** Starting a new module from scratch

```yaml
- id: P01-scaffold-auth
  description: "Create authentication module skeleton"

  scope:
    include:
      - "src/auth/**"
      - "tests/auth/**"
      - "docs/auth.md"

  artifacts:
    must_exist:
      - "src/auth/__init__.py"
      - "tests/auth/test_login.py"
      - "docs/auth.md"

  gates:
    tests:
      must_pass: true
      test_scope: "scope"
    docs:
      must_update: ["docs/auth.md"]
    drift:
      allowed_out_of_scope_changes: 0
```

**Brief template:**
```markdown
# Phase P01: Scaffold Auth Module

## Objective
Create basic structure for authentication module with placeholder tests

## Scope 🎯
✅ YOU MAY CREATE:
- src/auth/__init__.py
- src/auth/models.py (placeholder)
- tests/auth/test_login.py (one golden test)
- docs/auth.md (architecture plan)

❌ DO NOT TOUCH:
- Existing auth code (if any)
- API routes (separate phase)

## Required Artifacts
- [ ] src/auth/__init__.py - Module initialization
- [ ] tests/auth/test_login.py - At least one passing test
- [ ] docs/auth.md - Architecture overview

## Gates
- Tests: Must pass (even if minimal)
- Docs: auth.md must be created
- Drift: No out-of-scope changes

## Implementation Steps
1. Create directory structure
2. Add __init__.py with placeholder
3. Write one golden test (assert True or similar)
4. Document planned architecture in auth.md
```

### Template 2: Feature Implementation

**Use when:** Building actual functionality

```yaml
- id: P02-implement-jwt-login
  description: "Implement JWT-based login endpoint"

  scope:
    include:
      - "src/auth/jwt.py"
      - "src/auth/login.py"
      - "src/api/routes/auth.py"
      - "tests/auth/test_jwt.py"
      - "tests/api/test_auth_routes.py"
      - "docs/auth.md"

  artifacts:
    must_exist:
      - "src/auth/jwt.py"
      - "src/auth/login.py"
      - "tests/auth/test_jwt.py"

  gates:
    tests:
      must_pass: true
      test_scope: "scope"
    lint:
      must_pass: true
    docs:
      must_update: ["docs/auth.md#jwt-implementation"]
    llm_review:
      enabled: true  # Security-critical code
    drift:
      allowed_out_of_scope_changes: 0

  drift_rules:
    forbid_changes: ["requirements.txt"]  # No new dependencies yet
```

### Template 3: Refactoring Phase

**Use when:** Improving existing code without changing behavior

```yaml
- id: P03-refactor-auth-separation
  description: "Separate auth logic from API routes"

  scope:
    include:
      - "src/auth/**"
      - "src/api/routes/auth.py"
      - "tests/auth/**"
      - "tests/api/test_auth_routes.py"

  gates:
    tests:
      must_pass: true
      test_scope: "all"  # Run everything - refactors can break things
    lint:
      must_pass: true
    drift:
      allowed_out_of_scope_changes: 2  # Might touch nearby files
```

### Template 4: Integration Phase

**Use when:** Connecting multiple modules

```yaml
- id: P04-integrate-auth-api
  description: "Wire auth module to API endpoints"

  scope:
    include:
      - "src/api/middleware/auth.py"
      - "src/api/routes/**"
      - "tests/integration/test_auth_flow.py"
      - "docs/api.md"

  gates:
    tests:
      must_pass: true
      test_scope: "all"  # Integration needs full suite
    docs:
      must_update: ["docs/api.md#authentication"]
    drift:
      allowed_out_of_scope_changes: 1
```

### Template 5: Dependencies Phase

**Use when:** Adding/updating external dependencies

```yaml
- id: P05-add-auth-dependencies
  description: "Add PyJWT and cryptography libraries"

  scope:
    include:
      - "requirements.txt"
      - "docs/dependencies.md"

  artifacts:
    must_exist:
      - "requirements.txt"

  gates:
    tests:
      must_pass: true
      test_scope: "all"  # Make sure nothing breaks
    docs:
      must_update: ["docs/dependencies.md"]
    drift:
      allowed_out_of_scope_changes: 0

  drift_rules:
    forbid_changes: []  # This phase CAN touch requirements.txt
```

### Template 6: Documentation Phase

**Use when:** Batch-updating docs after multiple features

```yaml
- id: P06-document-auth-system
  description: "Comprehensive auth documentation"

  scope:
    include:
      - "docs/auth/**"
      - "README.md"
      - "docs/api.md"

  artifacts:
    must_exist:
      - "docs/auth/overview.md"
      - "docs/auth/api-reference.md"

  gates:
    docs:
      must_update: ["docs/auth/overview.md", "README.md"]
    drift:
      allowed_out_of_scope_changes: 0
```

---

## Planning Conversation Flow

### Step 1: Understand the Project

**Ask the human:**
- What are you building?
- What's the end goal?
- What's already built vs new?
- Any constraints (timeline, dependencies, tech stack)?

### Step 2: Propose High-Level Phases

**Break work into logical chunks:**

```
Example: "Build a REST API with auth"

Phases:
1. Database schema (users, sessions)
2. Auth module (JWT, login/logout)
3. API endpoints (CRUD)
4. Integration tests
5. Documentation
```

**Validate with human before proceeding.**

### Step 3: Define Each Phase in Detail

For each phase, discuss:
- **Scope:** Which files?
- **Artifacts:** What must exist?
- **Gates:** Which checks?
- **Dependencies:** What must be done first?

### Step 4: Write plan.yaml

Create the formal roadmap with all phases.

### Step 5: Write Briefs

For each phase, create `.repo/briefs/PXX-name.md` with:
- Objective (what to accomplish)
- Scope (files you may/may not touch)
- Required artifacts
- Gates
- Implementation steps

### Step 6: Initialize

Create `.repo/briefs/CURRENT.json`:
```json
{
  "phase_id": "P01-first-phase",
  "brief_path": ".repo/briefs/P01-first-phase.md",
  "status": "active",
  "started_at": 1234567890
}
```

### Step 7: Handoff to Execution

Tell the human:
```
"Planning complete! Now point me at PROTOCOL.md and I'll execute
autonomously. Run ./orient.sh to see the current phase, then tell
me to read PROTOCOL.md and start working."
```

---

## Example Planning Session

**Human:** "Help me plan a REST API for a blog"

**You (LLM):** "Great! Let me understand the scope:
- What features? (posts, comments, auth, etc.)
- What's your tech stack? (Python/Flask, Node/Express, etc.)
- Starting from scratch or adding to existing code?
- Any existing database or schema?"

**Human:** "Python/FastAPI, from scratch. Features: users, posts, comments. No auth yet."

**You:** "Perfect. I'd break this into 5 phases:

1. **P01-database-schema**: SQLAlchemy models (users, posts, comments)
2. **P02-api-users**: User CRUD endpoints
3. **P03-api-posts**: Post CRUD endpoints + user relationship
4. **P04-api-comments**: Comment endpoints + post relationship
5. **P05-integration-tests**: End-to-end API tests

Does this order make sense? Any constraints?"

**Human:** "Looks good, let's do it."

**You:** "I'll create plan.yaml now..."

*(Create plan.yaml with all 5 phases, then briefs for each)*

**You:** "Done! Created:
- `.repo/plan.yaml` with all 5 phases
- `.repo/briefs/P01-database-schema.md` through P05
- `.repo/briefs/CURRENT.json` pointing to P01

Next: Tell me to read PROTOCOL.md and I'll start executing P01 autonomously."

---

## Quick Reference

### Good Phase Checklist
- [ ] 1-3 days of work
- [ ] Single focus (one feature/module)
- [ ] Clear scope (specific files)
- [ ] Testable (can verify it works)
- [ ] Artifacts defined (must_exist files)
- [ ] Appropriate gates (tests at minimum)

### Common Mistakes
- ❌ Phases too large (>1 week)
- ❌ Scope too broad (src/**/*)
- ❌ No tests included
- ❌ Vague descriptions
- ❌ Missing dependencies between phases
- ❌ Forbidden files not specified

### File Naming
- **plan.yaml**: Always this name
- **Briefs**: `.repo/briefs/P01-descriptive-name.md`
- **Phase IDs**: P01, P02... (zero-padded numbers)

---

**END OF PLANNING GUIDE**

**Next step:** After plan created, read **PROTOCOL.md** for execution mode.

---

## Collective Intelligence Planning (for better execution)

### Enhanced Briefs: Add Hints and Guardrails Context
- Include a short "Hints" section in briefs when known pitfalls exist (e.g., test runner quirks).
- Add explicit guardrails in briefs: clear YOU MAY/DO NOT TOUCH lists, and guidance on when to split phases.

### Plan for Amendments (bounded mutability)
- Assume occasional runtime adjustments without editing governance files.
- Recommend initial budgets per phase (runtime defaults exist, but set expectations in the brief):
  - `add_scope`: up to 2
  - `set_test_cmd`: up to 1
  - `note_baseline_shift`: up to 1
- Instruct the agent to use `./tools/phasectl.py amend propose ...` rather than editing files directly.

### Outer Loop Considerations
- After each successful phase, a micro-retrospective is written and used for future hints.
- Encourage concise notes in briefs about what likely helps, to seed future patterns.

### Pattern Learning Guidance
- Patterns are auto-learned from successful amendments and stored in `.repo/collective_intelligence/patterns.jsonl`.
- You don't need to configure this in `plan.yaml`.
- Power users may review with `./tools/phasectl.py patterns list`.

### Phase Design Patterns (updated)
- Prefer phases with stable test commands; if unknown, allow one `set_test_cmd` amendment.
- For modules with sprawling tests, set `tests.test_scope: "scope"` to speed iteration.
- Use strict `drift.allowed_out_of_scope_changes: 0`, relying on `add_scope` amendments instead of broad includes.

### Amendment System Planning
- When you anticipate integration edges, note them in the brief and suggest `add_scope` targets.
- For CI variance, note acceptable `note_baseline_shift` usage.
