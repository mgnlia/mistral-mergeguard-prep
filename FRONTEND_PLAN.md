# MergeGuard — Frontend Plan

> **Status:** Pre-hackathon prep (UI design, not production code)

---

## 1. Pages

### Page 1: Home / Submit (`/`)
- Hero section: "MergeGuard — AI-Powered Multi-Agent Code Review"
- Two input modes:
  - **Paste Diff:** Large textarea for pasting unified diff
  - **GitHub URL:** Input field for `https://github.com/owner/repo/pull/123`
- Options panel (collapsible):
  - Focus areas checkboxes: Security, Bugs, Performance, Quality
  - Severity threshold dropdown
- "Start Review" button → redirects to `/review/[id]`

### Page 2: Review Pipeline (`/review/[id]`)
- **Top:** Review metadata (PR title, files changed count, timestamp)
- **Pipeline Visualization:** Horizontal stepper showing 4 agents
  - Each step shows: agent name, model, status (waiting/active/done)
  - Active step has animated pulse
  - Completed steps show green checkmark + duration
- **Activity Feed:** Real-time log of events (SSE)
  - Tool calls with expandable details
  - Findings as they're detected (with severity badge)
  - Handoff events with arrow animation
- **Results Panel** (appears when pipeline completes):
  - Verdict badge: APPROVE (green), COMMENT (yellow), REQUEST_CHANGES (red)
  - Summary paragraph
  - Stats bar: X critical, Y warnings, Z info, W style
  - Per-file accordion with findings
  - Each finding: severity badge, title, description, suggestion, verification status

## 2. Component Tree

```
App
├── Layout
│   ├── Header (logo, "Powered by Mistral AI" badge)
│   └── Footer
├── HomePage
│   ├── HeroSection
│   ├── DiffInput
│   │   ├── TabSwitch (Paste / GitHub URL)
│   │   ├── DiffTextarea
│   │   └── GitHubUrlInput
│   ├── ReviewOptions
│   └── SubmitButton
└── ReviewPage
    ├── ReviewHeader (PR info)
    ├── PipelineStepper
    │   ├── AgentStep (×4)
    │   │   ├── AgentIcon
    │   │   ├── AgentLabel
    │   │   ├── ModelBadge
    │   │   └── StatusIndicator
    │   └── HandoffArrow (×3)
    ├── ActivityFeed
    │   ├── EventCard (×N)
    │   │   ├── EventIcon
    │   │   ├── EventTimestamp
    │   │   └── EventDetail
    │   └── ScrollAnchor (auto-scroll)
    └── ResultsPanel
        ├── VerdictBadge
        ├── SummaryText
        ├── StatsBar
        ├── FileAccordion (×N)
        │   ├── FileHeader (path, language, finding count)
        │   ├── FindingCard (×N)
        │   │   ├── SeverityBadge
        │   │   ├── CategoryTag
        │   │   ├── Title
        │   │   ├── Description
        │   │   ├── CodeSnippet (syntax highlighted)
        │   │   ├── Suggestion
        │   │   └── VerificationBadge
        │   └── PositiveNotes
        └── RecommendationsList
```

## 3. Visual Design

### Color Palette
- **Background:** Dark (#0a0a0a) with subtle grid pattern
- **Cards:** Dark gray (#1a1a1a) with border (#2a2a2a)
- **Primary accent:** Mistral orange (#FF7000)
- **Severity colors:**
  - Critical: Red (#EF4444)
  - Warning: Amber (#F59E0B)
  - Info: Blue (#3B82F6)
  - Style: Gray (#6B7280)
- **Verdict colors:**
  - Approve: Green (#22C55E)
  - Comment: Yellow (#EAB308)
  - Request Changes: Red (#EF4444)
- **Verification status:**
  - Verified: Green (#22C55E) with checkmark
  - Likely: Blue (#3B82F6) with ~
  - Unverified: Gray (#6B7280) with ?
  - False Positive: Strikethrough

### Typography
- **Font:** Inter (system fallback)
- **Code:** JetBrains Mono
- **Headings:** Bold, tracking-tight

### Animations
- Pipeline stepper: Smooth transitions between steps
- Active agent: Pulsing glow effect
- Finding cards: Slide-in animation as they appear
- Verdict reveal: Scale-up with confetti for APPROVE

## 4. Key UX Decisions

1. **Real-time is critical for demo:** The pipeline visualization must update in real-time via SSE. This is the "wow factor" for judges.

2. **No auth required:** For the hackathon demo, no login needed. Just paste and go.

3. **Mobile responsive:** But optimized for desktop (judges will likely use laptops).

4. **Dark mode only:** Looks more professional for demos, faster to build.

5. **Loading states:** Each agent step has a skeleton loader while waiting.

6. **Error handling:** If pipeline fails, show which agent failed and why, with retry option.

## 5. Tech Choices

- **Next.js 14+** with App Router
- **Tailwind CSS** for styling
- **shadcn/ui** for base components (Button, Card, Badge, Accordion, Tabs)
- **Lucide React** for icons
- **react-syntax-highlighter** or **shiki** for code blocks
- **EventSource API** for SSE consumption
- **Framer Motion** for animations (if time permits, otherwise CSS transitions)

## 6. API Integration

```typescript
// Pseudocode for SSE consumption

function useReviewStream(reviewId: string) {
  const [state, dispatch] = useReducer(reviewReducer, initialState);

  useEffect(() => {
    const eventSource = new EventSource(`/api/review/${reviewId}/stream`);

    eventSource.addEventListener('agent.started', (e) => {
      dispatch({ type: 'AGENT_STARTED', payload: JSON.parse(e.data) });
    });

    eventSource.addEventListener('tool.called', (e) => {
      dispatch({ type: 'TOOL_CALLED', payload: JSON.parse(e.data) });
    });

    eventSource.addEventListener('finding.detected', (e) => {
      dispatch({ type: 'FINDING_DETECTED', payload: JSON.parse(e.data) });
    });

    eventSource.addEventListener('agent.handoff', (e) => {
      dispatch({ type: 'AGENT_HANDOFF', payload: JSON.parse(e.data) });
    });

    eventSource.addEventListener('pipeline.completed', (e) => {
      dispatch({ type: 'PIPELINE_COMPLETED', payload: JSON.parse(e.data) });
      eventSource.close();
    });

    return () => eventSource.close();
  }, [reviewId]);

  return state;
}
```
