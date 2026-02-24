"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  CredentialCreate,
  CredentialResponse,
  CredentialValidateResponse,
} from "@/types/api";
import { toast } from "sonner";

export function useListCredentials() {
  return useQuery<CredentialResponse[]>({
    queryKey: ["credentials"],
    queryFn: () => apiClient<CredentialResponse[]>("/credentials"),
  });
}

export function useSaveCredential() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CredentialCreate) =>
      apiClient<CredentialResponse>("/credentials", {
        method: "POST",
        body: data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["credentials"] });
    },
    onError: (error: Error) => {
      toast.error("Failed to save credentials", { description: error.message });
    },
  });
}

export function useDeleteCredential() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (service: string) =>
      apiClient<void>(`/credentials/${service}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["credentials"] });
    },
    onError: (error: Error) => {
      toast.error("Failed to disconnect", { description: error.message });
    },
  });
}

export function useValidateCredential() {
  return useMutation({
    mutationFn: (service: string) =>
      apiClient<CredentialValidateResponse>(
        `/credentials/${service}/validate`,
        { method: "POST" }
      ),
  });
}
