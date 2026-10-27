import { fmt } from "../format.js";

export default function ScoreBar({ label, value, color }) {
  return (
    <div className="scorebar">
      <div className="scorebar-top">
        <span>{label}</span>
        <span>{fmt(value)}</span>
      </div>
      <div className="bar">
        <i style={{ width: `${Math.max(0, Math.min(100, value))}%`, background: color }} />
      </div>
    </div>
  );
}
