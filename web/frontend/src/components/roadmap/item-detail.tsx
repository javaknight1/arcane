"use client";

import { useState, useCallback } from "react";
import { Check, Copy, Trash2, ChevronUp, ChevronDown, RefreshCw, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import type {
  RoadmapItem,
  ItemType,
  RoadmapTask,
  RoadmapEpic,
  RoadmapMilestone,
  RoadmapStory,
  Priority,
  ItemStatus,
} from "@/types/roadmap";
import { getEstimatedHours, getChildren } from "@/types/roadmap";
import {
  TYPE_STYLES,
  PRIORITY_STYLES,
  STATUS_BADGE,
  STATUS_LABEL,
  PRIORITY_LABEL,
} from "./constants";
import { EditableField, EditableList } from "./editable-field";
import type { ItemUpdate } from "@/types/api";

interface ItemDetailProps {
  item: RoadmapItem | null;
  type: ItemType | null;
  roadmapId?: string;
  onItemUpdated?: (itemId: string, updates: ItemUpdate) => void;
  onItemDeleted?: (itemId: string) => void;
  onReorder?: (parentId: string, itemIds: string[]) => void;
  onRegenerate?: (itemId: string) => void;
  onAiEdit?: (itemId: string) => void;
  parentId?: string | null;
  siblingIds?: string[];
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Button variant="ghost" size="sm" onClick={handleCopy} className="h-7 gap-1.5">
      {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
      {copied ? "Copied" : "Copy"}
    </Button>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-muted-foreground mb-1.5">{title}</h3>
      {children}
    </div>
  );
}

export function ItemDetail({
  item,
  type,
  roadmapId,
  onItemUpdated,
  onItemDeleted,
  onReorder,
  onRegenerate,
  onAiEdit,
  parentId,
  siblingIds,
}: ItemDetailProps) {
  const [deleteOpen, setDeleteOpen] = useState(false);
  const editable = !!roadmapId && !!onItemUpdated;

  if (!item || !type) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Select an item from the tree to view details
      </div>
    );
  }

  const hours = getEstimatedHours(item, type);
  const hasGoal = type === "milestone" || type === "epic";
  const goal = hasGoal ? (item as RoadmapMilestone | RoadmapEpic).goal : null;
  const hasAcceptanceCriteria = type === "story" || type === "task";
  const acceptanceCriteria = hasAcceptanceCriteria
    ? (item as RoadmapStory | RoadmapTask).acceptance_criteria
    : [];
  const hasPrerequisites = type === "epic" || type === "task";
  const prerequisites = hasPrerequisites
    ? (item as RoadmapEpic | RoadmapTask).prerequisites
    : [];
  const isTask = type === "task";
  const task = isTask ? (item as RoadmapTask) : null;

  const childCount = getChildren(item, type).length;
  const handleUpdate = (updates: ItemUpdate) => {
    if (onItemUpdated) {
      onItemUpdated(item.id, updates);
    }
  };

  // Reorder helpers
  const currentIndex = siblingIds?.indexOf(item.id) ?? -1;
  const canMoveUp = currentIndex > 0;
  const canMoveDown = siblingIds ? currentIndex < siblingIds.length - 1 : false;

  const handleMoveUp = () => {
    if (!onReorder || !parentId || !siblingIds || !canMoveUp) return;
    const newOrder = [...siblingIds];
    [newOrder[currentIndex - 1], newOrder[currentIndex]] = [newOrder[currentIndex], newOrder[currentIndex - 1]];
    onReorder(parentId, newOrder);
  };

  const handleMoveDown = () => {
    if (!onReorder || !parentId || !siblingIds || !canMoveDown) return;
    const newOrder = [...siblingIds];
    [newOrder[currentIndex], newOrder[currentIndex + 1]] = [newOrder[currentIndex + 1], newOrder[currentIndex]];
    onReorder(parentId, newOrder);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="space-y-5 p-4 overflow-y-auto flex-1">
        {/* Header badges */}
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <Badge variant="secondary" className={cn(TYPE_STYLES[type])}>
              {type}
            </Badge>
            {editable ? (
              <Select
                value={item.priority}
                onValueChange={(v) => handleUpdate({ priority: v })}
              >
                <SelectTrigger size="sm" className={cn("h-5 text-[10px] px-2 border-0 shadow-none", PRIORITY_STYLES[item.priority])}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(["critical", "high", "medium", "low"] as Priority[]).map((p) => (
                    <SelectItem key={p} value={p}>
                      {PRIORITY_LABEL[p]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Badge variant="secondary" className={cn(PRIORITY_STYLES[item.priority])}>
                {PRIORITY_LABEL[item.priority]}
              </Badge>
            )}
            {editable ? (
              <Select
                value={item.status}
                onValueChange={(v) => handleUpdate({ status: v })}
              >
                <SelectTrigger size="sm" className={cn("h-5 text-[10px] px-2 border-0 shadow-none", STATUS_BADGE[item.status])}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(["not_started", "in_progress", "blocked", "completed"] as ItemStatus[]).map((s) => (
                    <SelectItem key={s} value={s}>
                      {STATUS_LABEL[s]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Badge variant="secondary" className={cn(STATUS_BADGE[item.status])}>
                {STATUS_LABEL[item.status]}
              </Badge>
            )}
          </div>
          {editable ? (
            <EditableField
              value={item.name}
              onSave={(v) => handleUpdate({ name: v })}
              className="text-lg font-semibold"
            />
          ) : (
            <h2 className="text-lg font-semibold">{item.name}</h2>
          )}
        </div>

        {/* Description */}
        <Section title="Description">
          {editable ? (
            <EditableField
              value={item.description}
              onSave={(v) => handleUpdate({ description: v })}
              multiline
              placeholder="Add a description..."
            />
          ) : (
            <p className="text-sm">{item.description}</p>
          )}
        </Section>

        {/* Goal (milestones, epics) */}
        {hasGoal && (
          <Section title="Goal">
            {editable ? (
              <EditableField
                value={goal ?? ""}
                onSave={(v) => handleUpdate({ goal: v })}
                multiline
                placeholder="Set a goal..."
              />
            ) : (
              <p className="text-sm">{goal}</p>
            )}
          </Section>
        )}

        {/* Estimated Hours */}
        <Section title="Estimated Hours">
          {editable && isTask ? (
            <EditableField
              value={String(task!.estimated_hours)}
              onSave={(v) => {
                const n = parseInt(v, 10);
                if (!isNaN(n) && n > 0) handleUpdate({ estimated_hours: n });
              }}
              inputType="number"
              placeholder="Hours..."
            />
          ) : (
            <p className="text-sm tabular-nums">{hours}h</p>
          )}
        </Section>

        {/* Acceptance Criteria (stories, tasks) */}
        {hasAcceptanceCriteria && (
          <Section title="Acceptance Criteria">
            {editable ? (
              <EditableList
                items={acceptanceCriteria}
                onSave={(items) => handleUpdate({ acceptance_criteria: items })}
                placeholder="Add criterion..."
              />
            ) : acceptanceCriteria.length > 0 ? (
              <ul className="list-disc list-inside space-y-1 text-sm">
                {acceptanceCriteria.map((criterion, i) => (
                  <li key={i}>{criterion}</li>
                ))}
              </ul>
            ) : null}
          </Section>
        )}

        {/* Labels */}
        <Section title="Labels">
          {editable ? (
            <EditableList
              items={item.labels}
              onSave={(items) => handleUpdate({ labels: items })}
              placeholder="Add label..."
            />
          ) : item.labels.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {item.labels.map((label) => (
                <Badge key={label} variant="outline" className="text-xs">
                  {label}
                </Badge>
              ))}
            </div>
          ) : null}
        </Section>

        {/* Prerequisites (epics, tasks) */}
        {hasPrerequisites && prerequisites.length > 0 && (
          <Section title="Prerequisites">
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              {prerequisites.map((id) => (
                <li key={id}>{id}</li>
              ))}
            </ul>
          </Section>
        )}

        {/* Implementation Notes (tasks) */}
        {isTask && (
          <Section title="Implementation Notes">
            {editable ? (
              <EditableField
                value={task!.implementation_notes}
                onSave={(v) => handleUpdate({ implementation_notes: v })}
                multiline
                placeholder="Add implementation notes..."
                className="bg-muted rounded-md p-3"
              />
            ) : task?.implementation_notes ? (
              <p className="text-sm text-muted-foreground bg-muted rounded-md p-3">
                {task.implementation_notes}
              </p>
            ) : null}
          </Section>
        )}

        {/* Claude Code Prompt (tasks) */}
        {isTask && (
          <Section title="Claude Code Prompt">
            {editable ? (
              <div className="relative">
                <div className="absolute right-2 top-2 z-10">
                  <CopyButton text={task!.claude_code_prompt} />
                </div>
                <EditableField
                  value={task!.claude_code_prompt}
                  onSave={(v) => handleUpdate({ claude_code_prompt: v })}
                  multiline
                  placeholder="Add a Claude Code prompt..."
                  className="rounded-md bg-muted p-3 pr-20 text-xs font-mono"
                />
              </div>
            ) : task?.claude_code_prompt ? (
              <div className="relative">
                <div className="absolute right-2 top-2">
                  <CopyButton text={task.claude_code_prompt} />
                </div>
                <pre className="rounded-md bg-muted p-3 pr-20 text-xs font-mono whitespace-pre-wrap overflow-x-auto">
                  {task.claude_code_prompt}
                </pre>
              </div>
            ) : null}
          </Section>
        )}
      </div>

      {/* Footer: reorder + delete */}
      {editable && (
        <>
          <Separator />
          <div className="flex items-center justify-between p-3">
            <div className="flex items-center gap-1">
              {siblingIds && siblingIds.length > 1 && (
                <>
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-7 w-7"
                    disabled={!canMoveUp}
                    onClick={handleMoveUp}
                  >
                    <ChevronUp className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-7 w-7"
                    disabled={!canMoveDown}
                    onClick={handleMoveDown}
                  >
                    <ChevronDown className="h-3.5 w-3.5" />
                  </Button>
                </>
              )}
            </div>
            <div className="flex items-center gap-1">
              {onAiEdit && (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 gap-1.5"
                  onClick={() => onAiEdit(item.id)}
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  AI Edit
                </Button>
              )}
              {type !== "task" && onRegenerate && (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 gap-1.5"
                  onClick={() => onRegenerate(item.id)}
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  Regenerate
                </Button>
              )}
              <Button
                variant="destructive"
                size="sm"
                className="h-7 gap-1.5"
                onClick={() => setDeleteOpen(true)}
              >
                <Trash2 className="h-3.5 w-3.5" />
                Delete
              </Button>
            </div>
          </div>

          <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Delete {type}?</DialogTitle>
                <DialogDescription>
                  {childCount > 0
                    ? `This will permanently delete "${item.name}" and its ${childCount} child item${childCount === 1 ? "" : "s"}. This action cannot be undone.`
                    : `This will permanently delete "${item.name}". This action cannot be undone.`}
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDeleteOpen(false)}>
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => {
                    setDeleteOpen(false);
                    onItemDeleted?.(item.id);
                  }}
                >
                  Delete
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </>
      )}
    </div>
  );
}
