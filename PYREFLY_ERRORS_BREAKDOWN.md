# Pyrefly Type Checking Errors - Breakdown & Fixes

**Total Errors: 244**

Generated: Run `uvx pyrefly check --summarize-errors` to update

---

## Priority 1: Critical Errors (Block commits once fixed to high quality)

### 1. QdrantClient Type Mismatch (5 instances)
**Problem:** `registry.get_qdrant_client()` returns `QdrantClient | None`, but code expects just `QdrantClient`

**Files:**
- `agents/graphrag/architecture_mapper.py:90`
- `agents/graphrag/code_navigator.py:99`
- `agents/graphrag/dependency_tracer.py:87`
- `agents/graphrag/impact_analyzer.py:83`
- `agents/graphrag/multi_hop_searcher.py:95`
- `agents/graphrag/multi_hop_searcher.py:89` (QdrantRM variant)

**Fix:**
```python
# BEFORE:
qdrant = registry.get_qdrant_client()
graph_store = GraphStore(qdrant, ...)

# AFTER:
qdrant = registry.get_qdrant_client()
if qdrant is None:
    raise ValueError("Qdrant client not initialized")
graph_store = GraphStore(qdrant, ...)
```

---

### 2. Async/Await Coroutine Issues (4+ instances)
**Problem:** Async functions called without `await`, returning Coroutine instead of result

**Files:**
- `agents/graphrag/extractors/interaction_tracer.py:72-73` (accessing .parameter_mapping, .data_description)
- `agents/graphrag/multi_hop_searcher.py:129-130` (indexing into results)
- `agents/knowledge_gardener/orchestrator.py:65-82` (multiple attributes)
- `agents/workflow/every_style_editor_module.py:94-105` (analysis.analysis)

**Fix:**
```python
# BEFORE:
result = async_function()
value = result.parameter_mapping

# AFTER:
result = await async_function()
value = result.parameter_mapping
```

---

### 3. Missing Methods on CodeGraphRAG (2 instances)
**Problem:** Methods don't exist on CodeGraphRAG class

**Files:**
- `agents/graphrag/architecture_mapper.py:102` - `get_top_entities_by_pagerank()`
- `agents/graphrag/architecture_mapper.py:116` - `get_graph_clusters()`

**Fix:** Add methods to CodeGraphRAG class in `utils/knowledge/graphrag/code_graph_rag.py`

---

### 4. Missing Attributes on Services (2+ instances)
**Problem:** Service classes missing expected methods

**Files:**
- `agents/graphrag/extractors/temporal_extractor.py:26` - GitService missing `get_file_history()`
- `utils/memory/maintainer.py` - 4 missing attributes

**Fix:** Add methods to service classes

---

## Priority 2: Medium Errors (Clean up after priority 1)

### 5. __all__ Export Issues (43 instances)
**Problem:** `__all__` list format issues in __init__.py files

**Primary File:**
- `utils/knowledge/utils/__init__.py` (4 errors)

**Fix:**
```python
# Ensure __all__ is a list of strings
__all__ = ["module1", "module2", ...]
```

---

### 6. Bad Argument Types (36 instances)
**Problem:** Type mismatches when calling functions

**Major Files:**
- `utils/web/documentation.py` (3 errors) - httpx.Timeout arguments
- `server/mcp/sampling_handler.py` (3 errors)
- Collection of other files with type mismatches

**Example:**
```python
# BEFORE (wrong):
timeout_config = {"connect": 5.0, "read": 10.0}
client = httpx.Client(timeout=timeout_config)

# AFTER (correct):
timeout_config = httpx.Timeout(connect=5.0, read=10.0)
client = httpx.Client(timeout=timeout_config)
```

---

## Priority 3: Medium-Low Errors

### 7. Function Definition Issues (16 instances)
**Problem:** Function signatures don't match type hints

**Fix:** Update function signatures or type annotations to match

---

### 8. Not Callable (12 instances)
**Problem:** Trying to call objects that aren't callable

**Fix:** Check object types before calling

---

### 9. Bad Return Types (9 instances)
**Problem:** Functions return wrong types

**Fix:** Update return values or type annotations

---

## Priority 4: Low Priority (Polish)

### 10. Liskov Substitution Violations (2 instances)
**Files:**
- `agents/review/code_simplicity_reviewer.py:18` - SimplicityReport.findings override
- `agents/review/performance_oracle.py:16` - PerformanceReport.findings override

**Fix:** Make subclass return types covariant (compatible with parent)

---

### 11. Deprecated APIs (2 instances)
**Problem:** Using deprecated pydantic APIs

**File:**
- `agents/research/schema.py:43` - Using `.dict()` instead of `.model_dump()`

**Fix:**
```python
# BEFORE:
fields = self.dict().items()

# AFTER:
fields = self.model_dump().items()
```

---

### 12. Misc Errors (7+ instances)
- bad-index (2)
- unsupported-operation (7)
- bad-typed-dict-key (4)
- no-matching-overload (4)
- bad-assignment (6)
- unexpected-keyword (5)
- missing-import (1)
- not-a-type (1)

---

## Error Summary Table

| Category | Count | Priority | Complexity |
|----------|-------|----------|-----------|
| missing-attribute | 95 | 🔴 HIGH | Medium |
| bad-dunder-all | 43 | 🟡 MEDIUM | Low |
| bad-argument-type | 36 | 🔴 HIGH | Medium |
| bad-function-definition | 16 | 🟡 MEDIUM | Medium |
| not-callable | 12 | 🟡 MEDIUM | Low |
| bad-return | 9 | 🟡 MEDIUM | Medium |
| unsupported-operation | 7 | 🟢 LOW | Low |
| bad-assignment | 6 | 🟢 LOW | Low |
| unexpected-keyword | 5 | 🟢 LOW | Low |
| bad-typed-dict-key | 4 | 🟢 LOW | Low |
| no-matching-overload | 4 | 🟢 LOW | Medium |
| bad-index | 2 | 🟢 LOW | Low |
| deprecated | 2 | 🟢 LOW | Low |
| bad-override | 2 | 🟢 LOW | Low |
| Other | 1 | 🟢 LOW | - |

---

## Fixing Strategy

### Phase 1: Critical Path (95 missing-attribute errors)
1. Fix QdrantClient type issues (5 files)
2. Fix async/await issues (4 files)
3. Fix CodeGraphRAG missing methods
4. Fix service missing attributes

### Phase 2: Cleanup (43 bad-dunder-all)
1. Fix all __all__ exports in __init__.py files

### Phase 3: Type Safety (36 bad-argument-type)
1. Fix httpx and other argument type issues

### Phase 4: Polish (remaining)
1. Function definitions, returns, callables
2. Liskov violations
3. Deprecated APIs
4. Misc issues

---

## Running Type Checks

```bash
# Full check with summary
uvx pyrefly check --summarize-errors

# Manual script
./scripts/check-types.sh                # Informational
./scripts/check-types.sh --strict       # Fails on errors

# After fixing errors, verify progress
uvx pyrefly check --summarize-errors
```

---

## Workflow

1. Pick an error category from above
2. Mark TODO as `in_progress`
3. Fix all instances of that error type
4. Run `uvx pyrefly check --summarize-errors` to verify
5. Mark TODO as `completed`
6. Move to next category

**Goal:** Reduce from 244 → 0 errors over time
