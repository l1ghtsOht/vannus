// Session ID — UUID v4, no crypto dependency
export function generateSessionId() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}

// Fire-and-forget POST — never blocks UI
function postFeedback(endpoint, data) {
  fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).catch(() => {});
}

export function submitSearchFeedback(sessionId, queryText, constraints, survivors, eliminatedCount, rating, comment) {
  postFeedback('/feedback/search', {
    session_id: sessionId,
    query_text: queryText,
    constraints: constraints || [],
    survivors: survivors || [],
    eliminated_count: eliminatedCount || 0,
    rating,
    comment: comment || null,
  });
}

export function submitToolFeedback(sessionId, toolName, currentTier, suggestedTier, flagType, reason) {
  postFeedback('/feedback/tool', {
    session_id: sessionId,
    tool_name: toolName,
    current_tier: currentTier,
    suggested_tier: suggestedTier || null,
    flag_type: flagType,
    reason: reason || null,
  });
}

export function trackEvent(sessionId, eventType, payload) {
  postFeedback('/feedback/event', {
    session_id: sessionId,
    event_type: eventType,
    payload: payload || {},
  });
}
