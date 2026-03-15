import LogoLoop from './LogoLoop/LogoLoop';

const toolLogos = [
  { src: 'https://www.google.com/s2/favicons?domain=openai.com&sz=64', alt: 'OpenAI', title: 'OpenAI' },
  { src: 'https://www.google.com/s2/favicons?domain=anthropic.com&sz=64', alt: 'Anthropic', title: 'Anthropic' },
  { src: 'https://www.google.com/s2/favicons?domain=notion.so&sz=64', alt: 'Notion', title: 'Notion' },
  { src: 'https://www.google.com/s2/favicons?domain=figma.com&sz=64', alt: 'Figma', title: 'Figma' },
  { src: 'https://www.google.com/s2/favicons?domain=linear.app&sz=64', alt: 'Linear', title: 'Linear' },
  { src: 'https://www.google.com/s2/favicons?domain=vercel.com&sz=64', alt: 'Vercel', title: 'Vercel' },
  { src: 'https://www.google.com/s2/favicons?domain=github.com&sz=64', alt: 'GitHub Copilot', title: 'GitHub Copilot' },
  { src: 'https://www.google.com/s2/favicons?domain=midjourney.com&sz=64', alt: 'Midjourney', title: 'Midjourney' },
  { src: 'https://www.google.com/s2/favicons?domain=jasper.ai&sz=64', alt: 'Jasper', title: 'Jasper' },
  { src: 'https://www.google.com/s2/favicons?domain=grammarly.com&sz=64', alt: 'Grammarly', title: 'Grammarly' },
  { src: 'https://www.google.com/s2/favicons?domain=zapier.com&sz=64', alt: 'Zapier', title: 'Zapier' },
  { src: 'https://www.google.com/s2/favicons?domain=descript.com&sz=64', alt: 'Descript', title: 'Descript' },
  { src: 'https://www.google.com/s2/favicons?domain=runwayml.com&sz=64', alt: 'Runway', title: 'Runway' },
  { src: 'https://www.google.com/s2/favicons?domain=perplexity.ai&sz=64', alt: 'Perplexity', title: 'Perplexity' },
  { src: 'https://www.google.com/s2/favicons?domain=canva.com&sz=64', alt: 'Canva', title: 'Canva' },
  { src: 'https://www.google.com/s2/favicons?domain=replit.com&sz=64', alt: 'Replit', title: 'Replit' },
  { src: 'https://www.google.com/s2/favicons?domain=stability.ai&sz=64', alt: 'Stability AI', title: 'Stability AI' },
  { src: 'https://www.google.com/s2/favicons?domain=huggingface.co&sz=64', alt: 'Hugging Face', title: 'Hugging Face' },
  { src: 'https://www.google.com/s2/favicons?domain=elevenlabs.io&sz=64', alt: 'ElevenLabs', title: 'ElevenLabs' },
  { src: 'https://www.google.com/s2/favicons?domain=cursor.com&sz=64', alt: 'Cursor', title: 'Cursor' },
];

export default function TrustedTools() {
  return (
    <section className="relative py-10">
      <p style={{ textAlign: 'center', fontSize: '12px', fontWeight: 500, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.25)', marginBottom: '1.25rem' }}>
        Sovereign &amp; Durable rated tools we evaluate
      </p>
      <LogoLoop
        logos={toolLogos}
        speed={60}
        direction="left"
        logoHeight={32}
        gap={85}
        hoverSpeed={0}
        fadeOut={true}
        fadeOutColor="#0a0a0f"
        scaleOnHover={true}
        ariaLabel="Top-rated AI tools evaluated by Praxis"
      />
    </section>
  );
}
