import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from app.learner_state import create_default_learner_state
from app.agent_workflow import PlanningBasedTutorWorkflow
from app.schemas import InteractionContext, PerformanceEvent

QUERY = "已知一次函数 y = 2x + 3，求斜率和截距。"
NO_MATCH_QUERY = "今天天气很好，阳光明媚。"


@pytest.fixture
def workflow():
    return PlanningBasedTutorWorkflow()


@pytest.fixture
def state():
    return create_default_learner_state("s_wf")


@pytest.fixture
def ctx():
    return InteractionContext(question_difficulty="medium")


@pytest.fixture
def event():
    return PerformanceEvent(correct=False, used_hint=True)


# ---------------------------------------------------------------------------
# Execution plan tests
# ---------------------------------------------------------------------------

def test_preview_executed_steps(workflow, state, ctx):
    result = workflow.run_preview(QUERY, state, ctx)
    assert result.workflow_trace.executed_steps == [
        "question_analysis", "policy_selection", "tutor_generation"
    ]


def test_closed_loop_executed_steps(workflow, state, ctx, event):
    result = workflow.run_closed_loop(QUERY, state, ctx, event)
    assert result.workflow_trace.executed_steps == [
        "question_analysis", "policy_selection", "tutor_generation", "knowledge_modeling"
    ]


# ---------------------------------------------------------------------------
# Pipeline result content tests
# ---------------------------------------------------------------------------

def test_preview_mapping_result_nonempty(workflow, state, ctx):
    result = workflow.run_preview(QUERY, state, ctx)
    assert result.pipeline_result.mapping_result is not None
    assert result.pipeline_result.mapping_result.primary_node == "linear_function"


def test_preview_policy_result_nonempty(workflow, state, ctx):
    result = workflow.run_preview(QUERY, state, ctx)
    assert result.pipeline_result.policy_result is not None
    assert result.pipeline_result.policy_result.selected_policy != ""


def test_preview_generated_response_nonempty(workflow, state, ctx):
    result = workflow.run_preview(QUERY, state, ctx)
    assert len(result.pipeline_result.generated_response.answer_text) > 0


def test_closed_loop_mastery_update_not_none(workflow, state, ctx, event):
    result = workflow.run_closed_loop(QUERY, state, ctx, event)
    assert result.pipeline_result.mastery_update_result is not None


def test_closed_loop_updated_learner_state_not_none(workflow, state, ctx, event):
    result = workflow.run_closed_loop(QUERY, state, ctx, event)
    assert result.pipeline_result.updated_learner_state is not None


# ---------------------------------------------------------------------------
# Workflow trace message tests
# ---------------------------------------------------------------------------

def _message_types(result) -> list[str]:
    return [m.message_type for m in result.workflow_trace.messages]


def test_trace_contains_plan(workflow, state, ctx):
    result = workflow.run_preview(QUERY, state, ctx)
    assert "plan" in _message_types(result)


def test_trace_contains_mapping_result(workflow, state, ctx):
    result = workflow.run_preview(QUERY, state, ctx)
    assert "mapping_result" in _message_types(result)


def test_trace_contains_policy_result(workflow, state, ctx):
    result = workflow.run_preview(QUERY, state, ctx)
    assert "policy_result" in _message_types(result)


def test_trace_contains_generated_response(workflow, state, ctx):
    result = workflow.run_preview(QUERY, state, ctx)
    assert "generated_response" in _message_types(result)


def test_closed_loop_trace_contains_mastery_update_result(workflow, state, ctx, event):
    result = workflow.run_closed_loop(QUERY, state, ctx, event)
    assert "mastery_update_result" in _message_types(result)


# ---------------------------------------------------------------------------
# Fallback / no-match test
# ---------------------------------------------------------------------------

def test_no_match_query_returns_fallback_response(workflow, ctx):
    state = create_default_learner_state("s_fallback")
    result = workflow.run_preview(NO_MATCH_QUERY, state, ctx)
    assert result.pipeline_result.mapping_result.primary_node is None
    assert len(result.pipeline_result.generated_response.answer_text) > 0
