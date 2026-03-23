import Store from "electron-store";
import { safeStorage } from "electron";

interface AppDefaults {
  provider: "ollama" | "anthropic";
  ollamaModel: string;
  firstLaunch: boolean;
  [key: string]: unknown;
}

const store = new Store<AppDefaults>({
  defaults: {
    provider: "ollama",
    ollamaModel: "qwen3:8b",
    firstLaunch: true,
  },
});

export function saveApiKey(key: string): void {
  if (safeStorage.isEncryptionAvailable()) {
    const encrypted = safeStorage.encryptString(key);
    store.set("anthropic_key_encrypted", encrypted.toString("base64"));
  }
}

export function getApiKey(): string | null {
  const encrypted = store.get("anthropic_key_encrypted") as string | undefined;
  if (!encrypted || !safeStorage.isEncryptionAvailable()) return null;
  try {
    return safeStorage.decryptString(Buffer.from(encrypted, "base64"));
  } catch {
    return null;
  }
}

export function saveHfToken(token: string): void {
  if (safeStorage.isEncryptionAvailable()) {
    const encrypted = safeStorage.encryptString(token);
    store.set("hf_token_encrypted", encrypted.toString("base64"));
  }
}

export function getHfToken(): string | null {
  const encrypted = store.get("hf_token_encrypted") as string | undefined;
  if (!encrypted || !safeStorage.isEncryptionAvailable()) return null;
  try {
    return safeStorage.decryptString(Buffer.from(encrypted, "base64"));
  } catch {
    return null;
  }
}

export function getSettings(): AppDefaults {
  return store.store;
}

export function setSetting(key: string, value: unknown): void {
  store.set(key, value);
}

export function isFirstLaunch(): boolean {
  return store.get("firstLaunch") as boolean;
}

export function markSetupComplete(): void {
  store.set("firstLaunch", false);
}
