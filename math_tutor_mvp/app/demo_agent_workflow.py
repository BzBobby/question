"""
Demo: run from the math_tutor_mvp/ directory with:
    python -m app.demo_agent_workflow
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.learner_state import create_default_learner_state
from app.agent_workflow import PlanningBasedTutorWorkflow
from app.schemas import InteractionContext, PerformanceEvent

workflow = PlanningBasedTutorWorkflow()
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
result_a = workflow.run_preview(query_text, state_a, ctx)

pr = result_a.pipeline_result
tr = result_a.workflow_trace

print(f"executed_steps  : {tr.executed_steps}")
print(f"selected_policy : {pr.policy_result.selected_policy}")
print(f"\n[answer_text]\n{pr.generated_response.answer_text}")
print(f"\n[knowledge_summary]\n{pr.generated_response.knowledge_summary}")
print(f"\n[similar_question]\n{pr.generated_response.similar_question}")
print(f"\ntrace message_types: {[m.message_type for m in tr.messages]}")

# ─── Part B: closed-loop mode ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Part B: closed-loop mode")
print("=" * 60)

state_b = create_default_learner_state("student_loop")
event = PerformanceEvent(correct=False, used_hint=True, clarification_turns=2)
result_b = workflow.run_closed_loop(query_text, state_b, ctx, event)

pr_b = result_b.pipeline_result
tr_b = result_b.workflow_trace

print(f"executed_steps  : {tr_b.executed_steps}")
if pr_b.mastery_update_result and pr_b.mastery_update_result.updated_nodes:
    nu = pr_b.mastery_update_result.updated_nodes[0]
    print(f"mastery update  : {nu.node_id}  {nu.old_mastery:.4f} -> {nu.new_mastery:.4f}  (delta={nu.delta:+.4f})")
print(f"weak_nodes      : {pr_b.updated_learner_state.weak_nodes}")
print(f"prereq_gaps     : {pr_b.updated_learner_state.prerequisite_gaps}")
print(f"\ntrace message_types: {[m.message_type for m in tr_b.messages]}")
