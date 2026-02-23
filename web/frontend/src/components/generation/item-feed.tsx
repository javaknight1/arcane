"use client";

import { useEffect, useRef } from "react";
import { Badge } from "@/components/ui/badge";
import type { ItemCreatedData } from "@/types/generation";

const TYPE_STYLES: Record<string, string> = {
  milestone: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  epic: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  story: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  task: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
};

interface ItemFeedProps {
  items: ItemCreatedData[];
}

export function ItemFeed({ items }: ItemFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [items.length]);

  if (items.length === 0) {
    return (
      <div className="text-center text-sm text-muted-foreground py-8">
        Waiting for items...
      </div>
    );
  }

  return (
    <div className="max-h-80 overflow-y-auto space-y-2 pr-1">
      {items.map((item, i) => (
        <div
          key={i}
          className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm animate-in fade-in slide-in-from-bottom-1 duration-200"
        >
          <Badge
            variant="secondary"
            className={TYPE_STYLES[item.type] || ""}
          >
            {item.type}
          </Badge>
          <span className="font-medium truncate">{item.name}</span>
          {item.parent && (
            <span className="text-muted-foreground text-xs ml-auto shrink-0">
              in {item.parent}
            </span>
          )}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
