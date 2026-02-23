"use client";

import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Switch } from "@/components/ui/switch";
import { TagInput } from "./tag-input";
import type { WizardFormData } from "@/types/wizard";

interface StepTechnicalProps {
  data: WizardFormData;
  errors: Record<string, string>;
  onUpdate: <K extends keyof WizardFormData>(field: K, value: WizardFormData[K]) => void;
}

const INFRASTRUCTURE_OPTIONS = [
  "AWS",
  "GCP",
  "Azure",
  "Serverless",
  "Self-hosted",
  "No preference",
];

export function StepTechnical({ data, errors, onUpdate }: StepTechnicalProps) {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="tech_stack">Tech Stack</Label>
        <p className="text-sm text-muted-foreground">
          Technologies you want to use (optional). Press Enter or comma to add.
        </p>
        <TagInput
          id="tech_stack"
          value={data.tech_stack}
          onChange={(tags) => onUpdate("tech_stack", tags)}
          placeholder="e.g. React, Go, PostgreSQL"
        />
        {errors.tech_stack && (
          <p className="text-sm text-destructive">{errors.tech_stack}</p>
        )}
      </div>

      <div className="space-y-3">
        <Label>Infrastructure Preferences</Label>
        <RadioGroup
          value={data.infrastructure_preferences}
          onValueChange={(val) => onUpdate("infrastructure_preferences", val)}
        >
          {INFRASTRUCTURE_OPTIONS.map((option) => (
            <div key={option} className="flex items-center space-x-2">
              <RadioGroupItem value={option} id={`infra-${option}`} />
              <Label htmlFor={`infra-${option}`} className="font-normal">
                {option}
              </Label>
            </div>
          ))}
        </RadioGroup>
        {errors.infrastructure_preferences && (
          <p className="text-sm text-destructive">{errors.infrastructure_preferences}</p>
        )}
      </div>

      <div className="flex items-center justify-between rounded-lg border p-4">
        <div className="space-y-0.5">
          <Label htmlFor="existing_codebase">Existing Codebase</Label>
          <p className="text-sm text-muted-foreground">
            Are you adding to an existing codebase?
          </p>
        </div>
        <Switch
          id="existing_codebase"
          checked={data.existing_codebase}
          onCheckedChange={(checked) => onUpdate("existing_codebase", checked)}
        />
      </div>
    </div>
  );
}
