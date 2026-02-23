"use client";

import { useState, useCallback } from "react";
import { toast } from "sonner";
import type { RoadmapData, RoadmapItem, RoadmapMilestone, RoadmapEpic, RoadmapStory, ItemType } from "@/types/roadmap";
import { getChildren, getChildType, inferItemType } from "@/types/roadmap";
import type { ItemUpdate } from "@/types/api";
import {
  useUpdateItem,
  useDeleteItem,
  useReorderItems,
} from "@/hooks/use-roadmap-mutations";
import { RoadmapTree } from "./roadmap-tree";
import { ItemDetail } from "./item-detail";
import { AddItemDialog } from "./add-item-dialog";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface RoadmapViewerProps {
  data: RoadmapData;
  roadmapId?: string;
}

/** Find an item by id and return its parent info for reordering. */
function findItemContext(
  data: RoadmapData,
  targetId: string
): { parentId: string; siblingIds: string[] } | null {
  // Check milestones (parent = root)
  const msIds = data.milestones.map((m) => m.id);
  if (msIds.includes(targetId)) {
    return { parentId: "root", siblingIds: msIds };
  }

  for (const ms of data.milestones) {
    const epicIds = ms.epics.map((e) => e.id);
    if (epicIds.includes(targetId)) {
      return { parentId: ms.id, siblingIds: epicIds };
    }
    for (const ep of ms.epics) {
      const storyIds = ep.stories.map((s) => s.id);
      if (storyIds.includes(targetId)) {
        return { parentId: ep.id, siblingIds: storyIds };
      }
      for (const st of ep.stories) {
        const taskIds = st.tasks.map((t) => t.id);
        if (taskIds.includes(targetId)) {
          return { parentId: st.id, siblingIds: taskIds };
        }
      }
    }
  }
  return null;
}

/** Find an item by id in the roadmap data. */
function findItem(
  data: RoadmapData,
  targetId: string
): { item: RoadmapItem; type: ItemType } | null {
  for (const ms of data.milestones) {
    if (ms.id === targetId) return { item: ms, type: "milestone" };
    for (const ep of ms.epics) {
      if (ep.id === targetId) return { item: ep, type: "epic" };
      for (const st of ep.stories) {
        if (st.id === targetId) return { item: st, type: "story" };
        for (const t of st.tasks) {
          if (t.id === targetId) return { item: t, type: "task" };
        }
      }
    }
  }
  return null;
}

export function RoadmapViewer({ data, roadmapId }: RoadmapViewerProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<RoadmapItem | null>(null);
  const [selectedType, setSelectedType] = useState<ItemType | null>(null);

  // Add item dialog state
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [addParentId, setAddParentId] = useState("root");
  const [addParentType, setAddParentType] = useState<ItemType | "root">("root");

  // Delete confirmation from tree
  const [treeDeleteOpen, setTreeDeleteOpen] = useState(false);
  const [treeDeleteTarget, setTreeDeleteTarget] = useState<{
    id: string;
    type: ItemType;
    name: string;
  } | null>(null);

  const editable = !!roadmapId;
  const updateItem = useUpdateItem(roadmapId ?? "");
  const deleteItem = useDeleteItem(roadmapId ?? "");
  const reorderItems = useReorderItems(roadmapId ?? "");

  const handleSelect = useCallback(
    (item: RoadmapItem, type: ItemType) => {
      setSelectedId(item.id);
      setSelectedItem(item);
      setSelectedType(type);
    },
    []
  );

  // Re-sync selectedItem when data changes (after mutation + refetch)
  // We do this by looking up the selected id in the new data
  const resolvedItem = selectedId ? findItem(data, selectedId) : null;
  const currentItem = resolvedItem?.item ?? selectedItem;
  const currentType = resolvedItem?.type ?? selectedType;

  // If the selected item was deleted (not found in data), clear selection
  if (selectedId && !resolvedItem) {
    // Can't setState during render, so we use the stale values
    // and clear on next interaction. But we can show the empty state.
  }

  const itemContext = selectedId ? findItemContext(data, selectedId) : null;

  const handleItemUpdated = useCallback(
    (itemId: string, updates: ItemUpdate) => {
      if (!roadmapId) return;
      updateItem.mutate({ itemId, updates });
    },
    [roadmapId, updateItem]
  );

  const handleItemDeleted = useCallback(
    (itemId: string) => {
      if (!roadmapId) return;
      deleteItem.mutate(itemId, {
        onSuccess: () => {
          if (selectedId === itemId) {
            setSelectedId(null);
            setSelectedItem(null);
            setSelectedType(null);
          }
        },
      });
    },
    [roadmapId, deleteItem, selectedId]
  );

  const handleReorder = useCallback(
    (parentId: string, itemIds: string[]) => {
      if (!roadmapId) return;
      reorderItems.mutate({ parent_id: parentId, item_ids: itemIds });
    },
    [roadmapId, reorderItems]
  );

  const handleAddItem = useCallback(
    (parentId: string, parentType: ItemType | "root") => {
      setAddParentId(parentId);
      setAddParentType(parentType);
      setAddDialogOpen(true);
    },
    []
  );

  const handleTreeDelete = useCallback(
    (itemId: string, itemType: ItemType, itemName: string) => {
      setTreeDeleteTarget({ id: itemId, type: itemType, name: itemName });
      setTreeDeleteOpen(true);
    },
    []
  );

  const handleItemCreated = useCallback(
    (itemId: string) => {
      // After refetch, try to select the new item
      // We'll find it in data after the query invalidation
      setSelectedId(itemId);
    },
    []
  );

  return (
    <div className="flex flex-col lg:flex-row gap-4 h-[calc(100vh-12rem)]">
      {/* Left panel: tree */}
      <div className="lg:w-1/3 min-w-[300px] rounded-lg border overflow-hidden">
        <RoadmapTree
          data={data}
          selectedId={selectedId}
          onSelect={handleSelect}
          onAddItem={editable ? handleAddItem : undefined}
          onDeleteItem={editable ? handleTreeDelete : undefined}
        />
      </div>

      {/* Right panel: detail */}
      <div className="flex-1 rounded-lg border overflow-hidden">
        <ItemDetail
          item={currentItem ?? null}
          type={currentType ?? null}
          roadmapId={roadmapId}
          onItemUpdated={editable ? handleItemUpdated : undefined}
          onItemDeleted={editable ? handleItemDeleted : undefined}
          onReorder={editable ? handleReorder : undefined}
          parentId={itemContext?.parentId}
          siblingIds={itemContext?.siblingIds}
        />
      </div>

      {/* Add item dialog */}
      {editable && (
        <AddItemDialog
          open={addDialogOpen}
          onOpenChange={setAddDialogOpen}
          roadmapId={roadmapId!}
          parentId={addParentId}
          parentType={addParentType}
          onCreated={handleItemCreated}
        />
      )}

      {/* Tree delete confirmation */}
      {editable && treeDeleteTarget && (
        <Dialog open={treeDeleteOpen} onOpenChange={setTreeDeleteOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete {treeDeleteTarget.type}?</DialogTitle>
              <DialogDescription>
                This will permanently delete &quot;{treeDeleteTarget.name}&quot; and all its
                descendants. This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setTreeDeleteOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={() => {
                  setTreeDeleteOpen(false);
                  handleItemDeleted(treeDeleteTarget.id);
                }}
              >
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
