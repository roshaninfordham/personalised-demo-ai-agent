# Post-Demo Intelligence

Phase 13 adds the cold-path intelligence system that runs after a demo session ends. It extracts only evidence-backed sales insights, generates a structured lead summary, tracks product areas shown, and prepares a redacted CRM-ready payload.

It does not block live shutdown, does not send real HubSpot/Salesforce data, and does not persist unsupported claims as facts.

## Architecture

```mermaid
flowchart TB
    subgraph Evidence["Bounded Evidence Inputs"]
        Transcript["Transcript events"]
        Actions["Browser action events"]
        Screens["Screen snapshots<br/>metadata and summaries only"]
        Progress["Recipe step progress"]
        Existing["Existing lead insights"]
    end

    subgraph Intelligence["services/api/post_demo"]
        Loader["EvidenceLoader"]
        Index["EvidenceIndex"]
        Features["FeatureShownTracker"]
        Rules["DeterministicInsightExtractor"]
        LLM["Optional LLM validators"]
        Summary["LeadSummaryGenerator"]
        Mapper["CRM payload mapper"]
    end

    subgraph Safety["Policy + Safety"]
        EvidenceCheck["Evidence checking"]
        Redaction["RedactionEngine"]
        ExportPolicy["CRM export policy"]
    end

    subgraph Storage["Postgres + Events"]
        Jobs["post_demo_jobs"]
        Insights["lead_insights"]
        FeaturesDB["features_shown"]
        Summaries["lead_summaries"]
        Exports["crm_exports"]
        Events["Redis/session events"]
    end

    Transcript --> Loader
    Actions --> Loader
    Screens --> Loader
    Progress --> Loader
    Existing --> Loader
    Loader --> Index
    Loader --> Features
    Loader --> Rules
    Rules --> EvidenceCheck
    LLM --> EvidenceCheck
    Features --> Summary
    EvidenceCheck --> Summary
    Summary --> Redaction
    Redaction --> Mapper
    Mapper --> ExportPolicy
    ExportPolicy --> Exports
    Features --> FeaturesDB
    Rules --> Insights
    Summary --> Summaries
    Loader --> Jobs
    Summaries --> Events
    Exports --> Events
```

## Job Flow

```mermaid
sequenceDiagram
    participant API as API / Orchestrator
    participant Job as post_demo_jobs
    participant Loader as EvidenceLoader
    participant Extract as Insight + Feature Extractors
    participant Summary as Summary Generator
    participant CRM as CRM Adapter
    participant DB as Postgres
    participant Events as Redis Events

    API->>Job: upsert run_full_post_demo_intelligence
    API->>Events: post_demo.started
    API->>Loader: load bounded tenant-scoped evidence
    Loader-->>API: SessionEvidenceBundle
    API->>Extract: deterministic extraction
    Extract-->>API: insights + features with evidence IDs
    API->>DB: upsert lead_insights + features_shown
    API->>Summary: generate structured summary
    Summary-->>API: redacted validated summary
    API->>DB: upsert lead_summaries
    opt CRM export enabled
        API->>CRM: export redacted generic payload
        CRM-->>API: dry_run_completed / skipped / failed
        API->>DB: persist crm_exports
    end
    API->>Events: lead_summary.ready / crm_export.*
    API->>Job: completed
```

## Evidence Rules

```mermaid
flowchart LR
    Candidate["Candidate insight"] --> HasEvidence{"Evidence IDs present?"}
    HasEvidence -- No --> Reject["Reject"]
    HasEvidence -- Yes --> Exists{"IDs exist in EvidenceIndex?"}
    Exists -- No --> Reject
    Exists -- Yes --> Safe{"Content redacted and bounded?"}
    Safe -- No --> Reject
    Safe -- Yes --> Persist["Persist as lead_insight"]
```

Rules:

- Every persisted insight carries transcript, browser-action, screen, or recipe-step evidence.
- LLM output is treated as candidate data only and must pass schema and evidence validation.
- Summaries are generated from extracted insights, tracked features, counts, and evidence references.
- No raw screenshots, raw audio, cookies, tokens, provider responses, or raw prompts are included.

## CRM Adapter Boundary

```mermaid
classDiagram
    class CrmAdapter {
      <<Protocol>>
      provider_name
      adapter_version
      health_check()
      validate_payload(payload)
      export(request)
    }
    class MockCrmAdapter
    class HubSpotCrmAdapter
    class SalesforceCrmAdapter
    class WebhookCrmAdapter
    class CustomCrmAdapter

    CrmAdapter <|.. MockCrmAdapter
    CrmAdapter <|.. HubSpotCrmAdapter
    CrmAdapter <|.. SalesforceCrmAdapter
    CrmAdapter <|.. WebhookCrmAdapter
    CrmAdapter <|.. CustomCrmAdapter
```

Phase 13 fully implements only the mock adapter. HubSpot, Salesforce, webhook, and custom adapters are registered skeletons that validate configuration and fail honestly without claiming live export support.

## Durable Tables

```mermaid
erDiagram
    demo_sessions ||--o{ post_demo_jobs : has
    demo_sessions ||--o{ features_shown : shows
    demo_sessions ||--o{ lead_insights : extracts
    demo_sessions ||--|| lead_summaries : summarizes
    lead_summaries ||--o{ crm_exports : exports

    post_demo_jobs {
      uuid post_demo_job_id
      uuid organization_id
      uuid session_id
      text job_type
      text status
      text idempotency_key
    }

    features_shown {
      uuid feature_shown_id
      uuid organization_id
      uuid session_id
      uuid product_id
      text feature_key
      numeric confidence
    }

    crm_exports {
      uuid crm_export_id
      uuid organization_id
      uuid session_id
      uuid lead_summary_id
      text provider
      text status
      boolean dry_run
    }
```

## Security Notes

- CRM export defaults to `mock` and `CRM_EXPORT_DRY_RUN=true`.
- Mock export writes a local redacted JSON artifact and makes no external network call.
- Real CRM adapters must not send data until a later implementation explicitly enables and verifies them.
- Webhook URLs are checked for HTTPS and private/internal host restrictions outside local mode.
- Contact email preservation is limited to explicit lead/session fields. Transcript-derived emails remain subject to redaction.
- Screenshot pixel redaction is not implemented here; only text and metadata redaction are applied.

## Verification

```bash
make post-demo-test
make post-demo-test-integration
```
