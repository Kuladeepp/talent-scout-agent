"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

type Props = {
  onSubmit: (input: { jd_text?: string; jd_url?: string }) => void;
  loading: boolean;
};

export function JdInput({ onSubmit, loading }: Props) {
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
          Paste JD text
        </Button>
        <Button
          type="button"
          variant={mode === "url" ? "default" : "outline"}
          onClick={() => setMode("url")}
          size="sm"
        >
          From URL
        </Button>
      </div>

      {mode === "text" ? (
        <Textarea
          placeholder="Paste the full job description here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={8}
        />
      ) : (
        <Input
          placeholder="https://jobs.example.com/posting/1234"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
      )}

      <Button onClick={submit} disabled={loading} className="w-full">
        {loading ? "Scouting candidates..." : "Find & engage candidates"}
      </Button>
    </Card>
  );
}
