export default function Nav() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-center gap-8 px-6 py-3"
         style={{ background: 'rgba(6,6,14,0.75)', backdropFilter: 'blur(30px)', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
      <a href="/" className="font-bold text-[15px] text-white tracking-tight">Praxis</a>
      <a href="/static/tools.html" className="text-[13px] text-white/55 hover:text-white transition-colors">Tools</a>
      <a href="#how-it-works" className="text-[13px] text-white/55 hover:text-white transition-colors">How it works</a>
      <a href="/static/tuesday-test.html" className="text-[13px] text-white/55 hover:text-white transition-colors">ROI Calculator</a>
      <a href="/static/pricing.html" className="text-[13px] text-white/55 hover:text-white transition-colors">Pricing</a>
    </nav>
  );
}
