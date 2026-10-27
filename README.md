# AGENT ARENA — Hackathon Edition

**AI proposes. Mathematics verifies. Stress tests decide.**

A React/Vite + FastAPI decision-support prototype for illustrative sustainable building decisions. Three independent Groq-backed agents select catalogue materials and design features. A deterministic engine computes scenario scores, checks optional numerical claims, ranks agents and independently searches a hybrid design. A fixture-backed safe demo works without an API key.

**Important:** Costs, emissions factors, stress deltas, water and energy savings, and resilience points are **illustrative assumptions**. This system is not validated for real buildings, planning consent, structural safety or construction cost estimation.

## Windows 11 + VS Code setup (PowerShell)

Install **Python 3.11 or newer** and **Node.js 20 or newer** with npm. Unzip the project. In VS Code, select **File → Open Folder** and open `agent-arena` (the folder containing `requirements.txt` and `frontend`).

**Terminal 1 — backend:**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

If PowerShell refuses activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again. Ensure the backend is running at `http://127.0.0.1:8000/api/health`.

**Terminal 2 — frontend (new VS Code terminal in the project root):**

```powershell
cd frontend
npm ci
npm run dev
```

Open **http://localhost:5173**. Vite proxies `/api` to the backend at port 8000. Keep both terminals open.

### SAFE DEMO MODE — no key required

1. Leave the default **Safe demo** mode selected (or click **Safe demo**).
2. Click **Reset to demo scenario** to load the fixed illustrative 800 m² health centre.
3. Click **Start competition**. The fixture-backed proposals are visibly marked **FIXTURE**. No Groq request is made.
4. Show the agent cards, leaderboard metrics, five stress scenarios, recomputed hybrid, and the separate **Claim integrity control**.
5. The backend computes everything, including the winner; no demo score or winner is hardcoded.

### LIVE MODE — Groq setup

1. Create a Groq account and API key at https://console.groq.com/keys.
2. Stop the backend server and open the project-root `.env` file (do not commit it):

```dotenv
GROQ_API_KEY=your_actual_key_here
GROQ_MODEL=openai/gpt-oss-120b
GROQ_TIMEOUT_SECONDS=18
```

3. Restart the backend. `/api/health` should report `"llm_configured": true`. This only checks presence of the key, not whether it works.
4. **Verify your model is listed for the key** from a backend terminal (with venv active):

```powershell
python -c "import os,httpx;from dotenv import load_dotenv;load_dotenv();r=httpx.get('https://api.groq.com/openai/v1/models',headers={'Authorization':'Bearer '+os.environ['GROQ_API_KEY']},timeout=10);r.raise_for_status();print('model listed:',any(m['id']==os.getenv('GROQ_MODEL','openai/gpt-oss-120b') for m in r.json()['data']))"
```

5. In the UI select **Live agents**, click **Start competition**, and confirm each card says **LIVE**. This is the real account-specific verification. A missing key, model denial, 429 or timeout produces visibly labelled **FALLBACK** fixture output for affected agents; it never impersonates a live result. Use **Force fresh model calls** to bypass the 45-second live-result cache.
6. Watch backend-only per-agent latencies and total compute duration in the UI. These exclude browser render and round-trip network time.

The provider endpoint and model selection are backend-only. API keys are never sent to the browser. We could not run live inference during development because no `GROQ_API_KEY` was supplied. `GROQ_MODEL` can be changed, but the model must support **strict JSON Schema** and the configured reasoning parameters. The default model currently does.

### Run a single backend-served frontend

```powershell
cd frontend
npm ci
npm run build
cd ..
python -m uvicorn app.main:app --port 8000
```

Now open http://localhost:8000. Build the frontend **before** starting the server (assets are detected at import time). The development setup above is preferred for quick changes.

### Tests

```powershell
python -m pytest -q
```

**Results in this coding environment:** 37 passed in 0.54 seconds, Python 3.13; the complete Python API/test suite executed. Frontend build could **not** be verified here: `npm ci` could not reach `registry.npmjs.org` (DNS `EAI_AGAIN`) and `vite` was therefore unavailable. On a Windows machine with npm network access, run `npm ci; npm run build` before judging. Actual live Groq latency, account quotas, and visual rendering have **not** been verified. Do not claim otherwise.

## Fixed illustrative health-centre input

