import { useRoomState } from '../../context/RoomContext';

export default function CostPreview({ estimate }) {
  if (!estimate) return null;

  return (
    <div className="flex items-center gap-2 text-[11px] text-white/40 font-mono">
      <span>~${typeof estimate === 'number' ? estimate.toFixed(4) : '0.00'}</span>
      <span className="text-white/15">est.</span>
    </div>
  );
}
