# Local Demo Script

Use this for a short local run.

```bash
cp .env.example .env
make up
make open
```

Use fake providers unless you are intentionally testing real provider latency.

Flow:

1. Enter product URL.
2. Add text guidance from [demo-recipe-guide.md](../recipes/demo-recipe-guide.md).
3. Start session.
4. Wait for readiness.
5. Ask: `Can you show me the dashboard?`
6. Ask: `How do I create a new metric?`
7. Ask: `Does this integrate with Salesforce?`
8. End session.
9. Check lead summary.

Expected result: safe actions execute, unsupported claims are avoided, and resources are released.
