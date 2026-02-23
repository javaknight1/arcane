"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import type { WizardFormData } from "@/types/wizard";

interface StepConstraintsProps {
  data: WizardFormData;
  errors: Record<string, string>;
  onUpdate: <K extends keyof WizardFormData>(field: K, value: WizardFormData[K]) => void;
}

const TIMELINE_OPTIONS = [
  "1 month MVP",
  "3 months",
  "6 months",
  "1 year",
];

const EXPERIENCE_OPTIONS = [
  "junior",
  "mid-level",
  "senior",
  "mixed",
];

const BUDGET_OPTIONS = [
  "minimal (free tier everything)",
  "moderate",
  "flexible",
];

export function StepConstraints({ data, errors, onUpdate }: StepConstraintsProps) {
  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <Label>Timeline</Label>
        <RadioGroup
          value={data.timeline}
          onValueChange={(val) => onUpdate("timeline", val)}
        >
          {TIMELINE_OPTIONS.map((option) => (
            <div key={option} className="flex items-center space-x-2">
              <RadioGroupItem value={option} id={`timeline-${option}`} />
              <Label htmlFor={`timeline-${option}`} className="font-normal">
                {option}
              </Label>
            </div>
          ))}
        </RadioGroup>
        {errors.timeline && (
          <p className="text-sm text-destructive">{errors.timeline}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="team_size">Team Size</Label>
        <p className="text-sm text-muted-foreground">
          How many developers will work on this?
        </p>
        <Input
          id="team_size"
          type="number"
          min={1}
          max={100}
          value={data.team_size}
          onChange={(e) => onUpdate("team_size", parseInt(e.target.value) || 1)}
          className="w-24"
          aria-invalid={!!errors.team_size}
        />
        {errors.team_size && (
          <p className="text-sm text-destructive">{errors.team_size}</p>
        )}
      </div>

      <div className="space-y-3">
        <Label>Developer Experience</Label>
        <RadioGroup
          value={data.developer_experience}
          onValueChange={(val) => onUpdate("developer_experience", val)}
        >
          {EXPERIENCE_OPTIONS.map((option) => (
            <div key={option} className="flex items-center space-x-2">
              <RadioGroupItem value={option} id={`exp-${option}`} />
              <Label htmlFor={`exp-${option}`} className="font-normal capitalize">
                {option}
              </Label>
            </div>
          ))}
        </RadioGroup>
        {errors.developer_experience && (
          <p className="text-sm text-destructive">{errors.developer_experience}</p>
        )}
      </div>

      <div className="space-y-3">
        <Label>Budget</Label>
        <RadioGroup
          value={data.budget_constraints}
          onValueChange={(val) => onUpdate("budget_constraints", val)}
        >
          {BUDGET_OPTIONS.map((option) => (
            <div key={option} className="flex items-center space-x-2">
              <RadioGroupItem value={option} id={`budget-${option}`} />
              <Label htmlFor={`budget-${option}`} className="font-normal capitalize">
                {option}
              </Label>
            </div>
          ))}
        </RadioGroup>
        {errors.budget_constraints && (
          <p className="text-sm text-destructive">{errors.budget_constraints}</p>
        )}
      </div>
    </div>
  );
}
