import { useCallback } from 'react';
import { useRoomDispatch } from '../context/RoomContext';

export default function useExecution() {
  const dispatch = useRoomDispatch();

  const execute = useCallback(async (roomId, query, profileId = 'default') => {
    dispatch({ type: 'START_EXECUTION' });

    try {
      const res = await fetch(`/room/${encodeURIComponent(roomId)}/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, profile_id: profileId }),
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
              dispatchSSE(dispatch, event);
            } catch {}
          }
        }
      }
      if (buffer.startsWith('data: ')) {
        try {
          const event = JSON.parse(buffer.slice(6));
          dispatchSSE(dispatch, event);
        } catch {}
      }
      dispatch({ type: 'EXECUTION_COMPLETE' });
    } catch (err) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
    }
  }, [dispatch]);

  return { execute };
}

function dispatchSSE(dispatch, event) {
  const { type, ...data } = event;
  dispatch({ type: 'APPEND_EVENT', payload: event });

  const map = {
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

  const action = map[type];
  if (action) dispatch({ type: action, payload: data });
}
