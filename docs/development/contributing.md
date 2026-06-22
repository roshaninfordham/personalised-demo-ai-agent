# Contributing

Before opening a change:

```bash
make contracts
make policy-validate
make lint
make typecheck
make test-unit
make docs-all
```

For browser or session lifecycle changes:

```bash
make test-browser
make test-session-lifecycle
```

For docs changes:

```bash
make docs-all
```

Rules:

- keep changes scoped;
- add tests proportional to risk;
- do not commit `.env`;
- do not commit real secrets;
- update docs when commands, ports, provider variables, or architecture boundaries change.
