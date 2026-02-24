"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  ExportRequest,
  ExportJobResponse,
  CSVExportResponse,
} from "@/types/api";
import { toast } from "sonner";

export function useExportRoadmap(roadmapId: string) {
  return useMutation({
    mutationFn: (data: ExportRequest) =>
      apiClient<ExportJobResponse | CSVExportResponse>(
        `/roadmaps/${roadmapId}/export`,
        { method: "POST", body: data }
      ),
    onError: (error: Error) => {
      toast.error("Export failed", { description: error.message });
    },
  });
}

export function useExportJob(jobId: string | null) {
  return useQuery<ExportJobResponse>({
    queryKey: ["export-jobs", jobId],
    queryFn: () => apiClient<ExportJobResponse>(`/export-jobs/${jobId}`),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "pending" || status === "in_progress") return 2000;
      return false;
    },
  });
}

export function useExportHistory(roadmapId: string) {
  return useQuery<ExportJobResponse[]>({
    queryKey: ["roadmaps", roadmapId, "exports"],
    queryFn: () =>
      apiClient<ExportJobResponse[]>(`/roadmaps/${roadmapId}/exports`),
    enabled: !!roadmapId,
  });
}

export function triggerCSVDownload(csvContent: string, filename: string) {
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
