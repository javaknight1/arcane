"use client";

import { useState, useCallback, useMemo } from "react";
import { Search, ChevronsUpDown, Plus } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { RoadmapData, RoadmapItem, ItemType } from "@/types/roadmap";
import { getChildren, getChildType } from "@/types/roadmap";
import { TreeNode } from "./tree-node";

interface RoadmapTreeProps {
  data: RoadmapData;
  selectedId: string | null;
  onSelect: (item: RoadmapItem, type: ItemType) => void;
  onAddItem?: (parentId: string, parentType: ItemType | "root") => void;
  onDeleteItem?: (itemId: string, itemType: ItemType, itemName: string) => void;
}

function collectAllIds(items: RoadmapItem[], type: ItemType): string[] {
  const ids: string[] = [];
  for (const item of items) {
    const children = getChildren(item, type);
    if (children.length > 0) {
      ids.push(item.id);
      const childType = getChildType(type);
      if (childType) {
        ids.push(...collectAllIds(children, childType));
      }
    }
  }
  return ids;
}

function countItems(data: RoadmapData) {
  let epics = 0, stories = 0, tasks = 0;
  for (const m of data.milestones) {
    epics += m.epics.length;
    for (const e of m.epics) {
      stories += e.stories.length;
      for (const s of e.stories) {
        tasks += s.tasks.length;
      }
    }
  }
  return {
    milestones: data.milestones.length,
    epics,
    stories,
    tasks,
  };
}

export function RoadmapTree({ data, selectedId, onSelect, onAddItem, onDeleteItem }: RoadmapTreeProps) {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(() => {
    return new Set(data.milestones.map((m) => m.id));
  });
  const [searchQuery, setSearchQuery] = useState("");

  const allExpandableIds = useMemo(
    () => collectAllIds(data.milestones, "milestone"),
    [data.milestones]
  );

  const counts = useMemo(() => countItems(data), [data]);

  const handleToggle = useCallback((id: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const expandAll = useCallback(() => {
    setExpandedNodes(new Set(allExpandableIds));
  }, [allExpandableIds]);

  const collapseAll = useCallback(() => {
    setExpandedNodes(new Set());
  }, []);

  const handleAddChild = useCallback(
    (parentId: string, parentType: ItemType) => {
      onAddItem?.(parentId, parentType);
    },
    [onAddItem]
  );

  const handleDelete = useCallback(
    (itemId: string, itemType: ItemType, itemName: string) => {
      onDeleteItem?.(itemId, itemType, itemName);
    },
    [onDeleteItem]
  );

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="p-3 border-b space-y-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Search items..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 h-8 text-sm"
          />
        </div>
        <div className="flex items-center justify-between">
          <div className="flex gap-1.5 flex-wrap">
            <Badge variant="secondary" className="text-[10px]">{counts.milestones} milestones</Badge>
            <Badge variant="secondary" className="text-[10px]">{counts.epics} epics</Badge>
            <Badge variant="secondary" className="text-[10px]">{counts.stories} stories</Badge>
            <Badge variant="secondary" className="text-[10px]">{counts.tasks} tasks</Badge>
          </div>
          <div className="flex items-center gap-1">
            {onAddItem && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-xs"
                onClick={() => onAddItem("root", "root")}
              >
                <Plus className="h-3 w-3 mr-1" />
                Milestone
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-xs"
              onClick={expandedNodes.size === allExpandableIds.length ? collapseAll : expandAll}
            >
              <ChevronsUpDown className="h-3 w-3 mr-1" />
              {expandedNodes.size === allExpandableIds.length ? "Collapse" : "Expand"}
            </Button>
          </div>
        </div>
      </div>

      {/* Tree */}
      <div className="overflow-y-auto flex-1 p-1.5 space-y-0.5">
        {data.milestones.map((milestone) => (
          <TreeNode
            key={milestone.id}
            item={milestone}
            type="milestone"
            depth={0}
            expandedNodes={expandedNodes}
            selectedId={selectedId}
            onToggle={handleToggle}
            onSelect={onSelect}
            searchQuery={searchQuery}
            onAddChild={onAddItem ? handleAddChild : undefined}
            onDelete={onDeleteItem ? handleDelete : undefined}
          />
        ))}
      </div>
    </div>
  );
}
