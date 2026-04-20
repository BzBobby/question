from .schemas import (
    InteractionContext,
    LearnerState,
    MappingInput,
    MasteryUpdateResult,
    PerformanceEvent,
    PipelineResult,
)
from .knowledge_mapper import KnowledgeMapper
from .mastery_updater import MasteryUpdater
from .policy_selector import PolicySelector
from .response_generator import ResponseGenerator


class MVPPipeline:
    def __init__(self) -> None:
        self.knowledge_mapper = KnowledgeMapper()
        self.policy_selector = PolicySelector()
        self.response_generator = ResponseGenerator()
        self.mastery_updater = MasteryUpdater()

    def _map_select_generate(
        self,
        query_text: str,
        learner_state: LearnerState,
        interaction_context: InteractionContext,
    ):
        """Shared first three steps used by both run modes."""
        mapping_input = MappingInput(
            text=query_text,
            source_type=interaction_context.source_type,
        )
        mapping_result = self.knowledge_mapper.map_text_to_nodes(mapping_input)
        policy_result = self.policy_selector.select_policy(
            learner_state, mapping_result, interaction_context
        )
        generated_response = self.response_generator.generate(
            query_text, mapping_result, learner_state, policy_result
        )
        return mapping_result, policy_result, generated_response

    def run_preview(
        self,
        query_text: str,
        learner_state: LearnerState,
        interaction_context: InteractionContext,
    ) -> PipelineResult:
        """Map → select policy → generate response. No mastery update."""
        mapping_result, policy_result, generated_response = self._map_select_generate(
            query_text, learner_state, interaction_context
        )
        return PipelineResult(
            mapping_result=mapping_result,
            policy_result=policy_result,
            generated_response=generated_response,
        )

    def run_closed_loop(
        self,
        query_text: str,
        learner_state: LearnerState,
        interaction_context: InteractionContext,
        performance_event: PerformanceEvent,
    ) -> PipelineResult:
        """Map → select policy → generate response → update mastery."""
        mapping_result, policy_result, generated_response = self._map_select_generate(
            query_text, learner_state, interaction_context
        )
        mastery_update_result = self.mastery_updater.update(
            learner_state, mapping_result, performance_event
        )
        return PipelineResult(
            mapping_result=mapping_result,
            policy_result=policy_result,
            generated_response=generated_response,
            mastery_update_result=mastery_update_result,
            updated_learner_state=mastery_update_result.updated_learner_state,
        )
