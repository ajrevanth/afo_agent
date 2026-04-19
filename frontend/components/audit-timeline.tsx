import { Card, CardContent } from "@/components/ui/card";
import { formatDateFull, STATE_LABELS } from "@/lib/utils";
import { Bot, User, CheckCircle, XCircle, Clock } from "lucide-react";
import type { Document, StateTransition } from "@/lib/types";

interface Props {
  doc: Document;
}

function TransitionIcon({ actor }: { actor: string }) {
  if (actor === "agent") return <Bot className="h-3.5 w-3.5" />;
  return <User className="h-3.5 w-3.5" />;
}

export function AuditTimeline({ doc }: Props) {
  const history: StateTransition[] = doc.state_history ?? [];

  const syntheticCreation: StateTransition = {
    from_state: "received",
    to_state: "received",
    actor: "system",
    timestamp: doc.created_at,
    note: `Document ingested${doc.sender_email ? ` from ${doc.sender_email}` : ""}`,
  };

  const all = [syntheticCreation, ...history];

  return (
    <div className="space-y-3">
      <Card>
        <CardContent className="pt-5">
          <div className="relative space-y-4 pl-6 before:absolute before:left-2.5 before:top-2 before:h-[calc(100%-16px)] before:w-px before:bg-border">
            {all.map((t, i) => (
              <div key={i} className="relative">
                <div className="absolute -left-[22px] top-0.5 flex h-5 w-5 items-center justify-center rounded-full border bg-background text-muted-foreground">
                  <TransitionIcon actor={t.actor} />
                </div>

                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">
                      {STATE_LABELS[t.to_state] ?? t.to_state}
                    </span>
                    {(t.to_state === "approved") && (
                      <CheckCircle className="h-3.5 w-3.5 text-green-600" />
                    )}
                    {(t.to_state === "rejected") && (
                      <XCircle className="h-3.5 w-3.5 text-red-600" />
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    <span>{formatDateFull(t.timestamp)}</span>
                    <span>·</span>
                    <span className="capitalize">{t.actor === "agent" ? "AI Agent" : t.actor}</span>
                  </div>
                  {t.note && (
                    <p className="text-xs text-muted-foreground italic">{t.note}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="rounded-md bg-muted/40 px-4 py-3 text-xs text-muted-foreground">
        Document ID: <span className="font-mono">{doc.id}</span>
        <br />
        Created: {formatDateFull(doc.created_at)}
        <br />
        Last updated: {formatDateFull(doc.updated_at)}
      </div>
    </div>
  );
}
