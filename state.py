from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """Shared state passed between the LangGraph nodes."""
    input_data: dict[str, Any]
    contact_result: dict[str, Any]
    consent_result: dict[str, Any]
    final_result: dict[str, Any]
