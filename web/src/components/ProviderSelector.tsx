"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { OllamaModel } from "@/lib/types";
import { fetchOllamaModels } from "@/lib/api";

interface ProviderSelectorProps {
  provider: "anthropic" | "ollama";
  onProviderChange: (provider: "anthropic" | "ollama") => void;
  model: string;
  onModelChange: (model: string) => void;
}

export default function ProviderSelector({
  provider,
  onProviderChange,
  model,
  onModelChange,
}: ProviderSelectorProps) {
  const [ollamaModels, setOllamaModels] = useState<OllamaModel[]>([]);
  const [ollamaAvailable, setOllamaAvailable] = useState<boolean | null>(null);
  const fetchedRef = useRef(false);

  const handleModelsLoaded = useCallback(
    (models: OllamaModel[]) => {
      setOllamaModels(models);
      setOllamaAvailable(true);
      if (provider === "ollama" && !model && models.length > 0) {
        onModelChange(models[0].name);
      }
    },
    [provider, model, onModelChange]
  );

  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    fetchOllamaModels()
      .then(handleModelsLoaded)
      .catch(() => setOllamaAvailable(false));
  }, [handleModelsLoaded]);

  return (
    <div className="space-y-3">
      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
        Provider
      </label>

      <div className="space-y-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            name="provider"
            checked={provider === "anthropic"}
            onChange={() => onProviderChange("anthropic")}
            className="accent-primary"
          />
          <span className="text-sm text-slate-300">Anthropic</span>
        </label>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            name="provider"
            checked={provider === "ollama"}
            onChange={() => onProviderChange("ollama")}
            className="accent-primary"
          />
          <span className="text-sm text-slate-300">Ollama</span>
          {ollamaAvailable !== null && (
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                ollamaAvailable ? "bg-green-500" : "bg-red-500"
              }`}
              title={ollamaAvailable ? "Connected" : "Not available"}
            />
          )}
        </label>
      </div>

      {provider === "ollama" && (
        <div>
          <label className="mb-1 block text-xs text-slate-500">Model</label>
          {ollamaModels.length > 0 ? (
            <select
              value={model}
              onChange={(e) => onModelChange(e.target.value)}
              className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-primary focus:outline-none"
            >
              {ollamaModels.map((m) => (
                <option key={m.name} value={m.name}>
                  {m.name}
                </option>
              ))}
            </select>
          ) : (
            <p className="text-xs text-slate-500 italic">
              {ollamaAvailable === false
                ? "Ollama not reachable"
                : "No models available"}
            </p>
          )}
        </div>
      )}

      {provider === "anthropic" && (
        <div>
          <label className="mb-1 block text-xs text-slate-500">
            Model override (optional)
          </label>
          <input
            type="text"
            value={model}
            onChange={(e) => onModelChange(e.target.value)}
            placeholder="Default: claude-opus-4-5"
            className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-primary focus:outline-none"
          />
        </div>
      )}
    </div>
  );
}
