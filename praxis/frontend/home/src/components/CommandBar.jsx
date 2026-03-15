import { useState, useRef, forwardRef, useImperativeHandle } from 'react';

const MODES = [
  { id: 'find', label: 'Find', placeholder: 'Find the right AI tool...', icon: <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.5"/><path d="M10.5 10.5L13 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg> },
  { id: 'compare', label: 'Compare', placeholder: 'Compare vendors side-by-side...', icon: <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="3" width="5" height="10" rx="1" stroke="currentColor" strokeWidth="1.5"/><rect x="9" y="3" width="5" height="10" rx="1" stroke="currentColor" strokeWidth="1.5"/></svg> },
  { id: 'analyze', label: 'Analyze', placeholder: 'Analyze your current stack...', icon: <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="9" width="3" height="5" rx="0.5" stroke="currentColor" strokeWidth="1.5"/><rect x="6.5" y="5" width="3" height="9" rx="0.5" stroke="currentColor" strokeWidth="1.5"/><rect x="11" y="2" width="3" height="12" rx="0.5" stroke="currentColor" strokeWidth="1.5"/></svg> },
];

const CommandBar = forwardRef(function CommandBar({ onSubmit, value, onChange }, ref) {
  const [mode, setMode] = useState('find');
  const inputRef = useRef(null);
  const activeMode = MODES.find(m => m.id === mode);

  useImperativeHandle(ref, () => ({
    focus: () => inputRef.current?.focus(),
    setMode: (m) => setMode(m),
  }));

  const handleSubmit = () => {
    if (value?.trim()) onSubmit(value.trim());
  };

  return (
    <div className="max-w-[640px] w-full mx-auto px-4">
      <div
        className="flex items-center transition-shadow duration-200"
        style={{
          background: 'rgba(15,15,20,0.88)',
          backdropFilter: 'blur(24px)',
          border: '0.5px solid rgba(255,255,255,0.08)',
          borderRadius: '16px',
          padding: '6px',
          boxShadow: '0 8px 40px rgba(0,0,0,0.4)',
        }}
      >
        {/* Mode toggles */}
        <div className="flex items-center shrink-0" style={{ borderRight: '0.5px solid rgba(255,255,255,0.08)', paddingRight: '6px', marginRight: '6px' }}>
          {MODES.map(m => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              title={m.label}
              className="w-8 h-8 flex items-center justify-center rounded-lg transition-all"
              style={{ background: mode === m.id ? '#6366f1' : 'transparent', color: mode === m.id ? 'white' : 'rgba(255,255,255,0.4)' }}
            >
              {m.icon}
            </button>
          ))}
        </div>

        {/* Input */}
        <input
          ref={inputRef}
          type="text"
          value={value || ''}
          onChange={e => onChange?.(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') handleSubmit(); }}
          placeholder={activeMode.placeholder}
          className="flex-1 bg-transparent outline-none text-white/90 placeholder-white/25"
          style={{ height: '42px', fontSize: '15px', padding: '6px 8px', caretColor: '#6366f1' }}
        />

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={!value?.trim()}
          className="shrink-0 rounded-full flex items-center justify-center transition-all disabled:opacity-30 hover:scale-105 active:scale-95"
          style={{ width: '36px', height: '36px', background: value?.trim() ? '#6366f1' : 'rgba(255,255,255,0.06)', color: 'white' }}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </button>
      </div>
    </div>
  );
});

export default CommandBar;
