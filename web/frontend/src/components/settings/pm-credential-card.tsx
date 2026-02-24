"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  useSaveCredential,
  useDeleteCredential,
  useValidateCredential,
} from "@/hooks/use-credentials";
import { toast } from "sonner";

interface FieldConfig {
  key: string;
  label: string;
  type?: "text" | "password";
  placeholder?: string;
}

interface PMCredentialCardProps {
  service: string;
  title: string;
  description: string;
  fields: FieldConfig[];
  isConnected: boolean;
}

export function PMCredentialCard({
  service,
  title,
  description,
  fields,
  isConnected,
}: PMCredentialCardProps) {
  const [values, setValues] = useState<Record<string, string>>(
    Object.fromEntries(fields.map((f) => [f.key, ""]))
  );
  const [showForm, setShowForm] = useState(false);

  const saveCredential = useSaveCredential();
  const deleteCredential = useDeleteCredential();
  const validateCredential = useValidateCredential();

  const handleConnect = async () => {
    const hasEmpty = fields.some((f) => !values[f.key]?.trim());
    if (hasEmpty) {
      toast.error("Please fill in all fields");
      return;
    }

    try {
      await saveCredential.mutateAsync({
        service,
        credentials: values,
      });
      toast.success(`${title} connected`);
      setShowForm(false);
      setValues(Object.fromEntries(fields.map((f) => [f.key, ""])));
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to save credentials"
      );
    }
  };

  const handleDisconnect = async () => {
    try {
      await deleteCredential.mutateAsync(service);
      toast.success(`${title} disconnected`);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to disconnect"
      );
    }
  };

  const handleTest = async () => {
    try {
      const result = await validateCredential.mutateAsync(service);
      if (result.valid) {
        toast.success(result.message);
      } else {
        toast.error(result.message);
      }
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to test connection"
      );
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          <Badge variant={isConnected ? "default" : "secondary"}>
            {isConnected ? "Connected" : "Not Connected"}
          </Badge>
        </div>
      </CardHeader>

      {isConnected && !showForm ? (
        <CardFooter className="gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTest}
            disabled={validateCredential.isPending}
          >
            {validateCredential.isPending ? "Testing..." : "Test Connection"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowForm(true)}
          >
            Update
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleDisconnect}
            disabled={deleteCredential.isPending}
          >
            {deleteCredential.isPending ? "Disconnecting..." : "Disconnect"}
          </Button>
        </CardFooter>
      ) : !isConnected && !showForm ? (
        <CardFooter>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowForm(true)}
          >
            Connect
          </Button>
        </CardFooter>
      ) : (
        <CardContent className="space-y-3">
          {fields.map((field) => (
            <div key={field.key}>
              <Label htmlFor={`${service}-${field.key}`}>{field.label}</Label>
              <Input
                id={`${service}-${field.key}`}
                type={field.type || "text"}
                value={values[field.key] || ""}
                onChange={(e) =>
                  setValues((v) => ({ ...v, [field.key]: e.target.value }))
                }
                placeholder={field.placeholder}
                className="mt-1"
              />
            </div>
          ))}
          <div className="flex gap-2 pt-2">
            <Button
              size="sm"
              onClick={handleConnect}
              disabled={saveCredential.isPending}
            >
              {saveCredential.isPending ? "Saving..." : "Save"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setShowForm(false);
                setValues(Object.fromEntries(fields.map((f) => [f.key, ""])));
              }}
            >
              Cancel
            </Button>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
