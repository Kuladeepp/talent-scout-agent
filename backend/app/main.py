from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.candidate_pool import pool
from app.models import Conversation, JDStruct, ScoutRequest, ScoutResponse
from app.outreach_sim import explain_conversation as _explain
from app.pipeline import run as run_pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.load()
    yield


app = FastAPI(title="Talent Scout Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before production demo
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "candidates_loaded": str(len(pool.candidates))}


@app.post("/scout", response_model=ScoutResponse)
async def scout(req: ScoutRequest) -> ScoutResponse:
    try:
        return await run_pipeline(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"pipeline error: {e}")


class ExplainRequest(BaseModel):
    jd: JDStruct
    candidate_id: str
    conversation: Conversation
    interest_score: int


class ExplainResponse(BaseModel):
    explanation: str


@app.post("/explain", response_model=ExplainResponse)
async def explain(req: ExplainRequest) -> ExplainResponse:
    if req.candidate_id not in pool.candidates:
        raise HTTPException(status_code=404, detail="unknown candidate")
    c = pool.get(req.candidate_id)
    text = await _explain(req.jd, c, req.conversation, req.interest_score)
    return ExplainResponse(explanation=text)
