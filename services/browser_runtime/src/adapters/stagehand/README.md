Stagehand is optional and disabled by default.

This adapter boundary may propose observations or extraction results in later phases, but output must be mapped into deterministic `SafeAction` records and validated by the browser runtime action validator before execution.

It must not bypass safety policy or execute hot-path actions unless explicitly enabled for local experimentation.

