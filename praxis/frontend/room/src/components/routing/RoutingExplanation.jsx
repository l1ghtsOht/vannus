export default function RoutingExplanation({ reasoning }) {
  if (!reasoning) return null;

  return (
    <p className="text-xs text-white/30 mb-3 leading-relaxed pl-3 border-l border-white/[0.06]">
      {reasoning}
    </p>
  );
}
