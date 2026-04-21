"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge, TypeBadge } from "@/components/status-badge";
import { StateMachineTracker } from "@/components/state-machine-tracker";
import { formatDate, formatCurrency } from "@/lib/utils";
import { RefreshCw, ChevronDown, ChevronRight, RotateCcw, AlertCircle } from "lucide-react";
import { retryDocument } from "@/lib/api";
import { toast } from "@/components/ui/use-toast";
import type { Document } from "@/lib/types";

interface Props {
  documents: Document[];
  loading: boolean;
  onRefresh: () => void;
}

export function DocumentsTable({ documents, loading, onRefresh }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [retrying, setRetrying] = useState<string | null>(null);

  const handleRetry = async (id: string) => {
    setRetrying(id);
    try {
      await retryDocument(id);
      toast({ title: "Retry triggered", description: "Document re-queued for processing." });
      onRefresh();
    } catch (e) {
      toast({ variant: "destructive", title: "Retry failed", description: String(e) });
    } finally {
      setRetrying(null);
    }
  };

  return (
    <Card>
      <CardContent className="p-0">
        <div className="flex items-center justify-between border-b px-6 py-3">
          <p className="text-sm text-muted-foreground">
            {loading ? "Loading..." : `${documents.length} document${documents.length !== 1 ? "s" : ""}`}
          </p>
          <Button variant="ghost" size="icon" onClick={onRefresh} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40 text-left text-muted-foreground">
                <th className="w-8 px-4 py-3" />
                <th className="px-4 py-3 font-medium">File</th>
                <th className="px-4 py-3 font-medium">Sender</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">State</th>
                <th className="px-4 py-3 font-medium">Fund</th>
                <th className="px-4 py-3 font-medium">Amount</th>
                <th className="px-4 py-3 font-medium">Due Date</th>
                <th className="px-4 py-3 font-medium">Updated</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y">
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 9 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 animate-pulse rounded bg-muted" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : documents.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-4 py-12 text-center text-muted-foreground">
                    No documents found. Adjust filters or ingest a new document.
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <>
                    <tr
                      key={doc.id}
                      className="cursor-pointer hover:bg-muted/40"
                      onClick={() => setExpanded(expanded === doc.id ? null : doc.id)}
                    >
                      <td className="px-4 py-3 text-muted-foreground">
                        {expanded === doc.id ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </td>
                      <td className="px-4 py-3 font-medium">{doc.filename}</td>
                      <td className="px-4 py-3 text-muted-foreground">{doc.sender_email ?? "—"}</td>
                      <td className="px-4 py-3">
                        {doc.document_type && doc.document_type !== "unknown" ? <TypeBadge type={doc.document_type} /> : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge state={doc.state} />
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{doc.metadata?.fund_name ?? "—"}</td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {doc.metadata?.amount
                          ? formatCurrency(doc.metadata.amount, doc.metadata.currency)
                          : "—"}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{doc.metadata?.due_date ?? "—"}</td>
                      <td className="px-4 py-3 text-muted-foreground">{formatDate(doc.updated_at)}</td>
                      <td className="px-4 py-3">
                        {doc.state === "failed" && (
                          <Button
                            variant="ghost"
                            size="icon"
                            disabled={retrying === doc.id}
                            onClick={(e) => { e.stopPropagation(); handleRetry(doc.id); }}
                          >
                            <RotateCcw className={`h-4 w-4 ${retrying === doc.id ? "animate-spin" : ""}`} />
                          </Button>
                        )}
                      </td>
                    </tr>

                    {expanded === doc.id && (
                      <tr key={`${doc.id}-detail`} className="bg-muted/20">
                        <td colSpan={10} className="px-6 py-4">
                          <div className="space-y-4">
                            <StateMachineTracker state={doc.state} />
                            {doc.subject && (
                              <div>
                                <p className="text-xs font-medium text-muted-foreground">Subject</p>
                                <p className="text-sm">{doc.subject}</p>
                              </div>
                            )}
                            {doc.error_message && (
                              <div className="flex items-start gap-2 rounded-md bg-red-50 p-3 text-sm text-red-700">
                                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                                {doc.error_message}
                              </div>
                            )}
                            {doc.metadata && (
                              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                                {Object.entries(doc.metadata).map(([k, v]) => (
                                  <div key={k}>
                                    <p className="text-xs font-medium capitalize text-muted-foreground">
                                      {k.replace(/_/g, " ")}
                                    </p>
                                    <p className="text-sm">{String(v)}</p>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
