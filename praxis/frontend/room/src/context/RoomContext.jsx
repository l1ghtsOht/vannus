import { createContext, useContext, useReducer } from 'react';

const RoomContext = createContext(null);
const RoomDispatchContext = createContext(null);

export const PHASES = {
  IDLE: 'idle',
  ELIMINATING: 'eliminating',
  ROUTING: 'routing',
  EXECUTING: 'executing',
  COMPLETE: 'complete',
};

const initialState = {
  room: null,
  rooms: [],
  session: null,
  phase: PHASES.IDLE,
  query: '',

  // Context extraction
  contextVector: null,

  // Elimination
  differentialResult: null,

  // Routing
  routingDecision: null,

  // Execution
  executionEvents: [],
  streamingBuffers: {},
  activeModels: [],

  // Artifacts
  artifacts: [],
  selectedArtifactId: null,

  // Cost
  cost: { total: 0, perModel: {} },

  // Trust
  trustAlerts: [],
  healthData: null,

  // Activity feed
  activityLog: [],

  // Conversation history for multi-turn context
  conversationHistory: [],

  // Director stack — user-curated tool selections
  pinnedTools: [],   // array of tool name strings
  passedTools: [],   // array of tool name strings

  // Query history for multi-query collapse
  queryHistory: [],  // array of { query, toolsConsidered, matchCount, survivors }

  // UI
  leftPanelOpen: false,
  rightPanelOpen: false,
  error: null,
};

let _activityId = 0;

/* Normalize backend room objects: room_id → id */
function normalizeRoom(room) {
  if (!room) return room;
  if (room.id) return room;
  if (room.room_id) return { ...room, id: room.room_id };
  return room;
}

