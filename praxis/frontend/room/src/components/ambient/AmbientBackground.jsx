import { useRef, useEffect } from 'react';
import { useRoomState, PHASES } from '../../context/RoomContext';

const PHASE_COLORS = {
  [PHASES.IDLE]:        { a: [99, 102, 241],  b: [6, 182, 212],   c: [139, 92, 246]  },
  [PHASES.ELIMINATING]: { a: [99, 102, 241],  b: [79, 70, 229],   c: [67, 56, 202]   },
  [PHASES.ROUTING]:     { a: [99, 102, 241],  b: [245, 158, 11],  c: [6, 182, 212]   },
  [PHASES.EXECUTING]:   { a: [139, 92, 246],  b: [6, 182, 212],   c: [16, 185, 129]  },
  [PHASES.COMPLETE]:    { a: [16, 185, 129],  b: [6, 182, 212],   c: [99, 102, 241]  },
};

const DECAY_COLORS = { a: [239, 68, 68], b: [220, 38, 38], c: [185, 28, 28] };

function lerp(a, b, t) {
  return a.map((v, i) => v + (b[i] - v) * t);
}

export default function AmbientBackground() {
  const canvasRef = useRef(null);
  const { phase, trustAlerts } = useRoomState();
  const phaseRef = useRef(phase);
  const alertRef = useRef(trustAlerts);

  useEffect(() => { phaseRef.current = phase; }, [phase]);
  useEffect(() => { alertRef.current = trustAlerts; }, [trustAlerts]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;
    let prevColors = PHASE_COLORS[PHASES.IDLE];
    let currentColors = PHASE_COLORS[PHASES.IDLE];
    let blendT = 1;

    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    function draw(time) {
      const t = time / 1000;
      const w = canvas.width;
      const h = canvas.height;

      // Phase color transitions
      const targetColors = PHASE_COLORS[phaseRef.current] || PHASE_COLORS[PHASES.IDLE];
      if (targetColors !== currentColors && blendT >= 1) {
        prevColors = currentColors;
        currentColors = targetColors;
        blendT = 0;
      }
      if (blendT < 1) blendT = Math.min(1, blendT + 0.008);

      const ca = lerp(prevColors.a, currentColors.a, blendT);
      const cb = lerp(prevColors.b, currentColors.b, blendT);
      const cc = lerp(prevColors.c, currentColors.c, blendT);

      // Check for severe decay
      const hasSevere = alertRef.current?.some(a => a.severity === 'SEVERE');
      const decayPulse = hasSevere ? 0.15 + 0.1 * Math.sin(t * 3) : 0;

      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = '#0a0a0f';
      ctx.fillRect(0, 0, w, h);

      // Breathing cycle: 10s for IDLE, 4s for ELIMINATING, 6s for others
      const cycleSpeed = phaseRef.current === PHASES.ELIMINATING ? 4 : 
                         phaseRef.current === PHASES.IDLE ? 10 : 6;
      const breath = Math.sin(t * (2 * Math.PI / cycleSpeed)) * 0.5 + 0.5;

      // Blob A — top-left
      const ax = w * 0.2 + Math.sin(t * 0.3) * w * 0.08;
      const ay = h * 0.2 + Math.cos(t * 0.25) * h * 0.06;
      const ar = (w * 0.35 + breath * w * 0.05);
      const ga = ctx.createRadialGradient(ax, ay, 0, ax, ay, ar);
      ga.addColorStop(0, `rgba(${Math.round(ca[0])},${Math.round(ca[1])},${Math.round(ca[2])},${0.18 + breath * 0.08})`);
      ga.addColorStop(1, 'transparent');
      ctx.fillStyle = ga;
      ctx.fillRect(0, 0, w, h);

      // Blob B — bottom-right
      const bx = w * 0.75 + Math.cos(t * 0.35) * w * 0.06;
      const by = h * 0.75 + Math.sin(t * 0.28) * h * 0.08;
      const br = (w * 0.3 + breath * w * 0.04);
      const gb = ctx.createRadialGradient(bx, by, 0, bx, by, br);
      gb.addColorStop(0, `rgba(${Math.round(cb[0])},${Math.round(cb[1])},${Math.round(cb[2])},${0.14 + breath * 0.06})`);
      gb.addColorStop(1, 'transparent');
      ctx.fillStyle = gb;
      ctx.fillRect(0, 0, w, h);

      // Blob C — center
      const cx_ = w * 0.5 + Math.sin(t * 0.2) * w * 0.05;
      const cy = h * 0.45 + Math.cos(t * 0.3) * h * 0.05;
      const cr = (w * 0.25 + breath * w * 0.04);
      const gc = ctx.createRadialGradient(cx_, cy, 0, cx_, cy, cr);
      gc.addColorStop(0, `rgba(${Math.round(cc[0])},${Math.round(cc[1])},${Math.round(cc[2])},${0.10 + breath * 0.05})`);
      gc.addColorStop(1, 'transparent');
      ctx.fillStyle = gc;
      ctx.fillRect(0, 0, w, h);

      // Decay alert — red edge pulse
      if (decayPulse > 0) {
        const edgeGrad = ctx.createRadialGradient(w/2, h/2, Math.min(w,h)*0.3, w/2, h/2, Math.max(w,h)*0.7);
        edgeGrad.addColorStop(0, 'transparent');
        edgeGrad.addColorStop(1, `rgba(239,68,68,${decayPulse})`);
        ctx.fillStyle = edgeGrad;
        ctx.fillRect(0, 0, w, h);
      }

      animId = requestAnimationFrame(draw);
    }

    animId = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 z-0 pointer-events-none"
      aria-hidden="true"
    />
  );
}
