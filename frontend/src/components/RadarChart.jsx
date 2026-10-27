import { colorFor } from "../format.js";

const AXES = [
  { key: "cost", label: "Cost" },
  { key: "carbon", label: "Carbon" },
  { key: "resilience", label: "Resilience" },
];

// Dependency-free SVG radar chart comparing agents on the three sub-scores (0-100).
export default function RadarChart({ evaluations, size = 300 }) {
  const c = size / 2;
  const r = size / 2 - 50;
  const angle = (i) => (-Math.PI / 2) + (i * 2 * Math.PI) / AXES.length;
  const point = (i, value) => {
    const rad = (value / 100) * r;
    return [c + rad * Math.cos(angle(i)), c + rad * Math.sin(angle(i))];
  };

  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="radar" role="img" aria-label="Agent score comparison">
      {[25, 50, 75, 100].map((ring) => (
        <polygon
          key={ring}
          points={AXES.map((_, i) => point(i, ring).join(",")).join(" ")}
          fill="none"
          stroke="var(--line)"
        />
      ))}
      {AXES.map((a, i) => {
        const [x, y] = point(i, 100);
        const [lx, ly] = point(i, 122);
        return (
          <g key={a.key}>
            <line x1={c} y1={c} x2={x} y2={y} stroke="var(--line)" />
            <text x={lx} y={ly} textAnchor="middle" dominantBaseline="middle" className="radar-label">
              {a.label}
            </text>
          </g>
        );
      })}
      {evaluations.map((e) => {
        const pts = AXES.map((a, i) => point(i, e.sub_scores[a.key]).join(",")).join(" ");
        const col = colorFor(e.agent_name);
        return <polygon key={e.agent_name} points={pts} fill={col} fillOpacity="0.18" stroke={col} strokeWidth="2" />;
      })}
    </svg>
  );
}
