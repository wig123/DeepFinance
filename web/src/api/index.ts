import type {
  ProjectDetail,
  ProjectListResponse,
  CreateProjectResponse,
  ReportContent,
  Citation,
  AnalysisMode,
  AnalysisResponse,
  QASessionResponse,
  QASessionListResponse,
  QASuggestionsResponse,
  QAAnswerResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

class ApiError extends Error {
  status: number;
  code?: string;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new ApiError(
      response.status,
      error.detail?.message || error.message || 'Request failed',
      error.detail?.code
    );
  }
  return response.json();
}

// ==================== Projects API ====================

export async function createProject(
  file: File,
  userQuery?: string,
  mode: AnalysisMode = 'full'
): Promise<CreateProjectResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (userQuery) {
    formData.append('user_query', userQuery);
  }
  formData.append('mode', mode);

  const response = await fetch(`${API_BASE}/projects`, {
    method: 'POST',
    body: formData,
  });

  return handleResponse<CreateProjectResponse>(response);
}

export async function getProjects(
  limit = 20,
  offset = 0
): Promise<ProjectListResponse> {
  const response = await fetch(
    `${API_BASE}/projects?limit=${limit}&offset=${offset}`
  );
  return handleResponse<ProjectListResponse>(response);
}

export async function getProject(projectId: string): Promise<ProjectDetail> {
  const response = await fetch(`${API_BASE}/projects/${projectId}`);
  return handleResponse<ProjectDetail>(response);
}

export async function deleteProject(projectId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/projects/${projectId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new ApiError(response.status, 'Failed to delete project');
  }
}

// ==================== Report API ====================

export async function getReport(
  projectId: string,
  format: 'markdown' | 'html' | 'json' = 'markdown'
): Promise<ReportContent> {
  const response = await fetch(
    `${API_BASE}/projects/${projectId}/report?format=${format}`
  );
  return handleResponse<ReportContent>(response);
}

export async function getAnalysis(projectId: string): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE}/projects/${projectId}/analysis`);
  return handleResponse<AnalysisResponse>(response);
}

export async function getResearch(projectId: string): Promise<unknown> {
  const response = await fetch(`${API_BASE}/projects/${projectId}/research`);
  return handleResponse<unknown>(response);
}

// ==================== Citation API ====================

export async function getCitation(
  projectId: string,
  citationId: string
): Promise<Citation> {
  const response = await fetch(
    `${API_BASE}/projects/${projectId}/citations/${citationId}`
  );
  return handleResponse<Citation>(response);
}

// ==================== File API ====================

export function getFileUrl(projectId: string, filePath: string): string {
  return `${API_BASE}/projects/${projectId}/files/${filePath}`;
}

// ==================== WebSocket ====================

export function createProgressWebSocket(
  projectId: string,
  onMessage: (data: unknown) => void,
  onError?: (error: Event) => void,
  onClose?: () => void
): WebSocket {
  // Use relative WebSocket URL - Vite proxy handles routing to backend
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsBase = import.meta.env.VITE_WS_BASE || `${protocol}//${window.location.host}`;
  const ws = new WebSocket(`${wsBase}/ws/projects/${projectId}`);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    onError?.(error);
  };

  ws.onclose = () => {
    onClose?.();
  };

  return ws;
}

// ==================== QA API ====================

export async function createQASession(projectId: string): Promise<QASessionResponse> {
  const response = await fetch(`${API_BASE}/projects/${projectId}/qa/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  return handleResponse<QASessionResponse>(response);
}

export async function listQASessions(projectId: string): Promise<QASessionListResponse> {
  const response = await fetch(`${API_BASE}/projects/${projectId}/qa/sessions`);
  return handleResponse<QASessionListResponse>(response);
}

export async function getQASession(projectId: string, sessionId: string): Promise<QASessionResponse> {
  const response = await fetch(`${API_BASE}/projects/${projectId}/qa/sessions/${sessionId}`);
  return handleResponse<QASessionResponse>(response);
}

export async function deleteQASession(projectId: string, sessionId: string): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE}/projects/${projectId}/qa/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  return handleResponse<{ status: string }>(response);
}

export async function getQASuggestions(projectId: string): Promise<QASuggestionsResponse> {
  const response = await fetch(`${API_BASE}/projects/${projectId}/qa/suggestions`);
  return handleResponse<QASuggestionsResponse>(response);
}

export async function askQuestion(
  projectId: string,
  sessionId: string,
  question: string,
  contextMode: 'basic' | 'enhanced' | 'full' = 'basic'
): Promise<QAAnswerResponse> {
  const response = await fetch(
    `${API_BASE}/projects/${projectId}/qa/sessions/${sessionId}/ask`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, context_mode: contextMode }),
    }
  );
  return handleResponse<QAAnswerResponse>(response);
}

// Note: SSE streaming is handled by custom hook (useQAStream)

export { ApiError };
