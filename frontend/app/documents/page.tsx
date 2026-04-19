"use client";

import { useEffect, useState, useCallback } from "react";
import { InboxTabs } from "@/components/inbox-tabs";
import { DocumentFilters } from "@/components/document-filters";
import { fetchDocuments } from "@/lib/api";
import type { Document, DocumentFilters as Filters } from "@/lib/types";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<Filters>({});

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchDocuments(filters);
      setDocuments(data);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, [load]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Document Inbox</h1>
        <p className="text-muted-foreground">
          Review AI-classified documents before approving payments
        </p>
      </div>

      <DocumentFilters filters={filters} onChange={setFilters} />
      <InboxTabs documents={documents} loading={loading} onRefresh={load} />
    </div>
  );
}
