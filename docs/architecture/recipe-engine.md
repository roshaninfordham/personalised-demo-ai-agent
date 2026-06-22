# Recipe Engine

Recipes make demos more reliable by turning goals, talk tracks, hints, and safety constraints into a compiled plan.

```mermaid
flowchart TB
    Guidance["Text guidance or JSON recipe"] --> Validate["Schema and safety validation"]
    Validate --> Compile["Compile recipe"]
    Compile --> Step["Active step"]
    Step --> Context["Agent context"]
    Step --> Policy["Recipe policy"]
    Policy --> Browser["Safe action routing"]
```

Recipe modes:

- URL only: best for exploration.
- URL plus text guidance: faster authoring with better direction.
- URL plus JSON recipe: best for deterministic demos.

Generated recipes are drafts until validated. Raw selectors and JavaScript are rejected.
