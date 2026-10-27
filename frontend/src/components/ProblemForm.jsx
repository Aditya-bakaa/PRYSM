import { inr } from '../format.js';
const FIELDS = [
  ['floor_area_m2','Floor area (m²)',50], ['budget','Budget (₹)',500000],
  ['max_carbon_kg_per_m2_lifetime','Carbon limit (kgCO₂e/m²)',100], ['min_resilience','Minimum resilience (0–10)',.5],
  ['max_annual_water_m3_per_m2','Annual water limit (m³/m²)',.1],
];
export default function ProblemForm({problem, onChange}) {
  const edit = (k,v) => onChange({...problem,[k]:v});
  return <div className="problem-fields"><label className="field"><span>CHALLENGE TITLE</span><input value={problem.title} onChange={e=>edit('title',e.target.value)}/></label><label className="field"><span>DESIGN BRIEF</span><textarea rows="3" value={problem.description} onChange={e=>edit('description',e.target.value)}/></label><div className="fields">{FIELDS.map(([key,label,step])=><label className="field" key={key}><span>{label.toUpperCase()}</span><input type="number" step={step} value={problem[key]} onChange={e=>edit(key,Number(e.target.value))}/></label>)}</div><div className="muted tiny">Specified budget: {inr(problem.budget)} · All amounts use illustrative INR assumptions.</div></div>;
}
