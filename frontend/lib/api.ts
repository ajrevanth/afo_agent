import type {
  Document,
  DashboardStats,
  DocumentFilters,
  MockEmailPayload,
  ReviewPayload,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

export async function fetchDashboardStats(): Promise<DashboardStats> {
  return request<DashboardStats>("/api/stats");
}

export async function fetchDocuments(filters: DocumentFilters = {}): Promise<Document[]> {
  const params = new URLSearchParams();
  if (filters.state) params.set("state", filters.state);
  if (filters.document_type) params.set("document_type", filters.document_type);
  if (filters.search) params.set("search", filters.search);
  const qs = params.toString();
  return request<Document[]>(`/api/documents${qs ? `?${qs}` : ""}`);
}

export async function fetchRecentDocuments(limit = 5): Promise<Document[]> {
  return request<Document[]>(`/api/documents?limit=${limit}`);
}

export async function fetchPendingReview(): Promise<Document[]> {
  return request<Document[]>("/api/documents?state=pending_review");
}

export async function fetchDocument(id: string): Promise<Document> {
  return request<Document>(`/api/documents/${id}`);
}

export async function uploadDocument(file: File): Promise<Document> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/api/documents/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function triggerMockEmail(payload: MockEmailPayload): Promise<Document> {
  return request<Document>("/api/documents/mock-email", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function reviewDocument(id: string, payload: ReviewPayload): Promise<Document> {
  return request<Document>(`/api/documents/${id}/review`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function retryDocument(id: string): Promise<Document> {
  return request<Document>(`/api/documents/${id}/retry`, { method: "POST" });
}

export function documentFileUrl(id: string): string {
  return `${BASE}/api/documents/${id}/file`;
}
