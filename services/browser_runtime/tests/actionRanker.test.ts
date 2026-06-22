import { describe, expect, it } from "vitest";

import {
  ACTION_EXECUTION_SCORE_THRESHOLD,
  rankActionsForIntent,
  type RankedAction,
  type SafeActionInternal,
} from "../src/actions/actionRanker.js";

describe("action ranker", () => {
  it("ranks dashboard, metric creation, and reports intents deterministically", () => {
    expect(topLabel("Can you show me the dashboard?")).toBe("Open Dashboard");
    expect(topLabel("How do I create a new metric?")).toBe("Add Metric");
    expect(topLabel("Can I see reports?")).toBe("Reports");

    const first = rankActionsForIntent({ user_intent: "Can I see reports?", actions: actions() });
    const second = rankActionsForIntent({ user_intent: "Can I see reports?", actions: actions() });
    expect(first.ranked_actions.map((action) => action.action_id)).toEqual(
      second.ranked_actions.map((action) => action.action_id),
    );
  });

  it("does not produce executable destructive or confirmation-required actions", () => {
    const deleteResult = rankActionsForIntent({
      user_intent: "Delete this project",
      actions: actions(),
    });
    const exportResult = rankActionsForIntent({
      user_intent: "Can I export this?",
      actions: actions(),
    });

    const deleteAction = deleteResult.ranked_actions.find(
      (action) => action.label === "Delete Project",
    );
    expect(deleteAction?.executable).toBe(false);
    expect(deleteResult.top_executable_action?.label).not.toBe("Delete Project");
    expect(firstRanked(exportResult).label).toBe("Export Data");
    expect(firstRanked(exportResult).executable).toBe(false);
  });

  it("uses recipe hints, historical success, latency penalty, and stable tie-breakers", () => {
    const recipe = rankActionsForIntent({
      user_intent: "Continue",
      active_recipe_step: { step_key: "metric_creation", click_hint: "Add Metric" },
      actions: actions(),
    });
    const history = rankActionsForIntent({
      user_intent: "Create a metric",
      actions: [
        action("act_create_metric", "Create Metric", "low"),
        action("act_new_metric", "New Metric", "low"),
      ],
      historical_success: { act_create_metric: 0.95, act_new_metric: 0.4 },
    });
    const latency = rankActionsForIntent({
      user_intent: "Open reports",
      actions: [
        action("act_reports", "Reports", "low"),
        action("act_reports_slow", "Reports via Settings", "low"),
      ],
      latency_cost_ms: { act_reports: 200, act_reports_slow: 2_000 },
    });
    const tied = rankActionsForIntent({
      user_intent: "Open dashboard",
      actions: [action("b", "Dashboard", "low"), action("a", "Dashboard", "low")],
    });

    expect(firstRanked(recipe).label).toBe("Add Metric");
    expect(history.top_executable_action?.action_id).toBe("act_create_metric");
    expect(firstRanked(latency).action_id).toBe("act_reports");
    expect(tied.ranked_actions.map((ranked) => ranked.action_id)).toEqual(["a", "b"]);
  });

  it("ranks 1000 actions under the local hot-path budget", () => {
    const many = Array.from({ length: 1000 }, (_, index) =>
      action(
        `act_${String(index).padStart(4, "0")}`,
        index === 997 ? "Reports" : `Action ${String(index)}`,
        "low",
      ),
    );
    const started = performance.now();
    const result = rankActionsForIntent({ user_intent: "Show reports", actions: many, top_k: 8 });
    const elapsed = performance.now() - started;

    expect(firstRanked(result).label).toBe("Reports");
    expect(elapsed).toBeLessThanOrEqual(25);
    expect(ACTION_EXECUTION_SCORE_THRESHOLD).toBe(0.72);
  });
});

function firstRanked(result: ReturnType<typeof rankActionsForIntent>): RankedAction {
  const [first] = result.ranked_actions;
  if (!first) {
    throw new Error("expected at least one ranked action");
  }
  return first;
}

function topLabel(intent: string): string | undefined {
  return firstRanked(rankActionsForIntent({ user_intent: intent, actions: actions() })).label;
}

function actions(): SafeActionInternal[] {
  return [
    action("act_dashboard", "Open Dashboard", "low"),
    action("act_add_metric", "Add Metric", "low"),
    action("act_billing", "Billing", "blocked"),
    action("act_delete", "Delete Project", "blocked"),
    action("act_reports", "Reports", "low"),
    action("act_export", "Export Data", "high", true),
  ];
}

function action(
  actionId: string,
  label: string,
  riskLevel: SafeActionInternal["risk_level"],
  requiresConfirmation = false,
): SafeActionInternal {
  return {
    action_id: actionId,
    action_type: "click_element",
    element_id: `el_${actionId}`,
    label,
    risk_level: riskLevel,
    score: riskLevel === "blocked" ? 0 : 0.95,
    requires_confirmation: requiresConfirmation,
    reason: `${label} fixture action`,
    expires_at: "2026-06-21T00:00:00.000Z",
    screen_hash: "screen_hash",
  };
}
