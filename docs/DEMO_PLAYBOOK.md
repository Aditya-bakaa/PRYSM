# Presentation playbook — Agent Arena

## Recommended 90-second live / safe-demo script

**0–15s — Hook**

“Imagine asking one AI to design a health centre. It might optimize for cost and overlook a flood. Another might maximize sustainability and exceed the budget. Agent Arena makes those competing priorities explicit.”

**15–30s — Setup**

“We have an 800-square-metre community health centre, a 2.2-crore-rupee illustrative budget, heat and flood exposure, and possible power interruptions. Three specialized agents propose different materials and features.”

**30–45s — Run**

“I'll start the competition. Each agent proposes a design from a fixed set of options. In live mode they call Groq concurrently; in safe demo mode the proposals are labelled fixtures. All scores always come from Python.”

**45–65s — Engine and hazards**

“Here are the results: construction cost, lifetime carbon, energy, water and resilience. The radar and stress table reveal why designs that look good in normal conditions can fail under flooding, heat, price spikes or grid outages. Every design faces the same six tests.”

**65–80s — Hybrid and claims**

“The backend builds a hybrid from agent-proposed choices and independently rescores it. The result isn't declared superior in advance. We also have a separate test: deliberately understate the price by half, and the integrity engine applies an eight-point penalty.”

**80–90s — Close**

“The concept is straightforward: AI proposes; mathematics verifies; stress tests decide. These calculations are illustrative, but the evaluation logic is transparent, auditable and reproducible.”

## Three-minute backup plan — if the live API fails

**0:00–0:25 — Explain the failure honestly.** Show the Live mode badge indicating the provider failure and fixture fallback. Say “The provider request failed; the application has preserved its deterministic evaluation path. I am switching to the independently labelled safe demo.”

**0:25–0:55 — Run fixed scenario.** Click **Safe demo → Reset to demo scenario → Start competition**. State inputs: 800 m², ₹22m, carbon ≤2500 kg/m², resilience ≥6 and annual water intensity ≤1.0 m³/m².

**0:55–1:35 — Agent differences.** Open the three cards. Compare feature sets and accepted/refused trade-offs, baseline constraints, costs and carbon. Emphasize fixtures provide feature decisions, not frozen scores.

**1:35–2:15 — Deterministic checks.** Walk through heatwave/flood/quake/outage stress table, baseline constraints and the cost/carbon/resilience score profile. Describe fixed engine weights and the worst-case emphasis.

**2:15–2:45 — Hybrid and claim integrity.** Show the hybrid and its recomputed metrics; then scroll to integrity control and show the honest cost claim and 50%-understated cost claim on the same design. Explain the objective penalty.

**2:45–3:00 — Technical close.** Mention Pydantic, controlled Groq JSON schema, concurrent thread-pool requests, fast local deterministic evaluation, and the passing Python suite. Disclose that outputs are illustrative.

For screenshots/backup, present in **safe demo mode** the evening before and take local screenshots yourself. No screenshots are shipped or represented as verified in this ZIP because a frontend build/browser was unavailable in the current execution environment.

## Five likely judge questions with grounded answers

1. **“Why multiple agents if the same engine determines the winner?”** Different priorities produce different feature sets and explicit trade-offs. The engine then compares the actual proposals on common assumptions, preventing agents from awarding themselves favorable scores.
2. **“Are those construction and disaster estimates trustworthy?”** They are intentionally illustrative, catalogue-based approximations. They demonstrate an auditable decision framework, not regulatory, civil engineering or cost consultancy validation. Actual engineering use would require location-specific data, calibrated models and domain review.
3. **“How is the hybrid selected? Could it game the scores?”** We enumerate feature combinations proposed across the agents and their offered material choices. We reject incompatible roof selections, prioritize designs meeting baseline limits and compute every candidate with the same deterministic evaluator. We optimize stress scores without inheriting unverifiable agent claims. A hybrid is allowed to score below the original winner.
4. **“What happens on a 429, slow request or bad JSON?”** Each independent agent gets at most two attempts on temporary rate/network issues, strict schema output with Pydantic checking and a bounded per-attempt timeout. Failed agents receive clearly labelled fixture fallback; valid agents' results remain visible. Cached live runs say they are cached and can be bypassed.
5. **“What did you measure, and how do you know this is faster?”** The API measures real backend/per-agent/evaluation/hybrid runtimes using `perf_counter`. A concurrency test demonstrates overlapping mocked agent delays; it is not a live provider benchmark. Eliminating the sequential extra synthesis LLM call removes one remote round trip by design. Actual cloud latency depends on model capacity, quotas and network and must be benchmarked with the judge's account.

## Claims to avoid making

- “This design is structurally safe / seismic-certified / flood-proof / code-compliant.”
- “The health centre will definitely remain operational for 72 hours during an outage.”
- “These ₹ costs, carbon figures and energy/water savings are verified real-world forecasts.”
- “Our LLM has been proven the fastest / most accurate provider.” No comparative live benchmark was run.
- “The API is free/unlimited for everyone.” Rate limits, billing and availability are account-specific.
- “The hybrid is always superior to every other design.” Feasibility and score trade-offs can reverse the ranking.
- “The model produced every number.” The engine computes the numbers and independently checks optional agent claims.
- “Every agent seen on screen answered live.” Fixture/cached/fallback labels must match the actual source.
- “All 37 tests include browser-rendering and real-provider integration.” They are automated Python/API tests; the browser build and live call remain unverified here.
- “The system guarantees perfectly correct engineering recommendations.” Constrained JSON ensures format, not physical validity.
