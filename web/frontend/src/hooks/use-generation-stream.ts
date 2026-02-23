"use client";

import { useEffect, useRef, useState } from "react";
import { getTokens } from "@/lib/auth";
import type {
  ProgressData,
  ItemCreatedData,
  GenerationEvent,
} from "@/types/generation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type StreamStatus = "connecting" | "streaming" | "complete" | "error";

export function useGenerationStream(jobId: string | null) {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [items, setItems] = useState<ItemCreatedData[]>([]);
  const [status, setStatus] = useState<StreamStatus>("connecting");
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const controller = new AbortController();
    abortRef.current = controller;

    async function connect() {
      const { accessToken } = getTokens();
      if (!accessToken) {
        setError("Not authenticated");
        setStatus("error");
        return;
      }

      try {
        const res = await fetch(
          `${API_URL}/generation-jobs/${jobId}/stream`,
          {
            headers: { Authorization: `Bearer ${accessToken}` },
            signal: controller.signal,
          }
        );

        if (!res.ok) {
          setError(`Stream failed: ${res.status}`);
          setStatus("error");
          return;
        }

        const reader = res.body?.getReader();
        if (!reader) {
          setError("No response body");
          setStatus("error");
          return;
        }

        setStatus("streaming");
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // SSE messages are separated by double newlines
          const messages = buffer.split("\n\n");
          // Keep the last incomplete chunk in the buffer
          buffer = messages.pop() || "";

          for (const msg of messages) {
            const event = parseSSE(msg);
            if (!event) continue;

            switch (event.event) {
              case "progress":
                setProgress(event.data);
                break;
              case "item_created":
                setItems((prev) => [...prev, event.data]);
                break;
              case "complete":
                setProgress((prev) =>
                  prev ? { ...prev, phase: "complete" } : prev
                );
                setStatus("complete");
                return;
              case "error":
                setError(event.data.message);
                setStatus("error");
                return;
            }
          }
        }
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Stream failed");
        setStatus("error");
      }
    }

    connect();

    return () => {
      controller.abort();
    };
  }, [jobId]);

  return { progress, items, status, error };
}

function parseSSE(raw: string): GenerationEvent | null {
  let eventType = "";
  let data = "";

  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) {
      eventType = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      data = line.slice(5).trim();
    }
  }

  if (!eventType || !data) return null;

  try {
    const parsed = JSON.parse(data);
    return { event: eventType, data: parsed } as GenerationEvent;
  } catch {
    return null;
  }
}
