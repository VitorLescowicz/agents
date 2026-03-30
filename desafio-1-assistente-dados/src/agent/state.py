"""LangGraph agent state definition."""

from typing import Any, Optional, TypedDict


class AgentState(TypedDict):
    """State that flows through the LangGraph state machine."""

    question: str
    schema_info: str
    analysis_summary: str
    step_questions: list[str]
    current_step_index: int
    current_step_question: str
    step_summaries: list[str]
    trace: list[dict[str, Any]]
    executed_queries: list[str]
    sql_query: str
    sql_result: Optional[tuple]
    error: Optional[str]
    retry_count: int
    answer: str
    viz_type: str
    columns: list[str]
    rows: list[tuple]
