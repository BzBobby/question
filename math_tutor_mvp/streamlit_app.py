import sys
import os

# Ensure the project root is on sys.path so `app` package resolves correctly
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

from app.agent_workflow import PlanningBasedTutorWorkflow
from app.learner_state import create_default_learner_state
from app.knowledge_graph import KNOWLEDGE_NODES
from app.schemas import InteractionContext, PerformanceEvent

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Math Tutor MVP Demo",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------
if "workflow" not in st.session_state:
    st.session_state["workflow"] = PlanningBasedTutorWorkflow()

if "learner_state" not in st.session_state:
    st.session_state["learner_state"] = create_default_learner_state("demo_student")

if "last_result" not in st.session_state:
    st.session_state["last_result"] = None

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("Math Tutor MVP Demo")
st.caption(
    "This is a research demo for a planning-based closed-loop "
    "multi-agent personalised tutoring system."
)
st.divider()

# ---------------------------------------------------------------------------
# Two-column layout
# ---------------------------------------------------------------------------
left, right = st.columns([1, 1.6], gap="large")

# ═══════════════════════════════════════════════════════════════════════════
# LEFT COLUMN — inputs & controls
# ═══════════════════════════════════════════════════════════════════════════
with left:
    st.subheader("Input")

    query_text = st.text_area(
        "Question text",
        value="已知一次函数 y = 2x + 3，求斜率和截距。",
        height=90,
    )

    st.markdown("**Interaction Context**")
    col_a, col_b = st.columns(2)
    with col_a:
        difficulty = st.selectbox(
            "Question difficulty",
            options=["easy", "medium", "hard"],
            index=1,
        )
        clarification_turns_ctx = st.number_input(
            "Clarification turns (context)",
            min_value=0,
            value=2,
            step=1,
        )
    with col_b:
        used_hint_before = st.checkbox("Used hint before", value=True)

    st.divider()

    # --- Preview ---
    if st.button("▶  Run Preview", use_container_width=True, type="primary"):
        ctx = InteractionContext(
            question_difficulty=difficulty,
            clarification_turns=int(clarification_turns_ctx),
            used_hint_before=used_hint_before,
        )
        result = st.session_state["workflow"].run_preview(
            query_text, st.session_state["learner_state"], ctx
        )
        st.session_state["last_result"] = result

    st.divider()

    # --- Closed-loop ---
    st.markdown("**Closed-loop: student performance**")
    col_c, col_d = st.columns(2)
    with col_c:
        correct = st.radio(
            "Answer correct?",
            options=["Correct", "Incorrect"],
            index=1,
            horizontal=True,
        )
        used_hint_event = st.checkbox("Used hint (this attempt)", value=True)
    with col_d:
        clarification_turns_event = st.number_input(
            "Clarification turns (event)",
            min_value=0,
            value=2,
            step=1,
        )

    if st.button("↻  Run Closed Loop", use_container_width=True):
        ctx = InteractionContext(
            question_difficulty=difficulty,
            clarification_turns=int(clarification_turns_ctx),
            used_hint_before=used_hint_before,
        )
        event = PerformanceEvent(
            correct=(correct == "Correct"),
            used_hint=used_hint_event,
            clarification_turns=int(clarification_turns_event),
        )
        result = st.session_state["workflow"].run_closed_loop(
            query_text, st.session_state["learner_state"], ctx, event
        )
        st.session_state["last_result"] = result
        if result.pipeline_result.updated_learner_state is not None:
            st.session_state["learner_state"] = (
                result.pipeline_result.updated_learner_state
            )

    st.divider()

    if st.button("🔄  Reset Learner State", use_container_width=True):
        st.session_state["learner_state"] = create_default_learner_state("demo_student")
        st.session_state["last_result"] = None
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# RIGHT COLUMN — results
# ═══════════════════════════════════════════════════════════════════════════
with right:
    last = st.session_state.get("last_result")

    # ── 1. Knowledge Mapping ──────────────────────────────────────────────
    st.subheader("Knowledge Mapping")
    if last:
        mr = last.pipeline_result.mapping_result
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Primary node", mr.primary_node or "—")
        with col2:
            st.metric("Mapping confidence", f"{mr.mapping_confidence:.2%}")

        if mr.matched_nodes:
            rows = [
                {
                    "node_id": m.node_id,
                    "score": f"{m.score:.4f}",
                    "evidence": ", ".join(m.evidence),
                }
                for m in mr.matched_nodes
            ]
            st.table(rows)
        else:
            st.info("No matched nodes.")
    else:
        st.info("Run preview or closed-loop to see results.")

    # ── 2. Policy Selection ───────────────────────────────────────────────
    st.subheader("Policy Selection")
    if last:
        pr = last.pipeline_result.policy_result
        col3, col4 = st.columns(2)
        with col3:
            st.metric("Selected policy", pr.selected_policy)
        with col4:
            st.metric("Policy confidence", f"{pr.policy_confidence:.2%}")

        st.caption("Selection reasons: " + "  |  ".join(pr.selection_reasons))

        cand_rows = [
            {"policy": ps.policy, "score": f"{ps.score:.4f}"}
            for ps in pr.candidate_policies
        ]
        st.table(cand_rows)
    else:
        st.info("No policy selected yet.")

    # ── 3. Generated Response ─────────────────────────────────────────────
    st.subheader("Generated Response")
    if last:
        gr = last.pipeline_result.generated_response
        with st.expander("Answer", expanded=True):
            st.write(gr.answer_text)
        with st.expander("Knowledge Summary", expanded=False):
            st.write(gr.knowledge_summary)
        with st.expander("Similar Question", expanded=False):
            st.write(gr.similar_question)
    else:
        st.info("No response generated yet.")

    # ── 4. Learner State ──────────────────────────────────────────────────
    st.subheader("Learner State")
    ls = st.session_state["learner_state"]
    for node_id, node_zh in KNOWLEDGE_NODES.items():
        mastery = ls.node_mastery.get(node_id, 0.0)
        label = f"{node_zh}  ({node_id})"
        col_label, col_bar = st.columns([1.6, 2])
        with col_label:
            st.write(label)
        with col_bar:
            st.progress(mastery, text=f"{mastery:.0%}")

    col_wn, col_pg = st.columns(2)
    with col_wn:
        weak = ls.weak_nodes
        if weak:
            st.warning("Weak nodes: " + ", ".join(weak))
        else:
            st.success("No weak nodes")
    with col_pg:
        gaps = ls.prerequisite_gaps
        if gaps:
            st.error("Prereq gaps: " + ", ".join(gaps))
        else:
            st.success("No prerequisite gaps")

    # ── 5. Workflow Trace ─────────────────────────────────────────────────
    st.subheader("Workflow Trace")
    if last:
        trace = last.workflow_trace
        st.markdown(
            "**Executed steps:** "
            + "  →  ".join(f"`{s}`" for s in trace.executed_steps)
        )
        st.markdown("**Messages:**")
        for i, msg in enumerate(trace.messages, 1):
            with st.expander(
                f"{i}. `{msg.message_type}`  ({msg.sender} → {msg.receiver})",
                expanded=False,
            ):
                st.json(msg.payload)
    else:
        st.info("Workflow trace will appear here after running.")
