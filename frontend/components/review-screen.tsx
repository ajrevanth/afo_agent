"use client";

import { useState } from "react";
import { PdfViewer } from "@/components/pdf-viewer";
import { ExtractionForm } from "@/components/extraction-form";
import { AuditTimeline } from "@/components/audit-timeline";
import { AgentReasoning } from "@/components/agent-reasoning";
import { StatusBadge, TypeBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { UrgencyAlert } from "@/components/urgency-alert";
import { documentFileUrl } from "@/lib/api";
import type { Document } from "@/lib/types";
import { FileText, Clock, Brain } from "lucide-react";

interface Props {
  doc: Document;
  onUpdate: (doc: Document) => void;
}

export function ReviewScreen({ doc, onUpdate }: Props) {
  const [activeTab, setActiveTab] = useState("review");
  const fileUrl = documentFileUrl(doc.id);

  const isReviewable = doc.state === "pending_review" || doc.state === "needs_attention";
  const isSettled = doc.state === "approved" || doc.state === "rejected" || doc.state === "completed";

  return (
    <div className="space-y-3">
      {doc.metadata?.due_date && doc.document_type === "capital_call" && (
        <UrgencyAlert dueDate={doc.metadata.due_date} fundName={doc.metadata.fund_name} />
      )}

      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <StatusBadge state={doc.state} />
        {doc.document_type && doc.document_type !== "unknown" && <TypeBadge type={doc.document_type} />}
        {isSettled && doc.reviewed_by && (
          <span className="ml-2">
            {(doc.state === "approved" || doc.state === "completed") ? "Approved" : "Rejected"} by{" "}
            <strong>{doc.reviewed_by}</strong>
            {doc.reviewed_at && ` · ${new Date(doc.reviewed_at).toLocaleString()}`}
          </span>
        )}
      </div>

      <div className="grid h-[calc(100vh-220px)] grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Left: Document viewer */}
        <Card className="flex flex-col overflow-hidden">
          <CardHeader className="flex-none border-b py-3">
            <CardTitle className="flex items-center gap-2 text-sm font-semibold">
              <FileText className="h-4 w-4" />
              Original Document
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden p-0">
            <PdfViewer url={fileUrl} filename={doc.filename} />
          </CardContent>
        </Card>

        {/* Right: AI data + actions */}
        <div className="flex flex-col overflow-hidden">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex flex-1 flex-col overflow-hidden">
            <TabsList className="flex-none">
              <TabsTrigger value="review" className="gap-1.5">
                <FileText className="h-3.5 w-3.5" />
                AI Extraction
              </TabsTrigger>
              <TabsTrigger value="reasoning" className="gap-1.5">
                <Brain className="h-3.5 w-3.5" />
                Agent Log
              </TabsTrigger>
              <TabsTrigger value="history" className="gap-1.5">
                <Clock className="h-3.5 w-3.5" />
                Audit Trail
              </TabsTrigger>
            </TabsList>

            <TabsContent value="review" className="flex-1 overflow-auto mt-3">
              <ExtractionForm
                doc={doc}
                readOnly={!isReviewable}
                onUpdate={onUpdate}
              />
            </TabsContent>

            <TabsContent value="reasoning" className="flex-1 overflow-auto mt-3">
              <AgentReasoning doc={doc} />
            </TabsContent>

            <TabsContent value="history" className="flex-1 overflow-auto mt-3">
              <AuditTimeline doc={doc} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
