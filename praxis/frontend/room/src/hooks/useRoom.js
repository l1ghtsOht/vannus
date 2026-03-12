import { useCallback } from 'react';
import { useRoomState, useRoomDispatch } from '../context/RoomContext';

export default function useRoom() {
  const state = useRoomState();
  const dispatch = useRoomDispatch();

  const createRoom = useCallback(async (name = 'Untitled Room') => {
    try {
      const res = await fetch('/room', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, operator_context: {} }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const room = await res.json();
      dispatch({ type: 'SET_ROOM', payload: room });
      return room;
    } catch (err) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
      return null;
    }
  }, [dispatch]);

  const loadRoom = useCallback(async (roomId) => {
    try {
      const res = await fetch(`/room/${encodeURIComponent(roomId)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const room = await res.json();
      dispatch({ type: 'SET_ROOM', payload: room });
      return room;
    } catch (err) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
      return null;
    }
  }, [dispatch]);

  const listRooms = useCallback(async () => {
    try {
      const res = await fetch('/room');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const rooms = await res.json();
      dispatch({ type: 'SET_ROOMS', payload: rooms });
      return rooms;
    } catch (err) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
      return [];
    }
  }, [dispatch]);

  const updateRoom = useCallback(async (roomId, updates) => {
    try {
      const res = await fetch(`/room/${encodeURIComponent(roomId)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const room = await res.json();
      dispatch({ type: 'SET_ROOM', payload: room });
      return room;
    } catch (err) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
      return null;
    }
  }, [dispatch]);

  const eliminateModel = useCallback(async (roomId, modelId, reason) => {
    try {
      const res = await fetch(`/room/${encodeURIComponent(roomId)}/eliminate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId, reason }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
      return null;
    }
  }, [dispatch]);

  const readmitModel = useCallback(async (roomId, modelId) => {
    try {
      const res = await fetch(`/room/${encodeURIComponent(roomId)}/readmit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
      return null;
    }
  }, [dispatch]);

  return {
    ...state,
    createRoom,
    loadRoom,
    listRooms,
    updateRoom,
    eliminateModel,
    readmitModel,
  };
}
