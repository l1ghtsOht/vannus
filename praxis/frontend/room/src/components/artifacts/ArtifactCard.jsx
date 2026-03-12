import { useState } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';

const MODEL_COLORS = {
  claude: '#8b5cf6',
  gemini: '#06b6d4',
  grok: '#f59e0b',
  'gpt-4o': '#10b981',
  'gpt-4': '#10b981',
  local: '#6b7280',
};

function getModelColor(name) {
  const lower = (name || '').toLowerCase();
  for (const [key, color] of Object.entries(MODEL_COLORS)) {
    if (lower.includes(key)) return color;
  }
  return '#6366f1';
}

function CopyBtn({ text }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(text || '');
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      className="text-[10px] px-2 py-1 rounded border border-white/10 text-white/30 hover:text-white/60 hover:border-white/20 transition-colors"
    >
      {copied ? '\u2713 Copied' : 'Copy'}
    </button>
  );
}

export default function ArtifactCard({ artifact, index, canvas }) {
  const { model_id, content, artifact_type, title, created_at } = artifact;
  const color = getModelColor(model_id);

  if (canvas) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.3 }}
        className="rounded-xl overflow-hidden"
        style={{
          border: '1px solid rgba(16,185,129,0.15)',
          background: 'rgba(16,185,129,0.03)',
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/[0.06]">
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: color }} />
            <span className="text-xs font-medium text-white/50 truncate">{title || model_id}</span>
          </div>
          <CopyBtn text={content} />
        </div>

        {/* Full markdown content */}
        <div className="px-4 py-3 prose prose-invert prose-sm max-w-none text-white/70 leading-relaxed overflow-y-auto max-h-[60vh]">
          <ReactMarkdown>{content || ''}</ReactMarkdown>
        </div>

        {created_at && (
          <div className="px-4 py-2 border-t border-white/[0.04]">
            <span className="text-[9px] text-white/15">
              {new Date(created_at).toLocaleTimeString()}
            </span>
          </div>
        )}
      </motion.div>
    );
  }

  // Compact card mode (original)
  const preview = (content || '').slice(0, 120);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.1, type: 'spring', stiffness: 300, damping: 25 }}
      whileHover={{ scale: 1.02 }}
      className="glass shrink-0 w-56 cursor-pointer overflow-hidden"
    >
      {/* Color Stripe */}
      <div className="h-1" style={{ backgroundColor: color }} />

      <div className="p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-medium text-white/50">{model_id}</span>
          <div className="flex items-center gap-1">
            <CopyBtn text={content} />
            {artifact_type && (
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/5 text-white/30">{artifact_type}</span>
            )}
          </div>
        </div>
        <p className="text-xs text-white/40 line-clamp-3 font-mono leading-relaxed">{preview}</p>
        {created_at && (
          <span className="text-[9px] text-white/15 mt-2 block">
            {new Date(created_at).toLocaleTimeString()}
          </span>
        )}
      </div>
    </motion.div>
  );
}
