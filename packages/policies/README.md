# Live Demo Policies

Shared deterministic safety, RBAC, audit, recipe, and redaction rules.

Rules live in `rules/*.json`. Generated Python and TypeScript modules are checked in under
`generated/` so backend services and browser runtime consume the same source of truth.

```bash
pnpm --filter @live-demo-agent/policies validate
pnpm --filter @live-demo-agent/policies generate
```

Phase 9 implements text and metadata redaction. It does not guarantee pixel-level screenshot
redaction unless visual redaction is explicitly enabled and tested.
