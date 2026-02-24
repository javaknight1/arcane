"use client";

import { use, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { Navbar } from "@/components/navbar";
import { PageHeader } from "@/components/page-header";
import { DiscoveryWizard } from "@/components/wizard/discovery-wizard";
import { useGetRoadmap } from "@/hooks/use-roadmaps";
import { useProject } from "@/hooks/use-projects";
import type { WizardFormData } from "@/types/wizard";

function NewRoadmapContent({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const searchParams = useSearchParams();
  const fromId = searchParams.get("from");

  const { data: project } = useProject(id);
  const { data: sourceRoadmap, isLoading: sourceLoading } = useGetRoadmap(fromId ?? "");

  const initialData = useMemo<Partial<WizardFormData> | undefined>(() => {
    if (!fromId || !sourceRoadmap?.context) return undefined;
    const ctx = sourceRoadmap.context as Record<string, unknown>;
    // Extract wizard-compatible fields from context
    const data: Partial<WizardFormData> = {};
    if (typeof ctx.project_name === "string") data.project_name = ctx.project_name;
    if (typeof ctx.vision === "string") data.vision = ctx.vision;
    if (typeof ctx.problem_statement === "string") data.problem_statement = ctx.problem_statement;
    if (Array.isArray(ctx.target_users)) data.target_users = ctx.target_users as string[];
    if (typeof ctx.timeline === "string") data.timeline = ctx.timeline;
    if (typeof ctx.team_size === "number") data.team_size = ctx.team_size;
    if (typeof ctx.developer_experience === "string") data.developer_experience = ctx.developer_experience;
    if (typeof ctx.budget_constraints === "string") data.budget_constraints = ctx.budget_constraints;
    if (Array.isArray(ctx.tech_stack)) data.tech_stack = ctx.tech_stack as string[];
    if (typeof ctx.infrastructure_preferences === "string") data.infrastructure_preferences = ctx.infrastructure_preferences;
    if (typeof ctx.existing_codebase === "boolean") data.existing_codebase = ctx.existing_codebase;
    if (Array.isArray(ctx.must_have_features)) data.must_have_features = ctx.must_have_features as string[];
    if (Array.isArray(ctx.nice_to_have_features)) data.nice_to_have_features = ctx.nice_to_have_features as string[];
    if (Array.isArray(ctx.out_of_scope)) data.out_of_scope = ctx.out_of_scope as string[];
    if (Array.isArray(ctx.similar_products)) data.similar_products = ctx.similar_products as string[];
    if (typeof ctx.notes === "string") data.notes = ctx.notes;
    return data;
  }, [fromId, sourceRoadmap]);

  const sourceName = sourceRoadmap?.name;

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <PageHeader
          title="Discovery Wizard"
          description="Answer a few questions to generate the best roadmap for your project."
        />

        {fromId && sourceName && (
          <div className="mt-4 rounded-md border bg-muted/50 px-4 py-3 text-sm text-muted-foreground">
            Pre-filled from: <span className="font-medium text-foreground">{sourceName}</span>
          </div>
        )}

        <div className="mt-8">
          {fromId && sourceLoading ? (
            <p className="text-sm text-muted-foreground">Loading previous roadmap context...</p>
          ) : (
            <DiscoveryWizard
              projectId={id}
              initialData={initialData}
              existingRoadmaps={project?.roadmaps}
            />
          )}
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
