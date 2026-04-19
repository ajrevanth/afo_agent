import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge, TypeBadge } from "@/components/status-badge";
import { formatDate, formatCurrency } from "@/lib/utils";
import { RefreshCw } from "lucide-react";
import type { Document } from "@/lib/types";

interface Props {
  documents: Document[];
  loading: boolean;
  onRefresh: () => void;
}

export function RecentDocuments({ documents, loading, onRefresh }: Props) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base">Recent Documents</CardTitle>
        <Button variant="ghost" size="icon" onClick={onRefresh} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="pb-2 font-medium">File</th>
                <th className="pb-2 font-medium">Type</th>
                <th className="pb-2 font-medium">State</th>
                <th className="pb-2 font-medium">Fund</th>
                <th className="pb-2 font-medium">Amount</th>
                <th className="pb-2 font-medium">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {loading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 6 }).map((_, j) => (
                      <td key={j} className="py-3 pr-4">
                        <div className="h-4 animate-pulse rounded bg-muted" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : documents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-muted-foreground">
                    No documents ingested yet. Use the Ingest tab to add one.
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-muted/40">
                    <td className="py-3 pr-4 font-medium">{doc.filename}</td>
                    <td className="py-3 pr-4">
                      {doc.document_type ? <TypeBadge type={doc.document_type} /> : "—"}
                    </td>
                    <td className="py-3 pr-4">
                      <StatusBadge state={doc.state} />
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {doc.metadata?.fund_name ?? "—"}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {doc.metadata?.amount
                        ? formatCurrency(doc.metadata.amount, doc.metadata.currency)
                        : "—"}
                    </td>
                    <td className="py-3 text-muted-foreground">{formatDate(doc.updated_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
