# MergeGuard — Demo PR Plan

> **Pre-hackathon design only — not production code**
> This PR will be created during the hackathon as test material for the pipeline.

---

## Demo Repository: `mergeguard-demo-app`

A simple Python Flask API with intentional issues for MergeGuard to find.

### Base Branch (main) — Clean Codebase

A working Flask app with:
- User authentication (login/register)
- CRUD API for "projects"
- SQLAlchemy ORM
- Basic test suite
- ruff linting config

### PR Branch (feature/user-search) — Contains Intentional Issues

The PR adds a "user search" feature with these planted issues:

---

## Planted Issues (5)

### 1. 🔴 CRITICAL — SQL Injection

**File:** `src/api/users.py`
**What:** Raw f-string SQL query instead of parameterized query

```python
# The vulnerable code in the PR:
@app.route('/api/users/search')
def search_users():
    query = request.args.get('q', '')
    result = db.execute(f"SELECT * FROM users WHERE name LIKE '%{query}%'")
    return jsonify([dict(r) for r in result])
```

**Expected finding:** Critical security — SQL injection via user input

---

### 2. 🟠 HIGH — Missing Authentication

**File:** `src/api/users.py`
**What:** The search endpoint has no `@login_required` decorator

```python
# Missing @login_required on a sensitive endpoint
@app.route('/api/users/search')
def search_users():
    ...
```

**Expected finding:** High security — unauthenticated access to user data

---

### 3. 🟡 MEDIUM — N+1 Query

**File:** `src/api/projects.py`
**What:** Loading projects then querying users one-by-one in a loop

```python
def get_projects_with_owners():
    projects = Project.query.all()
    result = []
    for p in projects:
        owner = User.query.get(p.owner_id)  # N+1 query!
        result.append({"project": p.name, "owner": owner.name})
    return result
```

**Expected finding:** Medium performance — N+1 query pattern

---

### 4. 🟡 MEDIUM — Off-by-One Bug

**File:** `src/utils/pagination.py`
**What:** Pagination calculates wrong total pages

```python
def get_total_pages(total_items, per_page):
    return total_items // per_page  # Bug: should be ceil division
    # 10 items / 3 per_page = 3 (should be 4)
```

**Expected finding:** Medium bug — off-by-one in pagination

---

### 5. 🔵 LOW — Missing Tests

**File:** `src/api/users.py` (new search endpoint)
**What:** New endpoint with zero test coverage

**Expected finding:** Low test_coverage — no tests for search_users()

---

## Bonus Issues (if pipeline is thorough)

### 6. 🔵 LOW — Style Violation

**File:** `src/api/users.py`
**What:** Function uses `camelCase` instead of `snake_case`

```python
def searchUsers():  # Should be search_users
```

### 7. ℹ️ INFO — Missing Docstring

**File:** `src/utils/pagination.py`
**What:** No docstring on `get_total_pages`

---

## Expected MergeGuard Verdict

```json
{
  "verdict": "REQUEST_CHANGES",
  "confidence": 0.95,
  "summary": "Found 1 critical SQL injection vulnerability and 1 high-severity authentication bypass. Additionally identified 2 medium-severity issues (N+1 query, off-by-one bug) and 1 low-severity test coverage gap. The critical and high findings must be addressed before merging.",
  "total_findings": 5
}
```

## Demo Script

1. Show the clean base app running
2. Show the PR diff in GitHub UI
3. Paste the PR URL into MergeGuard
4. Watch the pipeline in real-time:
   - Planner identifies 5 files, 8 chunks, flags users.py as HIGH risk
   - Reviewer finds SQL injection, missing auth, N+1 query
   - Verifier confirms SQL injection with PoC, confirms off-by-one with test
   - Reporter produces structured verdict: REQUEST_CHANGES
5. Show the final report with all findings, evidence, and suggested fixes
6. Highlight: "4 agents, 3 handoffs, function calling, code interpreter, structured output — all in one pipeline"
