import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useRoomState, useRoomDispatch } from '../../context/RoomContext';

function activity(dispatch, type, text, detail) {
  dispatch({ type: 'APPEND_ACTIVITY', payload: { kind: type, text, detail } });
}

/* ── SSE stream parser (shared with RoutingPlan) ── */
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

  const action = eventMap[type];
  if (action) dispatch({ type: action, payload: data });

  switch (type) {
    case 'session_start':
      activity(dispatch, 'execution', 'Working on your request…');
      break;
    case 'routing_decision':
      activity(dispatch, 'routing', `Selected ${data.strategy === 'FAN_OUT' ? 'multiple models' : 'best model'}`);
      break;
    case 'model_start':
      activity(dispatch, 'execution', `${data.model_id} is writing…`);
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
  const hasBudget = /\$\d+|\bfree\b|\bbudget\b|\bunder\b/i.exec(query);
  const skillHint = /\bno.?code\b|\blow.?code\b|\bdeveloper\b|\bengineering\b/i.exec(query);

  return {
    task_type: { value: data.plan?.[0] || 'general', confidence: 0.7, reasoning: 'Inferred from query' },
    industry: { value: cats[0] || null, confidence: cats.length ? 0.5 : 0.2, reasoning: cats.length ? 'From tool categories' : 'Not specified' },
    budget: { value: hasBudget ? hasBudget[0] : null, confidence: hasBudget ? 0.8 : 0.1, reasoning: hasBudget ? 'Extracted from query' : 'Not specified' },
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
      const score = t.fit_score != null ? ` — ${Math.round(t.fit_score <= 1 ? t.fit_score * 100 : t.fit_score)}% fit` : '';
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

/* ── Build query with session context for multi-turn conversations ── */
function buildQuery(text, selectedArtifact) {
  if (!selectedArtifact) return text;
  // Extract tool names from prior artifact content
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

export default function IntentInput() {
  const { phase, room, query: stateQuery, artifacts, selectedArtifactId, activityLog, conversationHistory } = useRoomState();
  const dispatch = useRoomDispatch();
  const [text, setText] = useState('');
  const [focused, setFocused] = useState(false);
  const textareaRef = useRef(null);
  const justSubmittedRef = useRef(false);

  // Allow suggestion chips or SET_QUERY to populate the text field
  useEffect(() => {
    if (justSubmittedRef.current) {
      justSubmittedRef.current = false;
      return;
    }
    if (stateQuery && !text) setText(stateQuery);
  }, [stateQuery]);

  const isRunning = phase === 'eliminating' || phase === 'executing';

  /* ── Auto-execute: stream from /room/{id}/stream ── */
  async function autoExecute(dispatch, room, query, cognitiveData, refinementContext) {
    if (!room) return; // no room — skip streaming, fallback artifact will still render

    dispatch({ type: 'START_EXECUTION' });
    activity(dispatch, 'execution', 'Getting answers…');

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

    // Fallback artifact if stream produced none
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

    // Build enriched query with session context for the backend
    const query = buildQueryWithHistory(userText, conversationHistory, selectedArtifact);

    justSubmittedRef.current = true;
    setText('');
    dispatch({ type: 'SET_QUERY', payload: userText });

    // Visual divider between conversation turns
    if (activityLog.length > 0) {
      dispatch({ type: 'APPEND_ACTIVITY', payload: { kind: 'divider', text: '─── New query ───' } });
    }

    dispatch({ type: 'START_ELIMINATION' });
    activity(dispatch, 'system', `Understanding: "${userText}"`);
    activity(dispatch, 'elimination', 'Finding the best tools…');

    const controller = new AbortController();
    const timeoutWarning = setTimeout(() => {
      activity(dispatch, 'system', 'Still working — this is taking a bit longer than usual…');
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

      // Handle backend error payload (200 with error field)
      if (data.error) {
        activity(dispatch, 'error', `Something went wrong: ${data.error}`);
      }

      // Emit elimination activity
      const survivors = data.tools_recommended || data.survivors || [];
      const totalEval = data.tools_considered || survivors.length;
      const eliminatedCount = totalEval - survivors.length;
      if (totalEval > 0) {
        activity(dispatch, 'elimination',
          `Reviewed ${totalEval} tools. ${survivors.length} match your needs.`);
      }
      if (survivors.length > 0) {
        const names = survivors.slice(0, 5).map(s => s.name || s.tool || 'unknown');
        activity(dispatch, 'routing',
          `Recommended: ${names.join(', ')}${survivors.length > 5 ? ` +${survivors.length - 5} more` : ''}`);
      }

      // Store the query on the data for downstream use
      data.query = data.query || query;
      dispatch({ type: 'SET_DIFFERENTIAL_RESULT', payload: data });

      // Synthesize context vector from response data
      const ctx = data.context_vector || synthesizeContext(userText, data);
      dispatch({ type: 'SET_CONTEXT_VECTOR', payload: ctx });

      // Populate trust monitor with pipeline health
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

      // Auto-execute: skip the "Execute Plan" click
      if (!data.error && survivors.length > 0) {
        await autoExecute(dispatch, room, query, data, refinementContext);
      } else if (data.narrative) {
        // No survivors but have narrative — generate fallback artifact directly
        const fallback = buildFallbackArtifact(query, data);
        dispatch({ type: 'SSE_ARTIFACT_SAVED', payload: fallback });
        dispatch({ type: 'EXECUTION_COMPLETE' });
      } else {
        dispatch({ type: 'EXECUTION_COMPLETE' });
      }

      // Record this turn for multi-turn context
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
    <motion.div
      layout
      className="relative z-20 border-t border-white/[0.06] px-4 py-3"
      style={{ background: 'rgba(10,10,15,0.6)', backdropFilter: 'blur(20px)' }}
    >
      <div className="flex items-end gap-3 max-w-4xl mx-auto">
        <motion.div
          layout
          className="flex-1 relative"
        >
          <textarea
            ref={textareaRef}
            value={text}
            onChange={e => setText(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            onKeyDown={handleKeyDown}
            placeholder={selectedArtifactId && artifacts.length > 0
              ? "Refine this result — ask a follow-up question…"
              : "What do you want to build?"}
            disabled={isRunning}
            rows={focused || text ? 3 : 1}
            className="w-full resize-none bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 text-sm text-white/80 placeholder-white/20 outline-none transition-all focus:border-[#6366f1]/40 focus:bg-white/[0.06] disabled:opacity-40"
          />
        </motion.div>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleSubmit}
          disabled={!text.trim() || isRunning}
          className="shrink-0 px-5 py-3 rounded-xl text-sm font-medium transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          style={{
            background: isRunning
              ? 'rgba(99,102,241,0.15)'
              : 'rgba(99,102,241,0.25)',
            border: '1px solid rgba(99,102,241,0.3)',
            color: 'rgba(255,255,255,0.85)',
            boxShadow: !isRunning && text.trim() ? '0 0 20px rgba(99,102,241,0.15)' : 'none',
          }}
        >
          {isRunning ? (
            <motion.span
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              Thinking…
            </motion.span>
          ) : (
            'Run'
          )}
        </motion.button>
      </div>
    </motion.div>
  );
}
