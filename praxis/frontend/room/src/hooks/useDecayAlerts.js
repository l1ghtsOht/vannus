import { useEffect, useCallback, useRef } from 'react';
import { useRoomDispatch } from '../context/RoomContext';

export default function useDecayAlerts(intervalMs = 30000) {
  const dispatch = useRoomDispatch();
  const timerRef = useRef(null);

  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch('/health');
      if (!res.ok) return;
      const data = await res.json();
      dispatch({ type: 'SET_HEALTH_DATA', payload: data });

      // Extract decay alerts
      const alerts = [];
      if (data.decay_alerts) {
        for (const alert of data.decay_alerts) {
          alerts.push(alert);
        }
      }
      if (data.models) {
        for (const [modelId, mdata] of Object.entries(data.models)) {
          const trust = mdata.trust_score ?? mdata.trust ?? 1;
          if (trust < 0.5) {
            alerts.push({ model_id: modelId, severity: 'SEVERE', trust });
          } else if (trust < 0.8) {
            alerts.push({ model_id: modelId, severity: 'MILD', trust });
          }
        }
      }
      dispatch({ type: 'SET_TRUST_ALERTS', payload: alerts });
    } catch {}
  }, [dispatch]);

  useEffect(() => {
    checkHealth();
    timerRef.current = setInterval(checkHealth, intervalMs);
    return () => clearInterval(timerRef.current);
  }, [checkHealth, intervalMs]);

  return { checkHealth };
}
