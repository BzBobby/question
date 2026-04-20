"""
Demo: run from the math_tutor_mvp/ directory with:
    python -m app.demo_policy_selector
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.learner_state import create_default_learner_state
from app.policy_selector import PolicySelector
from app.schemas import InteractionContext, MappingResult, NodeMatch

# Build learner state: primary mastery = 0.35, with a prerequisite gap
state = create_default_learner_state("student_demo")
state.node_mastery["linear_function"] = 0.35
state.prerequisite_gaps = ["linear_equation_one_variable"]

# MappingResult pointing at linear_function
mapping = MappingResult(
    input_text="已知一次函数 y = 2x + 1，求斜率和截距",
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

# Interaction context: hard question, 2 clarification turns, hint used before
ctx = InteractionContext(
    question_difficulty="hard",
    clarification_turns=2,
    used_hint_before=True,
)

selector = PolicySelector()
result = selector.select_policy(state, mapping, ctx)

print("=== Policy Selection Result ===")
print(f"selected_policy   : {result.selected_policy}")
print(f"policy_confidence : {result.policy_confidence:.4f}")
print("\ncandidate_policies (ranked):")
for ps in result.candidate_policies:
    marker = " <-- selected" if ps.policy == result.selected_policy else ""
    print(f"  {ps.score:.4f}  {ps.policy}{marker}")
print(f"\nselection_reasons : {result.selection_reasons}")
