"use client";

import { AuthGuard } from "@/components/auth-guard";
import { Navbar } from "@/components/navbar";
import { PageHeader } from "@/components/page-header";

export default function GeneratingPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <PageHeader
            title="Generation Progress"
            description="Coming in T46"
          />
          <div className="mt-8 rounded-lg border border-dashed p-12 text-center text-muted-foreground">
            This page will show real-time generation progress via SSE streaming.
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
