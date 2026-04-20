import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from app.learner_state import create_default_learner_state
from app.mvp_pipeline import MVPPipeline
from app.schemas import InteractionContext, PerformanceEvent


QUERY = "已知一次函数 y = 2x + 3，求斜率和截距。"
NO_MATCH_QUERY = "今天天气很好，阳光明媚。"


@pytest.fixture
def pipeline():
    return MVPPipeline()


@pytest.fixture
def state():
    return create_default_learner_state("s_pipeline")


@pytest.fixture
def ctx():
    return InteractionContext(question_difficulty="medium")


@pytest.fixture
def event():
    return PerformanceEvent(correct=False, used_hint=True)


# ---------------------------------------------------------------------------
# run_preview tests
# ---------------------------------------------------------------------------

def test_preview_returns_mapping_result(pipeline, state, ctx):
    result = pipeline.run_preview(QUERY, state, ctx)
    assert result.mapping_result is not None
    assert result.mapping_result.primary_node == "linear_function"


def test_preview_returns_policy_result(pipeline, state, ctx):
    result = pipeline.run_preview(QUERY, state, ctx)
    assert result.policy_result is not None
    assert result.policy_result.selected_policy != ""


def test_preview_returns_generated_response(pipeline, state, ctx):
    result = pipeline.run_preview(QUERY, state, ctx)
    assert result.generated_response is not None
    assert len(result.generated_response.answer_text) > 0


def test_preview_mastery_update_is_none(pipeline, state, ctx):
    result = pipeline.run_preview(QUERY, state, ctx)
    assert result.mastery_update_result is None
    assert result.updated_learner_state is None


# ---------------------------------------------------------------------------
# run_closed_loop tests
# ---------------------------------------------------------------------------

def test_closed_loop_mastery_update_not_none(pipeline, state, ctx, event):
    result = pipeline.run_closed_loop(QUERY, state, ctx, event)
    assert result.mastery_update_result is not None


def test_closed_loop_updated_learner_state_not_none(pipeline, state, ctx, event):
    result = pipeline.run_closed_loop(QUERY, state, ctx, event)
    assert result.updated_learner_state is not None


def test_closed_loop_actually_updates_mastery(pipeline, ctx):
    state = create_default_learner_state("s_update")
    original = state.node_mastery["linear_function"]
    event = PerformanceEvent(correct=True, used_hint=False)
    result = pipeline.run_closed_loop(QUERY, state, ctx, event)
    new_mastery = result.updated_learner_state.node_mastery["linear_function"]
    assert new_mastery != original


# ---------------------------------------------------------------------------
# fallback / no-match test
# ---------------------------------------------------------------------------

def test_no_match_query_returns_fallback_response(pipeline, ctx):
    state = create_default_learner_state("s_fallback")
    result = pipeline.run_preview(NO_MATCH_QUERY, state, ctx)
    assert result.mapping_result.primary_node is None
    assert len(result.generated_response.answer_text) > 0
    assert len(result.generated_response.knowledge_summary) > 0
