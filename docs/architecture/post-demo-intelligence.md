# Post-Demo Intelligence

Post-demo intelligence runs after session shutdown. It extracts evidence-backed sales insights and builds a CRM-ready mock payload.

```mermaid
flowchart TB
    Transcript["Transcript evidence"]
    Actions["Browser actions"]
    Screens["Screen summaries"]
    Recipe["Recipe progress"]
    Features["Features shown"]
    Index["Evidence index"]
    Insights["Lead insights"]
    Summary["Lead summary"]
    CRM["Mock CRM payload"]

    Transcript --> Index
    Actions --> Index
    Screens --> Index
    Recipe --> Index
    Features --> Summary
    Index --> Insights
    Insights --> Summary
    Summary --> CRM
```

Rules:

- Every insight must reference evidence.
- LLM output is untrusted until schema-validated and evidence-checked.
- CRM payloads are redacted before export.
- Mock CRM export does not call external systems.
- HubSpot and Salesforce adapters are skeletons unless a later phase implements and live-tests them.

Full AI lead intelligence can be expanded in later phases without changing the evidence model.
