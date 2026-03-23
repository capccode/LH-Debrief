import type { Profile, Block, OllamaModel, LogMessage } from "@/lib/types";
import type { Settings } from "@/lib/api";

export const mockProfiles: Profile[] = [
  {
    id: "business",
    name: "Business Meeting",
    description: "Analyze business meetings",
    context: "Focus on action items, decisions, and follow-ups in a business context.",
    blocks: ["summary", "action_items", "decisions"],
  },
  {
    id: "therapy",
    name: "Therapy Session",
    description: "Analyze therapy sessions",
    context: "Focus on therapeutic themes and emotional dynamics.",
    blocks: ["themes", "emotions"],
  },
];

export const mockBlocks: Block[] = [
  {
    name: "summary",
    display_name: "Summary",
    description: "A concise summary of the conversation",
    prompt: "Summarize the transcript",
    json_example: '{"summary": "..."}',
  },
  {
    name: "action_items",
    display_name: "Action Items",
    description: "Extracted action items with owners",
    prompt: "List action items",
    json_example: '{"action_items": ["..."]}',
  },
  {
    name: "decisions",
    display_name: "Decisions",
    description: "Key decisions made during the meeting",
    prompt: "List decisions",
    json_example: '{"decisions": ["..."]}',
  },
  {
    name: "themes",
    display_name: "Themes",
    description: "Recurring themes in the session",
    prompt: "Identify themes",
    json_example: '{"themes": ["..."]}',
  },
  {
    name: "emotions",
    display_name: "Emotions",
    description: "Emotional dynamics observed",
    prompt: "Analyze emotions",
    json_example: '{"emotions": ["..."]}',
  },
];

export const mockOllamaModels: OllamaModel[] = [
  { name: "qwen3:8b", size: 4_500_000_000, modified: "2026-03-20T10:00:00Z" },
  { name: "llama3:8b", size: 4_000_000_000, modified: "2026-03-19T10:00:00Z" },
];

export const mockSettings: Settings = {
  hf_token_set: true,
  anthropic_key_set: false,
  ollama_host: "http://localhost:11434",
};

export const mockLogs: LogMessage[] = [
  { timestamp: "2026-03-23T10:00:00Z", stage: "diarize", message: "Starting diarization", status: "done" },
  { timestamp: "2026-03-23T10:00:05Z", stage: "transcribe", message: "Transcribing audio", status: "running" },
  { timestamp: "2026-03-23T10:00:10Z", stage: "analyze", message: "LLM call failed", status: "error" },
];

export function createMockFile(name: string, type = "audio/wav", size = 1024): File {
  const buffer = new ArrayBuffer(size);
  return new File([buffer], name, { type });
}
