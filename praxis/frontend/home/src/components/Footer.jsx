export default function Footer() {
  return (
    <footer style={{ background: 'rgba(0,0,0,0.3)', borderTop: '1px solid rgba(255,255,255,0.06)', padding: '48px 40px 24px', marginTop: '40px' }}>
      <div className="grid grid-cols-3 gap-8 max-w-[800px] mx-auto max-[600px]:grid-cols-1">
        <div>
          <div className="text-[12px] font-medium text-white/50 uppercase tracking-wider mb-3">Product</div>
          <a href="/static/tools.html" className="block text-[13px] text-white/35 no-underline leading-8 hover:text-white/70 transition-colors">All Tools</a>
          <a href="/static/differential.html" className="block text-[13px] text-white/35 no-underline leading-8 hover:text-white/70 transition-colors">Diagnosis</a>
          <a href="/journey" className="block text-[13px] text-white/35 no-underline leading-8 hover:text-white/70 transition-colors">Build My Stack</a>
          <a href="/room" className="block text-[13px] text-white/35 no-underline leading-8 hover:text-white/70 transition-colors">Room</a>
        </div>
        <div>
          <div className="text-[12px] font-medium text-white/50 uppercase tracking-wider mb-3">Resources</div>
          <a href="/static/tuesday-test.html" className="block text-[13px] text-white/35 no-underline leading-8 hover:text-white/70 transition-colors">ROI Calculator</a>
          <a href="/static/rfp.html" className="block text-[13px] text-white/35 no-underline leading-8 hover:text-white/70 transition-colors">RFP Builder</a>
          <a href="/static/stack-advisor.html" className="block text-[13px] text-white/35 no-underline leading-8 hover:text-white/70 transition-colors">Stack Advisor</a>
          <a href="/static/trust_badges.html" className="block text-[13px] text-white/35 no-underline leading-8 hover:text-white/70 transition-colors">Trust Badges</a>
        </div>
        <div>
          <div className="text-[12px] font-medium text-white/50 uppercase tracking-wider mb-3">Company</div>
          <a href="/static/pricing.html" className="block text-[13px] text-white/35 no-underline leading-8 hover:text-white/70 transition-colors">Pricing</a>
          <a href="/static/manifesto.html" className="block text-[13px] text-white/35 no-underline leading-8 hover:text-white/70 transition-colors">Methodology</a>
          <a href="/static/partners.html" className="block text-[13px] text-white/35 no-underline leading-8 hover:text-white/70 transition-colors">Partners</a>
        </div>
      </div>
      <div className="max-w-[800px] mx-auto mt-8 pt-5 text-center text-[11px] text-white/25" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        &copy; 2026 Praxis AI
      </div>
    </footer>
  );
}
