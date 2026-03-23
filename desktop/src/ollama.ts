import { net } from "electron";

interface OllamaStatus {
  running: boolean;
  models: string[];
}

export async function checkOllama(
  host: string = "http://localhost:11434"
): Promise<OllamaStatus> {
  try {
    const resp = await net.fetch(`${host}/api/tags`);
    if (!resp.ok) return { running: false, models: [] };
    const data = (await resp.json()) as { models?: { name: string }[] };
    const models = (data.models || []).map((m) => m.name);
    return { running: true, models };
  } catch {
    return { running: false, models: [] };
  }
}
