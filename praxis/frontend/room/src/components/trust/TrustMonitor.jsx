import { useRoomState } from '../../context/RoomContext';
import TrustIndicator from './TrustIndicator';
import DecayAlertList from './DecayAlertList';

export default function TrustMonitor() {
  const { healthData, trustAlerts } = useRoomState();

  return (
    <div className="space-y-3 mt-4">
      <h3 className="text-xs font-medium text-white/30 uppercase tracking-wider mb-2">System Health</h3>

      {healthData?.models ? (
        <div className="space-y-1">
          {Object.entries(healthData.models).map(([modelId, data]) => (
            <TrustIndicator key={modelId} modelId={modelId} data={data} />
          ))}
        </div>
      ) : (
        <p className="text-xs text-white/20 italic">No health data yet</p>
      )}

      {trustAlerts.length > 0 && <DecayAlertList alerts={trustAlerts} />}
    </div>
  );
}
