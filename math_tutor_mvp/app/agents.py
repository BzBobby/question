"""
Thin agent wrappers around the existing tool modules.
Each agent has a single .run() method, takes typed inputs, returns typed outputs.
Planner decides the execution order; agents do not know about each other.
"""
from .schemas import (
    GeneratedResponse,
    InteractionContext,
    LearnerState,
    MappingInput,
    MappingResult,
    MasteryUpdateResult,
    PerformanceEvent,
    PolicySelectionResult,
)
from .knowledge_mapper import KnowledgeMapper
from .mastery_updater import MasteryUpdater
from .policy_selector import PolicySelector
from .response_generator import ResponseGenerator


# ---------------------------------------------------------------------------
# PlannerAgent
# ---------------------------------------------------------------------------

_PLANS: dict[str, list[str]] = {
    "preview": [
        "question_analysis",
        "policy_selection",
        "tutor_generation",
    ],
    "closed_loop": [
        "question_analysis",
        "policy_selection",
        "tutor_generation",
        "knowledge_modeling",
    ],
}


class PlannerAgent:
    name = "planner"

    def plan(self, mode: str) -> list[str]:
        if mode not in _PLANS:
            raise ValueError(f"Unknown mode: {mode!r}. Choose from {list(_PLANS)}")
        return list(_PLANS[mode])


# ---------------------------------------------------------------------------
# QuestionAnalysisAgent
# ---------------------------------------------------------------------------

class QuestionAnalysisAgent:
    name = "question_analysis"

    def __init__(self) -> None:
        self._mapper = KnowledgeMapper()

    def run(
        self,
        query_text: str,
        interaction_context: InteractionContext,
    ) -> MappingResult:
        mapping_input = MappingInput(
            text=query_text,
            source_type=interaction_context.source_type,
        )
        return self._mapper.map_text_to_nodes(mapping_input)


# ---------------------------------------------------------------------------
# PolicySelectionAgent
# ---------------------------------------------------------------------------

class PolicySelectionAgent:
    name = "policy_selection"

    def __init__(self) -> None:
        self._selector = PolicySelector()

    def run(
        self,
        learner_state: LearnerState,
        mapping_result: MappingResult,
        interaction_context: InteractionContext,
    ) -> PolicySelectionResult:
        return self._selector.select_policy(
            learner_state, mapping_result, interaction_context
        )


# ---------------------------------------------------------------------------
# TutorGenerationAgent
# ---------------------------------------------------------------------------

class TutorGenerationAgent:
    name = "tutor_generation"

    def __init__(self) -> None:
        self._generator = ResponseGenerator()

    def run(
        self,
        query_text: str,
        mapping_result: MappingResult,
        learner_state: LearnerState,
        policy_result: PolicySelectionResult,
    ) -> GeneratedResponse:
        return self._generator.generate(
            query_text, mapping_result, learner_state, policy_result
        )


# ---------------------------------------------------------------------------
# KnowledgeModelingAgent
# ---------------------------------------------------------------------------

class KnowledgeModelingAgent:
    name = "knowledge_modeling"

    def __init__(self) -> None:
        self._updater = MasteryUpdater()

    def run(
        self,
        learner_state: LearnerState,
        mapping_result: MappingResult,
        performance_event: PerformanceEvent,
    ) -> MasteryUpdateResult:
        return self._updater.update(learner_state, mapping_result, performance_event)
