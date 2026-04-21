"use client";

import { useState } from "react";
import { FileText, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  url: string;
  filename: string;
  showDownload?: boolean;
}

export function PdfViewer({ url, filename, showDownload = false }: Props) {
  const [error, setError] = useState(false);
  const isPdf = filename.toLowerCase().endsWith(".pdf");
  const isImage = /\.(png|jpg|jpeg|webp)$/i.test(filename);

  if (error || (!isPdf && !isImage)) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 bg-muted/20 p-8 text-center">
        <FileText className="h-12 w-12 text-muted-foreground" />
        <div>
          <p className="font-medium">{filename}</p>
          <p className="text-sm text-muted-foreground">Preview not available for this file type</p>
        </div>
      </div>
    );
  }

  if (isImage) {
    return (
      <div className="relative h-full overflow-auto bg-muted/10">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={url}
          alt={filename}
          className="mx-auto max-w-full object-contain"
          onError={() => setError(true)}
        />
      </div>
    );
  }

  return (
    <div className="relative h-full">
      {showDownload && (
        <div className="absolute right-2 top-2 z-10">
          <Button variant="outline" size="sm" asChild>
            <a href={url} target="_blank" rel="noopener noreferrer" className="gap-1.5">
              <ExternalLink className="h-3.5 w-3.5" />
              Open
            </a>
          </Button>
        </div>
      )}
      <iframe
        src={`${url}#toolbar=0`}
        className="h-full w-full border-0"
        title={filename}
        onError={() => setError(true)}
      />
    </div>
  );
}
