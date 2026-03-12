import { useRef, useEffect } from 'react';
import { useRoomState, PHASES } from '../../context/RoomContext';

const PARTICLE_COUNT = 40;

export default function ParticleField() {
  const canvasRef = useRef(null);
  const { phase } = useRoomState();
  const phaseRef = useRef(phase);

  useEffect(() => { phaseRef.current = phase; }, [phase]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;

    const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
      x: Math.random(),
      y: Math.random(),
      vx: (Math.random() - 0.5) * 0.0003,
      vy: (Math.random() - 0.5) * 0.0003,
      size: Math.random() * 1.5 + 0.5,
      alpha: Math.random() * 0.15 + 0.05,
    }));

    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    function draw() {
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      const speedMult = phaseRef.current === PHASES.EXECUTING ? 2.5 :
                        phaseRef.current === PHASES.ELIMINATING ? 1.8 : 1;

      for (const p of particles) {
        p.x += p.vx * speedMult;
        p.y += p.vy * speedMult;

        if (p.x < 0) p.x = 1;
        if (p.x > 1) p.x = 0;
        if (p.y < 0) p.y = 1;
        if (p.y > 1) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x * w, p.y * h, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255,255,255,${p.alpha})`;
        ctx.fill();
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
      className="fixed inset-0 z-[1] pointer-events-none"
      aria-hidden="true"
    />
  );
}
