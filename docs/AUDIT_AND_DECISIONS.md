# Agent Arena — source audit and engineering decisions

## Initial repository audit (before changes)

| Area | Verified initial state | Priority / issue |
| --- | --- | --- |
| Web UI | React 18 + Vite 5; dark UI, cards and SVG radar chart | Good baseline; lacked observable status and clear source provenance |
| API | FastAPI synchronous `/api/arena/run`, `/api/health`, `/api/reference`, `/api/evaluate` | Basic flow worked; no timings or cache |
| LLM | `google-genai`, Gemini model from `.env`; `generate_content` JSON mime | Vendor-dependent, no enforced JSON schema |
| Agent calls | Sequential Python loop, each a remote request and up to two attempts | Main source of avoidable latency |
| Explanation | After the agents, an extra sequential Gemini call explained the leaderboard | Avoidable extra latency, could misrepresent math |
| Validation | Pydantic Proposal validated known features/materials | No duplicate/roof clash checks; typed numeric claims existed |
| Computation | `compute_metrics` → `_score` → six stress scenarios → weighted stress result | Core deterministic approach already worked |
| Claim integrity | Difference from computed number with >5% penalty | Fixture CostOptimizer falsely understated a cost by 20% *deliberately*, influencing normal rankings |
| Stress scenarios | Price spike, heat, flood, quake, outage | Price multiplier incorrectly increased add-on costs too |
| Hybrid | Greedy toggles on winner's material/features; scored by `final_score` | Could benefit by dropping original inaccurate claims; explored only winner's material |
| Fallback | All Gemini errors replaced agent output with local proposals | Reliable but labelled one global 'live' boolean even if all agents had failed |
| Tests | Six mostly engine-only tests; few failure paths | API/timeout/quota/partial fallback not covered |
| Deployment | `uvicorn`, Vite proxy, built assets optional; `.env.example` exposed old Gemini key setting | Functional local setup, no demo launch guide |

Input to leaderboard was: form → `runArena` HTTP POST → FastAPI → sequential Gemini/fixture proposals → deterministic baseline & scenarios → sorted leaderboard → greedy hybrid and optional extra LLM synthesis → React cards/radar.

## Prioritized changes completed

1. **Three independent concurrent agent calls** in a bounded thread pool, while FastAPI’s synchronous route runs in its worker pool. Partial failure uses individually labelled fixture data.
2. **Groq hosted GPT-OSS 120B** with strict JSON-schema output and Pydantic validation. Removed Gemini SDK and old environment settings.
3. **No synthesis model call**; a deterministic search evaluates every allowed combination from agents' offered material/feature pool, using the same `engine.evaluate` and ensuring baseline feasibility before optimizing stress score.
4. **Unbiased fallback**: fixture claims are empty, not fabricated. The deliberately inaccurate claim is only in the separately labelled integrity-control route.
5. **Tighter math**: base material-only price shock, multiplicative energy benefits with a 60% cap, added water/energy estimates and an enforced annual water limit. Exposed penalty and weight parameters.
6. **Traceability**: per-agent latency and source, evaluation and synthesis durations, total backend computation duration; 45s explicit live cache and manual refresh. Stage labels do not pretend to show actual agent progress before responses arrive.
7. **Dashboard polish**: explicit live/demo toggle, agent badges, metric comparison, radar, stress matrix and scenario constraint labels, baseline violations, hybrid explanation and separate integrity demonstration.
8. **Tests**: 37 executed pass, including deterministic score/winner, schema errors, all/partial failure, 429, timeout, API route health, cache and forced refresh. **Frontend build could not be run because npm registry DNS access is unavailable in this environment.**

## Provider decision (official documentation checked 26 October 2026)

**Selected: GroqCloud API with `openai/gpt-oss-120b`**. Official model card lists 131,072-token context and approximate 500-token/second generation capacity; $0.15 per million input tokens and $0.60 per million output tokens (do not confuse advertised throughput with observed app latency). It supports constrained `json_schema` strict output with `response_format`. GPT-OSS 120B offers more reasoning capacity than 20B for trade-off decisions; the priority is compact structured selection instead of long prose. The selected model is hosted by **Groq**, even though the model ID begins `openai/`.

Alternatives: Groq `openai/gpt-oss-20b` advertises approximately 1000 tokens/sec and $0.075/$0.30 per million in/out tokens; useful if latency dominates quality but 20B is a smaller model. Groq `qwen/qwen3.8-27b` also appears in the current strict-schema supported list. The OpenAI API supports structured output, but its account tier, availability, and model pricing must be verified individually. OpenAI's historical `gpt-5-mini` listing currently marks it deprecated, so hardcoding it as the recommendation would be inappropriate. We do **not** claim Groq 120B beat these alternatives in measured tasks; no real account/model benchmark was possible without a key.

