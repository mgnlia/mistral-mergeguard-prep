# MergeGuard — Demo PR Design

> **Status:** Pre-hackathon prep (demo design, not production code)
> **This diff will be created during the hackathon as test input.**

---

## Demo PR: "Add user search and pagination to API"

A realistic PR that a junior developer might submit, containing a mix of good code and intentional issues across all severity levels. This demonstrates MergeGuard's ability to catch diverse problems.

---

## Planned Files & Issues

### File 1: `src/api/users.py` — User search endpoint (MODIFIED)

**Intentional issues:**
1. **🔴 CRITICAL — SQL Injection** (Lines ~15-18)
   - String concatenation in SQL query: `f"SELECT * FROM users WHERE name LIKE '%{search_term}%'"`
   - Should use parameterized queries
   - Expected: Reviewer catches it, Verifier confirms with regex pattern match

2. **🟡 WARNING — Missing input validation** (Lines ~10-12)
   - `search_term` parameter accepted without length limit or sanitization
   - Could enable DoS via extremely long queries

3. **🔵 INFO — Missing error handling** (Lines ~25-30)
   - Database query has no try/except
   - Connection errors would crash the endpoint

### File 2: `src/api/pagination.py` — Pagination helper (NEW FILE)

**Intentional issues:**
4. **🟡 WARNING — Off-by-one error** (Lines ~8-10)
   - `offset = page * per_page` should be `offset = (page - 1) * per_page`
   - Page 1 would skip the first `per_page` results
   - Expected: Verifier writes a test case to prove it

5. **🔵 INFO — No bounds checking** (Lines ~5-7)
   - `page` and `per_page` accept negative values
   - Should clamp to minimum values

### File 3: `src/services/user_service.py` — User service layer (MODIFIED)

**Intentional issues:**
6. **🟡 WARNING — N+1 query** (Lines ~20-28)
   - Loop fetching user profiles one at a time: `for user in users: get_profile(user.id)`
   - Should batch fetch: `get_profiles([u.id for u in users])`

7. **⚪ STYLE — Inconsistent naming** (Lines ~5, ~12, ~30)
   - Mix of `snake_case` and `camelCase`: `getUserById` vs `get_user_list`

### File 4: `src/models/user.py` — User model (MODIFIED)

**Good code (no issues):**
8. **✅ POSITIVE — Well-structured model update**
   - Adds `last_search_at` field with proper type annotation
   - Includes migration note in docstring
   - Expected: Reporter notes this as positive

### File 5: `tests/test_users.py` — Tests (MODIFIED)

**Intentional issues:**
9. **🔵 INFO — Missing test coverage**
   - Tests added for `get_user_list` but NOT for the new search endpoint
   - Expected: Reviewer flags missing test for `search_users`

---

## Expected MergeGuard Verdict

```json
{
  "verdict": "request_changes",
  "summary": "This PR introduces a critical SQL injection vulnerability in the user search endpoint and contains an off-by-one pagination bug. While the user model changes are well-structured, the search functionality needs significant security hardening before merge.",
  "confidence": 0.92,
  "stats": {
    "total_files_reviewed": 5,
    "total_findings": 8,
    "critical_count": 1,
    "warning_count": 3,
    "info_count": 3,
    "style_count": 1,
    "verified_count": 4,
    "false_positive_count": 0
  }
}
```

---

## Demo Script (for video/live demo)

1. **Open MergeGuard dashboard** — Show clean UI
2. **Paste the demo diff** — Or enter a GitHub PR URL
3. **Click "Start Review"** — Pipeline begins
4. **Watch Planner** — Decomposes into 5 file chunks, categorizes security-sensitive files first
5. **Watch Reviewer** — Calls `get_file_context` on users.py, immediately flags SQL injection
6. **Watch Verifier** — Runs code_interpreter to test the off-by-one error with boundary values
7. **Watch Reporter** — Aggregates into structured verdict
8. **Show Results** — "REQUEST_CHANGES" verdict with all findings, severity badges, verification status
9. **Highlight:** "MergeGuard caught a SQL injection that could have reached production"

**Demo duration target:** 2-3 minutes for the full pipeline run + results walkthrough.

---

## Diff Format Reference

The demo diff will be in standard unified diff format:

```diff
diff --git a/src/api/users.py b/src/api/users.py
index abc1234..def5678 100644
--- a/src/api/users.py
+++ b/src/api/users.py
@@ -10,6 +10,20 @@ from src.db import get_connection
+
+@router.get("/users/search")
+async def search_users(search_term: str):
+    conn = get_connection()
+    cursor = conn.cursor()
+    query = f"SELECT * FROM users WHERE name LIKE '%{search_term}%'"
+    cursor.execute(query)
+    results = cursor.fetchall()
+    return {"users": results}
```

This format is what the Planner agent will parse.
