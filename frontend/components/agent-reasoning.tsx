import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TypeBadge } from "@/components/status-badge";
import { Brain, Sparkles } from "lucide-react";
import type { Document } from "@/lib/types";

interface Props {
  doc: Document;
}

export function AgentReasoning({ doc }: Props) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Brain className="h-4 w-4 text-purple-600" />
            Classification Decision
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {doc.document_type ? (
            <>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Classified as:</span>
                <TypeBadge type={doc.document_type} />
              </div>
              {doc.metadata?.confidence !== undefined && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">Confidence:</span>
                  <span className="text-sm font-medium">
                    {Math.round(doc.metadata.confidence * 100)}%
                  </span>
                  <div className="flex-1 rounded-full bg-muted h-2 max-w-32">
                    <div
                      className="h-2 rounded-full bg-primary transition-all"
                      style={{ width: `${doc.metadata.confidence * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Classification not yet available.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Sparkles className="h-4 w-4 text-amber-500" />
            Agent Reasoning
          </CardTitle>
        </CardHeader>
        <CardContent>
          {doc.agent_reasoning ? (
            <div className="rounded-md bg-muted/50 p-4">
              <p className="whitespace-pre-wrap font-mono text-xs leading-relaxed text-muted-foreground">
                {doc.agent_reasoning}
              </p>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground italic">
              No agent log available for this document.
            </p>
          )}
        </CardContent>
      </Card>

      {doc.error_message && (
        <Card className="border-red-200 bg-red-50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-red-700">Error Details</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-mono text-xs text-red-600">{doc.error_message}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
