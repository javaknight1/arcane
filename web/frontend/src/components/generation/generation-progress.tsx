"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useGenerationStream } from "@/hooks/use-generation-stream";
import { ItemFeed } from "./item-feed";

const PHASE_LABELS: Record<string, string> = {
  milestones: "Generating milestones...",
  epics: "Generating epics...",
  stories: "Generating stories...",
  tasks: "Generating tasks...",
  complete: "Generation complete!",
};

interface GenerationProgressProps {
  jobId: string;
  roadmapId: string;
}

export function GenerationProgress({ jobId, roadmapId }: GenerationProgressProps) {
  const { progress, items, status, error } = useGenerationStream(jobId);

  if (status === "error") {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-destructive">Generation Failed</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            {error || "An unexpected error occurred during generation."}
          </p>
          <Button variant="outline" asChild>
            <Link href="/projects">Back to Projects</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (status === "complete") {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-green-600 dark:text-green-400">
            Roadmap Generated!
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {progress && (
            <div className="flex flex-wrap gap-2">
              <CountBadge label="Milestones" count={progress.milestones} />
              <CountBadge label="Epics" count={progress.epics} />
              <CountBadge label="Stories" count={progress.stories} />
              <CountBadge label="Tasks" count={progress.tasks} />
            </div>
          )}
          <ItemFeed items={items} />
          <Button asChild>
            <Link href={`/roadmaps/${roadmapId}`}>View Roadmap</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Connecting or streaming
  const phase = progress?.phase || "milestones";
  const phaseLabel = PHASE_LABELS[phase] || "Generating...";

  // Progress bar: determinate during tasks phase, indeterminate otherwise
  const isTasksPhase = phase === "tasks";
  const progressPercent = isTasksPhase && progress && progress.stories_total > 0
    ? Math.round((progress.stories_completed / progress.stories_total) * 100)
    : undefined;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generation Progress</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <p className="text-sm font-medium">{phaseLabel}</p>
          {progressPercent !== undefined ? (
            <Progress value={progressPercent} />
          ) : (
            <Progress value={100} className="animate-pulse" />
          )}
          {progressPercent !== undefined && (
            <p className="text-xs text-muted-foreground text-right">
              {progress!.stories_completed} / {progress!.stories_total} stories expanded
            </p>
          )}
        </div>

        {progress && (
          <div className="flex flex-wrap gap-2">
            <CountBadge label="Milestones" count={progress.milestones} />
            <CountBadge label="Epics" count={progress.epics} />
            <CountBadge label="Stories" count={progress.stories} />
            <CountBadge label="Tasks" count={progress.tasks} />
          </div>
        )}

        <ItemFeed items={items} />
      </CardContent>
    </Card>
  );
}

function CountBadge({ label, count }: { label: string; count: number }) {
  return (
    <Badge variant="outline" className="text-sm">
      {label}: {count}
    </Badge>
  );
}
