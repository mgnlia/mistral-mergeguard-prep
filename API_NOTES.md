# MergeGuard — Mistral Agents API Notes

> **Status:** Pre-hackathon prep (API study notes)
> **Source:** https://docs.mistral.ai/agents/

---

## Key API Patterns Learned

### 1. Agent Creation (Beta)

```python
from mistralai import Mistral, CompletionArgs, ResponseFormat, JSONSchema

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

agent = client.beta.agents.create(
    model="mistral-large-latest",
    name="agent-name",
    description="What this agent does",
    instructions="System prompt / instructions",
    tools=[...],                    # List of tool configs
    completion_args=CompletionArgs(  # Optional
        response_format=ResponseFormat(
            type="json_schema",
            json_schema=JSONSchema(
                name="schema_name",
                schema=PydanticModel.model_json_schema(),
            )
        ),
        temperature=0.3,
        top_p=0.95,
    ),
)
```

### 2. Handoff Setup

Handoffs are set AFTER agent creation (need agent IDs):

```python
client.beta.agents.update(
    agent_id=planner.id,
    handoffs=[reviewer.id]
)
```

**Important:** No depth limit on chained handoffs. A→B→C→D is fine.

### 3. Conversations API

Start a conversation:
```python
response = client.beta.conversations.start(
    agent_id=planner.id,
    inputs=[{"role": "user", "content": "..."}]
)
```

Continue a conversation (for function call results):
```python
from mistralai import FunctionResultEntry

response = client.beta.conversations.append(
    conversation_id=response.conversation_id,
    inputs=[FunctionResultEntry(
        tool_call_id=response.outputs[-1].tool_call_id,
        result=json.dumps(result_dict),
    )]
)
```

### 4. Response Output Types

The `response.outputs` list contains entries with different `type` values:

| Type | Description | Action Needed |
|------|-------------|---------------|
| `message.output` | Text response from agent | Read content |
| `function.call` | Agent wants to call a custom function | Execute function, return result via `conversations.append` |
| `tool.execution` | Built-in tool was executed (web_search, code_interpreter) | No action — server-side |
| `handoff` | Agent handed off to another agent | Conversation continues with new agent |

### 5. Function Call Handling Loop

```python
import json
from mistralai import FunctionResultEntry

# Map of function names to implementations
FUNCTIONS = {
    "get_file_context": get_file_context_impl,
    "get_blame": get_blame_impl,
}

def run_pipeline(diff_text):
    response = client.beta.conversations.start(
        agent_id=planner.id,
        inputs=[{"role": "user", "content": diff_text}]
    )

    while True:
        last_output = response.outputs[-1]

        if last_output.type == "message.output":
            # Final response (from Reporter)
            return last_output.content
        elif last_output.type == "function.call":
            # Execute the function
            func = FUNCTIONS[last_output.name]
            args = json.loads(last_output.arguments)
            result = func(**args)

            response = client.beta.conversations.append(
                conversation_id=response.conversation_id,
                inputs=[FunctionResultEntry(
                    tool_call_id=last_output.tool_call_id,
                    result=json.dumps(result),
                )]
            )
        else:
            # Handoff or tool execution — check if there's a message
            # The API may return multiple outputs; find the last meaningful one
            break

    return response
```

### 6. Tool Configuration Formats

**Web Search:**
```python
{"type": "web_search"}
# or premium:
{"type": "web_search_premium"}
```

**Code Interpreter:**
```python
{"type": "code_interpreter"}
```

**Custom Function:**
```python
{
    "type": "function",
    "function": {
        "name": "function_name",
        "description": "What it does",
        "parameters": {
            "type": "object",
            "properties": { ... },
            "required": [...]
        }
    }
}
```

### 7. Model Selection

| Agent | Model | Rationale |
|-------|-------|-----------|
| Planner | `mistral-large-latest` | Best reasoning for decomposition |
| Reviewer | `mistral-large-latest` | Best analysis for code review |
| Verifier | `devstral-small-latest` | Code-specialized, good for writing test/lint code |
| Reporter | `mistral-large-latest` | Best at structured output generation |

**Note:** `devstral-small-latest` is the current Devstral model ID. Verify during hackathon — could also be `devstral-2512` or `devstral-small-2512`.

### 8. Structured Output with Agents

For the Reporter agent, use `completion_args` with `response_format`:

```python
from pydantic import BaseModel

class ReviewVerdict(BaseModel):
    verdict: str
    summary: str
    # ... full schema

reporter = client.beta.agents.create(
    model="mistral-large-latest",
    name="mergeguard-reporter",
    instructions="...",
    completion_args=CompletionArgs(
        response_format=ResponseFormat(
            type="json_schema",
            json_schema=JSONSchema(
                name="ReviewVerdict",
                schema=ReviewVerdict.model_json_schema(),
            )
        )
    ),
)
```

---

## Gotchas & Edge Cases to Watch

1. **Handoff outputs:** When an agent hands off, the response may contain multiple outputs (the handoff entry + the new agent's response). Need to iterate through all outputs.

2. **Multiple function calls:** An agent might make multiple function calls in sequence. The loop must handle this — after returning one function result, the agent may call another.

3. **Conversation state:** The conversation_id persists across handoffs. All agents share the same conversation thread.

4. **Rate limits:** With 4 agents + tool calls, a single review could make 10-20 API calls. Watch for rate limiting.

5. **Timeout handling:** Long pipelines could take 30-60 seconds. Need proper timeout handling and SSE keep-alive.

6. **Error recovery:** If an agent fails mid-pipeline, we need to handle gracefully — show partial results.

---

## SDK Installation

```bash
uv add mistralai
# or
uv pip install mistralai
```

Ensure latest version for beta agents API support.
