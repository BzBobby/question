"""
Demo: run from the math_tutor_mvp/ directory with:
    python -m app.demo_mvp_pipeline
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.learner_state import create_default_learner_state
from app.mvp_pipeline import MVPPipeline
from app.schemas import InteractionContext, PerformanceEvent

pipeline = MVPPipeline()
query_text = "已知一次函数 y = 2x + 3，求斜率和截距。"

ctx = InteractionContext(
    question_difficulty="hard",
    clarification_turns=2,
    used_hint_before=True,
)

# ─── Part A: preview mode ────────────────────────────────────────────────────
print("=" * 60)
print("Part A: preview mode")
print("=" * 60)

state_a = create_default_learner_state("student_preview")
result_a = pipeline.run_preview(query_text, state_a, ctx)

print(f"primary_node     : {result_a.mapping_result.primary_node}")
print(f"selected_policy  : {result_a.policy_result.selected_policy}")
print(f"\n[answer_text]\n{result_a.generated_response.answer_text}")
print(f"\n[knowledge_summary]\n{result_a.generated_response.knowledge_summary}")
print(f"\n[similar_question]\n{result_a.generated_response.similar_question}")
print(f"\nmastery_update_result: {result_a.mastery_update_result}")   # None

# ─── Part B: closed-loop mode ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Part B: closed-loop mode")
print("=" * 60)

state_b = create_default_learner_state("student_loop")
event = PerformanceEvent(correct=False, used_hint=True, clarification_turns=2)
result_b = pipeline.run_closed_loop(query_text, state_b, ctx, event)

node = result_b.mapping_result.primary_node
updates = result_b.mastery_update_result.updated_nodes
if updates:
    nu = updates[0]
    print(f"node             : {nu.node_id}")
    print(f"mastery update   : {nu.old_mastery:.4f} → {nu.new_mastery:.4f}  (delta={nu.delta:+.4f})")
print(f"weak_nodes       : {result_b.updated_learner_state.weak_nodes}")
print(f"prerequisite_gaps: {result_b.updated_learner_state.prerequisite_gaps}")
