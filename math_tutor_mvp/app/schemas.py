from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MappingInput:
    text: str
    source_type: str = "question"
    top_k: int = 3


@dataclass
class NodeMatch:
    node_id: str
    node_name_zh: str
    score: float
    evidence: List[str]


@dataclass
class MappingResult:
    input_text: str
    source_type: str
    matched_nodes: List[NodeMatch]
    primary_node: Optional[str]
    prerequisite_nodes: List[str]
    mapping_confidence: float


# ---------------------------------------------------------------------------
# Step 2: mastery update schemas
# ---------------------------------------------------------------------------

@dataclass
class PerformanceEvent:
    correct: bool
    attempt_count: int = 1
    used_hint: bool = False
    clarification_turns: int = 0
    response_latency_sec: float = 0.0
    source_type: str = "question"


@dataclass
class LearnerState:
    student_id: str
    node_mastery: Dict[str, float]
    weak_nodes: List[str] = field(default_factory=list)
    prerequisite_gaps: List[str] = field(default_factory=list)
    error_patterns: Dict[str, List[str]] = field(default_factory=dict)
    strategy_evidence: Dict[str, int] = field(default_factory=dict)


@dataclass
class NodeUpdate:
    node_id: str
    old_mastery: float
    new_mastery: float
    delta: float
    reason: str


@dataclass
class MasteryUpdateResult:
    updated_learner_state: LearnerState
    updated_nodes: List[NodeUpdate]
    prerequisite_gaps: List[str]


# ---------------------------------------------------------------------------
# Step 3: policy selector schemas
# ---------------------------------------------------------------------------

@dataclass
class InteractionContext:
    question_difficulty: str = "medium"
    clarification_turns: int = 0
    used_hint_before: bool = False
    source_type: str = "question"


@dataclass
class PolicyScore:
    policy: str
    score: float


@dataclass
class PolicySelectionResult:
    selected_policy: str
    policy_confidence: float
    candidate_policies: List[PolicyScore]
    selection_reasons: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Step 4: response generator schemas
# ---------------------------------------------------------------------------

@dataclass
class ResponseMetadata:
    primary_node: Optional[str]
    selected_policy: str
    policy_confidence: float


@dataclass
class GeneratedResponse:
    answer_text: str
    knowledge_summary: str
    similar_question: str
    response_metadata: ResponseMetadata


# ---------------------------------------------------------------------------
# Step 5: pipeline schema
# ---------------------------------------------------------------------------

@dataclass
class PipelineResult:
    mapping_result: MappingResult
    policy_result: PolicySelectionResult
    generated_response: GeneratedResponse
    mastery_update_result: Optional[MasteryUpdateResult] = None
    updated_learner_state: Optional[LearnerState] = None


# ---------------------------------------------------------------------------
# Step 6: multi-agent workflow schemas
# ---------------------------------------------------------------------------

@dataclass
class AgentMessage:
    sender: str
    receiver: str
    message_type: str
    payload: dict


@dataclass
class WorkflowTrace:
    executed_steps: List[str]
    messages: List[AgentMessage]
    final_status: str


@dataclass
class AgentWorkflowResult:
    pipeline_result: PipelineResult
    workflow_trace: WorkflowTrace
