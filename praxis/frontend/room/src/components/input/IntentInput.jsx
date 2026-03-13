import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRoomState, useRoomDispatch } from '../../context/RoomContext';

function activity(dispatch, type, text, detail) {
  dispatch({ type: 'APPEND_ACTIVITY', payload: { kind: type, text, detail } });
}

/* ── SSE stream parser ── */
function handleSSEEvent(dispatch, event) {
  const { type, ...data } = event;
  dispatch({ type: 'APPEND_EVENT', payload: event });

  const eventMap = {
    session_start: 'SSE_SESSION_START',
    context_extracted: 'SSE_CONTEXT_EXTRACTED',
    routing_decision: 'SSE_ROUTING_DECISION',
    model_start: 'SSE_MODEL_START',
    token_chunk: 'SSE_TOKEN_CHUNK',
    model_complete: 'SSE_MODEL_COMPLETE',
    collaboration_result: 'SSE_COLLABORATION_RESULT',
    artifact_saved: 'SSE_ARTIFACT_SAVED',
    spend_recorded: 'SSE_SPEND_RECORDED',
    journey_update: 'SSE_JOURNEY_UPDATE',
    session_end: 'SSE_SESSION_END',
    error: 'SSE_ERROR',
  };

  if (type === 'spend_recorded' && data.amount_usd != null && data.cost_usd == null) {
    data.cost_usd = data.amount_usd;
  }

  const action = eventMap[type];
  if (action) dispatch({ type: action, payload: data });

  switch (type) {
    case 'session_start':
      activity(dispatch, 'execution', 'Working on your request\u2026');
      break;
    case 'routing_decision':
      activity(dispatch, 'routing', `Selected ${data.strategy === 'FAN_OUT' ? 'multiple models' : 'best model'}`);
      break;
    case 'model_start':
      activity(dispatch, 'execution', `${data.model_id} is writing\u2026`);
      break;
    case 'model_complete':
      activity(dispatch, 'execution', `${data.model_id} finished`,
        data.tokens ? `${data.tokens} tokens` : undefined);
      break;
    case 'artifact_saved':
      activity(dispatch, 'artifact', `Result saved: ${data.title || data.id || 'output'}`);
      break;
    case 'spend_recorded':
      activity(dispatch, 'system', `Cost: $${(data.cost_usd || 0).toFixed(4)} (${data.model_id})`);
      break;
    case 'session_end':
      activity(dispatch, 'system', 'All done. See your results below.');
      break;
    case 'error':
      activity(dispatch, 'error', `Error: ${data.message || JSON.stringify(data)}`);
      break;
  }
}

/* ── Synthesize a context vector from cognitive response ── */
function synthesizeContext(query, data) {
  const survivors = data.tools_recommended || [];
  const cats = survivors.flatMap(t => t.categories || []);
  const comp = survivors.flatMap(t => t.compliance || []);
  const budgetMatch = /\$[\d,]+(?:\s*\/\s*mo(?:nth)?)?/i.exec(query)
    || /under\s+\$[\d,]+/i.exec(query)
    || /\bfree\b/i.exec(query);
  const skillHint = /\bno.?code\b|\blow.?code\b|\bdeveloper\b|\bengineering\b/i.exec(query);
  const taskValue = (data.plan || []).find(p =>
    typeof p === 'string' && p.length < 80 && !/^Step\s*\d/i.test(p) && !/sub-quer/i.test(p)
  ) || 'general';

  return {
    task_type: { value: taskValue, confidence: 0.7, reasoning: 'Inferred from query' },
    industry: { value: cats[0] || null, confidence: cats.length ? 0.5 : 0.2, reasoning: cats.length ? 'From tool categories' : 'Not specified' },
    budget: { value: budgetMatch ? budgetMatch[0] : null, confidence: budgetMatch ? 0.8 : 0.1, reasoning: budgetMatch ? 'Extracted from query' : 'Not specified' },
    compliance: { value: comp.length ? comp.slice(0, 3).join(', ') : null, confidence: comp.length ? 0.7 : 0.1, reasoning: comp.length ? 'From tool compliance data' : 'Not specified' },
    skill_level: { value: skillHint ? skillHint[0] : null, confidence: skillHint ? 0.6 : 0.2, reasoning: skillHint ? 'Keyword detected' : 'Not specified' },
  };
}

