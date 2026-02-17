# MergeGuard — Hackathon Sprint Plan

> **Event Window:** Feb 28 09:00 → Mar 1 19:00 (34 hours)
> **All production code must be written within this window.**

---

## Hour-by-Hour Execution Plan

### Phase 1: Scaffold (H+0 to H+2) — Feb 28 09:00–11:00

- [ ] Create `mergeguard` GitHub repo
- [ ] Initialize Python backend with `uv init`
- [ ] Install dependencies: `mistralai`, `fastapi`, `uvicorn`, `sse-starlette`
- [ ] Initialize Next.js frontend: `npx create-next-app@latest`
- [ ] Install frontend deps: `tailwindcss`, `shadcn/ui`, `lucide-react`
- [ ] Set up `.env` with `MISTRAL_API_KEY`
- [ ] Create basic project structure (directories, __init__.py files)
- [ ] Verify Mistral API access with a simple agent creation test
- [ ] Set up `vercel.json` for deployment

### Phase 2: Agent Pipeline Core (H+2 to H+8) — Feb 28 11:00–17:00

- [ ] Implement Pydantic schemas (ReviewVerdict, Finding, etc.)
- [ ] Implement agent factory (create all 4 agents, set up handoffs)
- [ ] Implement Planner agent config + instructions
- [ ] Implement Reviewer agent config + function tool schemas
- [ ] Implement `get_file_context` function handler
- [ ] Implement `get_blame` function handler
- [ ] Implement basic orchestrator (start conversation, handle function calls)
- [ ] Test Planner → Reviewer handoff with a simple diff
- [ ] **Checkpoint:** Planner + Reviewer working end-to-end

### Phase 3: Verifier + Reporter (H+8 to H+14) — Feb 28 17:00–23:00

- [ ] Implement Verifier agent config with code_interpreter
- [ ] Implement Reporter agent config with structured output
- [ ] Wire up full 4-agent handoff chain
- [ ] Implement the function call handling loop (handle multiple calls)
- [ ] Test full pipeline with demo diff
- [ ] Debug handoff issues, tune prompts
- [ ] **Checkpoint:** Full pipeline returns ReviewVerdict JSON

### Phase 4: API Server (H+14 to H+18) — Mar 1 00:00–04:00

- [ ] Implement FastAPI endpoints (POST /review, GET /review/{id})
- [ ] Implement SSE streaming (GET /review/{id}/stream)
- [ ] Add event emission throughout pipeline (agent.started, tool.called, etc.)
- [ ] Implement review storage (in-memory dict for hackathon)
- [ ] Implement async pipeline execution (background task)
- [ ] Test API with curl/httpie

### Phase 5: Frontend (H+18 to H+26) — Mar 1 04:00–12:00

- [ ] Build HomePage with DiffInput component
- [ ] Build PipelineStepper component
- [ ] Build ActivityFeed with SSE consumption
- [ ] Build ResultsPanel with VerdictBadge
- [ ] Build FindingCard components
- [ ] Wire up API calls
- [ ] Style everything with Tailwind (dark theme)
- [ ] Test full flow: paste diff → see pipeline → see results

### Phase 6: Polish & Deploy (H+26 to H+30) — Mar 1 12:00–16:00

- [ ] Create demo PR diff file
- [ ] End-to-end test with demo diff
- [ ] Fix bugs, tune prompts for best demo output
- [ ] Deploy frontend to Vercel
- [ ] Deploy backend (Vercel serverless or Railway)
- [ ] Test deployed version
- [ ] Write README.md with setup instructions

### Phase 7: Submission (H+30 to H+34) — Mar 1 16:00–19:00

- [ ] Record demo video (2-3 minutes)
- [ ] Write submission description
- [ ] Final testing of deployed app
- [ ] Submit to hackathon portal
- [ ] **Buffer time for emergencies**

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Agents API rate limiting | Cache agent IDs, reuse conversations |
| Handoff chain breaks | Test each pair independently first |
| Code interpreter unreliable | Have fallback: skip verification, mark as "unverified" |
| Frontend takes too long | Cut animations, use minimal UI |
| Deployment issues | Have Railway as Vercel backup for backend |
| Demo diff produces bad output | Pre-test multiple diffs, pick best one |

## MVP vs Nice-to-Have

**MVP (must ship):**
- 4-agent pipeline that produces ReviewVerdict JSON
- API with at least POST /review and GET /review/{id}
- Frontend that shows input → results
- Deployed on Vercel

**Nice-to-have (if time permits):**
- Real-time SSE pipeline visualization
- GitHub URL input (fetch diff from GitHub API)
- Animated pipeline stepper
- Code syntax highlighting in findings
- Confetti on APPROVE verdict
