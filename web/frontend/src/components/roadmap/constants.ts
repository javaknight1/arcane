import type { ItemType, ItemStatus, Priority } from "@/types/roadmap";

export const TYPE_STYLES: Record<ItemType, string> = {
  milestone: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  epic: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  story: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  task: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
};

export const STATUS_COLORS: Record<ItemStatus, string> = {
  not_started: "border-l-gray-300 dark:border-l-gray-600",
  in_progress: "border-l-blue-500",
  blocked: "border-l-red-500",
  completed: "border-l-green-500",
};

export const STATUS_BADGE: Record<ItemStatus, string> = {
  not_started: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  in_progress: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  blocked: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
  completed: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
};

export const PRIORITY_STYLES: Record<Priority, string> = {
  critical: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  high: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
  medium: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  low: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
};

export const STATUS_LABEL: Record<ItemStatus, string> = {
  not_started: "Not Started",
  in_progress: "In Progress",
  blocked: "Blocked",
  completed: "Completed",
};

export const PRIORITY_LABEL: Record<Priority, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};
