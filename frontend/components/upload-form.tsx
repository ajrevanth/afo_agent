"use client";

import { useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { uploadDocument } from "@/lib/api";
import { toast } from "@/components/ui/use-toast";
import { Upload, FileText, X } from "lucide-react";

export function UploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ id: string; filename: string } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const doc = await uploadDocument(file);
      setResult({ id: doc.id, filename: doc.filename });
      setFile(null);
      toast({ title: "Document ingested", description: `${doc.filename} is now processing.` });
    } catch (e) {
      toast({ variant: "destructive", title: "Upload failed", description: String(e) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Upload Document</CardTitle>
        <CardDescription>PDF or PNG attachments — simulates a file arriving via email</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => inputRef.current?.click()}
          className="flex cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed border-muted-foreground/30 p-10 text-center transition-colors hover:border-primary/50 hover:bg-muted/20"
        >
          <Upload className="h-8 w-8 text-muted-foreground" />
          <div>
            <p className="text-sm font-medium">Drop file here or click to browse</p>
            <p className="text-xs text-muted-foreground">PDF or PNG, up to 10 MB</p>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.png"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </div>

        {file && (
          <div className="flex items-center gap-3 rounded-md border bg-muted/30 px-4 py-3">
            <FileText className="h-5 w-5 text-muted-foreground" />
            <span className="flex-1 truncate text-sm">{file.name}</span>
            <button onClick={() => setFile(null)}>
              <X className="h-4 w-4 text-muted-foreground hover:text-foreground" />
            </button>
          </div>
        )}

        {result && (
          <div className="rounded-md bg-green-50 px-4 py-3 text-sm text-green-700">
            Ingested <strong>{result.filename}</strong> — ID: {result.id}
          </div>
        )}

        <Button onClick={handleSubmit} disabled={!file || loading} className="w-full">
          {loading ? "Uploading..." : "Ingest Document"}
        </Button>
      </CardContent>
    </Card>
  );
}