| Field | Value |
| --- | --- |
| Scenario | Flood-ready community health centre |
| Floor area | 800 m² |
| Approximate daily patient capacity | 40 (description only; not used in calculations) |
| Budget | ₹22,000,000 |
| Maximum lifetime carbon | 2,500 kgCO₂e/m² |
| Minimum resilience | 6 / 10 |
| Annual water limit | 1.0 m³/m²/year |
| Hazards | Seasonal flood, heatwave, moderate quake, grid outage |
| Operational carbon horizon | 30 years |
| Scenarios | Normal, 25% base-material price shock, heatwave, flood, earthquake, 72h grid outage |

The catalogue values in `app/reference_data.py` are illustrative and intentionally static; this is why the same fixture scenario is reproducible.

## Transparent engine

Material cost + feature costs (₹/m²) × floor area = construction cost. Material-price shock is applied to **base material** costs only. Embodied carbon = material + add-on embodied factors. Annual baseline energy = 120 kWh/m²/year; carbon starts at 45 kgCO₂e/m²/year with a fixed illustrative electricity carbon relationship. Independent fractional feature savings combine **multiplicatively**, capped at 60%. A heatwave raises operating load by 30%. Lifetime carbon uses the 30-year operational horizon. Water baseline = 1.2 m³/m²/year; rainwater harvesting reduces it by an illustrative 25%. Resilience begins with material points, adds catalogue feature effects and subtracts stress-scenario penalties, capped at 0–10.

Scoring: **30% normalized cost + 30% normalized carbon + 40% normalized resilience**. Each violated per-scenario constraint costs 10 points. Score for each scenario is clipped to 0–100. **Stress score = 60% mean of six scenario scores + 40% worst-case score**. An optional numeric model claim off by more than 5% costs 8 points, capped at 24. Final score is stress score minus claim penalties (bounded to 0–100). Energy is reflected in carbon; water is a constraint/visible metric rather than being double-counted as a weighted score. See `app/engine.py`.

The hybrid searches all combinations of features offered by the agents across their material choices. It rejects mutually exclusive roof options, **prioritizes proposals satisfying baseline constraints**, then maximizes the same stress score. It does not inherit an agent's unsupported claims. The best hybrid can be worse than the top original on score because feasibility is prioritized. `engine.evaluate` is used for both.

## API endpoints

- `GET /api/health` — backend / Groq key configuration (without exposing key).
- `GET /api/reference` — input preset, catalogue, stress scenarios, weights and assumptions.
- `POST /api/arena/run` — accepts `{"mode":"demo"}` or `{"mode":"live","problem":{...},"refresh":true}`. Response includes ranked proposals, source attribution, latencies, hybrid and notes.
- `POST /api/evaluate` — validate/evaluate a `Proposal` against the demo problem (including numerical claims).
- `GET /api/integrity-demo` — honest and deliberately false claims on the *same* design; visibly separate from the agent competition.

## Repository map

```
app/main.py                FastAPI routes, explicit cache and telemetry
app/agents.py              Groq requests, 3-agent concurrency, fixtures, hybrid search
app/schemas.py             Input/output validation and constraints
app/reference_data.py      Illustrative reference catalogue and scenario preset
app/engine.py              Source-of-truth mathematics
frontend/src/App.jsx       Competition dashboard and mode selection
frontend/src/components/  Form, cards, radar visualization and score bars
frontend/src/styles.css    Responsive dashboard design
frontend/src/api.js        JSON API client
tests/                      Engine, HTTP routes, errors, cache and concurrency
docs/AUDIT_AND_DECISIONS.md Initial audit, model choice, prioritized changes and limitations
docs/DEMO_PLAYBOOK.md       Presentation script, backup, judge answers and claims to avoid
```

## Known limitations

Physical suitability of materials, material compatibility, real hazard loads, medical-service requirements, equipment sizing, code compliance, and location-specific tariffs are **not modeled**. Resilience is an **illustrative 0–10 index**, not a safety forecast. Simulated outages do not establish hours of actual service continuity. Water consumption is a fixed intensity estimate, not plumbing engineering. Feature energy savings are rough estimates, even after reducing double counting with multiplicative combination. The catalogue lacks life-cycle replacement schedules, uncertainty distributions and confidence intervals; the material `lifespan_years` property is shown as reference data but does not enter carbon math. Budget and feasibility apply to the illustrative factors. Groq free and developer tiers have account-specific limits; 3 parallel calls may trigger token or request caps. A simple global single-process lock serializes arena runs; cache is in memory only and resets on restart. The UI reports run-stage completion after API response (there is no streaming agent-by-agent progress).

For audit, benchmarks and presentation guidance, read `docs/`.
