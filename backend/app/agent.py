"""
LangGraph agent: classify → extract → (returns result for human review)

The agent does NOT approve. It stops at pending_review.
A human must approve via the /review endpoint.
"""

import json
import os
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
    max_tokens=1024,
)

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
    text: str
    document_type: Optional[str]
    reasoning: Optional[str]
    metadata: Optional[dict]
    error: Optional[str]


def classify_node(state: AgentState) -> AgentState:
    prompt = CLASSIFY_PROMPT.format(text=state["text"][:6000])
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1])
    data = json.loads(raw)
    return {
        **state,
        "document_type": data["document_type"],
        "reasoning": data.get("reasoning", ""),
    }


def extract_node(state: AgentState) -> AgentState:
    prompt = EXTRACT_PROMPT.format(
        doc_type=state["document_type"],
        text=state["text"][:6000],
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1])
    data = json.loads(raw)
    return {**state, "metadata": data}


def should_extract(state: AgentState) -> str:
    return "extract" if state.get("document_type") != "unknown" else END


def build_graph() -> StateGraph:
    g = StateGraph(AgentState)
    g.add_node("classify", classify_node)
    g.add_node("extract", extract_node)
    g.set_entry_point("classify")
    g.add_conditional_edges("classify", should_extract, {"extract": "extract", END: END})
    g.add_edge("extract", END)
    return g.compile()


graph = build_graph()


async def run_agent(document_id: str, text: str) -> dict:
    result = await graph.ainvoke({
        "document_id": document_id,
        "text": text,
        "document_type": None,
        "reasoning": None,
        "metadata": None,
        "error": None,
    })
    return result
