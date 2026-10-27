import pytest
from pydantic import ValidationError
from app import agents, engine
from app.reference_data import DEFAULT_PROBLEM
from app.schemas import Claim, Problem, Proposal

PROBLEM = Problem(**DEFAULT_PROBLEM)


def make(material="reinforced_concrete", features=(), claims=()):
    return Proposal(agent_name="test", perspective="test", material=material,
                    features=list(features), summary="Testing proposal", claims=list(claims))


def test_deterministic():
    p = make(features=["raised_plinth", "rainwater_harvesting"])
    assert engine.evaluate(p, PROBLEM) == engine.evaluate(p, PROBLEM)


@pytest.mark.parametrize("field,value", [
    ("material", "unobtainium"), ("features", ["fake_feature"]),
    ("features", ["solar_panels", "solar_panels"]),
    ("features", ["green_roof", "cool_roof_coating"]),
    ("summary", "a"), ("claims", [{"metric": "total_cost", "value": -1}]),
    ("claims", [{"metric": "total_cost", "value": 10}, {"metric": "total_cost", "value": 20}]),
])
def test_invalid_proposal(field, value):
    d = make().model_dump()
    d[field] = value
    with pytest.raises(ValidationError):
        Proposal.model_validate(d)


def test_missing_and_extra_fields():
    data = make().model_dump()
    data.pop("material")
    with pytest.raises(ValidationError):
        Proposal.model_validate(data)
    data = make().model_dump()
    data["unknown"] = 3
    with pytest.raises(ValidationError):
        Proposal.model_validate(data)


def test_problem_constraints_validated():
    with pytest.raises(ValidationError):
        Problem(**{**DEFAULT_PROBLEM, "budget": 0})


def test_cost_math():
    m = engine.compute_metrics(make("red_brick"), PROBLEM)
    assert m.total_cost == 19000 * PROBLEM.floor_area_m2


def test_material_price_spike_only_applies_to_base():
    p = make("red_brick", ["raised_plinth"])
    base = engine.compute_metrics(p, PROBLEM)
    spike = engine.compute_metrics(p, PROBLEM, "material_price_spike")
    assert spike.total_cost - base.total_cost == pytest.approx(19000 * .25 * PROBLEM.floor_area_m2)


def test_energy_savings_multiplicative():
    solar = engine.compute_metrics(make(features=["solar_panels"]), PROBLEM)
    both = engine.compute_metrics(make(features=["solar_panels", "insulation_upgrade"]), PROBLEM)
    assert solar.annual_energy_kwh_per_m2 == pytest.approx(120 * .65)
    assert both.annual_energy_kwh_per_m2 == pytest.approx(120 * .65 * .82, abs=.01)
    assert both.lifetime_carbon_per_m2 < solar.lifetime_carbon_per_m2


def test_water_constraint_enforced():
    no_water = engine.evaluate(make(), PROBLEM)
    reduced = engine.evaluate(make(features=["rainwater_harvesting"]), PROBLEM)
    assert "water_limit_exceeded" in no_water.constraints_violated
    assert "water_limit_exceeded" not in reduced.constraints_violated
    assert reduced.baseline_metrics.annual_water_m3_per_m2 == .9


def test_false_claim_penalised():
    good = engine.compute_metrics(make(), PROBLEM)
    honest = make(claims=[Claim(metric="total_cost", value=good.total_cost)])
    liar = make(claims=[Claim(metric="total_cost", value=1_000_000)])
    a, b = engine.evaluate(honest, PROBLEM), engine.evaluate(liar, PROBLEM)
    assert a.final_score - b.final_score == 8
    assert b.claim_checks[0].verified is False


def test_claim_tolerance_threshold():
    actual = engine.compute_metrics(make(), PROBLEM).total_cost
    near = engine.evaluate(make(claims=[Claim(metric="total_cost", value=actual * 1.04)]), PROBLEM)
    assert near.claim_checks[0].verified is True


def test_flood_stress_hurts_without_plinth():
    dry = engine.compute_metrics(make(), PROBLEM, "flood").resilience
    safe = engine.compute_metrics(make(features=["raised_plinth"]), PROBLEM, "flood").resilience
    assert safe > dry


@pytest.mark.parametrize("scenario,feature", [
    ("earthquake", "seismic_bracing"), ("grid_outage", "battery_backup"),
    ("heatwave", "cool_roof_coating"),
])
def test_protection_improves_stress_resilience(scenario, feature):
    baseline = engine.compute_metrics(make(), PROBLEM, scenario).resilience
    protected = engine.compute_metrics(make(features=[feature]), PROBLEM, scenario).resilience
    assert protected > baseline


def test_scoring_weights():
    e = engine.evaluate(make(), PROBLEM)
    assert engine.WEIGHTS == {"cost": .3, "carbon": .3, "resilience": .4}
    assert e.stress_score == pytest.approx(.6 * sum(x.score for x in e.scenario_results) / 6
                                          + .4 * e.worst_case_score, abs=.02)
    assert sorted(engine.WEIGHTS) == sorted(e.sub_scores)


def test_winner_engine_decides():
    low = engine.evaluate(make("steel_frame", []), PROBLEM)
    high = engine.evaluate(make("aac_block", ["rainwater_harvesting", "raised_plinth"]), PROBLEM)
    ordered = engine.rank([low, high])
    assert ordered[0].final_score >= ordered[1].final_score
    assert ordered[0].rank == 1


def test_full_pipeline_fixture():
    proposals, timing, notes = agents.run_agents(PROBLEM, mode="demo")
    assert not notes
    assert {t.source for t in timing} == {"fixture"}
    evaluations = engine.rank([engine.evaluate(p, PROBLEM) for p in proposals])
    synthesis = agents.synthesize(evaluations, PROBLEM)
    assert len(evaluations) == 3
    hybrid = synthesis.hybrid_evaluation
    assert hybrid.final_score == engine.evaluate(hybrid.proposal, PROBLEM).final_score
    assert hybrid.constraints_violated == []
    assert set(hybrid.proposal.features).issubset({f for p in proposals for f in p.features})
    assert synthesis.winner == evaluations[0].agent_name
