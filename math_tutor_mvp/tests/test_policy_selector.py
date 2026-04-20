import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from app.learner_state import create_default_learner_state
from app.policy_selector import PolicySelector
from app.schemas import InteractionContext, MappingResult, NodeMatch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mapping(primary_node, confidence=0.8):
    if primary_node is None:
        return MappingResult(
            input_text="test",
            source_type="question",
            matched_nodes=[],
            primary_node=None,
            prerequisite_nodes=[],
            mapping_confidence=0.0,
        )
    return MappingResult(
        input_text="test",
        source_type="question",
        matched_nodes=[NodeMatch(node_id=primary_node, node_name_zh="", score=confidence, evidence=[])],
        primary_node=primary_node,
        prerequisite_nodes=[],
        mapping_confidence=confidence,
    )


def make_ctx(difficulty="medium", clarification_turns=0, used_hint_before=False):
    return InteractionContext(
        question_difficulty=difficulty,
        clarification_turns=clarification_turns,
        used_hint_before=used_hint_before,
    )


@pytest.fixture
def selector():
    return PolicySelector()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_low_mastery_favors_step_by_step(selector):
    """mastery < 0.4 should select step_by_step_guidance."""
    state = create_default_learner_state("s1")
    state.node_mastery["linear_equation_one_variable"] = 0.3
    result = selector.select_policy(state, make_mapping("linear_equation_one_variable"), make_ctx())
    assert result.selected_policy == "step_by_step_guidance"


def test_high_mastery_favors_direct_explanation(selector):
    """mastery > 0.7 should select direct_explicit_explanation."""
    state = create_default_learner_state("s2")
    state.node_mastery["factorization"] = 0.85
    result = selector.select_policy(state, make_mapping("factorization"), make_ctx())
    assert result.selected_policy == "direct_explicit_explanation"


def test_prerequisite_gap_boosts_step_by_step(selector):
    """prerequisite_gaps present should raise step_by_step_guidance score."""
    state_no_gap = create_default_learner_state("s3a")
    state_no_gap.node_mastery["linear_function"] = 0.35

    state_gap = create_default_learner_state("s3b")
    state_gap.node_mastery["linear_function"] = 0.35
    state_gap.prerequisite_gaps = ["linear_equation_one_variable"]

    mapping = make_mapping("linear_function")
    ctx = make_ctx()

    raw_no_gap, _ = selector.score_policies(state_no_gap, mapping, ctx)
    raw_gap, _ = selector.score_policies(state_gap, mapping, ctx)

    assert raw_gap["step_by_step_guidance"] > raw_no_gap["step_by_step_guidance"]
    assert "prerequisite_gap_detected" in selector.score_policies(state_gap, mapping, ctx)[1]


def test_clarification_turns_boosts_step_by_step(selector):
    """clarification_turns >= 2 should raise step_by_step_guidance score."""
    state = create_default_learner_state("s4")
    state.node_mastery["coordinate_system"] = 0.5
    mapping = make_mapping("coordinate_system")

    raw_0, _ = selector.score_policies(state, mapping, make_ctx(clarification_turns=0))
    raw_2, reasons = selector.score_policies(state, mapping, make_ctx(clarification_turns=2))

    assert raw_2["step_by_step_guidance"] > raw_0["step_by_step_guidance"]
    assert "multiple_clarification_turns" in reasons


def test_none_primary_node_returns_valid_policy(selector):
    """primary_node=None should still return a valid selected_policy."""
    state = create_default_learner_state("s5")
    result = selector.select_policy(state, make_mapping(None), make_ctx())
    assert result.selected_policy in [
        "worked_example_oriented_explanation",
        "direct_explicit_explanation",
        "step_by_step_guidance",
        "guided_questioning",
    ]
    assert "no_primary_node" in result.selection_reasons


def test_normalize_equal_distribution_when_zero_total(selector):
    """All-zero shifted scores should yield equal 0.25 per policy."""
    raw = {
        "worked_example_oriented_explanation": 0.0,
        "direct_explicit_explanation": 0.0,
        "step_by_step_guidance": 0.0,
        "guided_questioning": 0.0,
    }
    normed = selector.normalize_policy_scores(raw)
    for v in normed.values():
        assert abs(v - 0.25) < 1e-9


def test_candidates_sorted_descending(selector):
    """candidate_policies must be in descending score order."""
    state = create_default_learner_state("s7")
    state.node_mastery["quadratic_function"] = 0.6
    result = selector.select_policy(state, make_mapping("quadratic_function"), make_ctx())
    scores = [ps.score for ps in result.candidate_policies]
    assert scores == sorted(scores, reverse=True)


def test_hint_used_before_boosts_worked_example_and_step_by_step(selector):
    """used_hint_before=True should increase both worked_example and step_by_step scores."""
    state = create_default_learner_state("s8")
    state.node_mastery["polynomial_operations"] = 0.5
    mapping = make_mapping("polynomial_operations")

    raw_no_hint, _ = selector.score_policies(state, mapping, make_ctx(used_hint_before=False))
    raw_hint, reasons = selector.score_policies(state, mapping, make_ctx(used_hint_before=True))

    assert raw_hint["step_by_step_guidance"] > raw_no_hint["step_by_step_guidance"]
    assert raw_hint["worked_example_oriented_explanation"] > raw_no_hint["worked_example_oriented_explanation"]
    assert "hint_used_before" in reasons
