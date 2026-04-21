"""
LangGraph agent with PostgreSQL checkpointing and HITL (Human In The Loop).

Nodes: classify → extract → (interrupt) → human_review → apply_review → END

The graph is compiled with interrupt_before=["human_review"] so it halts after extraction.
When the human reviews, they call the resume API which resumes the graph with their decision.
"""

import json
import logging
from typing import Optional
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command
from google import genai
from google.genai import types
from app.settings import settings

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.gemini_api_key)
MODEL = "gemini-2.5-flash"

CLASSIFY_PROMPT = """You are a financial document classifier for a Fund of Funds (FoF) operation.

A Fund of Funds invests in many private equity and venture capital funds. It regularly receives:
- Capital Calls: Requests from a fund for the LP (the FoF) to wire capital. Usually say "Capital Call", "Draw Down", or "LP Contribution". URGENT because missing the deadline causes legal default.
- Invoices: Bills for management fees, legal fees, or other services.

Analyze this document text and classify it.

Document text:
{text}

Respond with ONLY valid JSON (no markdown):
{{
  "document_type": "invoice" | "capital_call" | "unknown",
  "confidence": 0.0-1.0,
  "reasoning": "2-3 sentence explanation of why you classified it this way, citing specific words or phrases you saw in the document"
}}"""

EXTRACT_PROMPT = """You are a financial data extraction agent for a Fund of Funds operation.

Document type: {doc_type}
Document text:
{text}

Extract all key payment metadata. Respond with ONLY valid JSON (no markdown):
{{
  "fund_name": "exact fund name as written, or null",
  "amount": number in base currency units (e.g. 500000 for $500k), or null,
  "currency": "USD" | "EUR" | "GBP" | "JPY" | null,
  "due_date": "YYYY-MM-DD format, or null if not found",
  "confidence": 0.0-1.0
}}"""


class AgentState(TypedDict):
    document_id: str
    thread_id: str
    text: str
    document_type: Optional[str]
    reasoning: Optional[str]
    metadata: Optional[dict]
    human_decision: Optional[str]   # "approve" | "reject" | None
    review_note: Optional[str]
    overrides: Optional[dict]
    error: Optional[str]


def classify_node(state: AgentState) -> AgentState:
    doc_id = state["document_id"]
    text_len = len(state["text"])
    logger.info(f"classify_node: doc_id={doc_id} text_len={text_len}")
    prompt = CLASSIFY_PROMPT.format(text=state["text"][:6000])
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        logger.error(f"classify_node: JSON parse error doc_id={doc_id} raw={response.text!r} error={exc}")
        raise
    doc_type = data["document_type"]
    confidence = data.get("confidence")
    logger.info(
        f"classify_node: doc_id={doc_id} document_type={doc_type} confidence={confidence} "
        f"reasoning={data.get('reasoning', '')[:120]!r}"
    )
    return {
        **state,
        "document_type": doc_type,
        "reasoning": data.get("reasoning", ""),
    }


def extract_node(state: AgentState) -> AgentState:
    doc_id = state["document_id"]
    if state.get("document_type") == "unknown":
        logger.info(f"extract_node: skipping extraction for unknown doc_id={doc_id}")
        return state
    logger.info(f"extract_node: doc_id={doc_id} document_type={state['document_type']}")
    prompt = EXTRACT_PROMPT.format(
        doc_type=state["document_type"],
        text=state["text"][:6000],
    )
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0,
        ),
    )
    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        logger.error(f"extract_node: JSON parse error doc_id={doc_id} raw={response.text!r} error={exc}")
        raise
    logger.info(
        f"extract_node: doc_id={doc_id} fund_name={data.get('fund_name')!r} "
        f"amount={data.get('amount')} currency={data.get('currency')} "
        f"due_date={data.get('due_date')} confidence={data.get('confidence')}"
    )
    data["document_type"] = state["document_type"]
    data["reasoning"] = state.get("reasoning", "")
    return {**state, "metadata": data}