/* ── Generate a fallback artifact from narrative + survivors ── */
function buildFallbackArtifact(query, data) {
  const survivors = data.tools_recommended || [];
  const lines = [];
  if (data.narrative) lines.push(data.narrative);
  if (survivors.length) {
    lines.push('');
    lines.push(`### Recommended Stack (${survivors.length} tools)`);
    survivors.forEach((t, i) => {
      const score = t.fit_score != null ? ` \u2014 ${Math.round(t.fit_score <= 1 ? t.fit_score * 100 : t.fit_score)}% fit` : '';
      lines.push(`${i + 1}. **${t.name}**${score}`);
      if (t.description) lines.push(`   ${t.description.slice(0, 120)}`);
    });
  }
  if (data.caveats?.length) {
    lines.push('');
    lines.push('### Caveats');
    data.caveats.forEach(c => lines.push(`- ${c}`));
  }
  if (data.follow_up_questions?.length) {
    lines.push('');
    lines.push('### Follow-Up Questions');
    data.follow_up_questions.forEach(q => lines.push(`- ${q}`));
  }
  return {
    id: `fallback_${Date.now()}`,
    model_id: data.mode || 'praxis',
    artifact_type: 'recommendation',
    title: `Stack Recommendation: "${query}"`,
    content: lines.join('\n'),
    created_at: new Date().toISOString(),
  };
}

function buildQuery(text, selectedArtifact) {
  if (!selectedArtifact) return text;
  const priorTools = selectedArtifact.content
    ?.match(/\*\*(.+?)\*\*/g)
    ?.slice(0, 5)
    ?.map(m => m.replace(/\*\*/g, ''))
    ?.join(', ') || '';
  const contextHint = priorTools
    ? `Following up on a previous recommendation that included ${priorTools}. `
    : '';
  return contextHint + text;
}

function buildQueryWithHistory(text, history, selectedArtifact) {
  const recentTurns = history.slice(-2);
  const historyHint = recentTurns.length
    ? `Context from this session: ${recentTurns.map(t => `"${t.query}" returned ${t.survivors.join(', ')}`).join('. ')}. `
    : '';
  return historyHint + buildQuery(text, selectedArtifact);
}

/* ── SVG Icons ── */
const IconFind = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.5"/>
    <path d="M10.5 10.5L13 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
);
const IconCompare = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <path d="M3 3h4v10H3zM9 3h4v10H9z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
  </svg>
);
const IconExplain = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeWidth="1.5"/>
    <path d="M8 7v4M8 5.5v.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
);
const IconArrow = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
    <path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);
const IconStop = () => (
  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
    <rect x="2" y="2" width="8" height="8" rx="1.5" fill="currentColor"/>
  </svg>
);

/* ── Inline constraint popover ── */
function ConstraintPopover({ label, value, onSet, onClose }) {
  const [val, setVal] = useState(value || '');
  const ref = useRef(null);
  useEffect(() => { ref.current?.focus(); }, []);
  const commit = () => { onSet(val.trim()); onClose(); };
  return (
    <div className="absolute bottom-full mb-2 left-0 z-50 flex items-center gap-2 px-3 py-2 rounded-xl"
         style={{ background: 'rgba(15,15,20,0.95)', border: '1px solid rgba(255,255,255,0.1)', boxShadow: '0 8px 24px rgba(0,0,0,0.5)' }}>
      <span className="text-[10px] text-white/40 uppercase tracking-wider shrink-0">{label}</span>
      <input
        ref={ref}
        type="text"
        value={val}
        onChange={e => setVal(e.target.value)}
        onBlur={commit}
        onKeyDown={e => { if (e.key === 'Enter') commit(); if (e.key === 'Escape') onClose(); }}
        placeholder={label === 'Budget' ? '$300/mo' : label === 'Team' ? '5' : ''}
        className="bg-transparent border-b border-white/20 focus:border-indigo-500/60 outline-none text-xs text-white/80 w-24 py-0.5"
      />
    </div>
  );
}

