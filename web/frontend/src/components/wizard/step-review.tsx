import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { WizardFormData } from "@/types/wizard";
import type { RoadmapSummary } from "@/types/api";

interface StepReviewProps {
  data: WizardFormData;
  existingRoadmaps?: RoadmapSummary[];
  buildOnRoadmapId?: string | null;
  onBuildOnChange?: (roadmapId: string | null) => void;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">
        {title}
      </h3>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-sm text-muted-foreground shrink-0">{label}</span>
      <span className="text-sm text-right">{value}</span>
    </div>
  );
}

function TagList({ tags }: { tags: string[] }) {
  if (tags.length === 0) return <span className="text-sm text-muted-foreground italic">None</span>;
  return (
    <div className="flex flex-wrap justify-end gap-1">
      {tags.map((tag, i) => (
        <Badge key={i} variant="secondary">
          {tag}
        </Badge>
      ))}
    </div>
  );
}

export function StepReview({ data, existingRoadmaps, buildOnRoadmapId, onBuildOnChange }: StepReviewProps) {
  const completedRoadmaps = existingRoadmaps?.filter((r) => r.status === "completed") ?? [];
  const showBuildOn = completedRoadmaps.length > 0 && onBuildOnChange;

  return (
    <div className="space-y-6">
      {showBuildOn && (
        <>
          <div className="rounded-md border p-4 space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="build-on-toggle" className="text-sm font-medium">
                Build on previous roadmap
              </Label>
              <Switch
                id="build-on-toggle"
                checked={!!buildOnRoadmapId}
                onCheckedChange={(checked) => {
                  if (checked) {
                    onBuildOnChange(completedRoadmaps[0].id);
                  } else {
                    onBuildOnChange(null);
                  }
                }}
              />
            </div>
            {buildOnRoadmapId && (
              <div className="space-y-2">
                <Select
                  value={buildOnRoadmapId}
                  onValueChange={(val) => onBuildOnChange(val)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a roadmap" />
                  </SelectTrigger>
                  <SelectContent>
                    {completedRoadmaps.map((r) => (
                      <SelectItem key={r.id} value={r.id}>
                        {r.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Milestone summaries from the selected roadmap will be included so the AI avoids duplicating previous work.
                </p>
              </div>
            )}
          </div>
          <Separator />
        </>
      )}

      <Section title="Basic Information">
        <Field label="Project Name" value={data.project_name} />
        <Field label="Vision" value={data.vision} />
        <Field label="Problem" value={data.problem_statement} />
        <Field label="Target Users" value={<TagList tags={data.target_users} />} />
      </Section>

      <Separator />

      <Section title="Constraints">
        <Field label="Timeline" value={data.timeline} />
        <Field label="Team Size" value={`${data.team_size} developer(s)`} />
        <Field label="Experience" value={data.developer_experience} />
        <Field label="Budget" value={data.budget_constraints} />
      </Section>

      <Separator />

      <Section title="Technical">
        <Field label="Tech Stack" value={<TagList tags={data.tech_stack} />} />
        <Field label="Infrastructure" value={data.infrastructure_preferences || "No preference"} />
        <Field label="Existing Codebase" value={data.existing_codebase ? "Yes" : "No"} />
      </Section>

      <Separator />

      <Section title="Requirements">
        <Field label="Must-Have" value={<TagList tags={data.must_have_features} />} />
        <Field label="Nice-to-Have" value={<TagList tags={data.nice_to_have_features} />} />
        <Field label="Out of Scope" value={<TagList tags={data.out_of_scope} />} />
        <Field label="Similar Products" value={<TagList tags={data.similar_products} />} />
        {data.notes && <Field label="Notes" value={data.notes} />}
      </Section>
    </div>
  );
}
