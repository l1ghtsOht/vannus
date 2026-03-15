const PATHS = [
  { title: 'Guided journey', sub: '4 questions, 2 min', href: '/journey', color: 'rgba(99,102,241,0.08)', textColor: '#6366f1', icon: <path d="M3 8l4 4 6-8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/> },
  { title: 'Browse catalog', sub: '253 tools', href: '/static/tools.html', color: 'rgba(80,227,194,0.08)', textColor: '#50e3c2', icon: <><path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></> },
  { title: 'Compare tools', sub: 'Side by side', action: 'compare', color: 'rgba(239,159,39,0.08)', textColor: '#f5a623', icon: <><rect x="2" y="3" width="5" height="10" rx="1" stroke="currentColor" strokeWidth="1.3"/><rect x="9" y="3" width="5" height="10" rx="1" stroke="currentColor" strokeWidth="1.3"/></> },
  { title: 'ROI calculator', sub: 'The Tuesday Test', href: '/static/tuesday-test.html', color: 'rgba(226,75,74,0.08)', textColor: '#e24b4a', icon: <path d="M8 2v12M4 6l4-4 4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/> },
];

export default function PathCards({ onCompare }) {
  return (
    <div className="max-w-[640px] mx-auto px-4 mt-5">
      <div className="flex items-center gap-2.5 mb-2">
        <span className="text-[11px] text-white/20 uppercase tracking-wide whitespace-nowrap">Or try a different approach</span>
        <div className="flex-1 h-px bg-white/[0.06]" />
      </div>
      <div className="grid grid-cols-4 gap-2 max-[700px]:grid-cols-2 max-[500px]:grid-cols-1">
        {PATHS.map(p => {
          const Tag = p.href ? 'a' : 'button';
          const props = p.href ? { href: p.href } : { onClick: onCompare };
          return (
            <Tag
              key={p.title}
              {...props}
              className="flex items-center gap-2 p-2.5 rounded-xl no-underline transition-all hover:border-white/15"
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', textDecoration: 'none' }}
            >
              <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0" style={{ background: p.color, color: p.textColor }}>
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">{p.icon}</svg>
              </div>
              <div>
                <div className="text-[11px] font-bold text-white/70">{p.title}</div>
                <div className="text-[10px] text-white/30">{p.sub}</div>
              </div>
            </Tag>
          );
        })}
      </div>
    </div>
  );
}
