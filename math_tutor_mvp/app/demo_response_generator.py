"""
Demo: run from the math_tutor_mvp/ directory with:
    python -m app.demo_response_generator
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.learner_state import create_default_learner_state
from app.response_generator import ResponseGenerator
from app.schemas import MappingResult, NodeMatch, PolicyScore, PolicySelectionResult

query_text = "已知一次函数 y = 2x + 3，求斜率和截距。"

# Learner state: linear_function mastery = 0.35
state = create_default_learner_state("student_demo")
state.node_mastery["linear_function"] = 0.35

# MappingResult
mapping = MappingResult(
    input_text=query_text,
    source_type="question",
    matched_nodes=[
        NodeMatch(
            node_id="linear_function",
            node_name_zh="一次函数",
            score=1.0,
            evidence=["一次函数(+4.0)", "斜率(+3.0)", "截距(+3.0)"],
        )
    ],
    primary_node="linear_function",
    prerequisite_nodes=["linear_equation_one_variable", "coordinate_system"],
    mapping_confidence=1.0,
)

# Policy result
policy_result = PolicySelectionResult(
    selected_policy="step_by_step_guidance",
    policy_confidence=0.82,
    candidate_policies=[
        PolicyScore(policy="step_by_step_guidance", score=0.82),
        PolicyScore(policy="worked_example_oriented_explanation", score=0.12),
        PolicyScore(policy="guided_questioning", score=0.04),
        PolicyScore(policy="direct_explicit_explanation", score=0.02),
    ],
    selection_reasons=["primary_mastery_low", "hint_used_before"],
)

generator = ResponseGenerator()
response = generator.generate(query_text, mapping, state, policy_result)

print("=== Generated Response ===\n")
print("[answer_text]")
print(response.answer_text)
print("\n[knowledge_summary]")
print(response.knowledge_summary)
print("\n[similar_question]")
print(response.similar_question)
print("\n[response_metadata]")
print(f"  primary_node      : {response.response_metadata.primary_node}")
print(f"  selected_policy   : {response.response_metadata.selected_policy}")
print(f"  policy_confidence : {response.response_metadata.policy_confidence}")
