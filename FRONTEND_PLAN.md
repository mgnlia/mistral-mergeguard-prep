# MergeGuard — Frontend Plan (Next.js)

> **Pre-hackathon design only — not production code**

---

## 1. Pages & Routes

```
/                    → Landing page with PR URL input
/review/:id          → Review dashboard (real-time pipeline view)
/review/:id/report   → Final report view (shareable)
```

## 2. Landing Page (`/`)

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│              🛡️  MergeGuard                              │
│         Multi-Agent Code Review Pipeline                 │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  https://github.com/owner/repo/pull/123           │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│              [ 🔍 Start Review ]                         │
│                                                          │
│  ─── or paste a diff ───                                 │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  (textarea for raw diff)                           │  │
│  │                                                    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Powered by Mistral Agents API                           │
│  Planner → Reviewer → Verifier → Reporter                │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## 3. Review Dashboard (`/review/:id`)

This is the **hero page** — shows real-time pipeline progress.

```
┌──────────────────────────────────────────────────────────┐
│  🛡️ MergeGuard  │  Review #rev_abc123                    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Pipeline Progress                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ PLANNER  │→│ REVIEWER  │→│ VERIFIER  │→│ REPORTER  ││
│  │ ✅ Done  │  │ 🔄 Active│  │ ⏳ Wait  │  │ ⏳ Wait  ││
│  │ 15s      │  │ 23s...   │  │          │  │          ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
│                                                          │
│  ── Live Activity Feed ──                                │
│                                                          │
│  12:00:00  🟢 Planner started                            │
│  12:00:05  📋 Analyzing 5 changed files                  │
│  12:00:12  📦 Decomposed into 8 review chunks            │
│  12:00:15  🔀 Handoff: Planner → Reviewer                │
│  12:00:18  🔍 Reviewing src/auth/login.py (HIGH risk)    │
│  12:00:20  🔧 Function call: get_file_context(login.py)  │
│  12:00:23  🚨 Finding: SQL Injection in login() [CRIT]   │
│  12:00:25  🔍 Reviewing src/api/users.py (MEDIUM risk)   │
│  ...                                                     │
│                                                          │
│  ── Findings So Far (3) ──                               │
│                                                          │
│  🔴 CRITICAL  SQL Injection in login()     login.py:15   │
│  🟡 MEDIUM    Missing input validation     users.py:42   │
│  🔵 LOW       Inconsistent naming          utils.py:8    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Key UI Components

1. **Pipeline Stepper** — 4 horizontal cards showing agent status
   - States: waiting (gray), active (blue pulse), complete (green), error (red)
   - Shows elapsed time for each agent

2. **Live Activity Feed** — Scrolling log of SSE events
   - Color-coded by event type
   - Auto-scrolls to bottom
   - Timestamps

3. **Findings Panel** — Cards for each finding as they come in
   - Color-coded by severity
   - Expandable for details
   - Verification badge (✅ verified, ❓ unverified)

## 4. Report View (`/review/:id/report`)

Final shareable report after pipeline completes.

```
┌──────────────────────────────────────────────────────────┐
│  🛡️ MergeGuard Review Report                             │
│  PR: owner/repo#123                                      │
│  Date: Feb 28, 2026 12:02 UTC                            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Verdict: 🔴 REQUEST_CHANGES                       │  │
│  │  Confidence: 0.92                                  │  │
│  │                                                    │  │
│  │  Found 1 critical security vulnerability and 2     │  │
│  │  medium-severity issues. The SQL injection in      │  │
│  │  login.py must be fixed before merging.            │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Summary Stats                                           │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │
│  │🔴 1    │ │🟠 0    │ │🟡 2    │ │🔵 1    │           │
│  │Critical│ │High    │ │Medium  │ │Low     │           │
│  └────────┘ └────────┘ └────────┘ └────────┘           │
│                                                          │
│  ── Findings ──                                          │
│                                                          │
│  F001 🔴 CRITICAL — SQL Injection in login()             │
│  ┌──────────────────────────────────────────────────┐    │
│  │ File: src/auth/login.py:15-15                     │    │
│  │ Category: Security                                │    │
│  │ Status: ✅ Verified                                │    │
│  │                                                   │    │
│  │ The login function uses f-string interpolation    │    │
│  │ to construct SQL queries, allowing injection.     │    │
│  │                                                   │    │
│  │ ```python                                         │    │
│  │ # Current (vulnerable)                            │    │
│  │ query = f"SELECT * FROM users WHERE name='{u}'"   │    │
│  │                                                   │    │
│  │ # Suggested fix                                   │    │
│  │ query = "SELECT * FROM users WHERE name = %s"     │    │
│  │ cursor.execute(query, (username,))                │    │
│  │ ```                                               │    │
│  │                                                   │    │
│  │ Evidence: Code interpreter confirmed injection    │    │
│  │ with payload: ' OR '1'='1                         │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  Pipeline Metrics                                        │
│  Total time: 2m 30s                                      │
│  Agents: Planner (15s) → Reviewer (45s) →                │
│          Verifier (60s) → Reporter (10s)                 │
│  Function calls: 3 │ Code executions: 4                  │
│                                                          │
│  [ 📋 Copy JSON ] [ 🔗 Share Link ]                      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## 5. Tech Choices

| Aspect | Choice | Rationale |
|--------|--------|-----------|
| Framework | Next.js 14 (App Router) | Vercel-native, SSR for report pages |
| Styling | Tailwind CSS | Fast to build, consistent |
| Components | shadcn/ui | Professional look, accessible |
| Icons | Lucide React | Clean, consistent icon set |
| SSE Client | EventSource API | Native browser support |
| State | React useState + useReducer | Simple, no external deps needed |
| Animation | Framer Motion (minimal) | Pipeline stepper transitions |

## 6. Color Palette

```
Background:  #0a0a0a (dark) / #ffffff (light)
Primary:     #f97316 (Mistral orange)
Critical:    #ef4444 (red)
High:        #f97316 (orange)
Medium:      #eab308 (yellow)
Low:         #3b82f6 (blue)
Info:        #6b7280 (gray)
Success:     #22c55e (green)
Active:      #6366f1 (indigo pulse)
```

## 7. Responsive Design

- Desktop: Full dashboard with side-by-side panels
- Tablet: Stacked layout, pipeline stepper wraps
- Mobile: Single column, collapsible sections
- Report page: Print-friendly CSS for PDF export
