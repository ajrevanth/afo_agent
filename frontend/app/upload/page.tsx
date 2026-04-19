"use client";

import { useState } from "react";
import { UploadForm } from "@/components/upload-form";
import { MockEmailForm } from "@/components/mock-email-form";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Upload, Mail } from "lucide-react";

export default function UploadPage() {
  const [activeTab, setActiveTab] = useState("file");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Ingest Document</h1>
        <p className="text-muted-foreground">
          Upload a file directly or simulate an email arriving in the shared mailbox
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="max-w-2xl">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="file" className="gap-2">
            <Upload className="h-4 w-4" />
            Direct Upload
          </TabsTrigger>
          <TabsTrigger value="email" className="gap-2">
            <Mail className="h-4 w-4" />
            Simulate Email
          </TabsTrigger>
        </TabsList>

        <TabsContent value="file" className="mt-6">
          <UploadForm />
        </TabsContent>

        <TabsContent value="email" className="mt-6">
          <MockEmailForm />
        </TabsContent>
      </Tabs>
    </div>
  );
}
