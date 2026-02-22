"use client";

import { AuthGuard } from "@/components/auth-guard";
import { Navbar } from "@/components/navbar";
import { PageHeader } from "@/components/page-header";
import { ProjectCard } from "@/components/project-card";
import { CreateProjectDialog } from "@/components/create-project-dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { useProjects } from "@/hooks/use-projects";

function Dashboard() {
  const { data: projects, isLoading, error } = useProjects();

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <PageHeader
          title="Projects"
          description="Manage your projects and generate roadmaps."
          action={<CreateProjectDialog />}
        />

        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {isLoading &&
            Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-lg" />
            ))}

          {error && (
            <p className="col-span-full text-sm text-destructive">
              Failed to load projects.
            </p>
          )}

          {projects?.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}

          {projects && projects.length === 0 && (
            <p className="col-span-full text-sm text-muted-foreground">
              No projects yet. Create one to get started.
            </p>
          )}
        </div>
      </main>
    </div>
  );
}

export default function HomePage() {
  return (
    <AuthGuard>
      <Dashboard />
    </AuthGuard>
  );
}
