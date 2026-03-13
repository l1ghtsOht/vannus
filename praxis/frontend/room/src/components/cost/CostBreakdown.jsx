import { useRoomState, PHASES } from '../../context/RoomContext';

export default function CostBreakdown() {
  const { cost, phase } = useRoomState();

  const models = Object.entries(cost.perModel || {});
  const hasData = cost.total > 0 || models.length > 0;

  // Hide the entire section if no cost data and a query has already completed
  if (!hasData && phase === PHASES.COMPLETE) return null;

  return (
    <div className="space-y-3">
      <h3 className="text-xs font-medium text-white/30 uppercase tracking-wider mb-2">Cost Breakdown</h3>

      {!hasData ? (
        <p className="text-xs text-white/20 italic">Awaiting query…</p>
      ) : (
        <>
          {/* Total */}
          <div className="flex items-center justify-between py-2 px-3 rounded-xl bg-white/[0.03] border border-white/[0.05]">
            <span className="text-xs text-white/50">Session Total</span>
            <span className="text-sm font-mono text-white/70">${cost.total.toFixed(4)}</span>
          </div>

          {/* Per Model */}
          {models.length > 0 && (
            <div className="space-y-1">
              <span className="text-[10px] text-white/25 uppercase tracking-wider">Per Model</span>
              {models.map(([modelId, amount]) => (
                <div key={modelId} className="flex items-center justify-between py-1 px-2 rounded-lg hover:bg-white/[0.02] transition-colors">
                  <span className="text-[11px] text-white/40 truncate">{modelId}</span>
                  <span className="text-[11px] text-white/30 font-mono">${amount.toFixed(4)}</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
