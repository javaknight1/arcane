"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useListCredentials } from "@/hooks/use-credentials";
import {
  useExportRoadmap,
  useExportJob,
  useExportHistory,
  triggerCSVDownload,
} from "@/hooks/use-exports";
import type { CSVExportResponse, ExportJobResponse } from "@/types/api";
import { toast } from "sonner";

const SERVICE_OPTIONS = [
  { value: "csv", label: "CSV", requiresCreds: false },
  { value: "linear", label: "Linear", requiresCreds: true },
  { value: "jira", label: "Jira Cloud", requiresCreds: true },
  { value: "notion", label: "Notion", requiresCreds: true },
] as const;

const WORKSPACE_FIELDS: Record<string, { key: string; label: string; placeholder: string }> = {
  linear: { key: "team_id", label: "Team ID", placeholder: "e.g. TEAM-123" },
  jira: { key: "project_key", label: "Project Key", placeholder: "e.g. PROJ" },
  notion: { key: "parent_page_id", label: "Parent Page ID", placeholder: "Notion page ID" },
};

interface ExportDialogProps {
  roadmapId: string;
}

export function ExportDialog({ roadmapId }: ExportDialogProps) {
  const [open, setOpen] = useState(false);
  const [selectedService, setSelectedService] = useState("csv");
  const [workspaceValue, setWorkspaceValue] = useState("");
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  const { data: credentials } = useListCredentials();
  const exportMutation = useExportRoadmap(roadmapId);
  const { data: activeJob } = useExportJob(activeJobId);
  const { data: exportHistory } = useExportHistory(roadmapId);

  const connectedServices = new Set(
    credentials?.map((c) => c.service) ?? []
  );

  const workspaceField = WORKSPACE_FIELDS[selectedService];
  const isExporting = exportMutation.isPending || (activeJob && activeJob.status !== "completed" && activeJob.status !== "failed");

  const handleExport = async () => {
    const workspaceParams = workspaceField && workspaceValue.trim()
      ? { [workspaceField.key]: workspaceValue.trim() }
      : undefined;

    try {
      const result = await exportMutation.mutateAsync({
        service: selectedService,
        workspace_params: workspaceParams,
      });

      if (selectedService === "csv") {
        const csvResult = result as CSVExportResponse;
        triggerCSVDownload(csvResult.csv_content, csvResult.filename);
        toast.success("CSV downloaded");
        setOpen(false);
      } else {
        const jobResult = result as ExportJobResponse;
        setActiveJobId(jobResult.id);
        toast.success(`Export to ${selectedService} started`);
      }
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Export failed"
      );
    }
  };

  const handleClose = (isOpen: boolean) => {
    if (!isOpen) {
      setActiveJobId(null);
      setWorkspaceValue("");
    }
    setOpen(isOpen);
  };

  const jobStatusColor: Record<string, "default" | "secondary" | "destructive"> = {
    pending: "secondary",
    in_progress: "default",
    completed: "default",
    failed: "destructive",
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          Export
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Export Roadmap</DialogTitle>
          <DialogDescription>
            Export to CSV or send directly to a PM tool.
          </DialogDescription>
        </DialogHeader>

        {/* Active job progress */}
        {activeJob && activeJob.status !== "completed" && activeJob.status !== "failed" && (
          <div className="space-y-2 py-2">
            <div className="flex items-center justify-between text-sm">
              <span>Exporting to {activeJob.service}...</span>
              <Badge variant={jobStatusColor[activeJob.status]}>
                {activeJob.status.replace("_", " ")}
              </Badge>
            </div>
            <Progress value={50} className="h-2" />
            {activeJob.progress && (
              <p className="text-xs text-muted-foreground">
                {(activeJob.progress as { current_item?: string }).current_item || "Processing..."}
              </p>
            )}
          </div>
        )}

        {/* Completed job result */}
        {activeJob?.status === "completed" && (
          <div className="rounded-md border border-green-200 bg-green-50 p-3 dark:border-green-900 dark:bg-green-950">
            <p className="text-sm font-medium text-green-800 dark:text-green-200">
              Export completed
            </p>
            {activeJob.result && (
              <p className="text-xs text-green-700 dark:text-green-300 mt-1">
                {(activeJob.result as { items_created?: number }).items_created || 0} items exported
                {(activeJob.result as { url?: string }).url && (
                  <> &mdash; <a href={(activeJob.result as { url: string }).url} target="_blank" rel="noopener noreferrer" className="underline">View in {activeJob.service}</a></>
                )}
              </p>
            )}
          </div>
        )}

        {/* Failed job */}
        {activeJob?.status === "failed" && (
          <div className="rounded-md border border-red-200 bg-red-50 p-3 dark:border-red-900 dark:bg-red-950">
            <p className="text-sm font-medium text-red-800 dark:text-red-200">Export failed</p>
            <p className="text-xs text-red-700 dark:text-red-300 mt-1">
              {activeJob.error || "Unknown error"}
            </p>
          </div>
        )}

        {/* Service selection */}
        {!activeJob && (
          <div className="space-y-4 py-2">
            <div>
              <Label>Export target</Label>
              <div className="mt-2 grid grid-cols-2 gap-2">
                {SERVICE_OPTIONS.map((svc) => {
                  const disabled =
                    svc.requiresCreds && !connectedServices.has(svc.value);
                  return (
                    <button
                      key={svc.value}
                      type="button"
                      disabled={disabled}
                      onClick={() => {
                        setSelectedService(svc.value);
                        setWorkspaceValue("");
                      }}
                      className={`
                        rounded-md border p-3 text-left text-sm transition-colors
                        ${selectedService === svc.value
                          ? "border-primary bg-primary/5"
                          : "border-input hover:bg-accent"
                        }
                        ${disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer"}
                      `}
                    >
                      <span className="font-medium">{svc.label}</span>
                      {disabled && (
                        <span className="block text-xs text-muted-foreground mt-0.5">
                          <Link href="/settings" className="underline">Connect in Settings</Link>
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Workspace params */}
            {workspaceField && selectedService !== "csv" && (
              <div>
                <Label htmlFor="workspace-param">{workspaceField.label}</Label>
                <Input
                  id="workspace-param"
                  value={workspaceValue}
                  onChange={(e) => setWorkspaceValue(e.target.value)}
                  placeholder={workspaceField.placeholder}
                  className="mt-1"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Optional. Leave blank to use the default.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Export history */}
        {exportHistory && exportHistory.length > 0 && !activeJob && (
          <div className="border-t pt-3">
            <p className="text-xs font-medium text-muted-foreground mb-2">Recent exports</p>
            <div className="space-y-1 max-h-24 overflow-y-auto">
              {exportHistory.slice(0, 5).map((job) => (
                <div key={job.id} className="flex items-center justify-between text-xs">
                  <span>{job.service}</span>
                  <div className="flex items-center gap-2">
                    <Badge variant={jobStatusColor[job.status]} className="text-xs">
                      {job.status}
                    </Badge>
                    <span className="text-muted-foreground">
                      {job.completed_at
                        ? new Date(job.completed_at).toLocaleDateString()
                        : ""}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => handleClose(false)}
          >
            {activeJob ? "Close" : "Cancel"}
          </Button>
          {!activeJob && (
            <Button
              onClick={handleExport}
              disabled={
                isExporting ||
                (SERVICE_OPTIONS.find((s) => s.value === selectedService)?.requiresCreds &&
                  !connectedServices.has(selectedService))
              }
            >
              {exportMutation.isPending ? "Exporting..." : `Export to ${SERVICE_OPTIONS.find((s) => s.value === selectedService)?.label}`}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
