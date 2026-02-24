"use client";

import { useState } from "react";
import { RefreshCw, CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { useRegenerateItem } from "@/hooks/use-roadmap-mutations";
import { useGenerationStream } from "@/hooks/use-generation-stream";
import { ItemFeed } from "@/components/generation/item-feed";
import type { ItemType } from "@/types/roadmap";

const CHILD_TYPE_LABEL: Record<string, string> = {
  milestone: "epics",
  epic: "stories",
  story: "tasks",
};

interface RegenerateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  roadmapId: string;
  itemId: string;
  itemName: string;
  itemType: ItemType;
  childCount: number;
  onComplete: () => void;
}

export function RegenerateDialog({
  open,
  onOpenChange,
  roadmapId,
  itemId,
  itemName,
  itemType,
  childCount,
  onComplete,
}: RegenerateDialogProps) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [phase, setPhase] = useState<"confirm" | "generating" | "done" | "error">("confirm");

  const regenerate = useRegenerateItem(roadmapId);
  const { items, status, error } = useGenerationStream(jobId);

  // Sync stream status to phase
  if (jobId && status === "complete" && phase === "generating") {
    setPhase("done");
  }
  if (jobId && status === "error" && phase === "generating") {
    setPhase("error");
  }

  const handleConfirm = () => {
    regenerate.mutate(itemId, {
      onSuccess: (data) => {
        setJobId(data.id);
        setPhase("generating");
      },
      onError: () => {
        setPhase("error");
      },
    });
  };

  const handleClose = () => {
    if (phase === "done") {
      onComplete();
    }
    // Reset state
    setJobId(null);
    setPhase("confirm");
    onOpenChange(false);
  };

  const childLabel = CHILD_TYPE_LABEL[itemType] || "children";

  return (
    <Dialog open={open} onOpenChange={phase === "generating" ? undefined : handleClose}>
      <DialogContent className="sm:max-w-lg">
        {phase === "confirm" && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <RefreshCw className="h-5 w-5" />
                Regenerate {childLabel}?
              </DialogTitle>
              <DialogDescription>
                This will replace{" "}
                {childCount > 0
                  ? `${childCount} existing ${childLabel} and all their descendants`
                  : `the ${childLabel}`}{" "}
                of &quot;{itemName}&quot; with newly AI-generated content.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handleConfirm} disabled={regenerate.isPending}>
                {regenerate.isPending ? "Starting..." : "Regenerate"}
              </Button>
            </DialogFooter>
          </>
        )}

        {phase === "generating" && (
          <>
            <DialogHeader>
              <DialogTitle>Regenerating {childLabel}...</DialogTitle>
              <DialogDescription>
                Generating new content for &quot;{itemName}&quot;. This may take a moment.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <Progress value={100} className="animate-pulse" />
              <ItemFeed items={items} />
            </div>
          </>
        )}

        {phase === "done" && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-green-600 dark:text-green-400">
                <CheckCircle2 className="h-5 w-5" />
                Regeneration Complete
              </DialogTitle>
              <DialogDescription>
                Generated {items.length} new item{items.length === 1 ? "" : "s"} for
                &quot;{itemName}&quot;.
              </DialogDescription>
            </DialogHeader>
            <ItemFeed items={items} />
            <DialogFooter>
              <Button onClick={handleClose}>Done</Button>
            </DialogFooter>
          </>
        )}

        {phase === "error" && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-destructive">
                <AlertCircle className="h-5 w-5" />
                Regeneration Failed
              </DialogTitle>
              <DialogDescription>
                {error || regenerate.error?.message || "An unexpected error occurred."}
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                Close
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
