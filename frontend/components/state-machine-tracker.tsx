import { cn, STATE_ORDER } from "@/lib/utils";
import type { DocumentState } from "@/lib/types";
import { Check, X } from "lucide-react";

interface Props {
  state: DocumentState;
}

export function StateMachineTracker({ state }: Props) {
  const isFailed = state === "failed";
  const currentIdx = STATE_ORDER.indexOf(state as typeof STATE_ORDER[number]);

  return (
    <div>
      <p className="mb-3 text-xs font-medium text-muted-foreground">Processing Pipeline</p>
      <div className="flex items-center gap-0">
        {STATE_ORDER.map((s, i) => {
          const isDone = currentIdx > i || state === "completed";
          const isCurrent = currentIdx === i && !isFailed;
          const isFailedStep = isFailed && currentIdx === i;

          return (
            <div key={s} className="flex items-center">
              <div className="flex flex-col items-center gap-1">
                <div
                  className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-full border-2 text-xs font-bold transition-colors",
                    isDone && "border-green-500 bg-green-500 text-white",
                    isCurrent && "border-blue-500 bg-blue-500 text-white animate-pulse",
                    isFailedStep && "border-red-500 bg-red-500 text-white",
                    !isDone && !isCurrent && !isFailedStep && "border-muted bg-background text-muted-foreground"
                  )}
                >
                  {isDone ? <Check className="h-3 w-3" /> : isFailedStep ? <X className="h-3 w-3" /> : i + 1}
                </div>
                <span className="text-xs capitalize text-muted-foreground">{s}</span>
              </div>
              {i < STATE_ORDER.length - 1 && (
                <div
                  className={cn(
                    "mx-1 mb-4 h-0.5 w-8",
                    currentIdx > i ? "bg-green-500" : "bg-muted"
                  )}
                />
              )}
            </div>
          );
        })}

        {isFailed && (
          <div className="ml-4 flex items-center gap-1.5 rounded-full bg-red-100 px-3 py-1">
            <X className="h-3 w-3 text-red-600" />
            <span className="text-xs font-medium text-red-700">Failed</span>
          </div>
        )}
      </div>
    </div>
  );
}
