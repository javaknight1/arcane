"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  RoadmapCreate,
  RoadmapDetail,
  GenerationJobResponse,
} from "@/types/api";

export function useGetRoadmap(id: string) {
  return useQuery<RoadmapDetail>({
    queryKey: ["roadmaps", id],
    queryFn: () => apiClient<RoadmapDetail>(`/roadmaps/${id}`),
    enabled: !!id,
  });
}

export function useCreateRoadmap(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: RoadmapCreate) =>
      apiClient<RoadmapDetail>(`/projects/${projectId}/roadmaps`, {
        method: "POST",
        body: data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
    },
  });
}

export function useStartGeneration() {
  return useMutation({
    mutationFn: (roadmapId: string) =>
      apiClient<GenerationJobResponse>(`/roadmaps/${roadmapId}/generate`, {
        method: "POST",
      }),
  });
}
