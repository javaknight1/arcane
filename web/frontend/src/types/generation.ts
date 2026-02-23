export interface ProgressData {
  milestones: number;
  epics: number;
  stories: number;
  tasks: number;
  stories_completed: number;
  stories_total: number;
  phase: "milestones" | "epics" | "stories" | "tasks" | "complete";
}

export interface ItemCreatedData {
  type: "milestone" | "epic" | "story" | "task";
  name: string;
  parent: string | null;
}

export interface CompleteData {
  roadmap_id: string;
  total_items: {
    milestones: number;
    epics: number;
    stories: number;
    tasks: number;
  };
}

export interface ErrorData {
  message: string;
}

export type GenerationEvent =
  | { event: "progress"; data: ProgressData }
  | { event: "item_created"; data: ItemCreatedData }
  | { event: "complete"; data: CompleteData }
  | { event: "error"; data: ErrorData };
