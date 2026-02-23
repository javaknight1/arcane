import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { WizardFormData } from "@/types/wizard";

interface StepReviewProps {
  data: WizardFormData;
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

export function StepReview({ data }: StepReviewProps) {
  return (
    <div className="space-y-6">
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
