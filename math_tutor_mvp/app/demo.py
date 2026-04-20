"""
Demo: run from the math_tutor_mvp/ directory with:
    python -m app.demo
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.knowledge_mapper import KnowledgeMapper
from app.schemas import MappingInput

mapper = KnowledgeMapper()

examples = [
    ("解方程 2x + 3 = 11", "question"),
    ("已知一次函数 y = 2x + 1，求斜率和截距", "question"),
    ("把 x^2 - 9 进行因式分解", "question"),
    ("点A在第二象限，它的横坐标和纵坐标分别满足什么条件？", "question"),
    ("求抛物线 y = x^2 - 4x + 3 的顶点坐标和对称轴", "question"),
    ("合并同类项：3x + 2y - x + 5y", "question"),
]

for text, src in examples:
    result = mapper.map_text_to_nodes(MappingInput(text=text, source_type=src))
    print(f"\n{'='*60}")
    print(f"Input : {result.input_text}")
    print(f"Primary: {result.primary_node}  (confidence={result.mapping_confidence:.4f})")
    print(f"Prerequisites: {result.prerequisite_nodes}")
    print("Matched nodes:")
    for m in result.matched_nodes:
        print(f"  [{m.score:.4f}] {m.node_id} ({m.node_name_zh})")
        print(f"           evidence: {', '.join(m.evidence)}")
