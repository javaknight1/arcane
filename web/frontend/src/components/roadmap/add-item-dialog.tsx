"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { ItemType, Priority } from "@/types/roadmap";
import { getChildType } from "@/types/roadmap";
import { useCreateItem } from "@/hooks/use-roadmap-mutations";

interface AddItemDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  roadmapId: string;
  parentId: string;
  parentType: ItemType | "root";
  onCreated?: (itemId: string) => void;
}

const TYPE_LABEL: Record<ItemType, string> = {
  milestone: "Milestone",
  epic: "Epic",
  story: "Story",
  task: "Task",
};

export function AddItemDialog({
  open,
  onOpenChange,
  roadmapId,
  parentId,
  parentType,
  onCreated,
}: AddItemDialogProps) {
  const childType: ItemType =
    parentType === "root" ? "milestone" : (getChildType(parentType) ?? "task");

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<Priority>("medium");

  const createItem = useCreateItem(roadmapId);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const data: Record<string, unknown> = {
      name: name.trim(),
      description: description.trim(),
      priority,
    };

    // Add type-specific defaults
    if (childType === "milestone" || childType === "epic") {
      data.goal = "";
    }
    if (childType === "story" || childType === "task") {
      data.acceptance_criteria = [];
    }
    if (childType === "task") {
      data.estimated_hours = 1;
      data.implementation_notes = "";
      data.claude_code_prompt = "";
    }

    createItem.mutate(
      { parentId, body: { item_type: childType, data } },
      {
        onSuccess: (res) => {
          onOpenChange(false);
          setName("");
          setDescription("");
          setPriority("medium");
          onCreated?.(res.item_id);
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Add {TYPE_LABEL[childType]}</DialogTitle>
            <DialogDescription>
              Create a new {childType} {parentType !== "root" ? `under this ${parentType}` : ""}.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="item-name">Name</Label>
              <Input
                id="item-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={`${TYPE_LABEL[childType]} name`}
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="item-desc">Description</Label>
              <Textarea
                id="item-desc"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description"
                className="min-h-[80px]"
              />
            </div>
            <div className="space-y-2">
              <Label>Priority</Label>
              <Select value={priority} onValueChange={(v) => setPriority(v as Priority)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!name.trim() || createItem.isPending}>
              {createItem.isPending ? "Creating..." : `Add ${TYPE_LABEL[childType]}`}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
