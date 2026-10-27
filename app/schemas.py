"""API contract; numbers are engine-derived unless explicitly labelled as agent claims."""
from typing import Literal
import math
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .reference_data import FEATURES, MATERIALS

MetricName = Literal["total_cost", "lifetime_carbon_per_m2", "resilience"]

class Problem(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=10, max_length=1500)
    floor_area_m2: float = Field(gt=0, le=100000)
    budget: float = Field(gt=0, le=1e12)
    max_carbon_kg_per_m2_lifetime: float = Field(gt=0, le=100000)
    min_resilience: float = Field(ge=0, le=10)
    max_annual_water_m3_per_m2: float = Field(default=1.0, gt=0, le=100)

class Claim(BaseModel):
    metric: MetricName
    value: float = Field(ge=0)

class Proposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_name: str = Field(min_length=1)
    perspective: str = Field(min_length=1)
    material: str
    features: list[str] = Field(default_factory=list, max_length=len(FEATURES))
    summary: str = Field(min_length=5, max_length=550)
    accepted_tradeoff: str = ""
    refused_tradeoff: str = ""
    claims: list[Claim] = Field(default_factory=list, max_length=3)
    assumptions: list[str] = Field(default_factory=list)

    @field_validator("material")
    @classmethod
    def material_known(cls, v):
        if v not in MATERIALS:
            raise ValueError(f"Unknown material: {v}")
        return v

    @field_validator("features")
    @classmethod
    def feature_checks(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Duplicate features are not allowed")
        if set(v) - FEATURES.keys():
            raise ValueError("Unknown feature selection")
        if {"green_roof", "cool_roof_coating"} <= set(v):
            raise ValueError("Choose either green roof or cool roof coating for this illustrative roof")
        return sorted(v)

    @model_validator(mode="after")
    def unique_claims(self):
        metrics = [c.metric for c in self.claims]
        if len(metrics) != len(set(metrics)):
            raise ValueError("Duplicate claims for one metric")
        return self

class Metrics(BaseModel):
    total_cost: float
    lifetime_carbon_per_m2: float
    resilience: float
    annual_energy_kwh_per_m2: float
    annual_water_m3_per_m2: float

class ClaimCheck(BaseModel):
    metric: MetricName
    claimed: float
    actual: float
    deviation_pct: float
    verified: bool

class ScenarioResult(BaseModel):
    scenario: str
    description: str
    metrics: Metrics
    score: float
    constraints_violated: list[str]

class Evaluation(BaseModel):
    agent_name: str
    perspective: str
    proposal: Proposal
    baseline_metrics: Metrics
    claim_checks: list[ClaimCheck]
    integrity_penalty: float
    scenario_results: list[ScenarioResult]
    stress_score: float
    worst_case_score: float
    sub_scores: dict[str, float]
    final_score: float
    constraints_violated: list[str]
    rank: int = 0

class SynthesisResult(BaseModel):
    winner: str
    explanation: str
    hybrid_suggestion: Proposal | None = None
    hybrid_evaluation: Evaluation | None = None

class AgentTiming(BaseModel):
    agent_name: str
    latency_ms: float
    source: Literal["live", "fixture", "fallback"]
    note: str = ""

class RunTimings(BaseModel):
    agents: list[AgentTiming]
    evaluation_ms: float
    hybrid_ms: float
    total_ms: float

class ArenaResult(BaseModel):
    problem: Problem
    evaluations: list[Evaluation]
    synthesis: SynthesisResult
    used_live_llm: bool
    mode: Literal["live", "demo"]
    cached: bool = False
    timings: RunTimings
    notes: list[str] = Field(default_factory=list)

class ArenaRequest(BaseModel):
    problem: Problem | None = None
    mode: Literal["live", "demo"] = "demo"
    refresh: bool = False
