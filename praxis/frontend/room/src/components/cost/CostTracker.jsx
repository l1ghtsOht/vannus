export default function CostTracker({ total }) {
  return (
    <div className="text-xs text-white/50 font-mono">
      ${(total || 0).toFixed(4)}
    </div>
  );
}
