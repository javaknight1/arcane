"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useWizard } from "@/hooks/use-wizard";
import { useCreateRoadmap, useStartGeneration } from "@/hooks/use-roadmaps";
import { STEPS } from "@/types/wizard";
import { WizardProgress } from "./wizard-progress";
import { StepBasicInfo } from "./step-basic-info";
import { StepConstraints } from "./step-constraints";
import { StepTechnical } from "./step-technical";
import { StepRequirements } from "./step-requirements";
import { StepReview } from "./step-review";
import { toast } from "sonner";

interface DiscoveryWizardProps {
  projectId: string;
}

export function DiscoveryWizard({ projectId }: DiscoveryWizardProps) {
  const router = useRouter();
  const { state, updateField, goToStep, nextStep, prevStep } = useWizard();
  const createRoadmap = useCreateRoadmap(projectId);
  const startGeneration = useStartGeneration();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const step = STEPS[state.currentStep];

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const roadmap = await createRoadmap.mutateAsync({
        name: state.formData.project_name,
        context: state.formData as unknown as Record<string, unknown>,
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
            <StepReview data={state.formData} />
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
