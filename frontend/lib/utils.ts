import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { DocumentState, DocumentType } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(iso: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

export function formatDateFull(iso: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(iso));
}

export function formatCurrency(amount: number, currency = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function daysUntil(dateStr: string): number {
  const due = new Date(dateStr);
  const now = new Date();
  return Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

export function isUrgent(dateStr?: string): boolean {
  if (!dateStr) return false;
  return daysUntil(dateStr) <= 3;
}

export const STATE_LABELS: Record<DocumentState, string> = {
  received: "Received",
  processing: "Processing",
  classified: "Classified",
  extracted: "Extracted",
  pending_review: "Pending Review",
  approved: "Approved",
  rejected: "Rejected",
  completed: "Completed",
  failed: "Failed",
  needs_attention: "Needs Attention",
};

export const STATE_COLORS: Record<DocumentState, string> = {
  received: "bg-slate-100 text-slate-700",
  processing: "bg-blue-100 text-blue-700",
  classified: "bg-purple-100 text-purple-700",
  extracted: "bg-amber-100 text-amber-700",
  pending_review: "bg-orange-100 text-orange-800 ring-1 ring-orange-400",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
  completed: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
  needs_attention: "bg-yellow-100 text-yellow-800 ring-1 ring-yellow-400",
};

export const TYPE_LABELS: Record<DocumentType, string> = {
  invoice: "Invoice",
  capital_call: "Capital Call",
  unknown: "Unknown",
};

export const TYPE_COLORS: Record<DocumentType, string> = {
  invoice: "bg-orange-100 text-orange-700",
  capital_call: "bg-indigo-100 text-indigo-700",
  unknown: "bg-gray-100 text-gray-600",
};

export const PIPELINE_STATES: DocumentState[] = [
  "received",
  "processing",
  "classified",
  "extracted",
  "pending_review",
  "approved",
  "completed",
];
