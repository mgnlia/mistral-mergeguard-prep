# MergeGuard — Hackathon Sprint Plan
## Mistral Worldwide Hackathon 2026 (Feb 28–Mar 1)

---

## Pre-Hackathon Checklist (Feb 17–27)

### Operator Actions (CRITICAL)
- [ ] 🔴 Register at https://lu.ma/mistralhack-online (approval NOT instant!)
- [ ] 🔴 Ensure Mistral API key is available and funded
- [ ] Attend/record Feb 25 online briefing (~5pm)
- [ ] Vercel account ready for deploy

### Dev Prep (study only, no production code)
- [ ] Read: https://docs.mistral.ai/agents/handoffs
- [ ] Read: https://docs.mistral.ai/agents/tools/
- [ ] Read: https://docs.mistral.ai/capabilities/structured-outputs/
- [ ] Run official handoffs example from docs (throwaway test)
- [ ] Verify `mistralai` Python SDK installed and working
- [ ] Verify `devstral-latest` model access
- [ ] Review ARCHITECTURE.md in this directory
- [ ] Set up Next.js dev environment

---

## Sprint Timeline (34 hours)

### Phase 1: Scaffold (H+0 to H+2) — 2 hours
**Goal:** Repo exists, agents created, handoff chain verified

- [ ] Create GitHub repo `mergeguard`
- [ ] `npx create-next-app@latest` with TypeScript + Tailwind
- [ ] Install `@mistralai/mistralai` SDK
- [ ] Create all 4 agents via API
- [ ] Wire handoff chain: Planner→Reviewer→Verifier→Reporter
- [ ] Test: send "hello" through the chain, verify handoffs work
- [ ] Commit: "scaffold: agents + handoff chain"

### Phase 2: Planner + Reviewer (H+2 to H+8) — 6 hours
**Goal:** Planner decomposes a PR diff, Reviewer produces findings

- [ ] Implement `get_pr_diff` tool (reads from demo PR files)
- [ ] Implement `get_file_context` tool
- [ ] Implement `get_blame` tool (mock for demo)
- [ ] Write Planner system prompt (decompose diff → review plan)
- [ ] Write Reviewer system prompt (plan → line-by-line findings)
- [ ] Test: Planner→Reviewer on demo PR produces findings array
- [ ] Commit: "feat: planner + reviewer agents with tools"

### Phase 3: Verifier + Reporter (H+8 to H+14) — 6 hours
**Goal:** Full pipeline produces structured verdict

- [ ] Write Verifier system prompt (findings → verified findings)
- [ ] Test code_interpreter tool runs linting on demo code
- [ ] Define `MergeVerdict` JSON schema for structured output
- [ ] Write Reporter system prompt (verified findings → verdict JSON)
- [ ] Test: full 4-agent pipeline on demo PR → verdict JSON
- [ ] Commit: "feat: verifier + reporter, full pipeline"

### Phase 4: End-to-End (H+14 to H+20) — 6 hours
**Goal:** Pipeline works reliably on demo PR

- [ ] Create demo PR with 5 known issues (see ARCHITECTURE.md §7)
- [ ] Run full pipeline 3x, verify consistent results
- [ ] Add error handling (timeout, API failure, fallback)
- [ ] Add streaming support (show agent progress in real-time)
- [ ] API route: POST /api/review accepts diff text
- [ ] API route: GET /api/health returns status
- [ ] Commit: "feat: end-to-end pipeline with error handling"

### Phase 5: Frontend (H+20 to H+26) — 6 hours
**Goal:** Beautiful demo UI

- [ ] Dashboard page: paste diff → start review
- [ ] Pipeline progress component (which agent is active)
- [ ] Findings list with severity badges and code snippets
- [ ] Verdict card with confidence score and decision
- [ ] Responsive design (judges may view on mobile)
- [ ] Deploy to Vercel
- [ ] Commit: "feat: frontend dashboard"

### Phase 6: Submission (H+26 to H+30) — 4 hours
**Goal:** Submission-ready package

- [ ] README.md with setup instructions, architecture diagram, demo
- [ ] Record 2-3 min demo video (screen recording)
- [ ] Write submission description (impact, technical depth, creativity)
- [ ] Screenshot collection for submission form
- [ ] Final Vercel deploy with production URL
- [ ] Commit: "docs: submission package"

### Phase 7: Buffer (H+30 to H+34) — 4 hours
**Goal:** Fix anything broken, polish, submit

- [ ] Fix any bugs found during submission prep
- [ ] Polish demo video if needed
- [ ] Submit on whatever portal is revealed at Feb 25 briefing
- [ ] Celebrate 🎉

---

## Demo Script (2-3 minutes)

### Opening (30s)
"MergeGuard is a multi-agent code review pipeline that catches bugs before they merge. Instead of one AI reviewing your code, MergeGuard uses four specialized agents that plan, review, verify, and report — just like a real engineering team."

### Live Demo (90s)
1. Show dashboard — paste a PR diff with known issues
2. Click "Start Review" — watch pipeline progress
3. Planner identifies 5 files, assigns risk levels
4. Reviewer finds: SQL injection (critical), N+1 query (warning), off-by-one (critical)
5. Verifier runs linting, confirms 2/3 critical findings
6. Reporter produces verdict: **BLOCK** with 92% confidence

### Closing (30s)
"MergeGuard uses 6+ Mistral features — Agents API, Handoffs, Function Calling, Code Interpreter, Structured Output, and Devstral. Each agent is specialized for its role, and the handoff chain ensures nothing falls through the cracks. It's not a chatbot — it's an engineering team in a box."

---

## Submission Talking Points

1. **Uses more Mistral features than any competitor** — 6+ features in one project
2. **Real-world impact** — PR review is the #1 bottleneck in software development
3. **Novel architecture** — Multi-agent pipeline with verification step, not a chatbot
4. **Measurable** — Review time, catch rate, false positive rate are all quantifiable
5. **Deployable** — Could ship as a GitHub Action tomorrow
