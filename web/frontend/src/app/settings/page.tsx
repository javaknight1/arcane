"use client";

import { AuthGuard } from "@/components/auth-guard";
import { Navbar } from "@/components/navbar";
import { PageHeader } from "@/components/page-header";

export default function SettingsPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <PageHeader
            title="Settings"
            description="Coming Soon"
          />
          <div className="mt-8 rounded-lg border border-dashed p-12 text-center text-muted-foreground">
            Settings for API keys, PM integrations, and preferences will go here.
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
