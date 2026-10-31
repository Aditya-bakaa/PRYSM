# PRYSM

### Multi-agent AI for sustainable building decisions

**AI proposes. Mathematics verifies. Stress tests decide.**

PRYSM is an experimental, multi-agent decision-support prototype for exploring trade-offs in sustainable building design. Three specialised AI agents independently propose building materials and features from a controlled catalogue. A deterministic Python evaluation engine then scores every proposal against the same cost, carbon, resilience and constraint rules, tests it across six scenarios, ranks the proposals and searches for a recomputed hybrid design.

PRYSM is designed to make competing priorities and trade-offs visible—not to replace architects, structural engineers, quantity surveyors or building-code review.

> **Important limitation:** The catalogue, cost assumptions, emissions factors, energy and water estimates, resilience points and scenario adjustments are illustrative. They are not calibrated or validated engineering predictions. PRYSM must not be used to certify structural safety, establish code compliance, approve construction, or produce reliable real-world cost estimates.

---

## At a glance

- **Three specialised agents:** CostOptimizer, GreenAdvocate and ResilienceGuardian.
- **Concurrent proposals:** In live mode, the three agents make independent Groq requests concurrently.
- **Structured outputs:** The model is asked for strict JSON Schema output, which is validated with Pydantic.
- **Independent evaluation:** Python—not the language model—calculates metrics, checks constraints and determines rankings.
- **Six stress scenarios:** Normal conditions, material price shock, heatwave, flood, earthquake and a 72-hour grid outage.
- **Hybrid search:** The backend explores combinations of agent-proposed materials and features, then evaluates the selected hybrid from scratch.
- **Transparent source labels:** The interface distinguishes live responses, safe-demo fixtures and fallback fixtures.
- **Claim-integrity demonstration:** A separate control compares an asserted numerical claim with the engine's computed value and applies a penalty when the deviation exceeds the configured tolerance.

## How PRYSM works

```text
User defines a building challenge
              |
              v
       React + Vite UI
              |
              v
        FastAPI backend
              |
       +------+------+
       |      |      |
       v      v      v
     Cost   Green  Resilience
    Optimizer Advocate Guardian
       |      |      |
       +------+------+
              |
     Structured proposals
      (Groq in live mode;
       fixtures in demo/fallback)
              |
              v
    Pydantic validation
              |
              v
 Deterministic Python engine
              |
    +---------+----------+
    |         |          |
    v         v          v
  Metrics  Constraints  Six scenario
                       evaluations
    |         |          |
    +---------+----------+
              |
              v
     Ranking + hybrid search
              |
              v
       Dashboard results
```

### The three agents

| Agent | Primary perspective | Typical trade-off |
|---|---|---|
| **CostOptimizer** | Minimise capital cost while avoiding unacceptable flood and outage risks | May accept lower resilience during extended outages to control upfront cost |
| **GreenAdvocate** | Reduce embodied and operational carbon | May accept a higher initial cost for lower modelled lifetime emissions |
| **ResilienceGuardian** | Improve performance under floods, heatwaves, earthquakes and grid outages | May accept higher cost and embodied carbon for additional protective features |

The agents are specialised proposal generators. Their outputs are not treated as verified facts: the backend validates their structure and independently evaluates the selected catalogue options.

### Six evaluation scenarios

Each proposal is assessed under the same six scenarios:

1. **Normal conditions**
2. **25% base-material price shock**
3. **Heatwave**
4. **Flood**
5. **Earthquake**
6. **72-hour grid outage**

The scenario adjustments are simplified assumptions in the reference catalogue. They are not physical simulations or engineering hazard models.

### Scoring model

The current weighted score uses:

| Dimension | Weight |
|---|---:|
| Cost | 30% |
| Carbon | 30% |
| Resilience | 40% |

A constraint violation incurs a 10-point penalty in that scenario. The overall stress score combines **60% of the mean scenario score** with **40% of the worst-case scenario score**. The final score then subtracts any applicable claim-integrity penalty and is bounded between 0 and 100.

An optional numerical claim is checked against the engine's computed baseline metric. A deviation greater than 5% is treated as unverified and incurs an 8-point penalty, capped at 24 points. Energy is reflected in the operational-carbon estimate; water is displayed and checked as a constraint rather than added again as a weighted scoring dimension.

### Hybrid design

After ranking the three proposals, PRYSM searches combinations of the materials and features proposed by those agents. It excludes the incompatible combination of `green_roof` and `cool_roof_coating`, prioritises baseline-feasible candidates, and compares candidates using the same stress evaluation. The chosen hybrid has no inherited agent claims and is evaluated again independently.

