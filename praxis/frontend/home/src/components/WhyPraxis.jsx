import MagicBento from './MagicBento/MagicBento';

export default function WhyPraxis() {
  return (
    <section className="relative py-24 px-6">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-16">
          <h2 style={{ color: '#f0f0f5', fontSize: '2.5rem', fontWeight: 600, marginBottom: '0.75rem' }}>
            Why Praxis
          </h2>
          <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: '1.125rem', maxWidth: '36rem', margin: '0 auto' }}>
            The only AI tool platform that eliminates first, recommends second.
          </p>
        </div>
        <MagicBento
          textAutoHide={true}
          enableStars={true}
          enableSpotlight={true}
          enableBorderGlow={true}
          enableTilt={false}
          enableMagnetism={false}
          clickEffect={true}
          spotlightRadius={400}
          particleCount={12}
          glowColor="99, 102, 241"
          disableAnimations={false}
        />
      </div>
    </section>
  );
}
