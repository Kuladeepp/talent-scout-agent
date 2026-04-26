"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { FileText, Link as LinkIcon, Loader2 } from "lucide-react";

type Props = {
  onSubmit: (input: { jd_text?: string; jd_url?: string }) => void;
  loading: boolean;
  loadingMessage?: string;
};

export function JdInput({ onSubmit, loading, loadingMessage }: Props) {
  const [mode, setMode] = useState<"text" | "url">("text");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");

  const submit = () => {
    if (mode === "text" && text.trim()) onSubmit({ jd_text: text });
    else if (mode === "url" && url.trim()) onSubmit({ jd_url: url });
  };

  return (
    <Card className="p-6 space-y-4">
      <div className="flex gap-2">
        <Button
          type="button"
          variant={mode === "text" ? "default" : "outline"}
          onClick={() => setMode("text")}
          size="sm"
        >
          <FileText className="w-4 h-4 mr-2" />
          Paste JD text
        </Button>
        <Button
          type="button"
          variant={mode === "url" ? "default" : "outline"}
          onClick={() => setMode("url")}
          size="sm"
        >
          <LinkIcon className="w-4 h-4 mr-2" />
          From URL
        </Button>
      </div>

      {mode === "text" ? (
        <Textarea
          placeholder="Paste the full job description here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={10}
          className="font-mono text-sm"
        />
      ) : (
        <Input
          placeholder="https://jobs.example.com/posting/1234"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
      )}

      {loading ? (
        <Button disabled className="w-full bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-medium disabled:opacity-50">
          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          {loadingMessage ?? "Running pipeline..."}
        </Button>
      ) : (
        <Button onClick={submit} className="w-full bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-medium hover:opacity-90">
          Find & engage candidates
        </Button>
      )}
    </Card>
  );
}
