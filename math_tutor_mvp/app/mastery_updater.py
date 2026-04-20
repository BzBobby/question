from typing import List
from .schemas import (
    LearnerState,
    MappingResult,
    MasteryUpdateResult,
    NodeUpdate,
    PerformanceEvent,
)
from .knowledge_graph import PREREQUISITE_GRAPH


class MasteryUpdater:
    BASE_DELTA = 0.1

    # ------------------------------------------------------------------
    # Core computation helpers
    # ------------------------------------------------------------------

    def compute_performance_factor(self, event: PerformanceEvent) -> float:
        """Map a PerformanceEvent to a signed performance factor."""
        if event.correct:
            factor = 1.0 if not event.used_hint else 0.4
        else:
            factor = -0.6 if not event.used_hint else -0.9
            if event.clarification_turns > 0:
                factor -= min(event.clarification_turns * 0.05, 0.2)
        return factor

    def compute_delta(self, confidence: float, performance_factor: float) -> float:
        """Mastery delta = base_delta × confidence × performance_factor."""
        return self.BASE_DELTA * confidence * performance_factor

    # ------------------------------------------------------------------
    # State-level helpers
    # ------------------------------------------------------------------

    def detect_prerequisite_gaps(
        self, learner_state: LearnerState, primary_node: str | None
    ) -> List[str]:
        """Return prerequisite nodes whose mastery is below 0.45."""
        if primary_node is None:
            return []
        prereqs = PREREQUISITE_GRAPH.get(primary_node, [])
        return [
            nid
            for nid in prereqs
            if learner_state.node_mastery.get(nid, 0.0) < 0.45
        ]

    def refresh_weak_nodes(self, learner_state: LearnerState) -> List[str]:
        """Return all nodes with mastery < 0.5."""
        return [
            nid
            for nid, mastery in learner_state.node_mastery.items()
            if mastery < 0.5
        ]

    # ------------------------------------------------------------------
    # Main update entry point
    # ------------------------------------------------------------------

    def update(
        self,
        learner_state: LearnerState,
        mapping_result: MappingResult,
        event: PerformanceEvent,
    ) -> MasteryUpdateResult:
        updated_nodes: List[NodeUpdate] = []
        primary_node = mapping_result.primary_node

        if primary_node is not None:
            old_mastery = learner_state.node_mastery[primary_node]
            performance_factor = self.compute_performance_factor(event)
            delta = self.compute_delta(mapping_result.mapping_confidence, performance_factor)
            new_mastery = max(0.0, min(1.0, old_mastery + delta))

            reason = _reason_label(event)

            learner_state.node_mastery[primary_node] = new_mastery
            updated_nodes.append(
                NodeUpdate(
                    node_id=primary_node,
                    old_mastery=round(old_mastery, 6),
                    new_mastery=round(new_mastery, 6),
                    delta=round(delta, 6),
                    reason=reason,
                )
            )

            if not event.correct:
                gaps = self.detect_prerequisite_gaps(learner_state, primary_node)
                learner_state.prerequisite_gaps = gaps
            # On a correct answer we keep existing gaps (caller decides when to clear them)

        learner_state.weak_nodes = self.refresh_weak_nodes(learner_state)

        return MasteryUpdateResult(
            updated_learner_state=learner_state,
            updated_nodes=updated_nodes,
            prerequisite_gaps=learner_state.prerequisite_gaps,
        )


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _reason_label(event: PerformanceEvent) -> str:
    if event.correct:
        return "correct_without_hint" if not event.used_hint else "correct_with_hint"
    return "incorrect_without_hint" if not event.used_hint else "incorrect_with_hint"
