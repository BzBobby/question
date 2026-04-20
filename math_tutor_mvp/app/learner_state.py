from .schemas import LearnerState
from .knowledge_graph import KNOWLEDGE_NODES


def create_default_learner_state(student_id: str) -> LearnerState:
    """Initialize a learner state with 0.5 mastery for every knowledge node."""
    return LearnerState(
        student_id=student_id,
        node_mastery={node_id: 0.5 for node_id in KNOWLEDGE_NODES},
    )
