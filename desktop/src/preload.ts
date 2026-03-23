import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("electronAPI", {
  getSettings: () => ipcRenderer.invoke("get-settings"),
  saveSettings: (settings: Record<string, unknown>) =>
    ipcRenderer.invoke("save-settings", settings),
  isFirstLaunch: () => ipcRenderer.invoke("is-first-launch"),
  getOllamaStatus: () => ipcRenderer.invoke("get-ollama-status"),
});
