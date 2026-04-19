"use client";

import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Search, X } from "lucide-react";
import type { DocumentFilters } from "@/lib/types";

interface Props {
  filters: DocumentFilters;
  onChange: (f: DocumentFilters) => void;
}

export function DocumentFilters({ filters, onChange }: Props) {
  const hasFilters = filters.state || filters.document_type || filters.search;

  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="relative flex-1 min-w-48">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search filename or sender..."
          value={filters.search ?? ""}
          onChange={(e) => onChange({ ...filters, search: e.target.value || undefined })}
          className="pl-9"
        />
      </div>

      <Select
        value={filters.state ?? "all"}
        onValueChange={(v) => onChange({ ...filters, state: v === "all" ? undefined : (v as DocumentFilters["state"]) })}
      >
        <SelectTrigger className="w-40">
          <SelectValue placeholder="All states" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All states</SelectItem>
          <SelectItem value="received">Received</SelectItem>
          <SelectItem value="processing">Processing</SelectItem>
          <SelectItem value="classified">Classified</SelectItem>
          <SelectItem value="extracted">Extracted</SelectItem>
          <SelectItem value="completed">Completed</SelectItem>
          <SelectItem value="failed">Failed</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={filters.document_type ?? "all"}
        onValueChange={(v) => onChange({ ...filters, document_type: v === "all" ? undefined : (v as DocumentFilters["document_type"]) })}
      >
        <SelectTrigger className="w-40">
          <SelectValue placeholder="All types" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All types</SelectItem>
          <SelectItem value="invoice">Invoice</SelectItem>
          <SelectItem value="capital_call">Capital Call</SelectItem>
          <SelectItem value="unknown">Unknown</SelectItem>
        </SelectContent>
      </Select>

      {hasFilters && (
        <Button variant="ghost" size="sm" onClick={() => onChange({})} className="gap-1">
          <X className="h-4 w-4" />
          Clear
        </Button>
      )}
    </div>
  );
}
