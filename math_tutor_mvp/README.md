# Math Tutor MVP — Knowledge Mapper

Rule-based + keyword-weighted knowledge mapper for a junior high school math AI tutoring system.

## Project Structure

```
math_tutor_mvp/
├── app/
│   ├── __init__.py
│   ├── schemas.py          # MappingInput / NodeMatch / MappingResult
│   ├── knowledge_graph.py  # Node registry & prerequisite graph
│   ├── keyword_rules.py    # Keyword-weight rules per node
│   ├── text_utils.py       # normalize_text()
│   ├── knowledge_mapper.py # KnowledgeMapper class
│   └── demo.py             # Quick demo script
└── tests/
    └── test_knowledge_mapper.py
```

## Knowledge Nodes

| ID | Chinese Name |
|----|-------------|
| `polynomial_operations` | 整式运算 |
| `factorization` | 因式分解 |
| `linear_equation_one_variable` | 一元一次方程 |
| `coordinate_system` | 平面直角坐标系 |
| `linear_function` | 一次函数 |
| `quadratic_function` | 二次函数 |

## Install & Run

```bash
pip install -r requirements.txt

# Run demo (from math_tutor_mvp/ directory)
python -m app.demo

# Run tests
pytest tests/
```

## Extending to Mastery Update

`MappingResult` surfaces `primary_node`, `prerequisite_nodes`, and `mapping_confidence`.
Feed these directly into a mastery-update module:

```python
mastery_update(
    student_id=...,
    node_id=result.primary_node,
    correct=True/False,
    confidence=result.mapping_confidence,
)
```

To add new knowledge nodes:
1. Add the node id/name to `knowledge_graph.py`.
2. Add its prerequisites to `PREREQUISITE_GRAPH`.
3. Add keyword rules to `keyword_rules.py`.
