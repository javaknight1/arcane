export interface WizardFormData {
  project_name: string;
  vision: string;
  problem_statement: string;
  target_users: string[];
  timeline: string;
  team_size: number;
  developer_experience: string;
  budget_constraints: string;
  tech_stack: string[];
  infrastructure_preferences: string;
  existing_codebase: boolean;
  must_have_features: string[];
  nice_to_have_features: string[];
  out_of_scope: string[];
  similar_products: string[];
  notes: string;
}

export const INITIAL_FORM_DATA: WizardFormData = {
  project_name: "",
  vision: "",
  problem_statement: "",
  target_users: [],
  timeline: "",
  team_size: 1,
  developer_experience: "",
  budget_constraints: "",
  tech_stack: [],
  infrastructure_preferences: "",
  existing_codebase: false,
  must_have_features: [],
  nice_to_have_features: [],
  out_of_scope: [],
  similar_products: [],
  notes: "",
};

export const STEPS = [
  { label: "Basic Info", description: "Project name, vision, and target users" },
  { label: "Constraints", description: "Timeline, team, and budget" },
  { label: "Technical", description: "Tech stack and infrastructure" },
  { label: "Requirements", description: "Features and scope" },
  { label: "Review", description: "Review and generate" },
] as const;

export type StepIndex = 0 | 1 | 2 | 3 | 4;

export interface WizardState {
  currentStep: StepIndex;
  formData: WizardFormData;
  errors: Record<string, string>;
}

export type WizardAction =
  | { type: "SET_STEP"; step: StepIndex }
  | { type: "UPDATE_FIELD"; field: keyof WizardFormData; value: WizardFormData[keyof WizardFormData] }
  | { type: "SET_ERRORS"; errors: Record<string, string> }
  | { type: "CLEAR_ERRORS" }
  | { type: "INIT"; data: Partial<WizardFormData> };
