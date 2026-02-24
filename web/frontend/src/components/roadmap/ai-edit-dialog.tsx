"use client";

import { useState } from "react";
import { Sparkles, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { useAiEditItem } from "@/hooks/use-roadmap-mutations";
import type { AiEditResponse } from "@/types/api";

/** Keys to skip when showing the diff. */
const SKIP_KEYS = new Set(["id", "epics", "stories", "tasks"]);

interface AiEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  roadmapId: string;
  itemId: string;
  itemName: string;
  itemType: string;
  onComplete: () => void;
}

function ChangedField({
  field,
  before,
  after,
}: {
  field: string;
  before: unknown;
  after: unknown;
}) {
  const formatValue = (v: unknown): string => {
    if (Array.isArray(v)) return v.join(", ");
    if (v === null || v === undefined) return "(empty)";
    return String(v);
  };

  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-muted-foreground capitalize">
        {field.replace(/_/g, " ")}
      </p>
      <div className="rounded-md bg-red-50 dark:bg-red-950/20 p-2 text-xs line-through text-muted-foreground">
        {formatValue(before)}
      </div>
      <div className="rounded-md bg-green-50 dark:bg-green-950/20 p-2 text-xs">
        {formatValue(after)}
      </div>
    </div>
  );
}

export function AiEditDialog({
  open,
  onOpenChange,
  roadmapId,
  itemId,
  itemName,
  itemType,
  onComplete,
}: AiEditDialogProps) {
  const [phase, setPhase] = useState<"command" | "loading" | "result" | "error">("command");
  const [command, setCommand] = useState("");
  const [result, setResult] = useState<AiEditResponse | null>(null);

  const aiEdit = useAiEditItem(roadmapId);

  const handleSubmit = () => {
    if (!command.trim()) return;
    setPhase("loading");
    aiEdit.mutate(
      { itemId, command: command.trim() },
      {
        onSuccess: (data) => {
          setResult(data);
          setPhase("result");
        },
        onError: () => {
          setPhase("error");
        },
      }
    );
  };

  const handleClose = () => {
    if (phase === "result") {
      onComplete();
    }
    setPhase("command");
    setCommand("");
    setResult(null);
    onOpenChange(false);
  };

  const changedFields = result
    ? Object.keys(result.edited).filter((key) => {
        if (SKIP_KEYS.has(key)) return false;
        return JSON.stringify(result.original[key]) !== JSON.stringify(result.edited[key]);
      })
    : [];

  return (
    <Dialog open={open} onOpenChange={phase === "loading" ? undefined : handleClose}>
      <DialogContent className="sm:max-w-lg">
        {phase === "command" && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                AI Edit: {itemName}
              </DialogTitle>
              <DialogDescription>
                Describe how you want to modify this {itemType}. The AI will edit it based on your
                instructions.
              </DialogDescription>
            </DialogHeader>
            <Textarea
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder="e.g., Make this more detailed with specific file paths..."
              rows={3}
              className="resize-none"
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                  handleSubmit();
                }
              }}
            />
            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handleSubmit} disabled={!command.trim()}>
                <Sparkles className="h-4 w-4 mr-1.5" />
                Edit with AI
              </Button>
            </DialogFooter>
          </>
        )}

        {phase === "loading" && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin" />
                Editing with AI...
              </DialogTitle>
              <DialogDescription>
                Applying your changes to &quot;{itemName}&quot;. This may take a moment.
              </DialogDescription>
            </DialogHeader>
          </>
        )}

        {phase === "result" && result && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-green-600 dark:text-green-400">
                <CheckCircle2 className="h-5 w-5" />
                Edit Complete
              </DialogTitle>
              <DialogDescription>
                {changedFields.length > 0
                  ? `${changedFields.length} field${changedFields.length === 1 ? "" : "s"} updated.`
                  : "No fields were changed."}
              </DialogDescription>
            </DialogHeader>
            {changedFields.length > 0 && (
              <div className="max-h-80 overflow-y-auto space-y-3">
                {changedFields.map((field) => (
                  <ChangedField
                    key={field}
                    field={field}
                    before={result.original[field]}
                    after={result.edited[field]}
                  />
                ))}
              </div>
            )}
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
                Edit Failed
              </DialogTitle>
              <DialogDescription>
                {aiEdit.error?.message || "An unexpected error occurred."}
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                Close
              </Button>
              <Button
                onClick={() => {
                  setPhase("command");
                }}
              >
                Try Again
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
