# Learner Worker

`services/learner_worker` is the cold-path product learner. It learns product basics asynchronously after a URL or session is created. It enriches future demos through summaries, category detection, safe exploration, demo graph updates, generated routes, knowledge chunks, embeddings, and retrieval.

It must never block first audio or live agent response.

## Cold-Path Pipeline

```mermaid
flowchart TD
    Job["Redis Stream learner job"] --> Lock["Idempotency lock"]
    Lock --> Browser["Read browser screen via browser runtime"]
    Browser --> Summary["First-screen summarizer"]
    Summary --> Category["Category detector"]
    Category --> Explore["Candidate action explorer"]
    Explore --> Graph["Demo graph builder"]
    Graph --> Match["Screen matching/self-healing"]
    Graph --> Route["Generated demo route"]
    Summary --> Chunks["Knowledge chunker"]
    Chunks --> Embed["Embedding writer"]
    Embed --> Retrieval["pgvector retrieval ready"]
```

## Job Lifecycle

```mermaid
stateDiagram-v2
    [*] --> pending
    pending --> running: acquired
    running --> completed: durable results persisted
    running --> pending: retryable failure requeued
    running --> dead_letter: max attempts
    running --> failed: nonretryable failure
```

Jobs are idempotent, restart-safe, tenant-scoped, and bounded by max attempts.

## Exploration Safety

```mermaid
flowchart TD
    SafeActions["Safe actions from browser runtime"] --> Score["Score demo value"]
    Score --> Policy["Policy validation"]
    Policy --> Risk{"Risk"}
    Risk -->|low| Explore["Explore"]
    Risk -->|medium| Recipe{"Recipe explicitly allows?"}
    Recipe -->|yes| Explore
    Recipe -->|no| Skip["Skip"]
    Risk -->|high/blocked| Skip
    Explore --> Graph["Persist graph edge"]
```

Default exploration does not submit forms, type text, click destructive actions, or navigate outside allowed domains.

## Knowledge Flow

```mermaid
flowchart LR
    Sources["Guidance, screen summaries, transcripts, routes"] --> Redact["Redact before chunking"]
    Redact --> Chunk["Deterministic chunks"]
    Chunk --> Dedupe["content_hash dedupe"]
    Dedupe --> Embed["EmbeddingProvider"]
    Embed --> Pgvector["knowledge_chunks.embedding"]
    Pgvector --> Retrieve["bounded top_k retrieval"]
```

## Verification

```bash
make learner-test
make learner-test-integration
```

