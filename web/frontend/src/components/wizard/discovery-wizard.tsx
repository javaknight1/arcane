"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useWizard } from "@/hooks/use-wizard";
import { useCreateRoadmap, useStartGeneration, useGetRoadmap } from "@/hooks/use-roadmaps";
import { STEPS } from "@/types/wizard";
import type { WizardFormData } from "@/types/wizard";
import type { RoadmapSummary } from "@/types/api";
import { WizardProgress } from "./wizard-progress";
import { StepBasicInfo } from "./step-basic-info";
import { StepConstraints } from "./step-constraints";
import { StepTechnical } from "./step-technical";
import { StepRequirements } from "./step-requirements";
import { StepReview } from "./step-review";
import { toast } from "sonner";

interface DiscoveryWizardProps {
  projectId: string;
  initialData?: Partial<WizardFormData>;
  existingRoadmaps?: RoadmapSummary[];
}

function buildMilestoneSummary(roadmapData: Record<string, unknown> | null): string {
  if (!roadmapData) return "";
  const milestones = roadmapData.milestones as Array<{ name: string; status?: string }> | undefined;
  if (!milestones || milestones.length === 0) return "";

  const parts = milestones.map(
    (m) => `${m.name} (${m.status ?? "unknown"})`
  );
  return `Previously generated milestones: ${parts.join(", ")}. Generate the NEXT phase of work, not what's already been done.`;
}

export function DiscoveryWizard({ projectId, initialData, existingRoadmaps }: DiscoveryWizardProps) {
  const router = useRouter();
  const { state, updateField, goToStep, nextStep, prevStep } = useWizard(initialData);
  const createRoadmap = useCreateRoadmap(projectId);
  const startGeneration = useStartGeneration();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [buildOnRoadmapId, setBuildOnRoadmapId] = useState<string | null>(null);

  // Fetch the "build on" roadmap data when selected
  const { data: buildOnRoadmap } = useGetRoadmap(buildOnRoadmapId ?? "");

  const step = STEPS[state.currentStep];

  const handleBuildOnChange = useCallback((roadmapId: string | null) => {
    setBuildOnRoadmapId(roadmapId);
  }, []);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      // Build context, optionally prepending milestone summary
      const context = { ...state.formData } as Record<string, unknown>;

      if (buildOnRoadmapId && buildOnRoadmap?.roadmap_data) {
        const summary = buildMilestoneSummary(buildOnRoadmap.roadmap_data);
        if (summary) {
          const existingNotes = (context.notes as string) || "";
          context.notes = existingNotes
            ? `${summary}\n\n${existingNotes}`
            : summary;
        }
      }

      const roadmap = await createRoadmap.mutateAsync({
        name: state.formData.project_name,
        context,
      });
      const job = await startGeneration.mutateAsync(roadmap.id);
      toast.success("Roadmap generation started!");
      router.push(`/roadmaps/${roadmap.id}/generating?job=${job.id}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create roadmap");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <WizardProgress currentStep={state.currentStep} onStepClick={goToStep} />

      <Card>
        <CardHeader>
          <CardTitle>{step.label}</CardTitle>
          <CardDescription>{step.description}</CardDescription>
        </CardHeader>
        <CardContent>
          {state.currentStep === 0 && (
            <StepBasicInfo data={state.formData} errors={state.errors} onUpdate={updateField} />
          )}
          {state.currentStep === 1 && (
            <StepConstraints data={state.formData} errors={state.errors} onUpdate={updateField} />
          )}
          {state.currentStep === 2 && (
            <StepTechnical data={state.formData} errors={state.errors} onUpdate={updateField} />
          )}
          {state.currentStep === 3 && (
            <StepRequirements data={state.formData} errors={state.errors} onUpdate={updateField} />
          )}
          {state.currentStep === 4 && (
            <StepReview
              data={state.formData}
              existingRoadmaps={existingRoadmaps}
              buildOnRoadmapId={buildOnRoadmapId}
              onBuildOnChange={handleBuildOnChange}
            />
          )}
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button
            variant="outline"
            onClick={prevStep}
            disabled={state.currentStep === 0}
          >
            Back
          </Button>
          {state.currentStep < 4 ? (
            <Button onClick={nextStep}>Next</Button>
          ) : (
            <Button onClick={handleSubmit} disabled={isSubmitting}>
              {isSubmitting ? "Generating..." : "Generate Roadmap"}
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
