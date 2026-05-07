import { useState, useCallback, useRef } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

interface UseQAStreamOptions {
  projectId: string;
  sessionId: string;
  onChunk?: (content: string) => void;
  onCitation?: (citationId: string) => void;
  onDone?: (citations: string[], contextUsed: string[]) => void;
  onError?: (error: string) => void;
}

interface UseQAStreamResult {
  answer: string;
  citations: string[];
  contextUsed: string[];
  isStreaming: boolean;
  error: string | null;
  lastQuestion: string | null;
  lastContextMode: 'basic' | 'enhanced' | 'full';
  ask: (question: string, contextMode?: 'basic' | 'enhanced' | 'full') => void;
  stop: () => void;
  reset: () => void;
  retry: () => void;
}

export function useQAStream({
  projectId,
  sessionId,
  onChunk,
  onCitation,
  onDone,
  onError,
}: UseQAStreamOptions): UseQAStreamResult {
  const [answer, setAnswer] = useState('');
  const [citations, setCitations] = useState<string[]>([]);
  const [contextUsed, setContextUsed] = useState<string[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);
  const [lastContextMode, setLastContextMode] = useState<'basic' | 'enhanced' | 'full'>('basic');

  // Refs for performance optimization
  const abortControllerRef = useRef<AbortController | null>(null);
  const answerBufferRef = useRef('');
  const rafIdRef = useRef<number | null>(null);
  const pendingUpdateRef = useRef(false);

  // Batch update answer using requestAnimationFrame
  const scheduleAnswerUpdate = useCallback(() => {
    if (pendingUpdateRef.current) return;
    
    pendingUpdateRef.current = true;
    rafIdRef.current = requestAnimationFrame(() => {
      setAnswer(answerBufferRef.current);
      pendingUpdateRef.current = false;
    });
  }, []);

  const stop = useCallback(() => {
    // Abort the fetch request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    
    // Cancel pending RAF
    if (rafIdRef.current) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }
    
    // Final update with buffered content
    if (answerBufferRef.current) {
      setAnswer(answerBufferRef.current);
    }
    
    setIsStreaming(false);
    pendingUpdateRef.current = false;
  }, []);

  const reset = useCallback(() => {
    setAnswer('');
    setCitations([]);
    setContextUsed([]);
    setError(null);
    answerBufferRef.current = '';
    stop();
  }, [stop]);

  const ask = useCallback(
    (question: string, contextMode: 'basic' | 'enhanced' | 'full' = 'basic') => {
      // Store for retry
      setLastQuestion(question);
      setLastContextMode(contextMode);
      
      // Reset state
      setAnswer('');
      setCitations([]);
      setContextUsed([]);
      setError(null);
      setIsStreaming(true);
      answerBufferRef.current = '';

      // Abort previous request if exists
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      
      // Create new AbortController
      abortControllerRef.current = new AbortController();

      // Build URL with query params
      const url = new URL(
        `${API_BASE}/projects/${projectId}/qa/sessions/${sessionId}/ask-stream`,
        window.location.origin
      );

      const askStream = async () => {
        try {
          const response = await fetch(url.toString(), {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              question,
              context_mode: contextMode,
            }),
            signal: abortControllerRef.current?.signal,
          });

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }

          if (!response.body) {
            throw new Error('Response body is null');
          }

          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              // Final sync update
              if (answerBufferRef.current) {
                setAnswer(answerBufferRef.current);
              }
              setIsStreaming(false);
              break;
            }

            buffer += decoder.decode(value, { stream: true });

            // Process complete SSE messages
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            for (const line of lines) {
              if (!line.trim()) continue;

              if (line.startsWith('event:')) {
                // Event type line
                continue;
              }

              if (line.startsWith('data:')) {
                const dataStr = line.slice(5).trim();
                try {
                  const data = JSON.parse(dataStr);

                  if (data.type === 'text' && data.content) {
                    // Buffer the content and schedule update
                    answerBufferRef.current += data.content;
                    scheduleAnswerUpdate();
                    onChunk?.(data.content);
                  } else if (data.type === 'citation' && data.citation_id) {
                    setCitations((prev) => [...prev, data.citation_id]);
                    onCitation?.(data.citation_id);
                  } else if (data.type === 'done') {
                    const finalCitations = data.citations || [];
                    const finalContext = data.context_used || [];
                    setCitations(finalCitations);
                    setContextUsed(finalContext);
                    setIsStreaming(false);
                    // Ensure final answer is set
                    setAnswer(answerBufferRef.current);
                    onDone?.(finalCitations, finalContext);
                  } else if (data.type === 'error' || data.error) {
                    const errorMsg = data.error || data.content || 'Unknown error';
                    setError(errorMsg);
                    setIsStreaming(false);
                    onError?.(errorMsg);
                  }
                } catch (e) {
                  console.error('Failed to parse SSE data:', e, dataStr);
                }
              }
            }
          }
        } catch (err) {
          // Ignore abort errors
          if (err instanceof Error && err.name === 'AbortError') {
            return;
          }
          
          const errorMsg = err instanceof Error ? err.message : 'Stream failed';
          setError(errorMsg);
          setIsStreaming(false);
          onError?.(errorMsg);
        }
      };

      askStream();
    },
    [projectId, sessionId, onChunk, onCitation, onDone, onError, scheduleAnswerUpdate]
  );

  // Retry with last question
  const retry = useCallback(() => {
    if (lastQuestion) {
      ask(lastQuestion, lastContextMode);
    }
  }, [ask, lastQuestion, lastContextMode]);

  return {
    answer,
    citations,
    contextUsed,
    isStreaming,
    error,
    lastQuestion,
    lastContextMode,
    ask,
    stop,
    reset,
    retry,
  };
}
