"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { apiClient } from "@/lib/api-client";
import type {
  ItemUpdate,
  ItemCreateRequest,
  ReorderRequest,
  ItemResponse,
  DeleteResponse,
  GenerationJobResponse,
  AiEditResponse,
} from "@/types/api";

export function useUpdateItem(roadmapId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, updates }: { itemId: string; updates: ItemUpdate }) =>
      apiClient<ItemResponse>(`/roadmaps/${roadmapId}/items/${itemId}`, {
        method: "PATCH",
        body: updates,
      }),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["roadmaps", roadmapId] });
      if (variables.updates.status !== undefined) {
        queryClient.invalidateQueries({ queryKey: ["roadmaps", roadmapId, "stats"] });
      }
    },
    onError: (error: Error) => {
      toast.error("Failed to update item", { description: error.message });
    },
  });
}

export function useDeleteItem(roadmapId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) =>
      apiClient<DeleteResponse>(`/roadmaps/${roadmapId}/items/${itemId}`, {
        method: "DELETE",
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["roadmaps", roadmapId] });
      const childMsg =
        data.children_deleted > 0
          ? ` and ${data.children_deleted} child item${data.children_deleted === 1 ? "" : "s"}`
          : "";
      toast.success(`Deleted ${data.deleted_type}${childMsg}`);
    },
    onError: (error: Error) => {
      toast.error("Failed to delete item", { description: error.message });
    },
  });
}

export function useCreateItem(roadmapId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ parentId, body }: { parentId: string; body: ItemCreateRequest }) =>
      apiClient<ItemResponse>(`/roadmaps/${roadmapId}/items/${parentId}/children`, {
        method: "POST",
        body,
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["roadmaps", roadmapId] });
      toast.success(`Created ${data.item_type}: ${(data.data as { name?: string }).name ?? ""}`);
    },
    onError: (error: Error) => {
      toast.error("Failed to create item", { description: error.message });
    },
  });
}

export function useReorderItems(roadmapId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ReorderRequest) =>
      apiClient<{ status: string }>(`/roadmaps/${roadmapId}/items/reorder`, {
        method: "PUT",
        body,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roadmaps", roadmapId] });
    },
    onError: (error: Error) => {
      toast.error("Failed to reorder items", { description: error.message });
    },
  });
}

export function useRegenerateItem(roadmapId: string) {
  return useMutation({
    mutationFn: (itemId: string) =>
      apiClient<GenerationJobResponse>(
        `/roadmaps/${roadmapId}/items/${itemId}/regenerate`,
        { method: "POST" }
      ),
  });
}

export function useAiEditItem(roadmapId: string) {
  return useMutation({
    mutationFn: ({ itemId, command }: { itemId: string; command: string }) =>
      apiClient<AiEditResponse>(
        `/roadmaps/${roadmapId}/items/${itemId}/ai-edit`,
        { method: "POST", body: { command } }
      ),
  });
}
