export const fmt = (n, digits = 1) =>
  Number(n).toLocaleString("en-IN", { maximumFractionDigits: digits });

export const inr = (n) => {
  const v = Number(n);
  if (v >= 1e7) return `₹${(v / 1e7).toFixed(2)} Cr`;
  if (v >= 1e5) return `₹${(v / 1e5).toFixed(1)} L`;
  return `₹${fmt(v, 0)}`;
};

export const pretty = (s) => s.replaceAll("_", " ");

export const AGENT_COLORS = {
  CostOptimizer: "#f5a524",
  GreenAdvocate: "#3ecf8e",
  ResilienceGuardian: "#7c9cff",
  Synthesis: "#e879f9",
  Hybrid: "#55d8ea",
};
export const colorFor = (name) => AGENT_COLORS[name] || "#9ca3af";
