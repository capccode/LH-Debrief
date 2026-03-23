"use client";

import { useEffect, useState } from "react";
import type { Block } from "@/lib/types";
import { fetchBlocks } from "@/lib/api";

interface BlockSelectorProps {
  selectedBlocks: string[];
  onBlocksChange: (blocks: string[]) => void;
  profileBlocks: string[];
}

export default function BlockSelector({
  selectedBlocks,
  onBlocksChange,
  profileBlocks,
}: BlockSelectorProps) {
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [expandedInfo, setExpandedInfo] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBlocks()
      .then(setBlocks)
      .catch(() => setError("Could not load blocks"));
  }, []);

  const isProfileBlock = (name: string) => profileBlocks.includes(name);
  const isSelected = (name: string) => isProfileBlock(name) || selectedBlocks.includes(name);

  const toggleBlock = (name: string) => {
    if (isProfileBlock(name)) return;
    if (selectedBlocks.includes(name)) {
      onBlocksChange(selectedBlocks.filter((b) => b !== name));
    } else {
      onBlocksChange([...selectedBlocks, name]);
    }
  };

  const profileBlockList = blocks.filter((b) => isProfileBlock(b.name));
  const additionalBlocks = blocks.filter((b) => !isProfileBlock(b.name));

  return (
    <div className="space-y-2">
      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
        Blocks
      </label>

      {error && <p className="text-xs text-red-400">{error}</p>}

      <div className="max-h-56 space-y-0.5 overflow-y-auto rounded-md border border-slate-700 bg-slate-800/50 p-2">
        {profileBlockList.map((block) => (
          <BlockRow
            key={block.name}
            block={block}
            checked={true}
            locked={true}
            expanded={expandedInfo === block.name}
            onToggle={() => {}}
            onInfoToggle={() =>
              setExpandedInfo(expandedInfo === block.name ? null : block.name)
            }
          />
        ))}

        {profileBlockList.length > 0 && additionalBlocks.length > 0 && (
          <div className="my-1 border-t border-slate-700" />
        )}

        {additionalBlocks.map((block) => (
          <BlockRow
            key={block.name}
            block={block}
            checked={isSelected(block.name)}
            locked={false}
            expanded={expandedInfo === block.name}
            onToggle={() => toggleBlock(block.name)}
            onInfoToggle={() =>
              setExpandedInfo(expandedInfo === block.name ? null : block.name)
            }
          />
        ))}
      </div>
    </div>
  );
}

function BlockRow({
  block,
  checked,
  locked,
  expanded,
  onToggle,
  onInfoToggle,
}: {
  block: Block;
  checked: boolean;
  locked: boolean;
  expanded: boolean;
  onToggle: () => void;
  onInfoToggle: () => void;
}) {
  return (
    <div>
      <div className="flex items-center gap-2 rounded px-1 py-1 hover:bg-slate-800">
        <input
          type="checkbox"
          checked={checked}
          disabled={locked}
          onChange={onToggle}
          className="h-3.5 w-3.5 rounded border-slate-600 accent-primary"
        />
        <span
          className={`flex-1 text-sm ${locked ? "text-slate-500" : "text-slate-300"}`}
        >
          {block.display_name}
        </span>
        <button
          onClick={onInfoToggle}
          className="text-xs text-slate-500 hover:text-accent"
          title="Show block info"
        >
          i
        </button>
      </div>

      {expanded && (
        <div className="ml-6 mb-1 rounded bg-slate-900 p-2 text-xs space-y-1">
          <p className="text-slate-400">{block.description}</p>
          <p className="font-mono text-slate-500">
            Output: {block.json_example.slice(0, 120)}
            {block.json_example.length > 120 ? "..." : ""}
          </p>
        </div>
      )}
    </div>
  );
}
