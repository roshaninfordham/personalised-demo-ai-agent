"""Safe candidate action explorer."""

from __future__ import annotations

from live_demo_learner_worker.browser.browser_runtime_client import (
    BrowserRuntimeClient,
    BrowserScreenRead,
    SafeAction,
)
from live_demo_learner_worker.exploration.action_outcome import ExplorationOutcome
from live_demo_learner_worker.exploration.action_scoring import rank_actions, score_action
from live_demo_learner_worker.exploration.exploration_frontier import ExplorationFrontier
from live_demo_learner_worker.exploration.exploration_limits import ExplorationLimits
from live_demo_learner_worker.exploration.exploration_policy import ExplorationPolicy


class CandidateActionExplorer:
    def __init__(
        self,
        browser_client: BrowserRuntimeClient,
        policy: ExplorationPolicy,
        limits: ExplorationLimits,
    ) -> None:
        self._browser_client = browser_client
        self._policy = policy
        self._limits = limits

    async def explore(self, start: BrowserScreenRead) -> ExplorationOutcome:
        frontier = ExplorationFrontier()
        visited_actions: set[str] = set()
        visited_screens: set[str] = {start.screen_state.screen_hash}
        action_by_id: dict[str, SafeAction] = {}
        for action in rank_actions(start.safe_actions, limit=self._limits.max_actions_per_screen):
            action_by_id[action.action_id] = action
            frontier.push(
                screen_id=start.screen_state.screen_hash,
                action_id=action.action_id,
                depth=0,
                path=(action.action_id,),
                score=score_action(action),
            )
        attempted = skipped = succeeded = failed = 0
        while len(frontier) > 0 and attempted < self._limits.max_total_actions:
            candidate = frontier.pop()
            if candidate is None:
                break
            action = action_by_id[candidate.action_id]
            action_key = f"{candidate.screen_id}:{action.element_fingerprint or action.action_id}"
            if action_key in visited_actions:
                continue
            visited_actions.add(action_key)
            if not self._policy.is_allowed(action):
                skipped += 1
                continue
            attempted += 1
            result = await self._browser_client.execute_action(action)
            if result.success and result.resulting_screen is not None:
                succeeded += 1
                screen = result.resulting_screen
                visited_screens.add(screen.screen_state.screen_hash)
                if candidate.depth + 1 < self._limits.max_depth:
                    for next_action in rank_actions(
                        screen.safe_actions, limit=self._limits.max_actions_per_screen
                    ):
                        action_by_id[next_action.action_id] = next_action
                        frontier.push(
                            screen_id=screen.screen_state.screen_hash,
                            action_id=next_action.action_id,
                            depth=candidate.depth + 1,
                            path=(*candidate.path, next_action.action_id),
                            score=score_action(next_action, seen_action_ids=visited_actions),
                        )
                await self._browser_client.go_back()
            else:
                failed += 1
        return ExplorationOutcome(
            attempted=attempted,
            skipped=skipped,
            succeeded=succeeded,
            failed=failed,
            visited_screens=len(visited_screens),
        )
