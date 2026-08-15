"""Nodes for the IOSA agent graph.

Each function takes state, returns a partial dict update.
"""
import time
from src.iosa.agent.state import AgentState
from src.iosa.llm.chat import chat
from src.iosa.logger import setup_logger
from src.iosa.retrieval.retriever import retrieve
from src.iosa.database.db import run_query

logger = setup_logger(__name__)

MAX_RETRIES = 2
RETRIEVE_K = 5


# ── Retrieval ───────────────────────────────────────────────

def retrieve_node(state: AgentState) -> dict:
    query = state["rewritten_query"]
    try:
        start = time.perf_counter()
        docs = retrieve(query, k=RETRIEVE_K)
        logger.info(f"retrieve: query={query!r} found={len(docs)} time={time.perf_counter()-start: .2f}s")
        return {"retrieved_docs": docs}
    except Exception:
        logger.exception("retrieve failed")
        return {"retrieved_docs": []}


# ── Grading ─────────────────────────────────────────────────

GRADE_PROMPT_SYSTEM = (
    "You judge whether retrieved document excerpts contain enough "
    "information to answer a question. Respond with exactly one word: "
    "RELEVANT or NOT_RELEVANT. No other text."
)


def grade_node(state: AgentState) -> dict:
    docs = state["retrieved_docs"]
    if not docs:
        logger.info("grade: no docs, marking not_relevant")
        return {"grade": "not_relevant"}

    try:
        start= time.perf_counter()
        context = "\n\n".join(
            f"[Source {i+1}] {d['text']}" for i, d in enumerate(docs)
        )
        prompt = (
            f"Question: {state['rewritten_query']}\n\n"
            f"Retrieved excerpts:\n{context}\n\n"
            "Do these excerpts contain enough information to answer the question?"
        )
        reply = chat(prompt=prompt, system=GRADE_PROMPT_SYSTEM).strip().upper()

        # check NOT_RELEVANT first because "RELEVANT" is a substring of it
        if "NOT_RELEVANT" in reply:
            grade = "not_relevant"
        elif "RELEVANT" in reply:
            grade = "relevant"
        else:
            grade = "not_relevant"

        logger.info(f"grade: query={state['rewritten_query']!r} result={grade} raw={reply!r} time={time.perf_counter()-start: .2f}s")
        return {"grade": grade}
    except Exception:
        logger.exception("grade failed, defaulting to not_relevant")
        return {"grade": "not_relevant"}


# ── Query rewriting ─────────────────────────────────────────

REWRITE_PROMPT_SYSTEM = (
    "You rewrite search queries to improve retrieval from a technical "
    "document corpus. Given a question that failed to retrieve a good "
    "match, produce a single reformulated search query using different "
    "phrasing or more specific terminology. Respond with only the "
    "rewritten query, no explanation."
)


def rewrite_node(state: AgentState) -> dict:
    try:
        start= time.perf_counter()
        prompt = (
            f"Original question: {state['query']}\n\n"
            f"Previous search attempt: {state['rewritten_query']}"
        )
        new_query = chat(prompt=prompt, system=REWRITE_PROMPT_SYSTEM).strip()
        retries = state["retries"] + 1
        logger.info(f"rewrite: {state['rewritten_query']!r} -> {new_query!r} (attempt {retries}) time={time.perf_counter()-start: .2f}s")
        return {"rewritten_query": new_query, "retries": retries}
    except Exception:
        logger.exception("rewrite failed, keeping previous query")
        return {"rewritten_query": state["rewritten_query"], "retries": state["retries"] + 1}


# ── SQL tool ────────────────────────────────────────────────

SCHEMA_INFO = """Tables:
- equipment (id, tag, name, type, unit, install_date, status)
- incidents (id, equipment_id, incident_date, severity, incident_type, description, root_cause, injuries_count, downtime_hours, resolved, resolved_date, reported_by)
- maintenance_logs (id, equipment_id, maintenance_date, maintenance_type, description, technician, duration_hours, cost, parts_replaced, next_scheduled_date)
- pump_readings (id, equipment_id, suction_pressure_bar, discharge_pressure_bar, differential_pressure_bar, flow_rate_m3_per_h, motor_current_amps, motor_power_kw, speed_rpm, bearing_temperature_c, motor_temperature_c, vibration_mm_s, seal_leakage, suction_level_percent, recorded_at)
- tank_readings (id, equipment_id, level_percent, volume_m3, temperature_c, pressure_bar, inlet_flow_rate_m3_per_h, outlet_flow_rate_m3_per_h, recorded_at)
- valve_readings, compressor_readings, heat_exchanger_readings, distillation_column_readings, reactor_readings (similar, with equipment_id and recorded_at)
Use JOIN equipment ON equipment.id = <table>.equipment_id to get tag/name."""

