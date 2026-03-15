import { motion } from 'framer-motion';

function getLogoDomain(url) {
  try { return new URL(url).hostname.replace(/^www\./, ''); }
  catch { return ''; }
}

export default function ToolCard({ tool, index, isTopPick }) {
  const name = tool.name || 'Unknown';
  const pct = tool._pct || 50;
  const desc = tool.description || '';
  const url = tool.url || '';
  const domain = getLogoDomain(url);
  const compliance = tool.compliance || [];
  const pricing = tool.pricing || {};
  const skill = tool.skill_level || '';

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06 }}
      whileHover={{ y: -2 }}
      className={`flex items-center gap-3.5 rounded-xl p-4 mb-2 transition-all ${isTopPick ? '' : ''}`}
      style={{
        background: 'rgba(255,255,255,0.03)',
        border: `1px solid ${isTopPick ? '#6366f1' : 'rgba(255,255,255,0.08)'}`,
        borderRadius: '12px',
      }}
    >
      {/* Favicon */}
      {domain ? (
        <img
          src={`https://www.google.com/s2/favicons?domain=${domain}&sz=32`}
          alt={name}
          className="w-8 h-8 rounded-lg object-contain shrink-0"
          style={{ background: 'rgba(255,255,255,0.06)', padding: '3px' }}
          onError={e => { e.target.style.display = 'none'; e.target.nextElementSibling.style.display = 'flex'; }}
        />
      ) : null}
      <div
        className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm shrink-0"
        style={{ display: domain ? 'none' : 'flex', background: 'linear-gradient(135deg, #6366f1, #50e3c2)' }}
      >
        {name.charAt(0)}
      </div>

      {/* Body */}
      <div className="flex-1 min-w-0">
        {isTopPick && <div className="text-[9px] font-bold uppercase tracking-widest text-[#6366f1] mb-0.5">Top pick</div>}
        <div className="flex items-center justify-between gap-2">
          <span className="text-[15px] font-bold text-white/85 truncate">{name}</span>
          <span className={`text-[15px] font-bold shrink-0 ${pct >= 70 ? 'text-[#6366f1]' : 'text-white/40'}`}>{pct}% fit</span>
        </div>
        <div className="text-[13px] text-white/35 truncate mt-0.5">{desc.slice(0, 120)}{desc.length > 120 ? '...' : ''}</div>
        <div className="flex items-center justify-between gap-2 mt-2">
          <div className="flex flex-wrap gap-1">
            {compliance.slice(0, 2).map((c, i) => (
              <span key={i} className="text-[10px] font-semibold px-2 py-0.5 rounded-full" style={{ background: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1px solid rgba(16,185,129,0.15)' }}>{c}</span>
            ))}
            {pricing.free_tier && <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full" style={{ background: 'rgba(80,227,194,0.1)', color: '#50e3c2', border: '1px solid rgba(80,227,194,0.15)' }}>Free tier</span>}
            {!pricing.free_tier && pricing.starter && <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full" style={{ background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.4)', border: '1px solid rgba(255,255,255,0.08)' }}>From ${pricing.starter}/mo</span>}
            {skill && <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full" style={{ background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.4)', border: '1px solid rgba(255,255,255,0.08)' }}>{skill}</span>}
          </div>
          {url && <a href={url} target="_blank" rel="noreferrer" className="text-[12px] text-white/30 hover:text-[#6366f1] transition-colors shrink-0 no-underline">Visit site →</a>}
        </div>
      </div>
    </motion.div>
  );
}
