import { useEffect, useRef, useState } from 'react';
import { getHealth, getIntegrityDemo, getReference, runArena } from './api.js';
import AgentCard from './components/AgentCard.jsx';
import ProblemForm from './components/ProblemForm.jsx';
import RadarChart from './components/RadarChart.jsx';
import { colorFor, fmt, inr, pretty } from './format.js';

const hazardNames = ['material_price_spike', 'heatwave', 'flood', 'earthquake', 'grid_outage'];

export default function App() {
  const [problem, setProblem] = useState(null);
  const [preset, setPreset] = useState(null);
  const [health, setHealth] = useState(null);
  const [reference, setReference] = useState(null);
  const [mode, setMode] = useState('demo');
  const [result, setResult] = useState(null);
  const [integrity, setIntegrity] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const runGuard = useRef(false);

  useEffect(() => {
    Promise.all([getReference(), getHealth(), getIntegrityDemo()])
      .then(([ref, status, check]) => {
        setReference(ref); setPreset(ref.default_problem); setProblem(ref.default_problem);
        setHealth(status); setIntegrity(check);
      })
      .catch((err) => setError(`Cannot connect to FastAPI at port 8000. ${err.message}`));
  }, []);

  async function run(refresh = false) {
    if (runGuard.current || !problem) return;
    runGuard.current = true; setBusy(true); setError(''); setResult(null);
    try { setResult(await runArena(problem, mode, refresh)); }
    catch (e) { setError(`Run failed: ${e.message}`); }
    finally { setBusy(false); runGuard.current = false; }
  }

  const ordered = result ? [...result.evaluations] : [];
  const currentTimes = Object.fromEntries((result?.timings.agents || []).map(a => [a.agent_name, a]));
  const modeTag = result?.cached ? 'Cached run (see agent source)' : result?.mode === 'demo' ? 'Fixture-backed demo' :
    result?.used_live_llm ? (result.timings.agents.some(a => a.source !== 'live') ? 'Mixed live / fallback' : 'Live Groq API') : 'Fallback only';
  const hybrid = result?.synthesis.hybrid_evaluation;
  const winner = result?.evaluations[0];

  return (
    <>
      <header className="topbar">
        <div className="brand"><span className="brand-mark">A<span>·</span></span><strong>AGENT <em>ARENA</em></strong><span className="top-divider"/><span className="tiny muted">BUILDING DECISION LAB</span></div>
        <div className="header-right"><span className="status-dot"/> {health ? 'ENGINE ONLINE' : 'CONNECTING'} <span className="top-divider"/> <span>v1.0 / PROTOTYPE</span></div>
      </header>
      <main>
        <section className="hero">
          <div className="eyebrow">MULTI-AGENT DECISION INTELLIGENCE <span className="rule" /></div>
          <h1>Better buildings start<br/>with <span>better arguments.</span></h1>
          <p>Three competing AI design perspectives. One independent scoring engine. Every assumption under pressure.</p>
          <div className="process"><span>01 <b>AI PROPOSES</b></span><i>→</i><span>02 <b>MATH VERIFIES</b></span><i>→</i><span>03 <b>STRESS TESTS DECIDE</b></span></div>
        </section>

        <section className="workbench panel">
          <div className="section-top"><div><div className="eyebrow">01 / CONFIGURATION</div><h2>Run a design challenge</h2></div><button className="text-button" onClick={() => { setProblem({...preset}); setResult(null); setError(''); }} disabled={!preset || busy}>↺ Reset to demo scenario</button></div>
          <div className="work-grid">
            <div className="config-left">{problem && <ProblemForm problem={problem} onChange={(next) => {setProblem(next); setResult(null);}} />}</div>
            <div className="config-right">
              <div className="muted tiny">EXECUTION MODE</div>
              <div className="mode-stack">
                <button className={`mode-option ${mode === 'demo' ? 'selected' : ''}`} onClick={() => setMode('demo')} disabled={busy}><span className="mode-icon">◉</span><span><strong>Safe demo</strong><small>Instant · Deterministic proposals · No key needed</small></span><span className="mode-radio">{mode === 'demo' ? '●' : '○'}</span></button>
                <button className={`mode-option ${mode === 'live' ? 'selected' : ''}`} onClick={() => setMode('live')} disabled={busy}><span className="mode-icon">⌁</span><span><strong>Live agents</strong><small>Three concurrent Groq requests · Fallback on errors</small></span><span className="mode-radio">{mode === 'live' ? '●' : '○'}</span></button>
              </div>
              <div className="key-status">Groq key <b className={health?.llm_configured ? 'good' : 'muted'}>{health?.llm_configured ? 'CONFIGURED' : 'NOT CONFIGURED'}</b><span className="muted">{health?.model || ''}</span></div>
              <button className="primary-button" disabled={busy || !problem} onClick={() => run()}>{busy ? 'Processing competition…' : 'Start competition'} <span>↗</span></button>
              {result && mode === 'live' && <button className="text-button" onClick={() => run(true)} disabled={busy}>Force fresh model calls ↻</button>}
              <p className="tiny muted centered">Fixture and fallback outputs are explicitly labelled. All metrics are recomputed.</p>
            </div>
          </div>
          {busy && <div className="progress-panel" role="status"><span className="spinner"/> <div><strong>{mode === 'demo' ? 'Evaluating deterministic demo…' : 'Awaiting concurrent model requests…'}</strong><small>Individual statuses are reported after the API completes; no simulated progress.</small></div></div>}
          {error && <div className="error" role="alert">{error} <button onClick={() => run(true)} disabled={busy}>Retry</button><button onClick={() => {setMode('demo'); setError('')}}>Switch to safe demo</button></div>}
        </section>

        {!result && !busy && <section className="empty-state"><div className="empty-circuit">A / A / A</div><strong>Ready to challenge the assumptions.</strong><p>Load the predefined health-centre scenario and run the competition to reveal the leaderboard, trade-offs and stress tests.</p></section>}

        {result && <>
          <section className="results-head"><div><div className="eyebrow">02 / COMPETITION RESULTS</div><h2>Decision overview</h2><p>Independent evaluation of all three proposals, using the same formula.</p></div><span className="run-label">{modeTag}</span></section>
          <div className="metric-strip"><div><small>WINNING AGENT</small><strong style={{color: colorFor(winner.agent_name)}}>{winner.agent_name}</strong></div><div><small>WINNING SCORE</small><strong>{fmt(winner.final_score)}<span>/100</span></strong></div><div><small>HYBRID SCORE</small><strong>{fmt(hybrid.final_score)}<span>/100</span></strong></div><div><small>ORIGINAL EXECUTION</small><strong>{fmt(result.timings.total_ms, 0)}<span> ms</span></strong></div></div>
          {result.notes.length > 0 && <div className="notice">{result.notes.join(' ')}</div>}
          <div className="section-top after-strip"><div><div className="eyebrow">THE CONTENDERS</div><h2>Three priorities. Three approaches.</h2></div><span className="tiny muted">Ranked by stress-adjusted score</span></div>
          <div className="agent-grid">{ordered.map(e => <AgentCard key={e.agent_name} evaluation={e} timing={currentTimes[e.agent_name]} isWinner={e.rank === 1} />)}</div>
          <div className="analysis-grid">
            <section className="panel"><div className="eyebrow">03 / COMPARISON</div><h2>Numbers behind the ranking</h2><div className="scroll-table"><table className="comparison"><thead><tr><th>DESIGN</th><th>SCORE</th><th>COST</th><th>CARBON kg/m²</th><th>ENERGY kWh/m²/yr</th><th>WATER m³/m²/yr</th><th>RESILIENCE</th></tr></thead><tbody>{[...result.evaluations,hybrid].map(e => <tr key={e.agent_name}><td><b style={{color: colorFor(e.agent_name)}}>{e.agent_name}</b></td><td><strong>{fmt(e.final_score)}</strong></td><td>{inr(e.baseline_metrics.total_cost)}</td><td>{fmt(e.baseline_metrics.lifetime_carbon_per_m2, 0)}</td><td>{fmt(e.baseline_metrics.annual_energy_kwh_per_m2)}</td><td>{fmt(e.baseline_metrics.annual_water_m3_per_m2, 2)}</td><td>{e.baseline_metrics.resilience}/10</td></tr>)}</tbody></table></div><p className="small muted">Cost, carbon and resilience determine the score. Energy contributes to carbon; water is shown separately to avoid double counting.</p></section>
            <section className="panel radar-panel"><div className="eyebrow">SCORE PROFILE</div><h2>Normalized dimensions</h2><RadarChart evaluations={result.evaluations} /><div className="legend">{ordered.map(e => <span key={e.agent_name}><i style={{background:colorFor(e.agent_name)}} />{e.agent_name}</span>)}</div></section>
          </div>
          <section className="panel"><div className="eyebrow">04 / STRESS ENGINE</div><div className="section-top"><h2>How the designs hold up</h2><span className="small muted">Scenario score / 100. Lower is worse.</span></div><div className="scroll-table"><table className="stress-table"><thead><tr><th>STRESS TEST</th>{[...ordered,hybrid].map(e=><th key={e.agent_name} style={{color:colorFor(e.agent_name)}}>{e.agent_name}</th>)}</tr></thead><tbody>{hazardNames.map(s=><tr key={s}><td>{pretty(s)}</td>{[...ordered,hybrid].map(e=>{const test=e.scenario_results.find(x=>x.scenario===s);return <td key={e.agent_name}><span className={`stress-value ${test.constraints_violated.length ? 'stress-bad' : ''}`}>{fmt(test.score)}</span> {test.constraints_violated.length > 0 && <span className="bad" title={test.constraints_violated.map(pretty).join(', ')}>!</span>}{test.constraints_violated.length > 0 && <small className="violation-list">{test.constraints_violated.map(pretty).join(' · ')}</small>}</td>})}</tr>)}</tbody></table></div><p className="small muted">! indicates a breached constraint in that scenario. Stress scores include fixed penalties for budget, carbon and resilience limits.</p></section>
          <section className="hybrid-section"><div className="eyebrow">05 / DETERMINISTIC SYNTHESIS</div><h2>Build the strongest combination.</h2><div className="hybrid-grid"><div className="panel"><div className="tiny muted">HYBRID EVALUATED SCORE</div><div className="large-score">{fmt(hybrid.final_score)}<span> / 100</span></div><p>{result.synthesis.explanation}</p><div className="chips"><span className="chip strong">{pretty(hybrid.proposal.material)}</span>{hybrid.proposal.features.map(f=><span className="chip" key={f}>{pretty(f)}</span>)}</div>{hybrid.constraints_violated.length > 0 && <div className="bad">Baseline constraints: {hybrid.constraints_violated.map(pretty).join(', ')}</div>}</div><div className="panel"><div className="eyebrow">HOW IT'S BUILT</div><h3>Search. Recompute. Compare.</h3><p>The engine searches combinations of materials and features offered by the three agents, enforces the roof exclusivity rule and evaluates each candidate using the identical six-scenario engine.</p><p>No LLM picks a winner. The hybrid is scored independently and may perform worse than the leading agent when baseline feasibility takes priority.</p><div className="formula">FINAL = 0.6 × SCENARIO MEAN + 0.4 × WORST − CLAIM PENALTIES</div></div></div></section>
          <section className="panel integrity"><div className="eyebrow">06 / CLAIM INTEGRITY CONTROL</div><h2>When an agent's numbers don't add up.</h2><p className="muted small">Separate deliberate test, unrelated to the competing agents. Identical design, only the claimed construction cost changes.</p>{integrity && <div className="integrity-grid"><div><div className="tiny muted">HONEST COST CLAIM</div><strong>{inr(integrity.honest.claim_checks[0].claimed)}</strong><span className="good">Verified · penalty {integrity.honest.integrity_penalty}</span></div><div><div className="tiny muted">FALSE COST CLAIM</div><strong>{inr(integrity.false.claim_checks[0].claimed)}</strong><span className="bad">Actual {inr(integrity.false.claim_checks[0].actual)} · −{integrity.false.integrity_penalty} points</span></div><div><div className="tiny muted">SCORE IMPACT</div><strong>−{fmt(integrity.honest.final_score - integrity.false.final_score)}</strong><span className="muted small">Engine-determined penalty</span></div></div>}</section>
          <section className="panel transparency"><div><div className="eyebrow">AUDITABLE BY DESIGN</div><h2>What these numbers represent</h2><p>Catalogue prices and carbon factors are illustrative. Energy uses a 30-year operational horizon; water reduction assumes a fixed rainwater-harvesting factor. Hazards use simplified score adjustments, not a physical or code-compliant safety model.</p></div><div className="audit-grid"><div><span className="muted tiny">WEIGHTS</span><strong>30% cost · 30% carbon · 40% resilience</strong></div><div><span className="muted tiny">CONSTRAINT VIOLATION</span><strong>−10 per scenario</strong></div><div><span className="muted tiny">INCORRECT CLAIM</span><strong>−8 per claim (max −24)</strong></div><div><span className="muted tiny">RUNTIME BREAKDOWN</span><strong>Eval {fmt(result.timings.evaluation_ms)}ms · hybrid {fmt(result.timings.hybrid_ms)}ms</strong></div></div></section>
        </>}
        <footer>AGENT ARENA <span>·</span> RESEARCH PROTOTYPE <span>·</span> NOT FOR ENGINEERING DESIGN APPROVAL</footer>
      </main>
    </>
  );
}
