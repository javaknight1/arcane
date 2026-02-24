"use client";

import { use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronDownIcon } from "lucide-react";
import { AuthGuard } from "@/components/auth-guard";
import { Navbar } from "@/components/navbar";
import { PageHeader } from "@/components/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useProject, useDeleteProject } from "@/hooks/use-projects";
import { toast } from "sonner";
import type { RoadmapSummary } from "@/types/api";

const statusColor: Record<string, "default" | "secondary" | "destructive"> = {
  draft: "secondary",
  generating: "default",
  completed: "default",
};

function RoadmapCard({ roadmap }: { roadmap: RoadmapSummary }) {
  return (
    <Link href={`/roadmaps/${roadmap.id}`}>
      <Card className="transition-colors hover:bg-accent/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">{roadmap.name}</CardTitle>
            <Badge variant={statusColor[roadmap.status] ?? "secondary"}>
              {roadmap.status}
            </Badge>
          </div>
          <CardDescription>
            Updated {new Date(roadmap.updated_at).toLocaleDateString()}
          </CardDescription>
        </CardHeader>
        {roadmap.item_counts && (
          <CardContent className="pt-0 space-y-2">
            <p className="text-xs text-muted-foreground">
              {roadmap.item_counts.milestones} milestones, {roadmap.item_counts.epics} epics, {roadmap.item_counts.stories} stories, {roadmap.item_counts.tasks} tasks
            </p>
            {roadmap.completion_percent !== null && (
              <div className="flex items-center gap-2">
                <Progress value={roadmap.completion_percent} className="h-1.5" />
                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  {roadmap.completion_percent}%
                </span>
              </div>
            )}
          </CardContent>
        )}
      </Card>
    </Link>
  );
}

function NewRoadmapButton({
  projectId,
  roadmaps,
}: {
  projectId: string;
  roadmaps: RoadmapSummary[];
}) {
  const latestCompleted = roadmaps.find((r) => r.status === "completed");

  if (!latestCompleted) {
    return (
      <Button asChild>
        <Link href={`/projects/${projectId}/new`}>New Roadmap</Link>
      </Button>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button>
          New Roadmap <ChevronDownIcon className="ml-1 size-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem asChild>
          <Link href={`/projects/${projectId}/new`}>Blank roadmap</Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href={`/projects/${projectId}/new?from=${latestCompleted.id}`}>
            New from &ldquo;{latestCompleted.name}&rdquo;
          </Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function ProjectDetailContent({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: project, isLoading, error } = useProject(id);
  const deleteProject = useDeleteProject();
  const router = useRouter();

  const handleDelete = async () => {
    if (!confirm("Delete this project and all its roadmaps?")) return;
    try {
      await deleteProject.mutateAsync(id);
      toast.success("Project deleted");
      router.push("/");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to delete");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <main className="container mx-auto px-4 py-8 space-y-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
          <Skeleton className="h-24 w-full" />
        </main>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <p className="text-sm text-destructive">Failed to load project.</p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <PageHeader
          title={project.name}
          description={`Created ${new Date(project.created_at).toLocaleDateString()}`}
          action={
            <div className="flex gap-2">
              <NewRoadmapButton projectId={id} roadmaps={project.roadmaps} />
            </div>
          }
        />

        <Separator className="my-6" />

        <h2 className="text-lg font-semibold mb-4">Roadmaps</h2>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {project.roadmaps.map((roadmap) => (
            <RoadmapCard key={roadmap.id} roadmap={roadmap} />
          ))}

          {project.roadmaps.length === 0 && (
            <p className="col-span-full text-sm text-muted-foreground">
              No roadmaps yet. Click &quot;New Roadmap&quot; to generate one.
            </p>
          )}
        </div>

        <Separator className="my-8" />

        <div>
          <Button variant="destructive" size="sm" onClick={handleDelete}>
            Delete Project
          </Button>
        </div>
      </main>
    </div>
  );
}

export default function ProjectPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return (
    <AuthGuard>
      <ProjectDetailContent params={params} />
    </AuthGuard>
  );
}
