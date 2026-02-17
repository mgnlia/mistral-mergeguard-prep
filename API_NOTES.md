# MergeGuard — Mistral Agents API Study Notes

> Notes from reading the official docs at docs.mistral.ai/agents/*

---

## Key API Patterns Learned

### 1. Agent Creation (`client.beta.agents.create`)

```python
agent = client.beta.agents.create(
    model="mistral-large-latest",       # or "devstral-latest"
    name="agent-name",
    description="What this agent does",  # Used by other agents to decide handoffs
    instructions="System prompt",        # Detailed behavioral instructions
    tools=[...],                         # function, web_search, code_interpreter
    completion_args=CompletionArgs(      # Optional: structured output, temperature
        response_format=ResponseFormat(
            type="json_schema",
            json_schema=JSONSchema(name="...", schema=Model.model_json_schema())
        ),
        temperature=0.1,
    ),
    handoffs=[other_agent.id],           # Set AFTER all agents created
)
```

### 2. Handoff Setup (Two-Step)

1. Create all agents first (no handoffs)
2. Update each agent with handoff targets:

```python
client.beta.agents.update(
    agent_id=planner.id,
    handoffs=[reviewer.id]
)
```

**Important:** Handoffs are one-directional. Planner → Reviewer doesn't mean Reviewer → Planner.

### 3. Conversation Flow

```python
# Start
response = client.beta.conversations.start(
    agent_id=planner.id,
    inputs="Review this diff: ...",
    handoff_execution="client"  # or "server"
)

# Continue
response = client.beta.conversations.append(
    conversation_id=response.conversation_id,
    inputs=[...]
)
```

### 4. Handoff Execution Modes

- **`server`** (default): Mistral cloud handles handoffs automatically. The conversation flows through agents without client intervention. Function calls are also handled server-side if possible.
- **`client`**: Handoffs and function calls are returned to the client. The client must handle them and continue the conversation.

**For MergeGuard:** We need `client` mode because:
- We need to intercept function calls (get_file_context, get_blame) and execute them locally against the GitHub API
- We want to emit SSE events for each step (agent_start, handoff, finding, etc.)

### 5. Response Output Types

When using `handoff_execution="client"`, response outputs can be:
- `type == "message"` → Agent produced a text response
- `type == "function.call"` → Agent wants to call a function
- `type == "handoff"` → Agent wants to hand off to another agent (only in client mode)

### 6. Function Call Handling

```python
from mistralai import FunctionResultEntry

if output.type == "function.call":
    result = my_functions[output.name](**json.loads(output.arguments))
    response = client.beta.conversations.append(
        conversation_id=response.conversation_id,
        inputs=[FunctionResultEntry(
            tool_call_id=output.tool_call_id,
            result=json.dumps(result)
        )]
    )
```

### 7. Structured Output with Agents

Use `completion_args` with `response_format`:

```python
from mistralai import CompletionArgs, ResponseFormat, JSONSchema
from pydantic import BaseModel

class Verdict(BaseModel):
    verdict: str
    confidence: float
    findings: list

reporter = client.beta.agents.create(
    model="mistral-large-latest",
    completion_args=CompletionArgs(
        response_format=ResponseFormat(
            type="json_schema",
            json_schema=JSONSchema(
                name="review_verdict",
                schema=Verdict.model_json_schema()
            )
        )
    ),
    ...
)
```

### 8. Streaming

```python
response = client.beta.conversations.start(
    agent_id=planner.id,
    inputs="...",
    stream=True  # If supported
)
```

**Note:** Need to verify if streaming is supported with conversations API during hackathon testing.

### 9. Code Interpreter

Built-in tool, no schema needed:

```python
verifier = client.beta.agents.create(
    model="devstral-latest",
    tools=[{"type": "code_interpreter"}],
    ...
)
```

The agent can write and execute code in a sandboxed environment. Output includes stdout, stderr, and any generated files.

### 10. Web Search

Built-in tool:

```python
reviewer = client.beta.agents.create(
    tools=[
        {"type": "web_search"},
        {"type": "function", "function": {...}},  # Can mix tool types
    ],
    ...
)
```

---

## Important Gotchas

1. **Agent IDs are persistent** — Created agents live on the Mistral platform. Don't recreate on every request. Create once at startup, reuse the IDs.

2. **Conversation state is server-side** — The conversation history is stored by Mistral. We don't need to manage it. Use `store=False` if we don't want persistence.

3. **Handoffs carry context** — When agent A hands off to agent B, the full conversation history is available to B. No need to re-inject context.

4. **Description matters for handoffs** — The agent's `description` field is what other agents see when deciding whether to hand off. Make it clear and specific.

5. **Multiple function calls** — An agent can make multiple function calls in sequence before producing a final response or handoff. Our loop must handle this.

6. **Devstral for code tasks** — `devstral-latest` is optimized for code. Use it for the Verifier (code_interpreter) for better code generation/analysis.

7. **Temperature for determinism** — Use low temperature (0.0-0.2) for Reviewer and Reporter to get consistent, deterministic results. Planner can be slightly higher (0.2-0.3).

---

## SDK Installation

```bash
uv add mistralai fastapi uvicorn httpx sse-starlette pydantic
```

## Environment Variables Needed

```
MISTRAL_API_KEY=...
GITHUB_TOKEN=...  (for PR diff fetching)
```
