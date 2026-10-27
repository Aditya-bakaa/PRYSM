
from .reference_data import (BASELINE_OPERATIONAL_CARBON_PER_M2_YEAR,
    FEATURES, MATERIALS, OPERATIONAL_HORIZON_YEARS, SCENARIOS)
from .schemas import ClaimCheck, Evaluation, Metrics, Problem, Proposal, ScenarioResult

CLAIM_TOLERANCE_PCT = 5.0
WEIGHTS = {"cost": .30, "carbon": .30, "resilience": .40}
PENALTY_PER_BAD_CLAIM = 8.0
MAX_INTEGRITY_PENALTY = 24.0
PENALTY_PER_VIOLATION = 10.0
BASELINE_ENERGY_KWH_PER_M2_YEAR = 120.0
BASELINE_WATER_M3_PER_M2_YEAR = 1.2


def _clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))


def compute_metrics(proposal: Proposal, problem: Problem, scenario="baseline") -> Metrics:
    sc = SCENARIOS[scenario]
    mat = MATERIALS[proposal.material]
    feats = [FEATURES[f] for f in proposal.features]
    has = set(proposal.features)
    # A material price shock affects only material cost, not add-on equipment/labour.
    total_cost = (mat["cost_per_m2"] * sc["cost_mult"] + sum(f["cost_per_m2"] for f in feats)) * problem.floor_area_m2
    embodied = mat["carbon_per_m2"] + sum(f["carbon_per_m2"] for f in feats)
    # Combine fractional savings multiplicatively to avoid summing overlapping benefits.
    energy_factor = 1.0
    for f in feats:
        energy_factor *= (1 - f["energy_saving"])
    energy_factor = max(.4, energy_factor)  # illustrative max 60% reduction
    heat_factor = 1.3 if sc["heat"] else 1.0
    annual_energy = BASELINE_ENERGY_KWH_PER_M2_YEAR * heat_factor * energy_factor
    operational = BASELINE_OPERATIONAL_CARBON_PER_M2_YEAR * heat_factor * energy_factor * OPERATIONAL_HORIZON_YEARS
    carbon = embodied + operational
    water_factor = .75 if "rainwater_harvesting" in has else 1.0
    resilience = mat["resilience"] + sum(f["resilience"] for f in feats)
    if sc["flood"] and "raised_plinth" not in has:
        resilience -= 3.0
    if sc["quake"]:
        if "seismic_bracing" not in has:
            resilience -= 3.0
        if proposal.material in ("red_brick", "fly_ash_brick", "aac_block"):
            resilience -= 1.0
    if sc["heat"] and not has.intersection({"cool_roof_coating", "insulation_upgrade", "green_roof"}):
        resilience -= 2.0
    if sc["grid_outage"] and "battery_backup" not in has:
        resilience -= 1.5 if "solar_panels" in has else 2.5
    return Metrics(total_cost=round(total_cost, 2), lifetime_carbon_per_m2=round(carbon, 2),
        resilience=round(_clamp(resilience, 0, 10), 2), annual_energy_kwh_per_m2=round(annual_energy, 2),
        annual_water_m3_per_m2=round(BASELINE_WATER_M3_PER_M2_YEAR * water_factor, 2))


def verify_claims(proposal, actual):
    checks = []
    for claim in proposal.claims:
        real = getattr(actual, claim.metric)
        deviation = abs(claim.value - real) / real * 100 if real else (0 if claim.value == 0 else 100)
        checks.append(ClaimCheck(metric=claim.metric, claimed=claim.value, actual=real,
            deviation_pct=round(deviation, 2), verified=deviation <= CLAIM_TOLERANCE_PCT))
    return checks


def _violations(m, problem):
    violations = []
    if m.total_cost > problem.budget:
        violations.append("over_budget")
    if m.lifetime_carbon_per_m2 > problem.max_carbon_kg_per_m2_lifetime:
        violations.append("carbon_limit_exceeded")
    if m.resilience < problem.min_resilience:
        violations.append("below_min_resilience")
    if m.annual_water_m3_per_m2 > problem.max_annual_water_m3_per_m2:
        violations.append("water_limit_exceeded")
    return violations


def _sub_scores(m, problem):
    cost = _clamp((1.3 - m.total_cost / problem.budget) / .6 * 100)
    carbon = _clamp((1.2 - m.lifetime_carbon_per_m2 / problem.max_carbon_kg_per_m2_lifetime) / .8 * 100)
    resilience = _clamp(m.resilience / 10 * 100)
    return {"cost": round(cost, 2), "carbon": round(carbon, 2), "resilience": round(resilience, 2)}


def _score(m, problem):
    subs = _sub_scores(m, problem)
    base = sum(WEIGHTS[k] * subs[k] for k in WEIGHTS)
    violations = _violations(m, problem)
    return _clamp(base - PENALTY_PER_VIOLATION * len(violations)), violations, subs


def evaluate(proposal: Proposal, problem: Problem) -> Evaluation:
    baseline = compute_metrics(proposal, problem)
    checks = verify_claims(proposal, baseline)
    penalty = min(MAX_INTEGRITY_PENALTY, PENALTY_PER_BAD_CLAIM * sum(not c.verified for c in checks))
    results = []
    for name, sc in SCENARIOS.items():
        m = compute_metrics(proposal, problem, name)
        score, violations, _ = _score(m, problem)
        results.append(ScenarioResult(scenario=name, description=sc["description"], metrics=m,
            score=round(score, 2), constraints_violated=violations))
    scores = [r.score for r in results]
    worst = min(scores)
    stress = .6 * (sum(scores) / len(scores)) + .4 * worst
    _, violations, subs = _score(baseline, problem)
    return Evaluation(agent_name=proposal.agent_name, perspective=proposal.perspective,
        proposal=proposal, baseline_metrics=baseline, claim_checks=checks,
        integrity_penalty=penalty, scenario_results=results, stress_score=round(stress, 2),
        worst_case_score=round(worst, 2), sub_scores=subs,
        final_score=round(_clamp(stress - penalty), 2), constraints_violated=violations)


def rank(evaluations):
    ranked = sorted(evaluations, key=lambda e: (-e.final_score, -e.stress_score, e.agent_name))
    for i, item in enumerate(ranked, 1):
        item.rank = i
    return ranked
