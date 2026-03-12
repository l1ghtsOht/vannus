import { useCallback } from 'react';
import { useRoomState, useRoomDispatch } from '../context/RoomContext';

export default function useArtifacts() {
  const { artifacts, room } = useRoomState();
  const dispatch = useRoomDispatch();

  const loadArtifacts = useCallback(async (roomId) => {
    const id = roomId || room?.id;
    if (!id) return [];
    try {
      const res = await fetch(`/room/${encodeURIComponent(id)}/artifact`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      dispatch({ type: 'SET_ARTIFACTS', payload: data });
      return data;
    } catch (err) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
      return [];
    }
  }, [dispatch, room]);

  return { artifacts, loadArtifacts };
}
