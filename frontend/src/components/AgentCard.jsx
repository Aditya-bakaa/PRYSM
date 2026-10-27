import { useState } from 'react';
import ScoreBar from './ScoreBar.jsx';
import { colorFor, fmt, inr, pretty } from '../format.js';
const DISPLAY_ROLES = { CostOptimizer: 'THE ECONOMIST', GreenAdvocate: 'THE ENVIRONMENTALIST', ResilienceGuardian: 'THE GUARDIAN' };
export default function AgentCard({evaluation:e, isWinner, timing}) {
  const [open,setOpen] = useState(false);
  const col = colorFor(e.agent_name);
  const m = e.baseline_metrics;
  return <article className={`card ${isWinner ? 'winner' : ''}`} style={{'--agent':col}}>
    <div className="agent-title"><div className="agent-symbol" style={{color:col}}>{e.agent_name === 'CostOptimizer' ? '₹' : e.agent_name === 'GreenAdvocate' ? '◇' : '⬡'}</div><div><div className="tiny muted">{DISPLAY_ROLES[e.agent_name] || e.agent_name}</div><h3>{e.agent_name}</h3></div><span className="rank">#{e.rank}</span></div>
    <div className="agent-meta"><span className={`source ${timing?.source || 'fixture'}`}>{timing?.source || 'fixture'}</span><span>{timing ? `${fmt(timing.latency_ms)} ms` : ''}</span>{isWinner && <span className="good">TOP RANKED</span>}</div>
    <p className="agent-description">{e.proposal.summary}</p>
    <div className="chip-row"><span className="chip strong">{pretty(e.proposal.material)}</span>{e.proposal.features.map(f=><span key={f} className="chip">{pretty(f)}</span>)}</div>
    <div className="agent-score-row"><div><div className="tiny muted">EVALUATED SCORE</div><strong style={{color:col}}>{fmt(e.final_score)}</strong><span>/100</span></div><div className="agent-price"><div className="tiny muted">CONSTRUCTION COST</div><strong>{inr(m.total_cost)}</strong></div></div>
    <ScoreBar label="Cost efficiency" value={e.sub_scores.cost} color={col}/><ScoreBar label="Carbon efficiency" value={e.sub_scores.carbon} color={col}/><ScoreBar label="Resilience" value={e.sub_scores.resilience} color={col}/>
    <div className="tradeoffs"><div><small>ACCEPT</small><p>{e.proposal.accepted_tradeoff || 'No explicit trade-off given'}</p></div><div><small>REFUSES</small><p>{e.proposal.refused_tradeoff || 'No explicit trade-off given'}</p></div></div>
    <div className="card-foot"><span className={e.constraints_violated.length ? 'bad' : 'good'}>{e.constraints_violated.length ? `${e.constraints_violated.length} constraint breach(es)` : 'Baseline constraints met'}</span><button className="text-button" onClick={()=>setOpen(!open)}>{open ? 'Hide detail −' : 'Inspect details +'}</button></div>
    {open && <div className="card-detail"><div><strong>Worst-case score:</strong> {fmt(e.worst_case_score)} · <strong>Integrity penalty:</strong> {e.integrity_penalty}</div><div><strong>Baseline metrics:</strong> {fmt(m.lifetime_carbon_per_m2,0)} kgCO₂e/m² · {m.resilience}/10 resilience</div>{e.constraints_violated.length>0 && <div className="bad">{e.constraints_violated.map(pretty).join(', ')}</div>}{timing?.note && <div className="muted">{timing.note}</div>}<div>{e.claim_checks.length ? e.claim_checks.map(c=><div key={c.metric}>{pretty(c.metric)}: claimed {fmt(c.claimed)}, computed {fmt(c.actual)} — {c.verified ? 'verified' : 'incorrect'}</div>) : 'No numerical claims supplied by this proposal.'}</div></div>}
  </article>;
}
