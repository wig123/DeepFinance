import { useState, useEffect, useCallback } from 'react';
import { createQASession, getQASession, getQASuggestions } from '../api';
import type { QASession, QASuggestionsResponse } from '../types';

interface UseQASessionResult {
  session: QASession | null;
  sessionId: string | null;
  suggestions: string[];
  isLoading: boolean;
  error: string | null;
  createSession: () => Promise<void>;
  refreshSession: () => Promise<void>;
  loadSuggestions: () => Promise<void>;
}

export function useQASession(projectId: string): UseQASessionResult {
  const [session, setSession] = useState<QASession | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Create a new QA session
  const createSession = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await createQASession(projectId);
      const newSession = response.session;
      setSession(newSession);
      setSessionId(newSession.session_id);

      // Store session ID in localStorage for persistence
      localStorage.setItem(`qa_session_${projectId}`, newSession.session_id);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to create session';
      setError(errorMsg);
      console.error('Failed to create QA session:', err);
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  // Refresh session data (fetch latest messages)
  const refreshSession = useCallback(async () => {
    if (!sessionId) return;

    try {
      const response = await getQASession(projectId, sessionId);
      setSession(response.session);
    } catch (err) {
      console.error('Failed to refresh session:', err);
    }
  }, [projectId, sessionId]);

  // Load question suggestions
  const loadSuggestions = useCallback(async () => {
    try {
      const response: QASuggestionsResponse = await getQASuggestions(projectId);
      setSuggestions(response.suggestions);
    } catch (err) {
      console.error('Failed to load suggestions:', err);
      // Set default suggestions on error
      setSuggestions([
        '请总结报告的核心内容',
        '报告中有哪些关键发现?',
        '有哪些值得关注的数据指标?',
      ]);
    }
  }, [projectId]);

  // Auto-create session on mount or restore from localStorage
  useEffect(() => {
    const storedSessionId = localStorage.getItem(`qa_session_${projectId}`);

    if (storedSessionId) {
      // Try to restore session
      setSessionId(storedSessionId);
      getQASession(projectId, storedSessionId)
        .then((response) => {
          setSession(response.session);
        })
        .catch((err) => {
          console.error('Failed to restore session:', err);
          // If restoration fails, create a new session
          createSession();
        });
    } else {
      // No stored session, create new one
      createSession();
    }

    // Load suggestions
    loadSuggestions();
  }, [projectId]); // Only run on mount or projectId change

  return {
    session,
    sessionId,
    suggestions,
    isLoading,
    error,
    createSession,
    refreshSession,
    loadSuggestions,
  };
}
