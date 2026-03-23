"use client";

import { useState, useEffect, useCallback } from "react";
import { fetchSettings, updateSettings, type Settings } from "@/lib/api";

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
}

export default function SettingsModal({ open, onClose }: SettingsModalProps) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [hfToken, setHfToken] = useState("");
  const [anthropicKey, setAnthropicKey] = useState("");
  const [ollamaHost, setOllamaHost] = useState("http://localhost:11434");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!open) return;
    fetchSettings()
      .then((s) => {
        setSettings(s);
        setOllamaHost(s.ollama_host);
        setHfToken("");
        setAnthropicKey("");
        setSaved(false);
      })
      .catch(() => {});
  }, [open]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    setSaved(false);
    const update: Record<string, string> = {};
    if (hfToken) update.hf_token = hfToken;
    if (anthropicKey) update.anthropic_key = anthropicKey;
    if (ollamaHost !== settings?.ollama_host) update.ollama_host = ollamaHost;

    if (Object.keys(update).length > 0) {
      await updateSettings(update);
      // Re-fetch to update status indicators
      const fresh = await fetchSettings();
      setSettings(fresh);
    }
    setHfToken("");
    setAnthropicKey("");
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }, [hfToken, anthropicKey, ollamaHost, settings]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-[480px] rounded-xl border border-slate-700 bg-slate-900 p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-slate-100">Settings</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 text-xl leading-none"
          >
            &times;
          </button>
        </div>

        <div className="space-y-5">
          {/* HF Token */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Hugging Face Token
              {settings && (
                <span
                  className={`ml-2 text-xs ${
                    settings.hf_token_set ? "text-green-400" : "text-yellow-400"
                  }`}
                >
                  {settings.hf_token_set ? "configured" : "not set"}
                </span>
              )}
            </label>
            <input
              type="password"
              value={hfToken}
              onChange={(e) => setHfToken(e.target.value)}
              placeholder={settings?.hf_token_set ? "••••••••  (leave blank to keep)" : "hf_..."}
              className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-primary focus:outline-none"
            />
            <p className="mt-1 text-xs text-slate-500">
              Required for speaker diarization. Get one at{" "}
              <span className="text-slate-400">huggingface.co/settings/tokens</span>
            </p>
          </div>

          {/* Anthropic Key */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Anthropic API Key
              {settings && (
                <span
                  className={`ml-2 text-xs ${
                    settings.anthropic_key_set ? "text-green-400" : "text-slate-500"
                  }`}
                >
                  {settings.anthropic_key_set ? "configured" : "not set (optional with Ollama)"}
                </span>
              )}
            </label>
            <input
              type="password"
              value={anthropicKey}
              onChange={(e) => setAnthropicKey(e.target.value)}
              placeholder={
                settings?.anthropic_key_set ? "••••••••  (leave blank to keep)" : "sk-ant-..."
              }
              className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-primary focus:outline-none"
            />
            <p className="mt-1 text-xs text-slate-500">
              Only needed if using Anthropic provider
            </p>
          </div>

          {/* Ollama Host */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Ollama Host
            </label>
            <input
              type="text"
              value={ollamaHost}
              onChange={(e) => setOllamaHost(e.target.value)}
              className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-primary focus:outline-none"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="mt-6 flex items-center justify-end gap-3">
          {saved && (
            <span className="text-sm text-green-400">Saved</span>
          )}
          <button
            onClick={onClose}
            className="rounded-md px-4 py-2 text-sm text-slate-400 hover:text-slate-200"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white hover:bg-primary-dark disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
