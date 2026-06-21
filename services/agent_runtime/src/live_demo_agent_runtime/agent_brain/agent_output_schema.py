"""JSON schema for structured agent decisions."""

AGENT_OUTPUT_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["spoken_response", "browser_action", "memory_updates", "confidence"],
    "properties": {
        "spoken_response": {"type": "string", "minLength": 0, "maxLength": 500},
        "browser_action": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["action_id", "tool_name", "reason"],
                    "properties": {
                        "action_id": {"type": "string", "minLength": 1, "maxLength": 200},
                        "tool_name": {
                            "type": "string",
                            "enum": [
                                "read_current_screen",
                                "highlight_element",
                                "click_element",
                                "type_demo_text",
                                "scroll",
                                "go_back",
                                "search_product_knowledge",
                                "save_lead_insight",
                            ],
                        },
                        "reason": {"type": "string", "minLength": 1, "maxLength": 500},
                        "arguments": {"type": "object", "additionalProperties": True},
                    },
                },
            ]
        },
        "memory_updates": {
            "type": "array",
            "maxItems": 5,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["type", "content", "confidence", "evidence"],
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "persona",
                            "pain_point",
                            "use_case",
                            "objection",
                            "buying_signal",
                            "feature_interest",
                            "question",
                            "urgency",
                            "preference",
                            "unanswered_question",
                        ],
                    },
                    "content": {"type": "string", "minLength": 1, "maxLength": 1000},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "importance": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.5,
                    },
                    "evidence": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "transcript_event_ids",
                            "screen_ids",
                            "action_ids",
                        ],
                        "properties": {
                            "transcript_event_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "maxItems": 10,
                            },
                            "screen_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "maxItems": 10,
                            },
                            "action_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "maxItems": 10,
                            },
                        },
                    },
                },
            },
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
}
