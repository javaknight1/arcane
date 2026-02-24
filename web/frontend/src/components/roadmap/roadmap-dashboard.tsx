"use client";

import { useState } from "react";
import { ChevronDownIcon, ChevronUpIcon, AlertTriangleIcon, ClockIcon } from "lucide-react";
import { useRoadmapStats } from "@/hooks/use-roadmaps";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { MilestoneStats } from "@/types/api";

const statusLabel: Record<string, string> = {
  not_started: "Not Started",
  in_progress: "In Progress",
  blocked: "Blocked",
  completed: "Completed",
};

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  not_started: "outline",
  in_progress: "default",
  blocked: "destructive",
  completed: "secondary",
};

function MilestoneRow({ ms }: { ms: MilestoneStats }) {
  const pct = ms.hours_total > 0
    ? Math.round((ms.hours_completed / ms.hours_total) * 100)
    : 0;

  return (
    <div className="flex flex-col gap-1.5 rounded-md border p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium truncate">{ms.name}</span>
        <div className="flex items-center gap-1.5 shrink-0">
          {ms.is_overdue && (
            <Badge variant="destructive" className="text-xs gap-1">
              <AlertTriangleIcon className="size-3" />
              Overdue
            </Badge>
          )}
          <Badge variant={statusVariant[ms.status] ?? "outline"}>
            {statusLabel[ms.status] ?? ms.status}
          </Badge>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Progress value={pct} className="h-1.5 flex-1" />
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {ms.hours_completed}/{ms.hours_total}h
        </span>
      </div>
      <p className="text-xs text-muted-foreground">
        {ms.epic_count} epics, {ms.story_count} stories, {ms.task_count} tasks
        {ms.completed_items > 0 && ` ({ms.completed_items}/{ms.total_items} tasks done)`}
      </p>
    </div>
  );
}

export function RoadmapDashboard({ roadmapId }: { roadmapId: string }) {
  const { data: stats, isLoading } = useRoadmapStats(roadmapId);
  const [expanded, setExpanded] = useState(true);

  if (isLoading) {
    return <Skeleton className="h-16 w-full mb-4" />;
  }

  if (!stats || stats.milestones.length === 0) {
    return null;
  }

  return (
    <Card className="mb-4">
      <CardContent className="pt-4 pb-3 px-4">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center justify-between w-full text-left"
        >
          <div className="flex items-center gap-3">
            <ClockIcon className="size-4 text-muted-foreground" />
            <span className="text-sm font-medium">
              {stats.hours_completed}/{stats.hours_total}h completed
            </span>
            <Progress value={stats.completion_percent} className="h-1.5 w-24 sm:w-32" />
            <span className="text-xs text-muted-foreground">
              {stats.completion_percent}%
            </span>
          </div>
          {expanded ? (
            <ChevronUpIcon className="size-4 text-muted-foreground" />
          ) : (
            <ChevronDownIcon className="size-4 text-muted-foreground" />
          )}
        </button>
        {expanded && (
          <div className="grid gap-2 mt-3 sm:grid-cols-2 lg:grid-cols-3">
            {stats.milestones.map((ms) => (
              <MilestoneRow key={ms.id} ms={ms} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
