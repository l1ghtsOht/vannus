import { useCallback } from 'react';
import { useRoomDispatch } from '../context/RoomContext';

export default function useRouting() {
  const dispatch = useRoomDispatch();

  const runElimination = useCallback(async (query, profileId = 'default') => {
    dispatch({ type: 'START_ELIMINATION' });

    try {
      const res = await fetch('/cognitive', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          profile_id: profileId,
          include_trace: true,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      dispatch({ type: 'SET_DIFFERENTIAL_RESULT', payload: data });
      if (data.context_vector) {
        dispatch({ type: 'SET_CONTEXT_VECTOR', payload: data.context_vector });
      }
      return data;
    } catch (err) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
      return null;
    }
  }, [dispatch]);

  return { runElimination };
}
