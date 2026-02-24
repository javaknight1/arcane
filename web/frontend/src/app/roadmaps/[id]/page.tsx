"use client";

import { use } from "react";
import Link from "next/link";
import { AuthGuard } from "@/components/auth-guard";
import { Navbar } from "@/components/navbar";
import { PageHeader } from "@/components/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useGetRoadmap } from "@/hooks/use-roadmaps";
import { RoadmapViewer } from "@/components/roadmap/roadmap-viewer";
import { RoadmapDashboard } from "@/components/roadmap/roadmap-dashboard";
import { ExportDialog } from "@/components/roadmap/export-dialog";
import type { RoadmapData } from "@/types/roadmap";

const statusColor: Record<string, "default" | "secondary" | "destructive"> = {
  draft: "secondary",
  generating: "default",
  completed: "default",
};

function RoadmapPageContent({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: roadmap, isLoading, error } = useGetRoadmap(id);

  if (isLoading) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <main className="container mx-auto px-4 py-8 space-y-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
          <div className="flex flex-col lg:flex-row gap-4 mt-6">
            <Skeleton className="lg:w-1/3 min-w-[300px] h-[60vh]" />
            <Skeleton className="flex-1 h-[60vh]" />
          </div>
        </main>
      </div>
    );
  }

  if (error || !roadmap) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <p className="text-sm text-destructive mb-4">
            Failed to load roadmap.
          </p>
          <Button variant="outline" asChild>
            <Link href="/">Back to projects</Link>
          </Button>
        </main>
      </div>
    );
  }

  const roadmapData = roadmap.roadmap_data as RoadmapData | null;
  const hasMilestones = roadmapData?.milestones && roadmapData.milestones.length > 0;

  if (!hasMilestones) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <PageHeader
            title={roadmap.name}
            action={
              <Badge variant={statusColor[roadmap.status] ?? "secondary"}>
                {roadmap.status}
              </Badge>
            }
          />
          <div className="mt-8 rounded-lg border border-dashed p-12 text-center text-muted-foreground">
            {roadmap.status === "generating"
              ? "This roadmap is currently being generated. Check back soon."
              : "This roadmap has no items yet. Start generation to populate it."}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <PageHeader
          title={roadmap.name}
          action={
            <div className="flex items-center gap-2">
              <ExportDialog roadmapId={id} />
              <Badge variant={statusColor[roadmap.status] ?? "secondary"}>
                {roadmap.status}
              </Badge>
            </div>
          }
        />
        <div className="mt-6">
          <RoadmapDashboard roadmapId={id} />
          <RoadmapViewer data={roadmapData} roadmapId={id} />
        </div>
      </main>
    </div>
  );
}

export default function RoadmapViewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return (
    <AuthGuard>
      <RoadmapPageContent params={params} />
    </AuthGuard>
  );
}