function roomReducer(state, action) {
  switch (action.type) {
    // ── Room Management ──
    case 'SET_ROOM':
      return { ...state, room: normalizeRoom(action.payload), error: null };
    case 'SET_ROOMS':
      return { ...state, rooms: (action.payload || []).map(normalizeRoom) };
    case 'UPDATE_ROOM_NAME':
      return { ...state, room: state.room ? { ...state.room, name: action.payload } : null };

    // ── Query ──
    case 'SET_QUERY':
      return { ...state, query: action.payload };

    // ── Phase Transitions ──
    case 'START_ELIMINATION':
      return {
        ...state,
        phase: PHASES.ELIMINATING,
        differentialResult: null,
        routingDecision: null,
        executionEvents: [],
        streamingBuffers: {},
        activeModels: [],
        selectedArtifactId: null,
        error: null,
      };
    case 'NEW_CONVERSATION':
      return {
        ...initialState,
        room: state.room,
        rooms: state.rooms,
      };
    case 'SET_DIFFERENTIAL_RESULT':
      return { ...state, differentialResult: action.payload, phase: PHASES.ROUTING };
    case 'SET_ROUTING_DECISION':
      return { ...state, routingDecision: action.payload };
    case 'START_EXECUTION':
      return {
        ...state,
        phase: PHASES.EXECUTING,
        executionEvents: [],
        streamingBuffers: {},
        activeModels: [],
        cost: { total: 0, perModel: {} },
      };
    case 'EXECUTION_COMPLETE':
      return { ...state, phase: PHASES.COMPLETE };

    // ── SSE Events ──
    case 'SSE_SESSION_START':
      return {
        ...state,
        session: action.payload,
        phase: PHASES.EXECUTING,
      };
    case 'SSE_CONTEXT_EXTRACTED':
      return { ...state, contextVector: action.payload };
    case 'SSE_ROUTING_DECISION':
      return { ...state, routingDecision: action.payload };
    case 'SSE_MODEL_START':
      return {
        ...state,
        activeModels: [...state.activeModels, action.payload.model_id],
        streamingBuffers: {
          ...state.streamingBuffers,
          [action.payload.model_id]: '',
        },
      };
    case 'SSE_TOKEN_CHUNK':
      return {
        ...state,
        streamingBuffers: {
          ...state.streamingBuffers,
          [action.payload.model_id]: (state.streamingBuffers[action.payload.model_id] || '') + action.payload.chunk,
        },
      };
    case 'SSE_MODEL_COMPLETE':
      return {
        ...state,
        activeModels: state.activeModels.filter(id => id !== action.payload.model_id),
      };
    case 'SSE_COLLABORATION_RESULT':
      return { ...state, routingDecision: { ...state.routingDecision, collaborationResult: action.payload } };
    case 'SSE_ARTIFACT_SAVED': {
      const newArtifacts = [...state.artifacts, action.payload];
      return { ...state, artifacts: newArtifacts, selectedArtifactId: action.payload.id || null, rightPanelOpen: true };
    }
    case 'SSE_SPEND_RECORDED':
      return {
        ...state,
        cost: {
          total: state.cost.total + (action.payload.cost_usd || 0),
          perModel: {
            ...state.cost.perModel,
            [action.payload.model_id]: (state.cost.perModel[action.payload.model_id] || 0) + (action.payload.cost_usd || 0),
          },
        },
      };
    case 'SSE_JOURNEY_UPDATE':
      return state; // handled by artifacts refresh
    case 'SSE_SESSION_END':
      return { ...state, phase: PHASES.COMPLETE };
    case 'SSE_ERROR':
      return { ...state, error: action.payload, phase: PHASES.IDLE };

    // ── Generic SSE event append ──
    case 'APPEND_EVENT':
      return { ...state, executionEvents: [...state.executionEvents, action.payload] };

    // ── Activity feed ──
    case 'APPEND_ACTIVITY':
      return {
        ...state,
        activityLog: [...state.activityLog, { id: ++_activityId, timestamp: Date.now(), ...action.payload }],
      };
    case 'CLEAR_ACTIVITY':
      return { ...state, activityLog: [] };

    // ── Conversation History ──
    case 'APPEND_CONVERSATION_TURN':
      return {
        ...state,
        conversationHistory: [...state.conversationHistory, action.payload],
      };

    // ── Context ──
    case 'SET_CONTEXT_VECTOR':
      return { ...state, contextVector: action.payload };

    // ── Artifacts ──
    case 'SET_ARTIFACTS':
      return { ...state, artifacts: action.payload };
    case 'SET_SELECTED_ARTIFACT':
      return { ...state, selectedArtifactId: action.payload };

    // ── Trust ──
    case 'SET_TRUST_ALERTS':
      return { ...state, trustAlerts: action.payload };
    case 'SET_HEALTH_DATA':
      return { ...state, healthData: action.payload };

    // ── Director Stack ──
    case 'PIN_TOOL': {
      const name = action.payload;
      if (state.pinnedTools.includes(name)) return state;
      return {
        ...state,
        pinnedTools: [...state.pinnedTools, name],
        passedTools: state.passedTools.filter(n => n !== name),
        rightPanelOpen: true,
      };
    }
    case 'UNPIN_TOOL':
      return { ...state, pinnedTools: state.pinnedTools.filter(n => n !== action.payload) };
    case 'REORDER_PINNED_TOOLS':
      return { ...state, pinnedTools: action.payload };
    case 'PASS_TOOL': {
      const name = action.payload;
      if (state.passedTools.includes(name)) return state;
      return {
        ...state,
        passedTools: [...state.passedTools, name],
        pinnedTools: state.pinnedTools.filter(n => n !== name),
      };
    }
    case 'UNPASS_TOOL':
      return { ...state, passedTools: state.passedTools.filter(n => n !== action.payload) };

    // ── Query History ──
    case 'ARCHIVE_QUERY':
      return { ...state, queryHistory: [...state.queryHistory, action.payload] };

    // ── UI ──
    case 'TOGGLE_LEFT_PANEL':
      return { ...state, leftPanelOpen: !state.leftPanelOpen };
    case 'TOGGLE_RIGHT_PANEL':
      return { ...state, rightPanelOpen: !state.rightPanelOpen };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'RESET':
      return { ...initialState, room: state.room, rooms: state.rooms };

    default:
      return state;
  }
}

export function RoomProvider({ children }) {
  const [state, dispatch] = useReducer(roomReducer, initialState);
  return (
    <RoomContext.Provider value={state}>
      <RoomDispatchContext.Provider value={dispatch}>
        {children}
      </RoomDispatchContext.Provider>
    </RoomContext.Provider>
  );
}

export function useRoomState() {
  const context = useContext(RoomContext);
  if (!context && context !== initialState) throw new Error('useRoomState must be used within RoomProvider');
  return context;
}

export function useRoomDispatch() {
  const context = useContext(RoomDispatchContext);
  if (!context) throw new Error('useRoomDispatch must be used within RoomProvider');
  return context;
}
