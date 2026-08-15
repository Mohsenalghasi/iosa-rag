"""FastAPI wrapper for the IOSA agent."""
import time

from fastapi import FastAPI
from pydantic import BaseModel

app=FastAPI(
    title='IOSA',
    description='Industrial Safety and Operations Assistant',
    version='0.1.0',
    )

class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str
    route: str
    query: str
    time_seconds: float
    sources: list[dict]=[]
    sql_query: str=""

from src.iosa.agent.graph import build_graph

agent=build_graph()

@app.post("/query", response_model=QueryResponse)
def query_agent(request:QueryRequest):
    start= time.perf_counter()

    result= agent.invoke({
        "query": request.query,
        "rewritten_query": request.query,
        "retries": 0,
        "retrieved_docs": [],
        "grade": "",
        "answer": "",
        "refused": False,
        "route": "",
        "sql_result": [],
        "sql_query": "",
    })

    elapsed= round(time.perf_counter() - start, 2)

    sources = []
    if result.get("route")=="vector":
        for d in result.get ("retrieved_docs",[]):
            sources.append({
                "source": d["source"],
                "page": d["page_number"],
                "score": round(d["score"], 3),
            })

    return QueryResponse(
        answer=result["answer"],
        route=result["route"],
        query=request.query,
        time_seconds=elapsed,
        sources=sources,
        sql_query=result.get("sql_query", ""),
    )

            