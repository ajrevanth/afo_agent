"use client";

import Link from "next/link";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge, TypeBadge } from "@/components/status-badge";
import { formatDate, formatCurrency, isUrgent } from "@/lib/utils";
import { RefreshCw, ArrowRight, AlertTriangle } from "lucide-react";
import type { Document } from "@/lib/types";

interface Props {
  documents: Document[];
  loading: boolean;
  onRefresh: () => void;
}

function DocumentRow({ doc }: { doc: Document }) {
  const urgent = doc.document_type === "capital_call" && isUrgent(doc.metadata?.due_date);

  return (
    <Link
      href={`/documents/${doc.id}`}
      className={`flex items-center gap-4 border-b px-4 py-3 transition-colors last:border-0 hover:bg-muted/40 ${
        urgent ? "bg-orange-50/60" : ""
      }`}
    >
      <div className="min-w-0 flex-1 space-y-0.5">
        <div className="flex items-center gap-2">
          {doc.document_type && <TypeBadge type={doc.document_type} />}
          {urgent && (
            <span className="flex items-center gap-1 text-xs font-semibold text-red-600">
              <AlertTriangle className="h-3 w-3" />
              Urgent
            </span>
          )}
        </div>
        <p className="truncate text-sm font-medium">{doc.filename}</p>
        <div className="flex gap-3 text-xs text-muted-foreground">
          <span>{doc.sender_email ?? "Direct upload"}</span>
          {doc.metadata?.fund_name && <span>· {doc.metadata.fund_name}</span>}
          {doc.metadata?.amount && (
            <span className="font-medium text-foreground">
              · {formatCurrency(doc.metadata.amount, doc.metadata.currency)}
            </span>
          )}
          {doc.metadata?.due_date && <span>· Due {doc.metadata.due_date}</span>}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-3">
        <span className="text-xs text-muted-foreground">{formatDate(doc.updated_at)}</span>
        <StatusBadge state={doc.state} />
        <ArrowRight className="h-4 w-4 text-muted-foreground" />
      </div>
    </Link>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="py-12 text-center text-sm text-muted-foreground">{label}</div>
  );
}

function TabPane({ docs, loading, emptyLabel }: { docs: Document[]; loading: boolean; emptyLabel: string }) {
  return (
    <Card>
      <CardContent className="p-0">
        {loading ? (
          <div className="space-y-px">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 animate-pulse border-b bg-muted/30 last:border-0" />
            ))}
          </div>
        ) : docs.length === 0 ? (
          <EmptyState label={emptyLabel} />
        ) : (
          docs.map((doc) => <DocumentRow key={doc.id} doc={doc} />)
        )}
      </CardContent>
    </Card>
  );
}

export function InboxTabs({ documents, loading, onRefresh }: Props) {
  const pending = documents.filter((d) => d.state === "pending_review" || d.state === "needs_attention");
  const inProgress = documents.filter((d) => ["received", "processing", "classified", "extracted"].includes(d.state));
  const processed = documents.filter((d) => d.state === "approved" || d.state === "completed");
  const rejected = documents.filter((d) => d.state === "rejected");
  const failed = documents.filter((d) => d.state === "failed");

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{documents.length} total documents</p>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={loading} className="gap-1.5">
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      <Tabs defaultValue="pending">
        <TabsList>
          <TabsTrigger value="pending" className="gap-1.5">
            Pending Review
            {pending.length > 0 && (
              <span className="rounded-full bg-orange-200 px-1.5 text-xs font-bold text-orange-900">
                {pending.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="processing">In Progress ({inProgress.length})</TabsTrigger>
          <TabsTrigger value="processed">Approved ({processed.length})</TabsTrigger>
          <TabsTrigger value="rejected">Rejected ({rejected.length})</TabsTrigger>
          {failed.length > 0 && (
            <TabsTrigger value="failed" className="text-red-600">
              Failed ({failed.length})
            </TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="pending" className="mt-4">
          <TabPane docs={pending} loading={loading} emptyLabel="No documents pending review" />
        </TabsContent>
        <TabsContent value="processing" className="mt-4">
          <TabPane docs={inProgress} loading={loading} emptyLabel="No documents in processing" />
        </TabsContent>
        <TabsContent value="processed" className="mt-4">
          <TabPane docs={processed} loading={loading} emptyLabel="No approved documents yet" />
        </TabsContent>
        <TabsContent value="rejected" className="mt-4">
          <TabPane docs={rejected} loading={loading} emptyLabel="No rejected documents" />
        </TabsContent>
        {failed.length > 0 && (
          <TabsContent value="failed" className="mt-4">
            <TabPane docs={failed} loading={loading} emptyLabel="No failed documents" />
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}