const MODES = [
  { id: 'find', icon: IconFind, label: 'Find' },
  { id: 'compare', icon: IconCompare, label: 'Compare' },
  { id: 'explain', icon: IconExplain, label: 'Explain' },
];

const CONSTRAINT_KEYS = [
  { key: 'budget', label: 'Budget' },
  { key: 'team', label: 'Team' },
  { key: 'compliance', label: 'Compliance' },
  { key: 'industry', label: 'Industry' },
];

export default function IntentInput() {
  const { phase, room, query: stateQuery, artifacts, selectedArtifactId, activityLog, conversationHistory, differentialResult } = useRoomState();
  const dispatch = useRoomDispatch();
  const [text, setText] = useState('');
  const [mode, setMode] = useState('find');
  const [constraints, setConstraints] = useState({ budget: '', team: '', compliance: '', industry: '' });
  const [editingConstraint, setEditingConstraint] = useState(null);
  const textareaRef = useRef(null);
  const justSubmittedRef = useRef(false);

  useEffect(() => {
    if (justSubmittedRef.current) {
      justSubmittedRef.current = false;
      return;
    }
    if (stateQuery && !text) setText(stateQuery);
  }, [stateQuery]);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 140) + 'px';
    }
  }, [text]);

  const isRunning = phase === 'eliminating' || phase === 'executing';
  const activeConstraints = Object.entries(constraints).filter(([, v]) => v);

  const setConstraint = useCallback((key, value) => {
    setConstraints(prev => ({ ...prev, [key]: value }));
  }, []);

  const removeConstraint = useCallback((key) => {
    setConstraints(prev => ({ ...prev, [key]: '' }));
  }, []);

  /* ── Build final query with constraints appended ── */
  function buildFinalQuery(userText) {
    let q = userText;
    if (constraints.budget) q += `, budget: ${constraints.budget}`;
    if (constraints.team) q += `, team size: ${constraints.team}`;
    if (constraints.compliance) q += `, compliance: ${constraints.compliance}`;
    if (constraints.industry) q += `, industry: ${constraints.industry}`;
    return q;
  }

  /* ── Auto-execute: stream from /room/{id}/stream ── */
  async function autoExecute(dispatch, room, query, cognitiveData, refinementContext) {
    if (!room?.id) return;

    dispatch({ type: 'START_EXECUTION' });
    activity(dispatch, 'execution', 'Getting answers\u2026');

    let gotArtifact = false;
    try {
      const res = await fetch(`/room/${room.id}/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, profile_id: 'default', refinement_context: refinementContext }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6));
              if (event.type === 'artifact_saved') gotArtifact = true;
              handleSSEEvent(dispatch, event);
            } catch {}
          }
        }
      }
      if (buffer.startsWith('data: ')) {
        try {
          const event = JSON.parse(buffer.slice(6));
          if (event.type === 'artifact_saved') gotArtifact = true;
          handleSSEEvent(dispatch, event);
        } catch {}
      }
    } catch (err) {
      activity(dispatch, 'system', `Couldn't stream results: ${err.message}. Showing what we found.`);
    }

    if (!gotArtifact && cognitiveData.narrative) {
      const fallback = buildFallbackArtifact(query, cognitiveData);
      dispatch({ type: 'SSE_ARTIFACT_SAVED', payload: fallback });
      activity(dispatch, 'artifact', `Result saved: ${fallback.title}`);
    }

    dispatch({ type: 'EXECUTION_COMPLETE' });
  }

  const handleSubmit = async () => {
    if (!text.trim() || isRunning) return;

    const userText = text.trim();
    const selectedArtifact = selectedArtifactId
      ? artifacts.find(a => a.id === selectedArtifactId)
      : null;
    const refinementContext = selectedArtifact
      ? { artifact_id: selectedArtifact.id, artifact_title: selectedArtifact.title?.slice(0, 80) }
      : null;

    const withConstraints = buildFinalQuery(userText);
    const query = buildQueryWithHistory(withConstraints, conversationHistory, selectedArtifact);

    justSubmittedRef.current = true;
    setText('');
    dispatch({ type: 'SET_QUERY', payload: userText });

    if (activityLog.length > 0) {
      dispatch({ type: 'APPEND_ACTIVITY', payload: { kind: 'divider', text: '\u2500\u2500\u2500 New query \u2500\u2500\u2500' } });
    }

    if (differentialResult) {
      const prevSurvivors = differentialResult.tools_recommended || differentialResult.survivors || [];
      dispatch({
        type: 'ARCHIVE_QUERY',
        payload: {
          query: stateQuery,
          toolsConsidered: differentialResult.tools_considered || prevSurvivors.length,
          matchCount: prevSurvivors.length,
          survivors: prevSurvivors.slice(0, 5).map(s => s.name || 'unknown'),
        },
      });
    }

    dispatch({ type: 'START_ELIMINATION' });
    activity(dispatch, 'system', `Understanding: "${userText}"`);
    activity(dispatch, 'elimination', 'Scanning 246 tools\u2026');

    const controller = new AbortController();
    const timeoutWarning = setTimeout(() => {
      activity(dispatch, 'system', 'Still working \u2014 this is taking a bit longer than usual\u2026');
    }, 30000);
    const hardTimeout = setTimeout(() => controller.abort(), 60000);

    try {
      const res = await fetch('/cognitive', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, profile_id: 'default', include_trace: true, refinement_context: refinementContext }),
        signal: controller.signal,
      });
      clearTimeout(timeoutWarning);
      clearTimeout(hardTimeout);

      let data;
      const contentType = res.headers.get('content-type') || '';
      if (!res.ok || !contentType.includes('application/json')) {
        const body = await res.text();
        data = {
          error: res.status === 404
            ? 'Cognitive pipeline not found. Is the server running on port 8000?'
            : `Server returned ${res.status}: ${body.slice(0, 100)}`,
          query: query,
          tools_recommended: [],
          eliminated: [],
          narrative: '',
        };
      } else {
        data = await res.json();
      }

      if (data.error) {
        activity(dispatch, 'error', `Something went wrong: ${data.error}`);
      }

      const survivors = data.tools_recommended || data.survivors || [];
      const totalEval = data.tools_considered || survivors.length;
      if (totalEval > 0) {
        activity(dispatch, 'elimination',
          `Reviewed ${totalEval} tools. ${survivors.length} match your needs.`);
      }
      if (survivors.length > 0) {
        const names = survivors.slice(0, 5).map(s => s.name || s.tool || 'unknown');
        activity(dispatch, 'routing',
          `Top matches: ${names.join(', ')}${survivors.length > 5 ? ` +${survivors.length - 5} more` : ''}`);
      }

      data.query = data.query || query;
      dispatch({ type: 'SET_DIFFERENTIAL_RESULT', payload: data });

      const ctx = data.context_vector || synthesizeContext(userText, data);
      dispatch({ type: 'SET_CONTEXT_VECTOR', payload: ctx });

      dispatch({
        type: 'SET_HEALTH_DATA',
        payload: {
          models: {
            [data.mode || 'local']: {
              status: data.error ? 'degraded' : 'healthy',
              latency_ms: data.total_elapsed_ms || 0,
              tools_evaluated: data.tools_considered || survivors.length,
            },
          },
        },
      });

      if (!data.error && survivors.length > 0) {
        await autoExecute(dispatch, room, query, data, refinementContext);
      } else if (data.narrative) {
        const fallback = buildFallbackArtifact(query, data);
        dispatch({ type: 'SSE_ARTIFACT_SAVED', payload: fallback });
        dispatch({ type: 'EXECUTION_COMPLETE' });
      } else {
        dispatch({ type: 'EXECUTION_COMPLETE' });
      }

      dispatch({
        type: 'APPEND_CONVERSATION_TURN',
        payload: {
          query: userText,
          survivors: survivors.slice(0, 5).map(s => s.name || s.tool || 'unknown'),
          timestamp: Date.now(),
        },
      });
    } catch (err) {
      clearTimeout(timeoutWarning);
      clearTimeout(hardTimeout);
      const msg = err.name === 'AbortError'
        ? 'Request timed out after 60s. Try a simpler query.'
        : `Routing error: ${err.message}`;
      activity(dispatch, 'error', msg);
      dispatch({ type: 'SET_ERROR', payload: msg });
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="relative z-20 px-4 py-4">
      <div
        className="max-w-3xl mx-auto"
        style={{
          background: 'rgba(15, 15, 20, 0.88)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: '20px',
          boxShadow: '0 8px 40px rgba(0,0,0,0.5), 0 1px 0 rgba(255,255,255,0.05) inset',
          padding: '12px 16px',
        }}
      >
        {/* ── Top strip: active constraints ── */}
        <AnimatePresence>
          {activeConstraints.length > 0 && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="flex flex-wrap gap-1.5 pb-2 mb-2 overflow-hidden"
              style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}
            >
              {activeConstraints.map(([key, val]) => (
                <span
                  key={key}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px]"
                  style={{ border: '1px solid rgba(99,102,241,0.4)', color: '#a5b4fc', background: 'rgba(99,102,241,0.08)' }}
                >
                  {key}: {val}
                  <button
                    onClick={() => removeConstraint(key)}
                    className="text-white/30 hover:text-white/70 ml-0.5"
                  >{'\u00d7'}</button>
                </span>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Middle: mode icons + textarea ── */}
        <div className="flex items-start gap-3">
          {/* Mode column */}
          <div className="flex flex-col gap-1 pt-1 shrink-0">
            {MODES.map(m => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                className={`w-9 h-9 flex items-center justify-center rounded-lg transition-all ${
                  mode === m.id
                    ? 'bg-indigo-500/20 text-indigo-400'
                    : 'text-white/30 hover:text-white/60 hover:bg-white/5'
                }`}
                title={m.label}
              >
                <m.icon />
              </button>
            ))}
          </div>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={selectedArtifactId && artifacts.length > 0
              ? "Refine this result \u2014 ask a follow-up question\u2026"
              : "What do you want to build?"}
            disabled={isRunning}
            rows={1}
            className="flex-1 resize-none bg-transparent outline-none text-sm text-white/80 placeholder-white/20 py-2 min-h-[36px] max-h-[140px] disabled:opacity-40"
          />
        </div>

        {/* ── Bottom row: constraint chips + submit ── */}
        <div className="flex items-center justify-between gap-3 mt-2 pt-2" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          {isRunning ? (
            <div className="flex items-center gap-2 flex-1">
              <motion.div
                className="w-2 h-2 rounded-full bg-indigo-400"
                animate={{ opacity: [0.4, 1, 0.4] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
              <span className="text-[11px] text-white/40">Running\u2026</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 flex-1 flex-wrap">
              {CONSTRAINT_KEYS.map(({ key, label }) => (
                <div key={key} className="relative">
                  <button
                    onClick={() => setEditingConstraint(editingConstraint === key ? null : key)}
                    className={`px-2.5 py-1 rounded-full text-[11px] border transition-all whitespace-nowrap ${
                      constraints[key]
                        ? 'border-indigo-500/50 text-indigo-300/80 bg-indigo-500/8'
                        : 'border-white/10 text-white/40 hover:border-indigo-500/40 hover:text-white/70'
                    }`}
                  >
                    + {label}
                  </button>
                  {editingConstraint === key && (
                    <ConstraintPopover
                      label={label}
                      value={constraints[key]}
                      onSet={(v) => setConstraint(key, v)}
                      onClose={() => setEditingConstraint(null)}
                    />
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Submit / Stop button */}
          <motion.button
            whileHover={!isRunning && text.trim() ? { scale: 1.08 } : {}}
            whileTap={!isRunning && text.trim() ? { scale: 0.95 } : {}}
            onClick={handleSubmit}
            disabled={!text.trim() && !isRunning}
            className="shrink-0 w-9 h-9 rounded-full flex items-center justify-center transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            style={{
              background: isRunning ? 'rgba(239,68,68,0.7)' : '#6366f1',
              boxShadow: !isRunning && text.trim() ? '0 0 16px rgba(99,102,241,0.4)' : 'none',
              color: 'white',
            }}
          >
            {isRunning ? <IconStop /> : <IconArrow />}
          </motion.button>
        </div>
      </div>
    </div>
  );
}
