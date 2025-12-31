
# AI Agent Enforcement Policy

## Scope

This policy applies to **all AI agents** that:

* Generate code
* Modify existing code
* Refactor, optimize, or format code
* Introduce new files or imports

Failure to comply **invalidates the output**.

---

## 1. Import Enforcement Rules (Hard Constraint)

### Rule 1.1 — Absolute Imports Only

* AI agents **MUST NOT** generate or modify code containing:

  * `from .`
  * `from ..`
  * `from ...`
* Relative imports are **categorically forbidden**

**Allowed pattern:**

```python
from app.domain.mock.entities import MockDefinition
```

**Forbidden patterns:**

```python
from .entities import MockDefinition
from ..use_cases.match_mock import MatchMockUseCase
from ...core.config import settings
```

### Rule 1.2 — Architectural Boundary Awareness

AI agents **MUST NOT** introduce imports that violate layer boundaries:

| Importing Layer | May Import From     |
| --------------- | ------------------- |
| Domain          | Domain only         |
| Application     | Domain              |
| Infrastructure  | Domain, Application |
| Presentation    | Application         |

Violations are **architecture defects**, not warnings.

---

## 2. Ruff Enforcement Rules (Mandatory Execution)

### Rule 2.1 — Mandatory Ruff Commands

After **every code change**, the agent must assume the following commands will be executed:

```bash
ruff check --fix
ruff check format
```

The agent must therefore:

* Emit code that **passes both commands**
* Avoid constructs that Ruff will rewrite or reject
* Prefer Ruff-compliant patterns by default

### Rule 2.2 — Ruff Is the Source of Truth

* Manual formatting preferences are **irrelevant**
* If Ruff would change the code, the agent’s output is **incorrect**
* The agent must not argue with or bypass Ruff behavior

---

## 3. File Size Constraints (Static Limits)

AI agents **MUST NOT** generate or expand files beyond:

* **100 lines** of executable Python code per file
* **50 lines** of overhead (imports, comments, blank lines)

If logic exceeds limits, the agent **MUST split the file**.

Test files are exempt.

---

## 4. Structural & Design Constraints

### Rule 4.1 — SOLID Compliance

AI agents must ensure:

* One clear responsibility per class or module
* No “do-everything” service objects
* No dependency inversion violations

If unsure, the agent must **prefer smaller, composable units**.

---

### Rule 4.2 — DRY Enforcement

The agent **MUST NOT**:

* Duplicate validation logic
* Repeat configuration values
* Copy-paste logic across modules

Instead, it must extract:

* Functions
* Services
* Utilities
* Configuration constants

---

## 5. Forbidden Anti-Patterns (Zero Tolerance)

AI agents **MUST NOT** introduce:

* God objects
* Deeply nested conditionals
* Magic numbers or strings
* Circular imports
* Import hacks to “make it work”
* Files that mix unrelated concerns
* Code that requires “manual cleanup later”

---

## 6. Post-Generation Self-Check (Required)

Before returning output, the AI agent must internally verify:

1. ❌ No `.` / `..` / `...` imports exist
2. ✅ All imports are absolute
3. ✅ Code would pass:

   * `ruff check --fix`
   * `ruff check format`
4. ✅ File size limits respected
5. ✅ Architectural boundaries preserved

If any check fails, the agent must **revise the output**, not explain the failure.

---

## 7. Failure Semantics

* **Non-compliant output is invalid**
* Partial compliance is not acceptable
* “This can be fixed later” is not acceptable
* The agent must **self-correct before responding**

---

## 8. Priority Order (Conflict Resolution)

If rules conflict, follow this order:

1. Import rules
2. Ruff compliance
3. File size limits
4. Architecture boundaries
5. Design principles

---

## Final Instruction to AI Agents

> **If you cannot comply with this policy, do not emit code.
> Revise until compliant.**

---
