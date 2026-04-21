"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ReviewScreen } from "@/components/review-screen";
import { fetchDocument } from "@/lib/api";
import type { Document } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { ArrowLeft, RefreshCw } from "lucide-react";
import Link from "next/link";

export function generateStaticParams() {
  return [];
}

export default function DocumentReviewPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [doc, setDoc] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      setDoc(await fetchDocument(id));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="flex flex-col items-center gap-4 py-20">
        <p className="text-muted-foreground">Document not found.</p>
        <Link href="/documents">
          <Button variant="outline">Back to inbox</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Link href="/documents">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-xl font-bold">{doc.filename}</h1>
          <p className="text-sm text-muted-foreground">
            From: {doc.sender_email ?? "Direct upload"} · {doc.subject ?? ""}
          </p>
        </div>
      </div>

      <ReviewScreen
        doc={doc}
        onUpdate={(updated) => {
          setDoc(updated);
          if (updated.state === "approved" || updated.state === "rejected") {
            setTimeout(() => router.push("/documents"), 1500);
          }
        }}
      />
    </div>
  );
}
