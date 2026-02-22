"use client";

import Link from "next/link";
import type { ProjectSummary } from "@/types/api";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ProjectCardProps {
  project: ProjectSummary;
}

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link href={`/projects/${project.id}`}>
      <Card className="transition-colors hover:bg-accent/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">{project.name}</CardTitle>
            <Badge variant="secondary">
              {project.roadmap_count}{" "}
              {project.roadmap_count === 1 ? "roadmap" : "roadmaps"}
            </Badge>
          </div>
          <CardDescription>
            Created {new Date(project.created_at).toLocaleDateString()}
          </CardDescription>
        </CardHeader>
      </Card>
    </Link>
  );
}
