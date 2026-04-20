from typing import Optional
from .schemas import (
    InteractionContext,
    LearnerState,
    MappingResult,
    PolicyScore,
    PolicySelectionResult,
)
from .policy_rules import (
    HIGH_MASTERY_THRESHOLD,
    LOW_MASTERY_THRESHOLD,
    POLICIES,
)


class PolicySelector:

    def get_primary_mastery(
        self,
        learner_state: LearnerState,
        mapping_result: MappingResult,
    ) -> Optional[float]:
        if mapping_result.primary_node is None:
            return None
        return learner_state.node_mastery.get(mapping_result.primary_node)

    def score_policies(
        self,
        learner_state: LearnerState,
        mapping_result: MappingResult,
        interaction_context: InteractionContext,
    ) -> tuple[dict[str, float], list[str]]:
        scores: dict[str, float] = {p: 0.0 for p in POLICIES}
        reasons: list[str] = []
        mastery = self.get_primary_mastery(learner_state, mapping_result)

        # --- A/B/C: mastery-based rules ---
        if mastery is None:
            # Rule I
            scores["direct_explicit_explanation"] += 0.20
            reasons.append("no_primary_node")
        elif mastery < LOW_MASTERY_THRESHOLD:
            # Rule A
            scores["step_by_step_guidance"] += 0.45
            scores["worked_example_oriented_explanation"] += 0.35
            scores["guided_questioning"] -= 0.10
            scores["direct_explicit_explanation"] -= 0.15
            reasons.append("primary_mastery_low")
        elif mastery <= HIGH_MASTERY_THRESHOLD:
            # Rule B
            scores["guided_questioning"] += 0.30
            scores["worked_example_oriented_explanation"] += 0.20
            scores["direct_explicit_explanation"] += 0.10
            reasons.append("primary_mastery_medium")
        else:
            # Rule C
            scores["direct_explicit_explanation"] += 0.40
            scores["guided_questioning"] += 0.20
            scores["step_by_step_guidance"] -= 0.10
            reasons.append("primary_mastery_high")

        # --- D: prerequisite gap ---
        if learner_state.prerequisite_gaps:
            scores["step_by_step_guidance"] += 0.30
            scores["worked_example_oriented_explanation"] += 0.15
            scores["guided_questioning"] -= 0.05
            reasons.append("prerequisite_gap_detected")

        # --- E: multiple clarification turns ---
        if interaction_context.clarification_turns >= 2:
            scores["step_by_step_guidance"] += 0.20
            scores["worked_example_oriented_explanation"] += 0.10
            scores["direct_explicit_explanation"] -= 0.10
            reasons.append("multiple_clarification_turns")

        # --- F: hint used before ---
        if interaction_context.used_hint_before:
            scores["step_by_step_guidance"] += 0.15
            scores["worked_example_oriented_explanation"] += 0.15
            reasons.append("hint_used_before")

        # --- G/H: question difficulty ---
        if interaction_context.question_difficulty == "easy":
            scores["direct_explicit_explanation"] += 0.10
            scores["guided_questioning"] += 0.10
            reasons.append("easy_question")
        elif interaction_context.question_difficulty == "hard":
            scores["step_by_step_guidance"] += 0.20
            scores["worked_example_oriented_explanation"] += 0.20
            reasons.append("hard_question")

        return scores, reasons

    def normalize_policy_scores(
        self, raw_scores: dict[str, float]
    ) -> dict[str, float]:
        min_val = min(raw_scores.values())
        shifted = {p: s - min_val for p, s in raw_scores.items()}
        total = sum(shifted.values())
        if total == 0:
            avg = round(1.0 / len(shifted), 4)
            return {p: avg for p in shifted}
        return {p: round(s / total, 4) for p, s in shifted.items()}

    def select_policy(
        self,
        learner_state: LearnerState,
        mapping_result: MappingResult,
        interaction_context: InteractionContext,
    ) -> PolicySelectionResult:
        raw_scores, reasons = self.score_policies(
            learner_state, mapping_result, interaction_context
        )
        norm_scores = self.normalize_policy_scores(raw_scores)

        candidates = sorted(
            [PolicyScore(policy=p, score=s) for p, s in norm_scores.items()],
            key=lambda x: x.score,
            reverse=True,
        )

        return PolicySelectionResult(
            selected_policy=candidates[0].policy,
            policy_confidence=candidates[0].score,
            candidate_policies=candidates,
            selection_reasons=reasons,
        )
