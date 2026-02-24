// Typed interfaces matching backend roadmap_data JSON

export type Priority = "critical" | "high" | "medium" | "low";
export type ItemStatus = "not_started" | "in_progress" | "blocked" | "completed";
export type ItemType = "milestone" | "epic" | "story" | "task";

interface BaseItem {
  id: string;
  name: string;
  description: string;
  priority: Priority;
  status: ItemStatus;
  labels: string[];
}

export interface RoadmapTask extends BaseItem {
  estimated_hours: number;
  prerequisites: string[];
  acceptance_criteria: string[];
  implementation_notes: string;
  claude_code_prompt: string;
}

export interface RoadmapStory extends BaseItem {
  acceptance_criteria: string[];
  tasks: RoadmapTask[];
}

export interface RoadmapEpic extends BaseItem {
  goal: string;
  prerequisites: string[];
  stories: RoadmapStory[];
}

export interface RoadmapMilestone extends BaseItem {
  goal: string;
  target_date: string | null;
  epics: RoadmapEpic[];
}

export interface RoadmapData {
  milestones: RoadmapMilestone[];
}

export type RoadmapItem = RoadmapMilestone | RoadmapEpic | RoadmapStory | RoadmapTask;

// Utility functions

export function getEstimatedHours(item: RoadmapItem, type: ItemType): number {
  switch (type) {
    case "task":
      return (item as RoadmapTask).estimated_hours;
    case "story":
      return (item as RoadmapStory).tasks.reduce((sum, t) => sum + t.estimated_hours, 0);
    case "epic":
      return (item as RoadmapEpic).stories.reduce(
        (sum, s) => sum + getEstimatedHours(s, "story"), 0
      );
    case "milestone":
      return (item as RoadmapMilestone).epics.reduce(
        (sum, e) => sum + getEstimatedHours(e, "epic"), 0
      );
  }
}

export function getChildren(item: RoadmapItem, type: ItemType): RoadmapItem[] {
  switch (type) {
    case "milestone":
      return (item as RoadmapMilestone).epics;
    case "epic":
      return (item as RoadmapEpic).stories;
    case "story":
      return (item as RoadmapStory).tasks;
    case "task":
      return [];
  }
}

export function getChildType(type: ItemType): ItemType | null {
  switch (type) {
    case "milestone": return "epic";
    case "epic": return "story";
    case "story": return "task";
    case "task": return null;
  }
}

export function inferItemType(item: RoadmapItem): ItemType {
  if ("epics" in item) return "milestone";
  if ("stories" in item) return "epic";
  if ("tasks" in item) return "story";
  return "task";
}

export function getCompletedHours(item: RoadmapItem, type: ItemType): number {
  switch (type) {
    case "task": {
      const t = item as RoadmapTask;
      return t.status === "completed" ? t.estimated_hours : 0;
    }
    case "story":
      return (item as RoadmapStory).tasks.reduce((sum, t) => sum + getCompletedHours(t, "task"), 0);
    case "epic":
      return (item as RoadmapEpic).stories.reduce(
        (sum, s) => sum + getCompletedHours(s, "story"), 0
      );
    case "milestone":
      return (item as RoadmapMilestone).epics.reduce(
        (sum, e) => sum + getCompletedHours(e, "epic"), 0
      );
  }
}
