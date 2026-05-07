import { useState, useEffect, useCallback, useRef } from 'react';
import type { PipelineStage, WSProgressMessage, StageName, StageStatus } from '../types';
import { getProject } from '../api';

const STAGE_ORDER: StageName[] = ['parsing', 'analysis', 'research', 'generation'];

interface UsePipelineProgressOptions {
  projectId: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

interface UsePipelineProgressReturn {
  stages: PipelineStage[];
  currentMessage: string | null;
  isComplete: boolean;
  error: string | null;
  reconnect: () => void;
}

export function usePipelineProgress({
  projectId,
  onComplete,
  onError,
}: UsePipelineProgressOptions): UsePipelineProgressReturn {
  const [stages, setStages] = useState<PipelineStage[]>(() =>
    STAGE_ORDER.map((name) => ({
      name,
      status: 'pending' as StageStatus,
    }))
  );
  const [currentMessage, setCurrentMessage] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Use refs to avoid recreating connect function on state changes
  const wsRef = useRef<WebSocket | null>(null);
  const isCompleteRef = useRef(false);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);

  // Keep refs in sync with props
  useEffect(() => {
    onCompleteRef.current = onComplete;
    onErrorRef.current = onError;
  }, [onComplete, onError]);

  // Sync isComplete state to ref
  useEffect(() => {
    isCompleteRef.current = isComplete;
  }, [isComplete]);

  const handleMessage = useCallback((message: WSProgressMessage) => {
    const { stage, status, details, error: msgError } = message;

    setCurrentMessage(message.message);

    // Handle error
    if (status === 'failed' || msgError) {
      const errorMsg = msgError?.message || '处理失败';
      setError(errorMsg);
      onErrorRef.current?.(errorMsg);
    }

    // Update stages
    setStages((prev) => {
      const newStages = [...prev];
      const stageIndex = STAGE_ORDER.indexOf(stage);

      if (stageIndex >= 0) {
        // Update current stage
        newStages[stageIndex] = {
          ...newStages[stageIndex],
          status,
          details: details as PipelineStage['details'],
          started_at:
            status === 'in_progress'
              ? message.timestamp
              : newStages[stageIndex].started_at,
          completed_at:
            status === 'completed' ? message.timestamp : undefined,
        };

        // Calculate duration if completed
        if (
          status === 'completed' &&
          newStages[stageIndex].started_at &&
          newStages[stageIndex].completed_at
        ) {
          const start = new Date(newStages[stageIndex].started_at!).getTime();
          const end = new Date(newStages[stageIndex].completed_at!).getTime();
          newStages[stageIndex].duration = (end - start) / 1000;
        }

        // Mark previous stages as completed
        for (let i = 0; i < stageIndex; i++) {
          if (newStages[i].status !== 'completed') {
            newStages[i].status = 'completed';
          }
        }
      }

      return newStages;
    });

    // Check if complete
    if (stage === 'generation' && status === 'completed') {
      setIsComplete(true);
      isCompleteRef.current = true;
      onCompleteRef.current?.();
      wsRef.current?.close();
    }
  }, []);

  // Sync pipeline state from HTTP API (catches stages when WS messages were missed)
  const syncStateFromAPI = useCallback(async () => {
    try {
      const project = await getProject(projectId);
      const { pipeline } = project;
      if (!pipeline?.stages) return;

      // Map API stages maintaining STAGE_ORDER
      setStages(
        STAGE_ORDER.map((name) => {
          const apiStage = pipeline.stages.find((s) => s.name === name);
          return apiStage ?? { name, status: 'pending' as StageStatus };
        })
      );

      // Handle terminal states
      if (project.status === 'completed' || pipeline.current_stage === 'completed') {
        setIsComplete(true);
        isCompleteRef.current = true;
        onCompleteRef.current?.();
      } else if (project.status === 'failed') {
        const failedStage = pipeline.stages.find((s) => s.status === 'failed');
        const errorMsg = (failedStage?.details as { error?: string })?.error ?? '处理失败';
        setError(errorMsg);
        onErrorRef.current?.(errorMsg);
      }
    } catch (e) {
      console.warn('Failed to sync state from API:', e);
    }
  }, [projectId]);

  const connect = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = undefined;
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = undefined;
    }

    // Connect directly to backend WebSocket (bypass Vite proxy for better compatibility)
    const wsBase = import.meta.env.VITE_WS_BASE || 'ws://localhost:8001';
    const wsUrl = `${wsBase}/ws/projects/${projectId}`;

    console.log('Connecting to WebSocket:', wsUrl);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected successfully');
      setError(null);
      // Sync current state from API on (re)connect to catch any missed messages
      syncStateFromAPI();
      // Start ping interval to keep connection alive
      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);
    };

    ws.onmessage = (event) => {
      // Ignore pong and heartbeat responses
      if (event.data === 'pong' || event.data === 'heartbeat') {
        console.log('Received:', event.data);
        return;
      }
      try {
        const message: WSProgressMessage = JSON.parse(event.data);
        console.log('Progress update:', message.stage, message.status, message.message);
        handleMessage(message);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e, 'Data:', event.data);
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      setError('连接出错，正在重试...');
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      // Clear ping interval
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = undefined;
      }
      // Attempt reconnect if not complete (use ref to get latest value)
      if (!isCompleteRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting reconnect...');
          connect();
        }, 3000);
      }
    };
  }, [projectId, handleMessage, syncStateFromAPI]);

  const reconnect = useCallback(() => {
    setError(null);
    setIsComplete(false);
    isCompleteRef.current = false;
    setStages(STAGE_ORDER.map((name) => ({
      name,
      status: 'pending' as StageStatus,
    })));
    connect();
  }, [connect]);

  // Connect on mount, cleanup on unmount
  useEffect(() => {
    // Fetch current state immediately so UI shows correct status before WS connects
    syncStateFromAPI();
    connect();

    return () => {
      // Mark as complete to prevent reconnect attempts during cleanup
      isCompleteRef.current = true;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect, syncStateFromAPI]);

  return {
    stages,
    currentMessage,
    isComplete,
    error,
    reconnect,
  };
}
