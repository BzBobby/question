import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from app.learner_state import create_default_learner_state
from app.response_generator import ResponseGenerator
from app.schemas import MappingResult, NodeMatch, PolicyScore, PolicySelectionResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mapping(primary_node):
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
        matched_nodes=[NodeMatch(node_id=primary_node, node_name_zh="", score=1.0, evidence=[])],
        primary_node=primary_node,
        prerequisite_nodes=[],
        mapping_confidence=1.0,
    )


def make_policy(selected, confidence=0.8):
    return PolicySelectionResult(
        selected_policy=selected,
        policy_confidence=confidence,
        candidate_policies=[PolicyScore(policy=selected, score=confidence)],
        selection_reasons=[],
    )


@pytest.fixture
def generator():
    return ResponseGenerator()


@pytest.fixture
def default_state():
    return create_default_learner_state("s_test")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_direct_explicit_contains_key_phrase(generator, default_state):
    result = generator.generate(
        "test", make_mapping("linear_function"), default_state,
        make_policy("direct_explicit_explanation"),
    )
    assert "这题的关键是" in result.answer_text


def test_step_by_step_contains_key_phrase(generator, default_state):
    result = generator.generate(
        "test", make_mapping("linear_equation_one_variable"), default_state,
        make_policy("step_by_step_guidance"),
    )
    assert "第一步" in result.answer_text


def test_worked_example_contains_key_phrase(generator, default_state):
    result = generator.generate(
        "test", make_mapping("factorization"), default_state,
        make_policy("worked_example_oriented_explanation"),
    )
    assert "我先示范一遍" in result.answer_text


def test_guided_questioning_contains_key_phrase(generator, default_state):
    result = generator.generate(
        "test", make_mapping("coordinate_system"), default_state,
        make_policy("guided_questioning"),
    )
    assert "你先想一想" in result.answer_text


def test_knowledge_summary_linear_function_nonempty(generator):
    mapping = make_mapping("linear_function")
    summary = generator.generate_knowledge_summary(mapping)
    assert isinstance(summary, str) and len(summary) > 0


def test_similar_question_quadratic_function_nonempty(generator):
    mapping = make_mapping("quadratic_function")
    q = generator.generate_similar_question(mapping)
    assert isinstance(q, str) and len(q) > 0


def test_fallback_when_primary_node_is_none(generator, default_state):
    result = generator.generate(
        "test", make_mapping(None), default_state,
        make_policy("direct_explicit_explanation"),
    )
    assert result.answer_text != ""
    assert result.knowledge_summary != ""
    assert result.similar_question != ""
    assert result.response_metadata.primary_node is None


def test_metadata_fields_written_correctly(generator, default_state):
    policy = make_policy("guided_questioning", confidence=0.65)
    result = generator.generate(
        "test", make_mapping("polynomial_operations"), default_state, policy
    )
    assert result.response_metadata.selected_policy == "guided_questioning"
    assert abs(result.response_metadata.policy_confidence - 0.65) < 1e-9
    assert result.response_metadata.primary_node == "polynomial_operations"
