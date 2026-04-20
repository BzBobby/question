import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from app.learner_state import create_default_learner_state
from app.mastery_updater import MasteryUpdater
from app.schemas import MappingResult, NodeMatch, PerformanceEvent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mapping(primary_node, confidence=0.8, prereqs=None):
    return MappingResult(
        input_text="test",
        source_type="question",
        matched_nodes=[
            NodeMatch(
                node_id=primary_node,
                node_name_zh="",
                score=confidence,
                evidence=[],
            )
        ] if primary_node else [],
        primary_node=primary_node,
        prerequisite_nodes=prereqs or [],
        mapping_confidence=confidence,
    )


def make_event(correct, used_hint=False, clarification_turns=0):
    return PerformanceEvent(
        correct=correct,
        used_hint=used_hint,
        clarification_turns=clarification_turns,
    )


@pytest.fixture
def updater():
    return MasteryUpdater()


@pytest.fixture
def default_state():
    return create_default_learner_state("s001")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_correct_no_hint_raises_mastery(updater, default_state):
    """Correct answer without hint should increase mastery."""
    mapping = make_mapping("linear_equation_one_variable")
    event = make_event(correct=True, used_hint=False)
    result = updater.update(default_state, mapping, event)
    nu = result.updated_nodes[0]
    assert nu.delta > 0
    assert nu.new_mastery > nu.old_mastery


def test_incorrect_with_hint_lowers_mastery(updater, default_state):
    """Incorrect answer with hint should decrease mastery."""
    mapping = make_mapping("linear_equation_one_variable")
    event = make_event(correct=False, used_hint=True)
    result = updater.update(default_state, mapping, event)
    nu = result.updated_nodes[0]
    assert nu.delta < 0
    assert nu.new_mastery < nu.old_mastery


def test_mastery_capped_at_1(updater):
    """Mastery should never exceed 1.0."""
    state = create_default_learner_state("s002")
    state.node_mastery["factorization"] = 0.99
    mapping = make_mapping("factorization", confidence=1.0)
    event = make_event(correct=True)
    result = updater.update(state, mapping, event)
    assert result.updated_nodes[0].new_mastery <= 1.0


def test_mastery_floored_at_0(updater):
    """Mastery should never go below 0.0."""
    state = create_default_learner_state("s003")
    state.node_mastery["factorization"] = 0.01
    mapping = make_mapping("factorization", confidence=1.0)
    event = make_event(correct=False, used_hint=True, clarification_turns=4)
    result = updater.update(state, mapping, event)
    assert result.updated_nodes[0].new_mastery >= 0.0


def test_prerequisite_gap_detected_on_incorrect(updater):
    """When linear_function is answered incorrectly and a prerequisite mastery < 0.45,
    that prerequisite should appear in prerequisite_gaps."""
    state = create_default_learner_state("s004")
    # Drive one prerequisite below threshold
    state.node_mastery["linear_equation_one_variable"] = 0.3
    mapping = make_mapping(
        "linear_function",
        prereqs=["linear_equation_one_variable", "coordinate_system"],
    )
    event = make_event(correct=False)
    result = updater.update(state, mapping, event)
    assert "linear_equation_one_variable" in result.prerequisite_gaps


def test_no_update_when_primary_node_is_none(updater, default_state):
    """If mapping has no primary_node, no mastery values should change."""
    original_mastery = dict(default_state.node_mastery)
    mapping = make_mapping(None, confidence=0.0)
    event = make_event(correct=True)
    result = updater.update(default_state, mapping, event)
    assert result.updated_nodes == []
    assert result.updated_learner_state.node_mastery == original_mastery


def test_weak_nodes_refreshed_after_update(updater, default_state):
    """weak_nodes should reflect nodes with mastery < 0.5 after update."""
    default_state.node_mastery["coordinate_system"] = 0.4
    mapping = make_mapping("factorization")
    event = make_event(correct=True)
    result = updater.update(default_state, mapping, event)
    assert "coordinate_system" in result.updated_learner_state.weak_nodes


def test_clarification_penalty_applied(updater, default_state):
    """Extra clarification turns should make delta more negative."""
    mapping = make_mapping("linear_equation_one_variable", confidence=1.0)

    event_no_clar = make_event(correct=False, used_hint=True, clarification_turns=0)
    event_with_clar = make_event(correct=False, used_hint=True, clarification_turns=4)

    state2 = create_default_learner_state("s005")
    r1 = updater.update(default_state, mapping, event_no_clar)
    r2 = updater.update(state2, mapping, event_with_clar)

    assert r2.updated_nodes[0].delta < r1.updated_nodes[0].delta


def test_reason_labels(updater, default_state):
    """Reason string should reflect hint/correct combination."""
    cases = [
        (True,  False, "correct_without_hint"),
        (True,  True,  "correct_with_hint"),
        (False, False, "incorrect_without_hint"),
        (False, True,  "incorrect_with_hint"),
    ]
    for correct, used_hint, expected_reason in cases:
        state = create_default_learner_state("s_reason")
        mapping = make_mapping("coordinate_system")
        event = make_event(correct=correct, used_hint=used_hint)
        result = updater.update(state, mapping, event)
        assert result.updated_nodes[0].reason == expected_reason
