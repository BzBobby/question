KNOWLEDGE_NODES: dict[str, str] = {
    "polynomial_operations": "整式运算",
    "factorization": "因式分解",
    "linear_equation_one_variable": "一元一次方程",
    "coordinate_system": "平面直角坐标系",
    "linear_function": "一次函数",
    "quadratic_function": "二次函数",
}

# key -> list of prerequisite node ids
PREREQUISITE_GRAPH: dict[str, list[str]] = {
    "polynomial_operations": [],
    "factorization": ["polynomial_operations"],
    "linear_equation_one_variable": ["polynomial_operations"],
    "coordinate_system": [],
    "linear_function": ["linear_equation_one_variable", "coordinate_system"],
    "quadratic_function": ["factorization", "coordinate_system", "linear_function"],
}
