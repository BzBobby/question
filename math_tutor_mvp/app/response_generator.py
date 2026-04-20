from .schemas import (
    GeneratedResponse,
    LearnerState,
    MappingResult,
    PolicySelectionResult,
    ResponseMetadata,
)
from .response_templates import (
    FALLBACK_SIMILAR_QUESTION,
    FALLBACK_SUMMARY,
    KNOWLEDGE_SUMMARIES,
    SIMILAR_QUESTIONS,
)

# ---------------------------------------------------------------------------
# Per-policy answer builders
# (Each returns a string given the topic name and query text.)
# ---------------------------------------------------------------------------

_NODE_NAME = {
    "polynomial_operations": "整式运算",
    "factorization": "因式分解",
    "linear_equation_one_variable": "一元一次方程",
    "coordinate_system": "平面直角坐标系",
    "linear_function": "一次函数",
    "quadratic_function": "二次函数",
}


def _answer_direct(node: str, query: str) -> str:
    topic = _NODE_NAME.get(node, node)
    return (
        f"这题的关键是掌握【{topic}】的核心方法。"
        f"根据题目条件，直接套用对应公式或定义即可得到答案。"
        f"解题时注意符号和单位，验算结果是否合理。"
    )


def _answer_step_by_step(node: str, query: str) -> str:
    topic = _NODE_NAME.get(node, node)
    return (
        f"我们来一步一步解决这道关于【{topic}】的题目。\n"
        f"第一步：仔细读题，找出题目中所有已知条件和问题目标。\n"
        f"第二步：回忆【{topic}】的相关定义、公式或解题步骤。\n"
        f"第三步：把已知条件代入公式或方法，逐步推导。\n"
        f"第四步：写出完整解题过程，注意每步的依据。\n"
        f"第五步：代入验算，确认答案正确。"
    )


def _answer_worked_example(node: str, query: str) -> str:
    topic = _NODE_NAME.get(node, node)
    return (
        f"我先示范一遍【{topic}】的解题思路，你再仿照这个思路自己做。\n"
        f"示范题的关键步骤如下：\n"
        f"  ① 确认题目类型，判断用哪种方法。\n"
        f"  ② 按照标准步骤逐步展开，不跳步。\n"
        f"  ③ 写出关键中间步骤，方便检查。\n"
        f"  ④ 最后写出结论，并做验算。\n"
        f"现在请你按照同样的思路解答你的题目，有问题随时告诉我。"
    )


def _answer_guided_questioning(node: str, query: str) -> str:
    topic = _NODE_NAME.get(node, node)
    return (
        f"你先想一想，这道题属于哪种类型？\n"
        f"关于【{topic}】，你还记得最核心的定义或公式是什么吗？\n"
        f"题目里给了哪些已知条件，你打算先从哪一步入手？\n"
        f"不急，先把你的思路说出来，我们一起分析。"
    )


_POLICY_BUILDERS = {
    "direct_explicit_explanation": _answer_direct,
    "step_by_step_guidance": _answer_step_by_step,
    "worked_example_oriented_explanation": _answer_worked_example,
    "guided_questioning": _answer_guided_questioning,
}

_FALLBACK_ANSWER = (
    "我先帮你确认一下题目类型和已知条件，再来讨论解法。"
    "你能告诉我这道题让你求什么，已知了什么吗？"
)


# ---------------------------------------------------------------------------
# ResponseGenerator
# ---------------------------------------------------------------------------

class ResponseGenerator:

    def generate_answer_text(
        self,
        query_text: str,
        mapping_result: MappingResult,
        learner_state: LearnerState,
        policy_result: PolicySelectionResult,
    ) -> str:
        node = mapping_result.primary_node
        if node is None:
            return _FALLBACK_ANSWER
        builder = _POLICY_BUILDERS.get(policy_result.selected_policy, _answer_direct)
        return builder(node, query_text)

    def generate_knowledge_summary(self, mapping_result: MappingResult) -> str:
        node = mapping_result.primary_node
        if node is None:
            return FALLBACK_SUMMARY
        return KNOWLEDGE_SUMMARIES.get(node, FALLBACK_SUMMARY)

    def generate_similar_question(self, mapping_result: MappingResult) -> str:
        node = mapping_result.primary_node
        if node is None:
            return FALLBACK_SIMILAR_QUESTION
        return SIMILAR_QUESTIONS.get(node, FALLBACK_SIMILAR_QUESTION)

    def generate(
        self,
        query_text: str,
        mapping_result: MappingResult,
        learner_state: LearnerState,
        policy_result: PolicySelectionResult,
    ) -> GeneratedResponse:
        return GeneratedResponse(
            answer_text=self.generate_answer_text(
                query_text, mapping_result, learner_state, policy_result
            ),
            knowledge_summary=self.generate_knowledge_summary(mapping_result),
            similar_question=self.generate_similar_question(mapping_result),
            response_metadata=ResponseMetadata(
                primary_node=mapping_result.primary_node,
                selected_policy=policy_result.selected_policy,
                policy_confidence=policy_result.policy_confidence,
            ),
        )
