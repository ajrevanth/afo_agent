"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { triggerMockEmail } from "@/lib/api";
import { toast } from "@/components/ui/use-toast";
import type { MockEmailPayload } from "@/lib/types";

const PRESETS: Record<string, MockEmailPayload> = {
  invoice: {
    sender: "finance@blackrock.com",
    subject: "Invoice #INV-2024-0042 — Management Fee Q3",
    body: "Please find attached the management fee invoice for Q3 2024. Amount due: $250,000 USD by Oct 15.",
    attachment_name: "invoice_q3_2024.pdf",
    attachment_type: "invoice",
  },
  capital_call: {
    sender: "ir@sequoiacapital.com",
    subject: "Capital Call Notice — Fund V LP",
    body: "Pursuant to Section 3.2 of the LPA, Sequoia Capital V is calling $5,000,000 of committed capital. Due: Nov 1, 2024.",
    attachment_name: "capital_call_fund_v.pdf",
    attachment_type: "capital_call",
  },
};

export function MockEmailForm() {
  const [form, setForm] = useState<MockEmailPayload>(PRESETS.invoice);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const set = (key: keyof MockEmailPayload, value: string) =>
    setForm((f) => ({ ...f, [key]: value }));

  const handlePreset = (key: string) => setForm(PRESETS[key]);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const doc = await triggerMockEmail(form);
      setResult(doc.id);
      toast({ title: "Email simulated", description: `Document ID: ${doc.id} is now processing.` });
    } catch (e) {
      toast({ variant: "destructive", title: "Failed", description: String(e) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Simulate Incoming Email</CardTitle>
        <CardDescription>Mimics an email arriving in the shared mailbox with an attachment</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => handlePreset("invoice")}>
            Invoice preset
          </Button>
          <Button variant="outline" size="sm" onClick={() => handlePreset("capital_call")}>
            Capital Call preset
          </Button>
        </div>

        <div className="space-y-2">
          <Label>Sender Email</Label>
          <Input value={form.sender} onChange={(e) => set("sender", e.target.value)} />
        </div>

        <div className="space-y-2">
          <Label>Subject</Label>
          <Input value={form.subject} onChange={(e) => set("subject", e.target.value)} />
        </div>

        <div className="space-y-2">
          <Label>Email Body</Label>
          <Textarea
            rows={4}
            value={form.body}
            onChange={(e) => set("body", e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Attachment Name</Label>
            <Input value={form.attachment_name} onChange={(e) => set("attachment_name", e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Attachment Type</Label>
            <Select
              value={form.attachment_type}
              onValueChange={(v) => set("attachment_type", v)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="invoice">Invoice</SelectItem>
                <SelectItem value="capital_call">Capital Call</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {result && (
          <div className="rounded-md bg-green-50 px-4 py-3 text-sm text-green-700">
            Email processed — Document ID: <strong>{result}</strong>
          </div>
        )}

        <Button onClick={handleSubmit} disabled={loading} className="w-full">
          {loading ? "Simulating..." : "Trigger Email Ingestion"}
        </Button>
      </CardContent>
    </Card>
  );
}
