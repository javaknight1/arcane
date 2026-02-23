"use client";

import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { TagInput } from "./tag-input";
import type { WizardFormData } from "@/types/wizard";

interface StepRequirementsProps {
  data: WizardFormData;
  errors: Record<string, string>;
  onUpdate: <K extends keyof WizardFormData>(field: K, value: WizardFormData[K]) => void;
}

export function StepRequirements({ data, errors, onUpdate }: StepRequirementsProps) {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="must_have_features">Must-Have Features</Label>
        <p className="text-sm text-muted-foreground">
          Features absolutely required for launch. Press Enter or comma to add.
        </p>
        <TagInput
          id="must_have_features"
          value={data.must_have_features}
          onChange={(tags) => onUpdate("must_have_features", tags)}
          placeholder="e.g. user auth, job scheduling"
        />
        {errors.must_have_features && (
          <p className="text-sm text-destructive">{errors.must_have_features}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="nice_to_have_features">Nice-to-Have Features</Label>
        <p className="text-sm text-muted-foreground">
          Features that would be nice but aren&apos;t critical (optional)
        </p>
        <TagInput
          id="nice_to_have_features"
          value={data.nice_to_have_features}
          onChange={(tags) => onUpdate("nice_to_have_features", tags)}
          placeholder="e.g. analytics dashboard, dark mode"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="out_of_scope">Out of Scope</Label>
        <p className="text-sm text-muted-foreground">
          Anything explicitly out of scope (optional)
        </p>
        <TagInput
          id="out_of_scope"
          value={data.out_of_scope}
          onChange={(tags) => onUpdate("out_of_scope", tags)}
          placeholder="e.g. mobile app, internationalization"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="similar_products">Similar Products</Label>
        <p className="text-sm text-muted-foreground">
          Any similar products or competitors to reference (optional)
        </p>
        <TagInput
          id="similar_products"
          value={data.similar_products}
          onChange={(tags) => onUpdate("similar_products", tags)}
          placeholder="e.g. Trello, Asana"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="notes">Additional Notes</Label>
        <p className="text-sm text-muted-foreground">
          Any additional context (optional)
        </p>
        <Textarea
          id="notes"
          value={data.notes}
          onChange={(e) => onUpdate("notes", e.target.value)}
          placeholder="Anything else the AI should know..."
          rows={3}
        />
      </div>
    </div>
  );
}
