"use client";

import { use } from "react";
import { AuthGuard } from "@/components/auth-guard";
import { Navbar } from "@/components/navbar";
import { PageHeader } from "@/components/page-header";
import { DiscoveryWizard } from "@/components/wizard/discovery-wizard";

function NewRoadmapContent({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <PageHeader
          title="Discovery Wizard"
          description="Answer a few questions to generate the best roadmap for your project."
        />
        <div className="mt-8">
          <DiscoveryWizard projectId={id} />
        </div>
      </main>
    </div>
  );
}

export default function NewRoadmapPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return (
    <AuthGuard>
      <NewRoadmapContent params={params} />
    </AuthGuard>
  );
}