Current official sources:

- https://console.groq.com/docs/structured-outputs
- https://console.groq.com/docs/model/openai/gpt-oss-120b
- https://console.groq.com/docs/model/openai/gpt-oss-20b
- https://console.groq.com/docs/models
- https://console.groq.com/docs/rate-limits
- https://console.groq.com/docs/reasoning
- https://developers.openai.com/api/docs/models/gpt-5-mini

The published Groq rate-limit reference shows example/base limits; **account-specific quota and free-tier availability are not guaranteed**. Check the limits page at https://console.groq.com/settings/limits and test a live request. A per-request setup can create **three** concurrent requests. You may receive an HTTP 429 or billing/model-access error. The app handles these individually by labelling the substitution and continuing. Max two attempts per agent on temporary rate limits/network failure. `GROQ_TIMEOUT_SECONDS=18` applies to each attempt; the overall request is not promised to finish within a fixed few seconds.

## Actual verification and performance boundaries

**Executed** on Python 3.13:

```text
python -m pytest -q
37 passed in 0.54s
```

A local fixture-only backend request and standalone engine runs also succeeded. Backend timing varies by machine; response `timings.total_ms` is captured with `time.perf_counter`, not estimated from model generation speed. A concurrency unit test injected 110ms delays per agent and verified the calls completed faster than the approximate 330ms sequential baseline. This checks Python scheduling, **not real Groq latency**.

**Not executed**: genuine Groq API call (no key supplied); a Vite browser build (npm registry DNS failure); visual UI verification in a real browser; real construction-model validation. The next required pre-demo check is to run `npm ci; npm run build` and one `Live agents` invocation on the actual machine/account.

## List of changed files

| File | Change |
| --- | --- |
| `app/agents.py` | Groq strict schema API, differentiated prompts, concurrent calls, source/timing tracking, fallback fixture and exhaustive hybrid |
| `app/engine.py` | Corrected price spike, multiplicative energy, water/energy metrics, water constraint, retained deterministic scoring |
| `app/reference_data.py` | Fixed health-centre demo preset, water limit, explicit illustrative input |
| `app/schemas.py` | Strict Proposal checks, added trade-offs, metadata and latency/traceability schema |
| `app/main.py` | Updated endpoints, short tagged live cache, latency, deliberate integrity control |
| `frontend/src/App.jsx` | Competition dashboard, modes, scenario reset, leaderboard, stress comparison, recomputed hybrid, audit panel |
| `frontend/src/components/AgentCard.jsx` | Attribution/latency, trade-offs, violations and claim detail |
| `frontend/src/components/ProblemForm.jsx` | Water limit field and new form style |
| `frontend/src/styles.css` | Responsive, presentation-ready visual system |
| `frontend/src/format.js` | Hybrid chart palette |
| `frontend/src/api.js` | Mode/refresh APIs and useful error details |
| `frontend/src/components/Synthesis.jsx` | Removed unused legacy view; synthesis now renders directly in the dashboard |
| `requirements.txt` | Removed Gemini dependency; reused HTTPX already present |
| `.env.example` | Groq credentials, model and timeout |
| `tests/test_engine.py` | Scoring and deterministic-contract tests |
| `tests/test_api.py` | Expanded API, concurrency, fallback, cache and provider error tests |
| `README.md` | Windows setup, app use, all commands, limits and formulas |
| `docs/*` | Audit, provider comparison, scripts and disclosure guidance |

## Design trade-offs and outstanding risks

- Reference data has no domain/region certification; quantitative outputs **must** be presented as demonstrative.
- Energy/carbon savings use multiplicative combining rather than independent physical modeling. Roof combinations are simplified, not a complete engineering compatibility matrix.
- The 0–10 resilience index saturates and cannot establish 72-hour medical power availability, structural safety or compliance.
- Water is a hard illustrative threshold rather than a weighted score to avoid adding an unsupported duplicate dimension.
- The hybrid's exhaustive search is practical only because this demo has 8 available features. With large catalogues use bounded search or an integer-programming formulation.
- A global lock serializes backend runs across different users. Appropriate for a one-machine demo, not a scalable distributed deployment. Cache is memory-only, short TTL, no persistence or multi-process coordination.
- Model completions are schema-constrained but may still select impractical materials. JSON compliance does not establish engineering correctness. Invalid selections fall back rather than being repaired indefinitely.
- The UI currently waits for the full batch; it does not stream per-agent completed results. Do not describe the loading spinner as actual individual progress.
