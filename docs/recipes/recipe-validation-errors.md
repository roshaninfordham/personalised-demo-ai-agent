# Recipe Validation Errors

| Error code | Component | Meaning | Fix |
| --- | --- | --- | --- |
| `step_order_not_contiguous` | compiler | Step order has gaps or duplicates | Renumber steps from 0 |
| `duplicate_step_key` | compiler | Step key repeats | Use unique keys |
| `destructive_action_not_allowed` | policy | Destructive action appears in allowed actions | Remove it |
| `raw_selector_not_allowed` | policy | CSS/XPath selector was supplied | Use labels and hints |
| `javascript_not_allowed` | policy | Arbitrary script was supplied | Remove it |
| `domain_not_allowed` | domain policy | Domain is outside allowed set | Use a safe product domain |
| `sensitive_form_field_not_allowed` | form policy | Sensitive field was allowed | Remove the field |

Validation fails closed. A recipe cannot override global browser safety policy.
