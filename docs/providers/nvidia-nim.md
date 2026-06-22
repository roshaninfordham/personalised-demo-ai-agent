# NVIDIA NIM

NVIDIA NIM is an optional hosted text provider.

```env
AI_TEXT_PROVIDER=nvidia_nim
AI_TEXT_BASE_URL=https://integrate.api.nvidia.com/v1
AI_TEXT_API_KEY=<your-key>
AI_TEXT_MODEL=<model-name>
AI_TEXT_ENABLE_STREAMING=true
AI_TEXT_ENABLE_TOOL_CALLING=true
```

NVIDIA documents NIM LLM as OpenAI-compatible for chat completions with streaming and tool-calling support: [NVIDIA NIM LLM API reference](https://docs.nvidia.com/nim/large-language-models/latest/api-reference.html).

No NVIDIA-specific code should appear in business orchestration, agent, learner, or post-demo logic.
