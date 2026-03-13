import { useEffect } from 'react';
import { RoomProvider, useRoomState, useRoomDispatch, PHASES } from './context/RoomContext';
import AmbientBackground from './components/ambient/AmbientBackground';
import ParticleField from './components/ambient/ParticleField';
import Header from './components/layout/Header';
import LeftPanel from './components/layout/LeftPanel';
import RightPanel from './components/layout/RightPanel';
import ContextPanel from './components/context/ContextPanel';
import IntentInput from './components/input/IntentInput';
import EliminationDisplay from './components/elimination/EliminationDisplay';
import RoutingPlan from './components/routing/RoutingPlan';
import ExecutionStream from './components/execution/ExecutionStream';
import TrustMonitor from './components/trust/TrustMonitor';
import CostBreakdown from './components/cost/CostBreakdown';
import ActivityFeed from './components/activity/ActivityFeed';
import PhaseSteps from './components/activity/PhaseSteps';
import EmptyCanvas from './components/EmptyCanvas';
import useDecayAlerts from './hooks/useDecayAlerts';

function RoomShell() {
  const { room, error, phase, activityLog } = useRoomState();
  const dispatch = useRoomDispatch();

  // Auto-create or load most recent room on mount
  useEffect(() => {
    async function init() {
      try {
        // GET /room may return SPA HTML (route collision) — try to parse as JSON,
        // and if it fails, just create a default room instead.
        let rooms = [];
        try {
          const res = await fetch('/room');
          const ct = res.headers.get('content-type') || '';
          if (res.ok && ct.includes('application/json')) {
            const body = await res.json();
            rooms = body.data || body || [];
          }
        } catch { /* HTML response or network issue — proceed with empty */ }

        if (Array.isArray(rooms) && rooms.length > 0) {
          dispatch({ type: 'SET_ROOMS', payload: rooms });
          const latest = rooms[rooms.length - 1];
          dispatch({ type: 'SET_ROOM', payload: latest });
        } else {
          // Create default room
          const createRes = await fetch('/room', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: 'My Room', operator_context: {} }),
          });
          if (createRes.ok) {
            const body = await createRes.json();
            const newRoom = body.data || body;
            dispatch({ type: 'SET_ROOM', payload: newRoom });
          }
        }
      } catch (err) {
        // Room init failure is non-fatal — user can still query
        console.warn('Room init failed:', err.message);
      }
    }
    init();
  }, [dispatch]);

  // Poll health for decay alerts
  useDecayAlerts(30000);

  return (
    <>
      <AmbientBackground />
      <ParticleField />
      <div className="noise" />
      <div className="relative z-10 flex flex-col h-screen w-screen">
        <Header />

        {error && (
          <div className="relative z-20 mx-4 mt-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-xs flex items-center gap-3">
            <span className="text-red-400/60">✕</span>
            <div className="flex-1 min-w-0">
              <span className="text-red-400/90 font-medium">Routing Error</span>
              <span className="text-red-400/60 ml-2">{error}</span>
            </div>
            <button
              onClick={() => {
                dispatch({ type: 'SET_ERROR', payload: null });
                dispatch({ type: 'RESET' });
              }}
              className="text-[10px] text-white/60 hover:text-white/90 px-2.5 py-1 rounded-md bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all shrink-0"
            >Retry</button>
            <button
              onClick={() => dispatch({ type: 'SET_ERROR', payload: null })}
              className="text-red-400/30 hover:text-red-400/70 shrink-0"
            >✕</button>
          </div>
        )}

        <div className="flex flex-1 overflow-hidden relative">
          <LeftPanel>
            <ContextPanel />
            <TrustMonitor />
          </LeftPanel>

          {/* Center Stage */}
          <main className="flex-1 flex flex-col overflow-hidden relative">
            <PhaseSteps />
            {phase === PHASES.IDLE && activityLog.length === 0 ? (
              <EmptyCanvas />
            ) : (
              <div className="flex-1 overflow-y-auto">
                <ActivityFeed />
                <div className="px-6 py-4 space-y-2">
                  <EliminationDisplay />
                  <RoutingPlan />
                  <ExecutionStream />
                </div>
              </div>
            )}
            <IntentInput />
          </main>

          <RightPanel>
            <CostBreakdown />
          </RightPanel>
        </div>
      </div>
    </>
  );
}

export default function App() {
  return (
    <RoomProvider>
      <RoomShell />
    </RoomProvider>
  );
}