The hybrid is **not guaranteed to beat the highest-ranked agent**. It is a search over the options proposed in that run, not an unrestricted building-design optimiser.

---

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite 5, JavaScript, CSS |
| Backend | Python, FastAPI, Uvicorn |
| AI provider | Groq API, OpenAI-compatible chat completions endpoint |
| Default model | `openai/gpt-oss-120b` (configurable with `GROQ_MODEL`) |
| Validation | Pydantic v2 and strict JSON Schema response format |
| Concurrent requests | Python `ThreadPoolExecutor` (three workers) |
| HTTP client | HTTPX |
| Tests | Pytest and HTTPX test client |

The API key is read by the backend only; it is not sent to the browser.

---

## Getting started

### Prerequisites

- Python **3.11 or newer**
- Node.js **20 or newer** and npm
- Windows, macOS or Linux

Open the extracted `PRYSM` project folder in VS Code or a terminal. The folder should contain `requirements.txt`, `app/` and `frontend/`.

### 1. Set up the backend

**Windows PowerShell:**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

If PowerShell blocks virtual-environment activation, run this in the same terminal and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

The backend health endpoint is available at `http://127.0.0.1:8000/api/health`.

### 2. Set up the frontend

Open a second terminal in the project root:

```bash
cd frontend
npm ci
npm run dev
```

Open **http://localhost:5173**. During development, Vite proxies `/api` requests to the backend on port 8000. Keep both terminals running.

---

## Run PRYSM in Safe Demo mode

Safe Demo mode does not require a Groq API key and does not make model requests.

1. Open the frontend at `http://localhost:5173`.
2. Select **Safe demo** mode.
3. Click **Reset to demo scenario** to load the illustrative 800 m² community health-centre scenario.
4. Click **Start competition**.
5. Confirm that agent proposals are labelled **FIXTURE**.
6. Explore the agent cards, comparison metrics, leaderboard, six-scenario stress results, hybrid evaluation and separate claim-integrity control.

The proposals are fixed illustrative fixtures, but the metrics, constraint checks, scenario scores, ranking and hybrid evaluation are computed by the backend engine for the selected input. Scores and winners are not hardcoded demo results.

---

## Configure Live mode (Groq)

Live mode asks Groq to generate the three agent proposals. A working API key and model access are required.

1. Create or access a Groq API key at <https://console.groq.com/keys>.
2. Open the project-root `.env` file and set:

```dotenv
GROQ_API_KEY=your_actual_key_here
GROQ_MODEL=openai/gpt-oss-120b
GROQ_TIMEOUT_SECONDS=18
```

3. Restart the backend after changing `.env`.
4. Check `http://127.0.0.1:8000/api/health`. `llm_configured: true` confirms that a key is present; it does **not** prove that the key or model can successfully complete a request.
5. In the UI, select **Live agents** and click **Start competition**.
6. Verify that each agent card reports **LIVE**. If a request fails, the affected agent is visibly labelled **FALLBACK** and uses its fixture proposal.
7. Use **Force fresh model calls** to bypass the 45-second live-result cache.

The default model must be available to your Groq account and support the strict JSON Schema response format used by this project. The backend makes up to two attempts for selected transient network/provider failures. Missing keys, access errors, rate limits, timeouts or invalid responses can result in a clearly labelled fixture fallback.

**Security:** Keep `.env` private. Never commit or share a real API key. The supplied `.env.example` contains an empty key placeholder.

**Development verification note:** Live Groq inference was not verified in the environment used to prepare this repository because no working API key was supplied. Verify Live mode with your own account before presenting it as a live integration.

---

## Build and serve the frontend from FastAPI (optional)

From the project root:

```bash
cd frontend
npm ci
npm run build
cd ..
python -m uvicorn app.main:app --port 8000
```

Then open **http://localhost:8000**. Build the frontend before starting FastAPI; the backend checks for built frontend assets when the app is imported. For development, the two-terminal Vite setup is recommended.

---

## Run the tests

From the project root, with the Python virtual environment active:

```bash
python -m pytest -q
```

**Recorded test result in the development environment:** 37 Python tests passed (Python 3.13). These cover the Python engine and API behaviour, including validation and mocked execution paths. They do not establish live Groq integration, frontend production-build success, browser rendering quality or real-world engineering validity.

The frontend build could not be verified in that environment because npm could not reach `registry.npmjs.org` (DNS `EAI_AGAIN`). Run `npm ci` and `npm run build` on a machine with npm registry access before the hackathon. Actual live-provider latency and account quotas are also unverified.

