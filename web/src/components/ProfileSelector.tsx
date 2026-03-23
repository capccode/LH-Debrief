"use client";

import { useEffect, useState } from "react";
import type { Profile } from "@/lib/types";
import { fetchProfiles } from "@/lib/api";

interface ProfileSelectorProps {
  selected: Profile | null;
  onSelect: (profile: Profile | null) => void;
}

export default function ProfileSelector({ selected, onSelect }: ProfileSelectorProps) {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProfiles()
      .then(setProfiles)
      .catch(() => setError("Could not load profiles"));
  }, []);

  return (
    <div className="space-y-2">
      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
        Profile
      </label>

      <select
        value={selected?.id ?? ""}
        onChange={(e) => {
          const id = e.target.value;
          onSelect(id ? profiles.find((p) => p.id === id) ?? null : null);
        }}
        className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-primary focus:outline-none"
      >
        <option value="">None (use blocks directly)</option>
        {profiles.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {selected && (
        <div className="rounded-md border border-slate-700 bg-slate-800/50 p-3 space-y-2">
          <p className="text-sm font-medium text-primary-light">{selected.name}</p>
          <p className="text-xs text-slate-400">{selected.description}</p>
          <div className="border-t border-slate-700 pt-2">
            <p className="mb-1 text-xs font-medium text-slate-500">Context lens</p>
            <p className="text-xs text-slate-400 italic leading-relaxed">
              {selected.context.length > 200
                ? selected.context.slice(0, 200) + "..."
                : selected.context}
            </p>
          </div>
          <div className="border-t border-slate-700 pt-2">
            <p className="mb-1 text-xs font-medium text-slate-500">Blocks</p>
            <div className="flex flex-wrap gap-1">
              {selected.blocks.map((b) => (
                <span
                  key={b}
                  className="rounded bg-primary/20 px-1.5 py-0.5 text-xs text-primary-light"
                >
                  {b}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
