"use client";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { TagInput } from "./tag-input";
import type { WizardFormData } from "@/types/wizard";

interface StepBasicInfoProps {
  data: WizardFormData;
  errors: Record<string, string>;
  onUpdate: <K extends keyof WizardFormData>(field: K, value: WizardFormData[K]) => void;
}

export function StepBasicInfo({ data, errors, onUpdate }: StepBasicInfoProps) {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="project_name">Project Name</Label>
        <Input
          id="project_name"
          value={data.project_name}
          onChange={(e) => onUpdate("project_name", e.target.value)}
          placeholder="My Awesome App"
          aria-invalid={!!errors.project_name}
        />
        {errors.project_name && (
          <p className="text-sm text-destructive">{errors.project_name}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="vision">Vision</Label>
        <p className="text-sm text-muted-foreground">
          Describe your app in 2-3 sentences. What does it do?
        </p>
        <Textarea
          id="vision"
          value={data.vision}
          onChange={(e) => onUpdate("vision", e.target.value)}
          placeholder="A platform that..."
          rows={3}
          aria-invalid={!!errors.vision}
        />
        {errors.vision && (
          <p className="text-sm text-destructive">{errors.vision}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="problem_statement">Problem Statement</Label>
        <p className="text-sm text-muted-foreground">
          What problem does this solve for users?
        </p>
        <Textarea
          id="problem_statement"
          value={data.problem_statement}
          onChange={(e) => onUpdate("problem_statement", e.target.value)}
          placeholder="Currently, users struggle with..."
          rows={3}
          aria-invalid={!!errors.problem_statement}
        />
        {errors.problem_statement && (
          <p className="text-sm text-destructive">{errors.problem_statement}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="target_users">Target Users</Label>
        <p className="text-sm text-muted-foreground">
          Press Enter or comma to add each user type
        </p>
        <TagInput
          id="target_users"
          value={data.target_users}
          onChange={(tags) => onUpdate("target_users", tags)}
          placeholder="e.g. field technicians, dispatchers"
        />
        {errors.target_users && (
          <p className="text-sm text-destructive">{errors.target_users}</p>
        )}
      </div>
    </div>
  );
}
