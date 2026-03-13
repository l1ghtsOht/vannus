import { motion } from 'framer-motion';
import ReasonCodeBadge from './ReasonCodeBadge';

export default function ToolDetailDrawer({ tool, isEliminated }) {
  const reasons = tool.survival_reasons || tool.reasons || [];
  const pricing = tool.pricing;
  const integrations = tool.integrations || [];
  const compliance = tool.compliance || [];
  const resilience = tool.resilience;
  const penalties = tool.penalties_applied || tool.caveats || [];

  const reasonCode = tool.code || tool.reason_type;
  const explanation = tool.explanation;

  const hasSurvivorContent = reasons.length > 0 || pricing || integrations.length > 0 ||
    compliance.length > 0 || resilience || penalties.length > 0;
  const hasEliminatedContent = isEliminated && (reasonCode || explanation);

  if (!hasSurvivorContent && !hasEliminatedContent) return null;

  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
      className="overflow-hidden"
    >
      <div
        className="px-4 pb-3 pt-2 space-y-3"
        style={{
          background: 'rgba(255,255,255,0.02)',
          borderTop: '1px solid rgba(255,255,255,0.04)',
        }}
      >
        {/* Why it survived */}
        {!isEliminated && reasons.length > 0 && (
          <div>
            <div className="text-[10px] uppercase tracking-wider text-white/25 mb-1.5">Why it survived</div>
            <ul className="space-y-1">
              {reasons.map((r, i) => (
                <li key={i} className="text-xs text-white/50 flex items-start gap-2">
                  <span className="text-emerald-400/60 mt-0.5 shrink-0">{'\u2713'}</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Pricing */}
        {pricing && Object.keys(pricing).length > 0 && (
          <div>
            <div className="text-[10px] uppercase tracking-wider text-white/25 mb-1.5">Pricing</div>
            <div className="flex flex-wrap gap-2">
              {pricing.free_tier && (
                <span className="text-[11px] px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400/70 border border-emerald-500/15">
                  Free tier
                </span>
              )}
              {pricing.starter != null && (
                <span className="text-[11px] px-2 py-0.5 rounded-md bg-white/5 text-white/50 border border-white/8">
                  Starter ${pricing.starter}/mo
                </span>
              )}
              {pricing.enterprise != null && (
                <span className="text-[11px] px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400/70 border border-indigo-500/15">
                  Enterprise {typeof pricing.enterprise === 'string' ? pricing.enterprise : `$${pricing.enterprise}/mo`}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Integrations */}
        {integrations.length > 0 && (
          <div>
            <div className="text-[10px] uppercase tracking-wider text-white/25 mb-1.5">Integrations</div>
            <div className="flex flex-wrap gap-1">
              {integrations.map((name, i) => (
                <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/40 border border-white/8">
                  {name}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Compliance */}
        {compliance.length > 0 && (
          <div>
            <div className="text-[10px] uppercase tracking-wider text-white/25 mb-1.5">Compliance</div>
            <div className="flex flex-wrap gap-1.5">
              {compliance.map((c, i) => (
                <span key={i} className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400/80 border border-cyan-500/15">
                  {c}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Trust Score */}
        {resilience && resilience.score != null && (
          <div>
            <div className="text-[10px] uppercase tracking-wider text-white/25 mb-1.5">Trust Score</div>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden max-w-[120px]">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${Math.min(100, resilience.score)}%`,
                    background: resilience.score >= 70 ? '#10b981' : resilience.score >= 40 ? '#f59e0b' : '#ef4444',
                  }}
                />
              </div>
              <span className="text-[11px] font-mono text-white/50">{resilience.score}</span>
              {resilience.grade && (
                <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-white/5 text-white/40">
                  {resilience.grade}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Limitations (penalties on survivors) */}
        {!isEliminated && penalties.length > 0 && (
          <div>
            <div className="text-[10px] uppercase tracking-wider text-white/25 mb-1.5">Limitations</div>
            <ul className="space-y-1">
              {penalties.map((p, i) => (
                <li key={i} className="text-[11px] text-white/30 flex items-start gap-2">
                  <span className="text-amber-400/40 mt-0.5 shrink-0">{'\u26A0'}</span>
                  <span>{typeof p === 'string' ? p : p.reason || 'penalty'}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Why not (eliminated tools) */}
        {isEliminated && (reasonCode || explanation) && (
          <div>
            <div className="text-[10px] uppercase tracking-wider text-white/25 mb-1.5">Why not</div>
            <div className="space-y-1.5">
              {reasonCode && <ReasonCodeBadge code={reasonCode} />}
              {explanation && <p className="text-xs text-white/40 leading-relaxed">{explanation}</p>}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}
