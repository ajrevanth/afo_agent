export type DocumentState =
  | "received"
  | "processing"
  | "classified"
  | "extracted"
  | "pending_review"   // agent done, waiting for human
  | "approved"         // human approved, payment can proceed
  | "rejected"         // human rejected
  | "completed"        // fully processed
  | "failed"           // agent error
  | "needs_attention"; // agent flagged it, can't process automatically

export type DocumentType = "invoice" | "capital_call" | "unknown";

export interface ExtractedMetadata {
  fund_name?: string;
  amount?: number;
  currency?: string;
  due_date?: string;
  confidence?: number;
}

export interface StateTransition {
  from_state: DocumentState;
  to_state: DocumentState;
  actor: string;   // "agent" | reviewer name
  timestamp: string;
  note?: string;
}

export interface Document {
  id: string;
  filename: string;
  sender_email?: string;
  subject?: string;
  state: DocumentState;
  document_type?: DocumentType;
  metadata?: ExtractedMetadata;
  agent_reasoning?: string;
  state_history?: StateTransition[];
  reviewed_by?: string;
  reviewed_at?: string;
  review_note?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface DashboardStats {
  total: number;
  by_state: Record<string, number>;
  by_type: Record<DocumentType, number>;
  approved: number;
  failed_today: number;
  pending_review_count: number;
  urgent_count: number; // due within 3 days
}

export interface DocumentFilters {
  state?: DocumentState;
  document_type?: DocumentType;
  search?: string;
}

export interface ReviewPayload {
  action: "approve" | "reject";
  reviewer_name: string;
  note?: string;
  overrides?: Partial<ExtractedMetadata>;
}
