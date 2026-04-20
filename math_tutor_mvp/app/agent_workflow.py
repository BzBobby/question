"""
PlanningBasedTutorWorkflow
  1. Ask PlannerAgent for an execution plan.
  2. Execute agents in the planned order.
  3. Pass results between agents via typed calls.
  4. Record every hand-off as an AgentMessage in WorkflowTrace.
"""
from .schemas import (
    AgentMessage,
    AgentWorkflowResult,
    InteractionContext,
    LearnerState,
    PerformanceEvent,
    PipelineResult,
    WorkflowTrace,
)
from .agents import (
    KnowledgeModelingAgent,
    PlannerAgent,
    PolicySelectionAgent,
    QuestionAnalysisAgent,
    TutorGenerationAgent,
)


def _msg(sender: str, receiver: str, message_type: str, payload: dict) -> AgentMessage:
    return AgentMessage(
        sender=sender,
        receiver=receiver,
        message_type=message_type,
        payload=payload,
    )


class PlanningBasedTutorWorkflow:
    def __init__(self) -> None:
        self.planner = PlannerAgent()
        self.question_analysis_agent = QuestionAnalysisAgent()
        self.policy_selection_agent = PolicySelectionAgent()
        self.tutor_generation_agent = TutorGenerationAgent()
        self.knowledge_modeling_agent = KnowledgeModelingAgent()

    # ------------------------------------------------------------------
    # Internal: shared execution core
    # ------------------------------------------------------------------

    def _execute(
        self,
        mode: str,
        query_text: str,
        learner_state: LearnerState,
        interaction_context: InteractionContext,
        performance_event: PerformanceEvent | None,
    ) -> AgentWorkflowResult:
        messages: list[AgentMessage] = []
        executed_steps: list[str] = []

        # 1. Planning
        plan = self.planner.plan(mode)
        messages.append(_msg(
            sender="orchestrator",
            receiver="planner",
            message_type="plan",
            payload={"mode": mode, "plan": plan},
        ))

        # 2. Question analysis
        mapping_result = self.question_analysis_agent.run(query_text, interaction_context)
        executed_steps.append("question_analysis")
        messages.append(_msg(
            sender="question_analysis",
            receiver="policy_selection",
            message_type="mapping_result",
            payload={
                "primary_node": mapping_result.primary_node,
                "mapping_confidence": mapping_result.mapping_confidence,
                "matched_nodes": [m.node_id for m in mapping_result.matched_nodes],
            },
        ))

        # 3. Policy selection
        policy_result = self.policy_selection_agent.run(
            learner_state, mapping_result, interaction_context
        )
        executed_steps.append("policy_selection")
        messages.append(_msg(
            sender="policy_selection",
            receiver="tutor_generation",
            message_type="policy_result",
            payload={
                "selected_policy": policy_result.selected_policy,
                "policy_confidence": policy_result.policy_confidence,
                "selection_reasons": policy_result.selection_reasons,
            },
        ))

        # 4. Tutor response generation
        generated_response = self.tutor_generation_agent.run(
            query_text, mapping_result, learner_state, policy_result
        )
        executed_steps.append("tutor_generation")
        messages.append(_msg(
            sender="tutor_generation",
            receiver="orchestrator",
            message_type="generated_response",
            payload={
                "answer_text": generated_response.answer_text[:80],  # truncated for trace
                "primary_node": generated_response.response_metadata.primary_node,
                "selected_policy": generated_response.response_metadata.selected_policy,
            },
        ))

        # 5. Knowledge modeling (closed-loop only)
        mastery_update_result = None
        updated_learner_state = None
        if "knowledge_modeling" in plan:
            assert performance_event is not None, (
                "performance_event is required for closed_loop mode"
            )
            mastery_update_result = self.knowledge_modeling_agent.run(
                learner_state, mapping_result, performance_event
            )
            updated_learner_state = mastery_update_result.updated_learner_state
            executed_steps.append("knowledge_modeling")
            messages.append(_msg(
                sender="knowledge_modeling",
                receiver="orchestrator",
                message_type="mastery_update_result",
                payload={
                    "updated_nodes": [
                        {
                            "node_id": u.node_id,
                            "old_mastery": u.old_mastery,
                            "new_mastery": u.new_mastery,
                            "delta": u.delta,
                        }
                        for u in mastery_update_result.updated_nodes
                    ],
                    "weak_nodes": updated_learner_state.weak_nodes,
                    "prerequisite_gaps": updated_learner_state.prerequisite_gaps,
                },
            ))

        pipeline_result = PipelineResult(
            mapping_result=mapping_result,
            policy_result=policy_result,
            generated_response=generated_response,
            mastery_update_result=mastery_update_result,
            updated_learner_state=updated_learner_state,
        )
        trace = WorkflowTrace(
            executed_steps=executed_steps,
            messages=messages,
            final_status="success",
        )
        return AgentWorkflowResult(pipeline_result=pipeline_result, workflow_trace=trace)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_preview(
        self,
        query_text: str,
        learner_state: LearnerState,
        interaction_context: InteractionContext,
    ) -> AgentWorkflowResult:
        return self._execute(
            mode="preview",
            query_text=query_text,
            learner_state=learner_state,
            interaction_context=interaction_context,
            performance_event=None,
        )

    def run_closed_loop(
        self,
        query_text: str,
        learner_state: LearnerState,
        interaction_context: InteractionContext,
        performance_event: PerformanceEvent,
    ) -> AgentWorkflowResult:
        return self._execute(
            mode="closed_loop",
            query_text=query_text,
            learner_state=learner_state,
            interaction_context=interaction_context,
            performance_event=performance_event,
        )
