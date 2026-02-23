"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { RoadmapItem, ItemType, RoadmapTask, RoadmapEpic, RoadmapMilestone, RoadmapStory } from "@/types/roadmap";
import { getEstimatedHours } from "@/types/roadmap";
import {
  TYPE_STYLES,
  PRIORITY_STYLES,
  STATUS_BADGE,
  STATUS_LABEL,
  PRIORITY_LABEL,
} from "./constants";

interface ItemDetailProps {
  item: RoadmapItem | null;
  type: ItemType | null;
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

export function ItemDetail({ item, type }: ItemDetailProps) {
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

  return (
    <div className="space-y-5 p-4 overflow-y-auto h-full">
      {/* Header */}
      <div>
        <div className="flex flex-wrap items-center gap-2 mb-2">
          <Badge variant="secondary" className={cn(TYPE_STYLES[type])}>
            {type}
          </Badge>
          <Badge variant="secondary" className={cn(PRIORITY_STYLES[item.priority])}>
            {PRIORITY_LABEL[item.priority]}
          </Badge>
          <Badge variant="secondary" className={cn(STATUS_BADGE[item.status])}>
            {STATUS_LABEL[item.status]}
          </Badge>
        </div>
        <h2 className="text-lg font-semibold">{item.name}</h2>
      </div>

      {/* Description */}
      <Section title="Description">
        <p className="text-sm">{item.description}</p>
      </Section>

      {/* Goal (milestones, epics) */}
      {goal && (
        <Section title="Goal">
          <p className="text-sm">{goal}</p>
        </Section>
      )}

      {/* Estimated Hours */}
      <Section title="Estimated Hours">
        <p className="text-sm tabular-nums">{hours}h</p>
      </Section>

      {/* Acceptance Criteria (stories, tasks) */}
      {acceptanceCriteria.length > 0 && (
        <Section title="Acceptance Criteria">
          <ul className="list-disc list-inside space-y-1 text-sm">
            {acceptanceCriteria.map((criterion, i) => (
              <li key={i}>{criterion}</li>
            ))}
          </ul>
        </Section>
      )}

      {/* Labels */}
      {item.labels.length > 0 && (
        <Section title="Labels">
          <div className="flex flex-wrap gap-1.5">
            {item.labels.map((label) => (
              <Badge key={label} variant="outline" className="text-xs">
                {label}
              </Badge>
            ))}
          </div>
        </Section>
      )}

      {/* Prerequisites (epics, tasks) */}
      {prerequisites.length > 0 && (
        <Section title="Prerequisites">
          <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
            {prerequisites.map((id) => (
              <li key={id}>{id}</li>
            ))}
          </ul>
        </Section>
      )}

      {/* Implementation Notes (tasks) */}
      {task?.implementation_notes && (
        <Section title="Implementation Notes">
          <p className="text-sm text-muted-foreground bg-muted rounded-md p-3">
            {task.implementation_notes}
          </p>
        </Section>
      )}

      {/* Claude Code Prompt (tasks) */}
      {task?.claude_code_prompt && (
        <Section title="Claude Code Prompt">
          <div className="relative">
            <div className="absolute right-2 top-2">
              <CopyButton text={task.claude_code_prompt} />
            </div>
            <pre className="rounded-md bg-muted p-3 pr-20 text-xs font-mono whitespace-pre-wrap overflow-x-auto">
              {task.claude_code_prompt}
            </pre>
          </div>
        </Section>
      )}
    </div>
  );
}
