"use client";

import { useState, useCallback } from "react";
import type { RoadmapData, RoadmapItem, ItemType } from "@/types/roadmap";
import { RoadmapTree } from "./roadmap-tree";
import { ItemDetail } from "./item-detail";

interface RoadmapViewerProps {
  data: RoadmapData;
}

export function RoadmapViewer({ data }: RoadmapViewerProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<RoadmapItem | null>(null);
  const [selectedType, setSelectedType] = useState<ItemType | null>(null);

  const handleSelect = useCallback((item: RoadmapItem, type: ItemType) => {
    setSelectedId(item.id);
    setSelectedItem(item);
    setSelectedType(type);
  }, []);

  return (
    <div className="flex flex-col lg:flex-row gap-4 h-[calc(100vh-12rem)]">
      {/* Left panel: tree */}
      <div className="lg:w-1/3 min-w-[300px] rounded-lg border overflow-hidden">
        <RoadmapTree
          data={data}
          selectedId={selectedId}
          onSelect={handleSelect}
        />
      </div>

      {/* Right panel: detail */}
      <div className="flex-1 rounded-lg border overflow-hidden">
        <ItemDetail item={selectedItem} type={selectedType} />
      </div>
    </div>
  );
}
