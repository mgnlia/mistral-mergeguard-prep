# MergeGuard — 48h Sprint Plan

> Hackathon: Feb 28 09:00 → Mar 1 19:00 (34h active, 14h buffer/sleep)

---

## Phase 1: Scaffold (H+0 to H+2) — 2 hours

- [ ] Create `mergeguard` repo on GitHub
- [ ] Initialize Python backend (FastAPI + uv)
  - `pyproject.toml` with deps: `mistralai`, `fastapi`, `uvicorn`, `httpx`, `sse-starlette`
  - Basic project structure: `backend/`, `frontend/`
- [ ] Initialize Next.js frontend
  - `npx create-next-app@latest` with App Router, Tailwind, TypeScript
  - Install shadcn/ui
- [ ] Create all 4 Mistral agents via API
- [ ] Test basic handoff chain with a "hello world" message
- [ ] Verify handoff_execution="client" works for function call interception

## Phase 2: Core Pipeline (H+2 to H+8) — 6 hours

- [ ] Implement Planner agent with proper instructions
- [ ] Implement Reviewer agent with function calling tools
- [ ] Build function executors: `get_file_context`, `get_blame`, `get_pr_comments`
  - Wire to GitHub REST API (httpx)
- [ ] Build the conversation loop (handle function calls + handoffs)
- [ ] Test Planner → Reviewer flow with a real diff
- [ ] Verify function calls are intercepted and results returned correctly

## Phase 3: Verifier + Reporter (H+8 to H+14) — 6 hours

- [ ] Implement Verifier agent with code_interpreter
- [ ] Test Verifier receives Reviewer findings and runs verification
- [ ] Implement Reporter agent with structured output (ReviewVerdict schema)
- [ ] Test full 4-agent chain end-to-end
- [ ] Build SSE streaming from backend (FastAPI SSE endpoint)

## Phase 4: End-to-End on Demo PR (H+14 to H+20) — 6 hours

- [ ] Create demo repository with planted issues
- [ ] Create the demo PR (feature/user-search)
- [ ] Run full pipeline on demo PR
- [ ] Debug and fix any handoff/function-call issues
- [ ] Ensure all 5 planted issues are found
- [ ] Tune agent instructions based on results

## Phase 5: Frontend Dashboard (H+20 to H+26) — 6 hours

- [ ] Build landing page (PR URL input)
- [ ] Build pipeline stepper component
- [ ] Build live activity feed (SSE consumer)
- [ ] Build findings panel
- [ ] Build final report page
- [ ] Connect frontend to backend API
- [ ] Deploy to Vercel
- [ ] Test end-to-end in production

## Phase 6: Polish & Submit (H+26 to H+30) — 4 hours

- [ ] Error handling and edge cases
- [ ] Loading states, error states in UI
- [ ] README with architecture diagram, setup instructions
- [ ] Record 3-minute demo video
  - Show the problem (slow PR reviews)
  - Show MergeGuard in action (real-time pipeline)
  - Highlight Mistral features used (6+)
  - Show the verdict
- [ ] Write submission text
- [ ] Submit via hackathon portal

## Phase 7: Buffer (H+30 to H+34) — 4 hours

- Reserved for unexpected issues, final fixes, re-recording demo if needed

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Handoff chain breaks mid-pipeline | Fall back to sequential conversation.append() calls |
| Function calling doesn't work with agents | Use chat completion API directly with tool_choice |
| Code interpreter timeout | Pre-write simpler verification scripts |
| API rate limits | Cache agent IDs, reuse conversations |
| Vercel deploy issues | Have Railway as backup |
| Demo PR too simple | Add more issues, show multiple PRs |

## Key Decision Points

- **H+2:** If handoff chain doesn't work → pivot to sequential agents with manual orchestration
- **H+8:** If function calling in agents is buggy → simplify to 3 agents (drop function calling, embed context in prompt)
- **H+14:** If end-to-end is working → invest more in UI polish; if not → cut frontend to minimal and focus on pipeline
- **H+20:** If demo works → record early backup video; if not → simplify demo scenario
