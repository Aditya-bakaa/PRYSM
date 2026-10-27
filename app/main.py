"""FastAPI routes; request deduplication, reproducible demo and timing metadata."""
import os
from copy import deepcopy
from pathlib import Path
from threading import Lock
from time import perf_counter, monotonic

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()
from . import agents, engine
from .reference_data import DEFAULT_PROBLEM, FEATURES, MATERIALS, SCENARIOS
from .schemas import (ArenaRequest, ArenaResult, Claim, Evaluation, Problem, Proposal, RunTimings)

app = FastAPI(title="Agent Arena", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])
DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
_CACHE: dict[str, tuple[float, ArenaResult]] = {}
_CACHE_LOCK = Lock()
_CACHE_SECONDS = 45
# The sole inflight lock prevents concurrent identical costly backend calls in this single process.
_RUN_LOCK = Lock()

@app.get("/api/health")
def health():
    return {"status": "ok", "llm_configured": agents.llm_available(), "provider": "Groq",
            "model": os.getenv("GROQ_MODEL", agents.MODEL_DEFAULT), "demo_available": True}

@app.get("/api/reference")
def reference():
    return {"default_problem": DEFAULT_PROBLEM, "materials": MATERIALS, "features": FEATURES,
            "scenarios": SCENARIOS, "weights": engine.WEIGHTS,
            "scoring": {"scenario_aggregation": "60% mean of 6 scenarios + 40% worst case",
                        "constraint_penalty": engine.PENALTY_PER_VIOLATION,
                        "false_claim_penalty": engine.PENALTY_PER_BAD_CLAIM,
                        "carbon_horizon_years": 30, "catalogue": "Illustrative, not engineering-validated"}}


def _make_result(req, problem):
    started = perf_counter()
    proposals, timings, notes = agents.run_agents(problem, req.mode)
    evaluation_start = perf_counter()
    evaluations = engine.rank([engine.evaluate(p, problem) for p in proposals])
    evaluation_ms = round((perf_counter() - evaluation_start) * 1000, 2)
    hybrid_start = perf_counter()
    synthesis = agents.synthesize(evaluations, problem)
    hybrid_ms = round((perf_counter() - hybrid_start) * 1000, 2)
    return ArenaResult(problem=problem, evaluations=evaluations, synthesis=synthesis,
        used_live_llm=any(t.source == "live" for t in timings), mode=req.mode,
        notes=notes, timings=RunTimings(agents=timings, evaluation_ms=evaluation_ms,
                              hybrid_ms=hybrid_ms, total_ms=round((perf_counter() - started) * 1000, 2)))

@app.post("/api/arena/run", response_model=ArenaResult)
def run_arena(req: ArenaRequest):
    problem = req.problem or Problem(**DEFAULT_PROBLEM)
    key = problem.model_dump_json() + "|" + req.mode + "|" + os.getenv("GROQ_MODEL", agents.MODEL_DEFAULT)
    # Cache only live results, with TTL, explicit metadata and refresh opt-out.
    with _RUN_LOCK:
        with _CACHE_LOCK:
            item = _CACHE.get(key)
        if req.mode == "live" and not req.refresh and item and monotonic() - item[0] < _CACHE_SECONDS:
            cached = deepcopy(item[1])
            cached.cached = True
            return cached
        result = _make_result(req, problem)
        if req.mode == "live":
            with _CACHE_LOCK:
                _CACHE[key] = (monotonic(), deepcopy(result))
                if len(_CACHE) > 40:
                    _CACHE.pop(next(iter(_CACHE)))
        return result

@app.post("/api/evaluate", response_model=Evaluation)
def evaluate_one(proposal: Proposal):
    return engine.evaluate(proposal, Problem(**DEFAULT_PROBLEM))

@app.get("/api/integrity-demo")
def integrity_demo():
    baseline = Proposal(agent_name="Integrity control", perspective="deliberate misstatement",
        material="reinforced_concrete", features=["raised_plinth"], summary="A deliberately false cost claim for demonstration.")
    actual = engine.compute_metrics(baseline, Problem(**DEFAULT_PROBLEM))
    honest = baseline.model_copy(update={"claims": [Claim(metric="total_cost", value=actual.total_cost)]})
    false = baseline.model_copy(update={"claims": [Claim(metric="total_cost", value=actual.total_cost * .5)]})
    return {"label": "Deliberate false claim — NOT agent output", "honest": engine.evaluate(honest, Problem(**DEFAULT_PROBLEM)),
            "false": engine.evaluate(false, Problem(**DEFAULT_PROBLEM))}

if (DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")
    @app.get("/")
    def index():
        return FileResponse(DIST / "index.html")
else:
    @app.get("/")
    def index():
        return JSONResponse({"message": "Build frontend or run npm run dev on port 5173"})
