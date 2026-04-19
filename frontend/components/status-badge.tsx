import { cn, STATE_LABELS, STATE_COLORS, TYPE_LABELS, TYPE_COLORS } from "@/lib/utils";
import type { DocumentState, DocumentType } from "@/lib/types";

export function StatusBadge({ state }: { state: DocumentState }) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", STATE_COLORS[state])}>
      {STATE_LABELS[state]}
    </span>
  );
}

export function TypeBadge({ type }: { type: DocumentType }) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", TYPE_COLORS[type])}>
      {TYPE_LABELS[type]}
    </span>
  );
}
