"use client";

import { AuthGuard } from "@/components/auth-guard";
import { Navbar } from "@/components/navbar";
import { PageHeader } from "@/components/page-header";
import { PMCredentialCard } from "@/components/settings/pm-credential-card";
import { Skeleton } from "@/components/ui/skeleton";
import { useListCredentials } from "@/hooks/use-credentials";

const PM_SERVICES = [
  {
    service: "linear",
    title: "Linear",
    description: "Export roadmaps to Linear projects and issues",
    fields: [
      { key: "api_key", label: "API Key", type: "password" as const, placeholder: "lin_api_..." },
    ],
  },
  {
    service: "jira",
    title: "Jira Cloud",
    description: "Export roadmaps to Jira epics, stories, and tasks",
    fields: [
      { key: "domain", label: "Domain", placeholder: "yourteam.atlassian.net" },
      { key: "email", label: "Email", placeholder: "you@company.com" },
      { key: "api_token", label: "API Token", type: "password" as const, placeholder: "Your Jira API token" },
    ],
  },
  {
    service: "notion",
    title: "Notion",
    description: "Export roadmaps to Notion databases and pages",
    fields: [
      { key: "api_key", label: "API Key", type: "password" as const, placeholder: "ntn_..." },
    ],
  },
];

function SettingsContent() {
  const { data: credentials, isLoading } = useListCredentials();

  const connectedServices = new Set(
    credentials?.map((c) => c.service) ?? []
  );

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <PageHeader
          title="Settings"
          description="Manage your PM tool integrations"
        />
        <div className="mt-8 space-y-4">
          <h2 className="text-lg font-semibold">PM Integrations</h2>
          <p className="text-sm text-muted-foreground">
            Connect your project management tools to export roadmaps directly.
          </p>
          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          ) : (
            <div className="grid gap-4">
              {PM_SERVICES.map((svc) => (
                <PMCredentialCard
                  key={svc.service}
                  service={svc.service}
                  title={svc.title}
                  description={svc.description}
                  fields={svc.fields}
                  isConnected={connectedServices.has(svc.service)}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <AuthGuard>
      <SettingsContent />
    </AuthGuard>
  );
}
