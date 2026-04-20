"""
Demo: run from the math_tutor_mvp/ directory with:
    python -m app.demo_mastery_update
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.learner_state import create_default_learner_state
from app.mastery_updater import MasteryUpdater
from app.schemas import MappingResult, PerformanceEvent, NodeMatch

# 1. Create default learner state
state = create_default_learner_state("student_001")
print("=== Initial mastery ===")
for nid, m in state.node_mastery.items():
    print(f"  {nid}: {m}")

# 2. Construct a MappingResult (as if produced by KnowledgeMapper)
mapping = MappingResult(
    input_text="解方程 2x + 3 = 11",
    source_type="question",
    matched_nodes=[
        NodeMatch(
            node_id="linear_equation_one_variable",
            node_name_zh="一元一次方程",
            score=1.0,
            evidence=["解方程(+3.0)", "方程(+2.0)"],
        )
    ],
    primary_node="linear_equation_one_variable",
    prerequisite_nodes=["polynomial_operations"],
    mapping_confidence=0.8,
)

# 3. Incorrect answer with hint and 2 clarification turns
event = PerformanceEvent(
    correct=False,
    used_hint=True,
    clarification_turns=2,
)

# 4. Run updater
updater = MasteryUpdater()
result = updater.update(state, mapping, event)

# 5. Print results
print("\n=== Mastery update result ===")
for nu in result.updated_nodes:
    print(
        f"  {nu.node_id}: {nu.old_mastery:.4f} -> {nu.new_mastery:.4f}  "
        f"(delta={nu.delta:+.4f}, reason={nu.reason})"
    )

print(f"\nweak_nodes       : {result.updated_learner_state.weak_nodes}")
print(f"prerequisite_gaps: {result.prerequisite_gaps}")
