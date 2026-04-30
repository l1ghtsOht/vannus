import { useRef, forwardRef, useImperativeHandle } from 'react';

const SEARCH_ICON = <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.5"/><path d="M10.5 10.5L13 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>;

const CommandBar = forwardRef(function CommandBar({ onSubmit, value, onChange }, ref) {
  const inputRef = useRef(null);

  useImperativeHandle(ref, () => ({
    focus: () => inputRef.current?.focus(),
  }));

  const handleSubmit = () => {
    if (value?.trim()) onSubmit(value.trim());
  };

  return (
    <div className="max-w-[640px] w-full mx-auto px-4">
      <div
        className="flex items-center command-bar-wrap"
        style={{
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.07)',
          borderRadius: '18px',
          padding: '8px 14px',
          transition: 'border-color 0.3s ease, box-shadow 0.3s ease',
        }}
      >
        {/* Search icon */}
        <div className="shrink-0 flex items-center justify-center w-8 h-8" style={{ color: 'rgba(255,255,255,0.35)', marginRight: '4px' }}>
          {SEARCH_ICON}
        </div>

        {/* Input */}
        <input
          ref={inputRef}
          type="text"
          value={value || ''}
          onChange={e => onChange?.(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') handleSubmit(); }}
          placeholder="Search by task or role — we eliminate what doesn't fit."
          className="flex-1 bg-transparent outline-none"
          style={{ height: '38px', fontSize: '15px', padding: '6px 8px', caretColor: '#6366f1', color: '#f0f0f5' }}
        />

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={!value?.trim()}
          className="shrink-0 flex items-center justify-center transition-all disabled:opacity-30"
          style={{
            width: '34px', height: '34px',
            background: value?.trim() ? '#6366f1' : 'rgba(255,255,255,0.05)',
            border: value?.trim() ? 'none' : '1px solid rgba(255,255,255,0.07)',
            borderRadius: '10px',
            color: 'white',
            boxShadow: value?.trim() ? '0 0 12px rgba(99,102,241,0.3)' : 'none',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </button>
      </div>
    </div>
  );
});

export default CommandBar;