SQL_PROMPT_SYSTEM = (
    "You are a SQL query generator for a refinery equipment database. "
    "Given a question and the schema below, write a single SQLite SELECT "
    "query. Respond with only the SQL, no explanation, no markdown.\n\n"
    + SCHEMA_INFO
)


def sql_tool_node(state: AgentState) -> dict:
    try:
        start= time.perf_counter()
        sql = chat(prompt=state["rewritten_query"], system=SQL_PROMPT_SYSTEM).strip()

        # clean up common LLM formatting quirks
        sql = sql.strip("`").strip()
        if sql.lower().startswith("sql"):
            sql = sql[3:].strip()

        if not sql.upper().startswith("SELECT"):
            logger.warning(f"sql_tool: blocked non-SELECT: {sql!r} ")
            return {"sql_result": [], "sql_query": sql}

        rows = run_query(sql)
        logger.info(f"sql_tool: query={state['rewritten_query']!r} rows={len(rows)} time={time.perf_counter()-start: .2f}s")
        return {"sql_result": rows, "sql_query": sql}
    except Exception:
        logger.exception("sql_tool failed")
        return {"sql_result": [], "sql_query": ""}


# ── Generation ──────────────────────────────────────────────

GENERATE_PROMPT_SYSTEM = (
    "You are a technical assistant answering questions about industrial "
    "safety documents. Answer using only the sources provided. Cite the "
    "source number for every factual claim, like [Source 1]. Do not state "
    "anything as fact that the sources do not support. If the sources "
    "disagree or a figure was later corrected, say so explicitly."
)


def generate_node(state: AgentState) -> dict:
    try:
        start= time.perf_counter()
        route = state.get("route", "vector")

        if route == "sql":
            rows = state.get("sql_result", [])
            sql = state.get("sql_query", "")
            if not rows:
                return {"answer": "The query returned no results from the database."}
            context = f"SQL query: {sql}\n\nResults:\n"
            for i, row in enumerate(rows):
                context += f"Row {i+1}: {row}\n"
            prompt = (
                f"{context}\n"
                f"Question: {state['query']}\n\n"
                "Summarize these database results in a clear, readable answer."
            )
        else:
            docs = state["retrieved_docs"]
            context = "\n\n".join(
                f"[Source {i+1}: {d['source']} p{d['page_number']}]\n{d['text']}"
                for i, d in enumerate(docs)
            )
            prompt = f"{context}\n\nQuestion: {state['query']}"

        answer = chat(prompt=prompt, system=GENERATE_PROMPT_SYSTEM)
        logger.info(f"generate: route={route} answer_len={len(answer)} time={time.perf_counter()-start: .2f}s")
        return {"answer": answer}
    except Exception:
        logger.exception("generate failed")
        return {"answer": "Something went wrong generating the answer.", "refused": True}


# ── Refusal ─────────────────────────────────────────────────

REFUSAL_MESSAGE = (
    "I don't have enough information in the indexed documents to answer "
    "that question confidently. You may want to check the source "
    "documents directly or rephrase the question."
)


def refuse_node(state: AgentState) -> dict:
    logger.info(f"refuse: query={state['query']!r} retries={state['retries']}")
    return {"answer": REFUSAL_MESSAGE, "refused": True}


# ── Router ──────────────────────────────────────────────────

ROUTER_PROMPT_SYSTEM = (
    "You classify user questions into one of three categories. "
    "Respond with exactly one word, nothing else.\n\n"
    "VECTOR - questions about document content, safety reports, "
    "procedures, investigation findings, regulations\n"
    "SQL - questions about specific equipment data, incident counts, "
    "maintenance history, sensor readings, equipment status\n"
    "DIRECT - greetings, small talk, or unrelated questions"
)


def router_node(state: AgentState) -> dict:
    try:
        start= time.perf_counter()
        reply = chat(prompt=state["query"], system=ROUTER_PROMPT_SYSTEM).strip().upper()
        if "SQL" in reply:
            route = "sql"
        elif "VECTOR" in reply:
            route = "vector"
        else:
            route = "direct"
        logger.info(f"router: query={state['query']!r} -> {route} (raw={reply!r}) time={time.perf_counter() - start: .2f}s")
        return {"route": route}
    except Exception:
        logger.exception("router failed, defaulting to vector")
        return {"route": "vector"}


# ── Direct response (no tools) ──────────────────────────────

DIRECT_PROMPT_SYSTEM = (
    "You are IOSA, an Industrial Safety and Operations Assistant. "
    "You help with questions about refinery safety documents and "
    "equipment data. If the user greets you, respond briefly and "
    "explain what you can help with."
)


def direct_node(state: AgentState) -> dict:
    try:
        start= time.perf_counter()
        answer = chat(prompt=state["query"], system=DIRECT_PROMPT_SYSTEM)
        logger.info(f"direct: query={state['query']!r} time={time.perf_counter() - start: .2f}s")
        return {"answer": answer}
    except Exception:
        logger.exception("direct failed")
        return {"answer": "Something went wrong. Please try again."}
