"use client";

import { AuthGuard } from "@/components/auth-guard";
import { Navbar } from "@/components/navbar";
import { PageHeader } from "@/components/page-header";

export default function RoadmapViewPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <PageHeader
            title="Roadmap Viewer"
            description="Coming in T47"
          />
          <div className="mt-8 rounded-lg border border-dashed p-12 text-center text-muted-foreground">
            The roadmap viewer will show the full hierarchy of milestones,
            epics, stories, and tasks.
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