def should_extract(state: AgentState) -> str:
    return "extract" if state.get("document_type") != "unknown" else END


def human_review_node(state: AgentState) -> AgentState:
    return state


def apply_review_node(state: AgentState) -> AgentState:
    if not state.get("human_decision"):
        return state

    if state["human_decision"] == "approve":
        if state.get("overrides"):
            existing = dict(state.get("metadata") or {})
            existing.update({k: v for k, v in state["overrides"].items() if v is not None})
            return {**state, "metadata": existing}

    return state


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("classify", classify_node)
    builder.add_node("extract", extract_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("apply_review", apply_review_node)

    builder.set_entry_point("classify")
    builder.add_conditional_edges("classify", should_extract, {"extract": "extract", END: END})
    builder.add_edge("extract", "human_review")
    builder.add_edge("human_review", "apply_review")
    builder.add_edge("apply_review", END)

    return builder


# Singleton instances kept alive for the duration of the app process
graph = None
_checkpointer = None
_checkpointer_ctx = None


async def initialize_graph():
    global graph, _checkpointer, _checkpointer_ctx
    logger.info("initialize_graph: setting up LangGraph with PostgreSQL checkpointer")
    _checkpointer_ctx = AsyncPostgresSaver.from_conn_string(settings.database_url)
    _checkpointer = await _checkpointer_ctx.__aenter__()
    await _checkpointer.setup()
    graph = build_graph().compile(
        checkpointer=_checkpointer,
        interrupt_before=["human_review"],
    )
    logger.info("initialize_graph: LangGraph compiled successfully (interrupt_before=human_review)")


async def shutdown_graph():
    global _checkpointer_ctx
    if _checkpointer_ctx:
        logger.info("shutdown_graph: closing PostgreSQL checkpointer connection")
        await _checkpointer_ctx.__aexit__(None, None, None)


async def start_agent_run(document_id: str, text: str) -> dict:
    """
    Initial run — classifies text, extracts metadata, then suspends at human_review.
    Returns the state snapshot at interruption point.
    """
    if graph is None:
        await initialize_graph()

    thread_id = document_id
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "document_id": document_id,
        "thread_id": thread_id,
        "text": text,
        "document_type": None,
        "reasoning": None,
        "metadata": None,
        "human_decision": None,
        "review_note": None,
        "overrides": None,
        "error": None,
    }

    logger.info(f"start_agent_run: doc_id={document_id} text_len={len(text)}")
    try:
        result = await graph.ainvoke(initial_state, config=config)
        logger.info(
            f"start_agent_run: completed doc_id={document_id} "
            f"document_type={result.get('document_type')} error={result.get('error')}"
        )
        return result
    except Exception as e:
        logger.error(f"start_agent_run: exception doc_id={document_id} error={e}", exc_info=True)
        return {**initial_state, "error": str(e)}


async def resume_agent_run(document_id: str, human_decision: str, note: str, overrides: dict) -> dict:
    """
    Resume graph execution after human review with their decision.
    Passes the decision to human_review_node which applies it in apply_review_node.
    """
    if graph is None:
        await initialize_graph()

    config = {"configurable": {"thread_id": document_id}}
    resume_value = {
        "human_decision": human_decision,
        "review_note": note,
        "overrides": overrides or {},
    }

    logger.info(
        f"resume_agent_run: doc_id={document_id} decision={human_decision} "
        f"overrides={list((overrides or {}).keys())}"
    )
    try:
        result = await graph.ainvoke(Command(resume=resume_value), config=config)
        logger.info(f"resume_agent_run: completed doc_id={document_id} error={result.get('error')}")
        return result
    except Exception as e:
        logger.error(f"resume_agent_run: exception doc_id={document_id} error={e}", exc_info=True)
        return {"error": str(e), "human_decision": human_decision}
