import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from app.knowledge_mapper import KnowledgeMapper
from app.schemas import MappingInput


@pytest.fixture
def mapper():
    return KnowledgeMapper()


def map_primary(mapper: KnowledgeMapper, text: str) -> str | None:
    result = mapper.map_text_to_nodes(MappingInput(text=text))
    return result.primary_node


def test_linear_equation(mapper):
    assert map_primary(mapper, "解方程 2x + 3 = 11") == "linear_equation_one_variable"


def test_linear_function(mapper):
    assert map_primary(mapper, "已知一次函数 y = 2x + 1，求斜率和截距") == "linear_function"


def test_factorization(mapper):
    assert map_primary(mapper, "把 x^2 - 9 进行因式分解") == "factorization"


def test_coordinate_system(mapper):
    assert (
        map_primary(mapper, "点A在第二象限，它的横坐标和纵坐标分别满足什么条件？")
        == "coordinate_system"
    )


def test_quadratic_function(mapper):
    assert (
        map_primary(mapper, "求抛物线 y = x^2 - 4x + 3 的顶点坐标和对称轴")
        == "quadratic_function"
    )


def test_no_match_returns_none(mapper):
    result = mapper.map_text_to_nodes(MappingInput(text="今天天气很好"))
    assert result.primary_node is None
    assert result.mapping_confidence == 0.0
    assert result.matched_nodes == []


def test_prerequisite_nodes_linear_function(mapper):
    result = mapper.map_text_to_nodes(MappingInput(text="已知一次函数 y = 2x + 1，求斜率和截距"))
    assert set(result.prerequisite_nodes) == {"linear_equation_one_variable", "coordinate_system"}


def test_top_k_respected(mapper):
    result = mapper.map_text_to_nodes(
        MappingInput(text="求抛物线 y = x^2 - 4x + 3 的顶点坐标和对称轴", top_k=2)
    )
    assert len(result.matched_nodes) <= 2


def test_polynomial_operations(mapper):
    assert map_primary(mapper, "合并同类项：3x + 2y - x + 5y") == "polynomial_operations"
