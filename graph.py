import logging
from langgraph.graph import StateGraph, START, END

from state import AgentState
from supervisor import get_chatqna, get_notes, create_final_output
from contact_agent import extract_contacts
from consent_agent import extract_consent

logger = logging.getLogger(__name__)


def supervisor_node(state: AgentState):
    """Prepare the unchanged input for both extraction agents."""
    input_data = state.get("input_data", {})
    chatqna = get_chatqna(input_data)
    notes = get_notes(input_data)
    logger.info("Supervisor started")
    logger.info("Inputs prepared. Chatqna length=%d Notes length=%d", len(chatqna), len(notes))
    return {"input_data": input_data}


def contact_node(state: AgentState):
    logger.info("========== CONTACT AGENT STARTED ==========")
    input_data = state.get("input_data", {})
    result = extract_contacts(get_chatqna(input_data), get_notes(input_data))
    logger.info("========== CONTACT AGENT COMPLETED ==========")
    return {"contact_result": result}


def consent_node(state: AgentState):
    logger.info("========== CONSENT AGENT STARTED ==========")
    input_data = state.get("input_data", {})
    result = extract_consent(get_chatqna(input_data), get_notes(input_data))
    logger.info("========== CONSENT AGENT COMPLETED ==========")
    return {"consent_result": result}


def final_supervisor_node(state: AgentState):
    logger.info("Final Supervisor started")
    final_result = create_final_output(
        input_data=state.get("input_data", {}),
        contact_result=state.get("contact_result", {}),
        consent_result=state.get("consent_result", {}),
    )
    logger.info("Final Supervisor completed")
    return {"final_result": final_result}


builder = StateGraph(AgentState)
builder.add_node("supervisor", supervisor_node)
builder.add_node("contact", contact_node)
builder.add_node("consent", consent_node)
builder.add_node("final_supervisor", final_supervisor_node)
builder.add_edge(START, "supervisor")
builder.add_edge("supervisor", "contact")
builder.add_edge("supervisor", "consent")
# Barrier: run final supervisor only after BOTH extraction agents finish.
builder.add_edge(["contact", "consent"], "final_supervisor")
builder.add_edge("final_supervisor", END)

graph = builder.compile()
