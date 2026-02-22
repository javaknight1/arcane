"use client";

import { AuthGuard } from "@/components/auth-guard";
import { Navbar } from "@/components/navbar";
import { PageHeader } from "@/components/page-header";

export default function NewRoadmapPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <PageHeader
            title="Discovery Wizard"
            description="Coming in T45"
          />
          <div className="mt-8 rounded-lg border border-dashed p-12 text-center text-muted-foreground">
            The discovery wizard will guide you through project questions
            before generating a roadmap.
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
