// Generated from packages/policies/rules. Do not edit manually.

export const actionSafetyRules = {
  "version": 1,
  "weights": {
    "label": 0.3,
    "role": 0.1,
    "context": 0.2,
    "recipe": 0.2,
    "domain": 0.1,
    "field": 0.05,
    "actor": 0.05
  },
  "categories": [
    {
      "category": "blocked_destructive",
      "risk_level": "blocked",
      "default_decision": "blocked",
      "reason_code": "blocked_destructive_action",
      "phrases": [
        "delete",
        "delete account",
        "delete workspace",
        "delete project",
        "remove",
        "remove user",
        "destroy",
        "wipe",
        "erase",
        "reset account",
        "close account",
        "cancel subscription",
        "revoke access",
        "disable account"
      ]
    },
    {
      "category": "payment_billing",
      "risk_level": "blocked",
      "default_decision": "blocked",
      "reason_code": "payment_billing_blocked",
      "phrases": [
        "billing",
        "payment",
        "pay now",
        "checkout",
        "purchase",
        "buy",
        "upgrade plan",
        "upgrade",
        "change plan",
        "subscription",
        "invoice",
        "credit card"
      ]
    },
    {
      "category": "communication_side_effect",
      "risk_level": "high",
      "default_decision": "confirmation_required",
      "reason_code": "high_risk_requires_confirmation",
      "phrases": [
        "send",
        "send email",
        "invite",
        "invite user",
        "send invite",
        "publish",
        "go live",
        "share externally",
        "export",
        "export data",
        "notify",
        "message customer"
      ]
    },
    {
      "category": "account_settings",
      "risk_level": "high",
      "default_decision": "confirmation_required",
      "reason_code": "account_settings_confirmation_required",
      "phrases": [
        "account settings",
        "admin",
        "users",
        "permissions",
        "api key",
        "token",
        "webhook",
        "integration settings",
        "security settings"
      ]
    },
    {
      "category": "medium_form_action",
      "risk_level": "medium",
      "default_decision": "allowed_if_recipe_allows",
      "reason_code": "medium_risk_action",
      "phrases": [
        "create",
        "add",
        "new",
        "edit",
        "update",
        "save",
        "apply",
        "generate",
        "import",
        "configure"
      ]
    },
    {
      "category": "low_navigation",
      "risk_level": "low",
      "default_decision": "allowed",
      "reason_code": "safe_read_action",
      "phrases": [
        "view",
        "open",
        "show",
        "dashboard",
        "reports",
        "analytics",
        "metrics",
        "back",
        "next",
        "search",
        "scroll",
        "learn more",
        "read current screen",
        "highlight"
      ]
    }
  ],
  "forbidden_authority": {
    "javascript_markers": [
      "document.",
      "window.",
      "evaluate(",
      "<script",
      "javascript:"
    ],
    "selector_markers": [
      "querySelector",
      "getElementById",
      "xpath",
      "css selector",
      "#"
    ]
  },
  "sensitive_field_phrases": [
    "password",
    "token",
    "api key",
    "secret",
    "private key",
    "credit card",
    "card number",
    "cvv",
    "ssn",
    "social security",
    "bank account",
    "routing number",
    "personal email",
    "customer email"
  ]
} as const;
