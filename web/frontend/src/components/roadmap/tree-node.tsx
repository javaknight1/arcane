"use client";

import { ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";
import type { RoadmapItem, ItemType } from "@/types/roadmap";
import { getChildren, getChildType, getEstimatedHours } from "@/types/roadmap";
import { TYPE_STYLES, STATUS_COLORS, PRIORITY_STYLES } from "./constants";

interface TreeNodeProps {
  item: RoadmapItem;
  type: ItemType;
  depth: number;
  expandedNodes: Set<string>;
  selectedId: string | null;
  onToggle: (id: string) => void;
  onSelect: (item: RoadmapItem, type: ItemType) => void;
  searchQuery: string;
}

function matchesSearch(
  item: RoadmapItem,
  type: ItemType,
  query: string
): boolean {
  if (!query) return true;
  const lower = query.toLowerCase();
  if (item.name.toLowerCase().includes(lower)) return true;
  const children = getChildren(item, type);
  const childType = getChildType(type);
  if (childType) {
    return children.some((child) => matchesSearch(child, childType, query));
  }
  return false;
}

export function TreeNode({
  item,
  type,
  depth,
  expandedNodes,
  selectedId,
  onToggle,
  onSelect,
  searchQuery,
}: TreeNodeProps) {
  const children = getChildren(item, type);
  const childType = getChildType(type);
  const isLeaf = children.length === 0;
  const isExpanded = expandedNodes.has(item.id);
  const isSelected = selectedId === item.id;
  const hours = getEstimatedHours(item, type);

  if (searchQuery && !matchesSearch(item, type, searchQuery)) {
    return null;
  }

  return (
    <Collapsible open={isExpanded} onOpenChange={() => !isLeaf && onToggle(item.id)}>
      <CollapsibleTrigger asChild>
        <button
          className={cn(
            "flex w-full items-center gap-1.5 rounded-md border-l-2 px-2 py-1.5 text-left text-sm transition-colors hover:bg-accent/50",
            STATUS_COLORS[item.status],
            isSelected && "bg-accent"
          )}
          style={{ paddingLeft: depth * 16 + 8 }}
          onClick={(e) => {
            e.preventDefault();
            onSelect(item, type);
            if (!isLeaf) onToggle(item.id);
          }}
        >
          {!isLeaf ? (
            <ChevronRight
              className={cn(
                "h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform",
                isExpanded && "rotate-90"
              )}
            />
          ) : (
            <span className="w-3.5 shrink-0" />
          )}
          <Badge
            variant="secondary"
            className={cn("shrink-0 text-[10px] px-1.5 py-0", TYPE_STYLES[type])}
          >
            {type}
          </Badge>
          <span className="truncate font-medium">{item.name}</span>
          <span className="ml-auto flex shrink-0 items-center gap-1.5">
            <Badge
              variant="secondary"
              className={cn("text-[10px] px-1 py-0", PRIORITY_STYLES[item.priority])}
            >
              {item.priority}
            </Badge>
            <span className="text-[10px] text-muted-foreground tabular-nums">
              {hours}h
            </span>
          </span>
        </button>
      </CollapsibleTrigger>
      {!isLeaf && childType && (
        <CollapsibleContent>
          {children.map((child) => (
            <TreeNode
              key={child.id}
              item={child}
              type={childType}
              depth={depth + 1}
              expandedNodes={expandedNodes}
              selectedId={selectedId}
              onToggle={onToggle}
              onSelect={onSelect}
              searchQuery={searchQuery}
            />
          ))}
        </CollapsibleContent>
      )}
    </Collapsible>
  );
}