---

## Default illustrative demo scenario

| Input | Default value |
|---|---:|
| Project | Flood-ready community health centre (demo description) |
| Floor area | 800 m² |
| Approximate daily patient capacity | 40 (descriptive only; not used in calculations) |
| Budget | ₹22,000,000 |
| Maximum lifetime carbon | 2,500 kgCO₂e/m² |
| Minimum resilience | 6 / 10 |
| Annual water limit | 1.0 m³/m²/year |
| Hazards | Seasonal flood, heatwave, moderate earthquake and grid outage |
| Operational-carbon horizon | 30 years |

The material and feature catalogue is intentionally static and illustrative. See `app/reference_data.py` for the source values and scenario adjustments.

## Calculation assumptions and limitations

The engine is deterministic, but its inputs are simplified assumptions:

- Construction cost is calculated from catalogue material and feature costs per square metre, multiplied by floor area. The price-shock scenario changes base-material cost only.
- Embodied carbon is combined with estimated operational carbon over a 30-year horizon.
- The model uses a fixed baseline energy intensity and baseline operational-carbon intensity. Feature energy savings are combined multiplicatively and capped at a maximum 60% reduction; heatwave conditions increase the modelled operating load.
- Rainwater harvesting applies a fixed illustrative reduction to baseline water intensity.
- Resilience starts from catalogue material points, adds feature effects and subtracts scenario-specific penalties, then is bounded to a 0–10 index.
- The catalogue does not model structural calculations, material compatibility, local building codes, detailed hazard loads, equipment sizing, location-specific utility tariffs, replacement schedules or uncertainty ranges.
- The material `lifespan_years` reference field is not currently included in the carbon calculation.

Resilience is an illustrative index, not a safety forecast. A simulated 72-hour outage does not prove that a real building can maintain services for 72 hours. The health-centre patient-capacity description is not used in the calculations.

## API reference

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Backend status and whether a Groq key is configured (the key itself is never returned) |
| `GET` | `/api/reference` | Default input, catalogue, scenarios, weights and assumptions |
| `POST` | `/api/arena/run` | Run Safe Demo or Live agents, evaluate proposals and return ranking plus hybrid result |
| `POST` | `/api/evaluate` | Evaluate a supplied proposal against the default demo problem |
| `GET` | `/api/integrity-demo` | Compare an honest and deliberately inaccurate claim on the same example design; this is a separate demonstration, not agent output |

The `/api/arena/run` route name is retained in the current API implementation; the product and user-facing project name is **PRYSM**.

## Repository structure

```text
PRYSM/
├── app/
│   ├── agents.py           # Groq calls, concurrent agents, fixtures and hybrid search
│   ├── engine.py           # Deterministic metrics, constraints, scoring and ranking
│   ├── main.py             # FastAPI routes, cache and timing metadata
│   ├── reference_data.py   # Illustrative materials, features and scenarios
│   └── schemas.py          # Pydantic request and response models
├── frontend/
│   ├── src/
│   │   ├── components/     # Form, agent cards, radar chart and score bars
│   │   ├── App.jsx         # Main dashboard
│   │   ├── api.js          # Backend API client
│   │   ├── format.js       # Display formatting and agent colours
│   │   └── styles.css      # Dashboard styling
│   ├── package.json
│   └── vite.config.js
├── tests/
│   ├── test_api.py         # API and integration-style tests
│   └── test_engine.py      # Evaluation-engine tests
├── docs/
│   ├── AUDIT_AND_DECISIONS.md
│   └── DEMO_PLAYBOOK.md
├── .env.example
├── requirements.txt
└── README.md
```

## Demo and judging guidance

For a reliable presentation, rehearse the Safe Demo flow first and verify Live mode separately using your own Groq credentials. Be transparent about whether each agent response is live, fixture-backed, cached or fallback output.

Do not describe PRYSM's illustrative outputs as verified construction estimates, certified structural designs, guaranteed carbon savings, flood-proofing, seismic safety or guaranteed 72-hour service continuity. The project's value is its transparent demonstration of competing design priorities, deterministic evaluation and scenario-based comparison.

For a timed demo script, backup plan and likely judge questions, see [`docs/DEMO_PLAYBOOK.md`](docs/DEMO_PLAYBOOK.md). For design decisions and audit notes, see [`docs/AUDIT_AND_DECISIONS.md`](docs/AUDIT_AND_DECISIONS.md).
