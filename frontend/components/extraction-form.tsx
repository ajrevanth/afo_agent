"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { reviewDocument } from "@/lib/api";
import { toast } from "@/components/ui/use-toast";
import { CheckCircle, XCircle, AlertCircle, Sparkles } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import type { Document, ExtractedMetadata } from "@/lib/types";

interface Props {
  doc: Document;
  readOnly: boolean;
  onUpdate: (doc: Document) => void;
}

export function ExtractionForm({ doc, readOnly, onUpdate }: Props) {
  const meta = doc.metadata ?? {};
  const [fields, setFields] = useState<Partial<ExtractedMetadata>>({
    fund_name: meta.fund_name ?? "",
    amount: meta.amount,
    currency: meta.currency ?? "USD",
    due_date: meta.due_date ?? "",
  });
  const [reviewerName, setReviewerName] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState<"approve" | "reject" | null>(null);

  const setField = <K extends keyof ExtractedMetadata>(k: K, v: ExtractedMetadata[K]) =>
    setFields((f) => ({ ...f, [k]: v }));

  const submit = async (action: "approve" | "reject") => {
    if (!reviewerName.trim()) {
      toast({ variant: "destructive", title: "Enter your name before submitting" });
      return;
    }
    setLoading(action);
    try {
      const updated = await reviewDocument(doc.id, {
        action,
        reviewer_name: reviewerName,
        note: note || undefined,
        overrides: action === "approve" ? fields : undefined,
      });
      onUpdate(updated);
      toast({
        title: action === "approve" ? "Document approved" : "Document rejected",
        description: action === "approve"
          ? "Payment details confirmed and logged."
          : "Document flagged for rejection.",
      });
    } catch (e) {
      toast({ variant: "destructive", title: "Error", description: String(e) });
    } finally {
      setLoading(null);
    }
  };

  const confidence = meta.confidence ?? null;

  return (
    <div className="space-y-4">
      {/* Confidence indicator */}
      {confidence !== null && (
        <div className={cn(
          "flex items-center gap-2 rounded-md px-3 py-2 text-sm",
          confidence >= 0.85
            ? "bg-green-50 text-green-700"
            : confidence >= 0.6
            ? "bg-amber-50 text-amber-700"
            : "bg-red-50 text-red-700"
        )}>
          <Sparkles className="h-4 w-4" />
          <span>
            AI confidence: <strong>{Math.round(confidence * 100)}%</strong>
            {confidence < 0.85 && " — please verify fields carefully"}
          </span>
        </div>
      )}

      {doc.state === "needs_attention" && (
        <div className="flex items-start gap-2 rounded-md bg-yellow-50 px-3 py-2 text-sm text-yellow-800">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          Agent could not fully process this document. Manual entry required.
        </div>
      )}

      {/* Extracted fields */}
      <Card>
        <CardContent className="space-y-4 pt-5">
          <div className="space-y-1.5">
            <Label>Fund Name</Label>
            <Input
              value={fields.fund_name ?? ""}
              onChange={(e) => setField("fund_name", e.target.value)}
              disabled={readOnly}
              placeholder="e.g. Sequoia Capital Fund V"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Amount</Label>
              <Input
                type="number"
                value={fields.amount ?? ""}
                onChange={(e) => setField("amount", parseFloat(e.target.value) || undefined)}
                disabled={readOnly}
                placeholder="e.g. 500000"
              />
              {fields.amount && (
                <p className="text-xs text-muted-foreground">
                  = {formatCurrency(fields.amount, fields.currency)}
                </p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label>Currency</Label>
              <Input
                value={fields.currency ?? ""}
                onChange={(e) => setField("currency", e.target.value)}
                disabled={readOnly}
                placeholder="USD"
                maxLength={3}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Due Date</Label>
            <Input
              type="date"
              value={fields.due_date ?? ""}
              onChange={(e) => setField("due_date", e.target.value)}
              disabled={readOnly}
            />
          </div>
        </CardContent>
      </Card>

      {/* Settled state display */}
      {(doc.state === "approved" || doc.state === "completed" || doc.state === "rejected") && (
        <div className={cn(
          "flex items-start gap-3 rounded-md p-4 text-sm",
          (doc.state === "approved" || doc.state === "completed") ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"
        )}>
          {(doc.state === "approved" || doc.state === "completed")
            ? <CheckCircle className="mt-0.5 h-4 w-4 shrink-0" />
            : <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
          }
          <div>
            <p className="font-medium">
              {(doc.state === "approved" || doc.state === "completed") ? "Approved" : "Rejected"} by {doc.reviewed_by}
            </p>
            {doc.review_note && <p className="mt-0.5 text-xs opacity-80">{doc.review_note}</p>}
          </div>
        </div>
      )}

      {/* Review actions */}
      {!readOnly && (
        <div className="space-y-3 rounded-lg border bg-muted/30 p-4">
          <p className="text-sm font-medium">Human Review</p>

          <div className="space-y-1.5">
            <Label>Your Name</Label>
            <Input
              value={reviewerName}
              onChange={(e) => setReviewerName(e.target.value)}
              placeholder="e.g. Sarah Chen"
            />
          </div>

          <div className="space-y-1.5">
            <Label>Note (optional)</Label>
            <Textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Any corrections or comments..."
              rows={2}
            />
          </div>

          <div className="flex gap-3 pt-1">
            <Button
              className="flex-1 bg-green-600 hover:bg-green-700"
              onClick={() => submit("approve")}
              disabled={loading !== null}
            >
              <CheckCircle className="mr-2 h-4 w-4" />
              {loading === "approve" ? "Approving..." : "Approve"}
            </Button>
            <Button
              variant="outline"
              className="flex-1 border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700"
              onClick={() => submit("reject")}
              disabled={loading !== null}
            >
              <XCircle className="mr-2 h-4 w-4" />
              {loading === "reject" ? "Rejecting..." : "Reject"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
