"""LLM-as-judge: grades a reply against the case's rubric and the actual
tool results, so a reply that sounds right but states facts the tools
never returned still fails."""

import json

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field


PASSING_SCORE = 4

_INSTRUCTIONS = """You grade a shuttle-booking assistant's final reply.

Score 1-5:
5 = fully meets the rubric, every fact is supported by the tool results
4 = meets the rubric with minor wording issues
3 = partly meets the rubric, or vague where it should be specific
2 = misses the main point of the rubric
1 = wrong, or states facts not supported by the tool results (hallucination)

A reply that contradicts or goes beyond the tool results scores at most 2,
even if it sounds plausible. Suggesting a sensible next step (another day,
another shuttle) is fine as long as it doesn't assert facts the tools didn't
return. Times may be written in any format."""


class Verdict(BaseModel):
    score: int = Field(ge=1, le=5)
    reason: str = Field(description="One sentence explaining the score.")

    @property
    def passed(self) -> bool:
        return self.score >= PASSING_SCORE


def judge(
    model: BaseChatModel,
    turns: list[str],
    reply: str,
    tool_results: list[tuple[str, str]],
    rubric: str,
) -> Verdict:
    evidence = "\n".join(
        f"- {name}: {result[:1200]}" for name, result in tool_results
    ) or "(no tools were called)"

    prompt = f"""{_INSTRUCTIONS}

User messages, in order:
{json.dumps(turns, ensure_ascii=False)}

Tool results the assistant saw:
{evidence}

Final reply:
{reply}

Rubric for the final reply:
{rubric}"""

    return model.with_structured_output(Verdict).invoke(prompt)
