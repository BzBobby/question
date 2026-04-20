from typing import Optional
from .schemas import MappingInput, MappingResult, NodeMatch
from .knowledge_graph import KNOWLEDGE_NODES, PREREQUISITE_GRAPH
from .keyword_rules import KEYWORD_RULES
from .text_utils import normalize_text


class KnowledgeMapper:
    def __init__(self) -> None:
        self.nodes = KNOWLEDGE_NODES
        self.prereqs = PREREQUISITE_GRAPH
        self.rules = KEYWORD_RULES

    def score_node(self, text: str, node_id: str) -> tuple[float, list[str]]:
        """Return (raw_score, evidence_list) for one node."""
        keywords = self.rules.get(node_id, [])
        score = 0.0
        evidence: list[str] = []
        for keyword, weight in keywords:
            if normalize_text(keyword) in text:
                score += weight
                evidence.append(f"{keyword}(+{weight})")
        return score, evidence

    def normalize_scores(self, raw_scores: dict[str, float]) -> dict[str, float]:
        """Normalize to [0, 1] by dividing by the total sum."""
        total = sum(raw_scores.values())
        if total == 0:
            return {k: 0.0 for k in raw_scores}
        return {k: v / total for k, v in raw_scores.items()}

    def get_prerequisites(self, node_id: str) -> list[str]:
        """Return the direct prerequisite node ids for a given node."""
        return self.prereqs.get(node_id, [])

    def map_text_to_nodes(self, mapping_input: MappingInput) -> MappingResult:
        text = normalize_text(mapping_input.text)

        # Score every node
        raw_scores: dict[str, float] = {}
        evidence_map: dict[str, list[str]] = {}
        for node_id in self.nodes:
            score, evidence = self.score_node(text, node_id)
            raw_scores[node_id] = score
            evidence_map[node_id] = evidence

        norm_scores = self.normalize_scores(raw_scores)

        # Build NodeMatch list for nodes with score > 0, sorted descending
        matches: list[NodeMatch] = [
            NodeMatch(
                node_id=nid,
                node_name_zh=self.nodes[nid],
                score=round(norm_scores[nid], 4),
                evidence=evidence_map[nid],
            )
            for nid in self.nodes
            if norm_scores[nid] > 0
        ]
        matches.sort(key=lambda m: m.score, reverse=True)
        top_matches = matches[: mapping_input.top_k]

        if top_matches:
            primary_node: Optional[str] = top_matches[0].node_id
            prerequisite_nodes = self.get_prerequisites(primary_node)
            mapping_confidence = top_matches[0].score
        else:
            primary_node = None
            prerequisite_nodes = []
            mapping_confidence = 0.0

        return MappingResult(
            input_text=mapping_input.text,
            source_type=mapping_input.source_type,
            matched_nodes=top_matches,
            primary_node=primary_node,
            prerequisite_nodes=prerequisite_nodes,
            mapping_confidence=mapping_confidence,
        )
