import { AlertTriangle, Clock } from "lucide-react";
import { daysUntil } from "@/lib/utils";

interface Props {
  dueDate: string;
  fundName?: string;
}

export function UrgencyAlert({ dueDate, fundName }: Props) {
  const days = daysUntil(dueDate);
  const overdue = days < 0;
  const critical = days >= 0 && days <= 1;
  const urgent = days >= 0 && days <= 3;

  if (!urgent && !overdue) return null;

  return (
    <div
      className={`flex items-start gap-3 rounded-lg border-2 p-4 ${
        overdue || critical
          ? "border-red-400 bg-red-50 text-red-800"
          : "border-orange-400 bg-orange-50 text-orange-800"
      }`}
    >
      {overdue || critical ? (
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
      ) : (
        <Clock className="mt-0.5 h-5 w-5 shrink-0 text-orange-600" />
      )}
      <div>
        <p className="font-bold text-sm">
          {overdue
            ? `OVERDUE — Capital Call was due ${Math.abs(days)} day${Math.abs(days) !== 1 ? "s" : ""} ago`
            : critical
            ? `CRITICAL — Capital Call due ${days === 0 ? "TODAY" : "TOMORROW"}`
            : `URGENT — Capital Call due in ${days} days`}
        </p>
        <p className="text-xs mt-0.5 opacity-80">
          {fundName ? `${fundName} · ` : ""}Due: {dueDate}
          {(overdue || critical) && " · Failure to wire may result in legal default."}
        </p>
      </div>
    </div>
  );
}
