import {
  app,
  BrowserWindow,
  dialog,
  ipcMain,
  net,
} from "electron";
import { type ChildProcess, spawn } from "node:child_process";
import * as nodePath from "node:path";
import * as nodeNet from "node:net";

import {
  getApiKey,
  getHfToken,
  getSettings,
  isFirstLaunch,
  markSetupComplete,
  saveApiKey,
  saveHfToken,
  setSetting,
} from "./settings.js";
import { checkOllama } from "./ollama.js";

let mainWindow: BrowserWindow | null = null;
let fastApiProcess: ChildProcess | null = null;
let nextJsProcess: ChildProcess | null = null;
let fastApiPort = 8000;
let nextJsPort = 3000;

// ---------------------------------------------------------------------------
// Resource / path helpers
// ---------------------------------------------------------------------------

function getResourcePath(): string {
  if (app.isPackaged) {
    return nodePath.join(process.resourcesPath);
  }
  return nodePath.join(__dirname, "..", "..");
}

function resolveUvPath(): string {
  // In development, rely on the user's PATH
  return "uv";
}

// ---------------------------------------------------------------------------
// Port helpers
// ---------------------------------------------------------------------------

async function isPortAvailable(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const server = nodeNet.createServer();
    server.once("error", () => resolve(false));
    server.once("listening", () => {
      server.close();
      resolve(true);
    });
    server.listen(port, "127.0.0.1");
  });
}

async function findAvailablePort(start: number): Promise<number> {
  for (let port = start; port < start + 100; port++) {
    if (await isPortAvailable(port)) return port;
  }
  throw new Error(`No available port found starting from ${start}`);
}

// ---------------------------------------------------------------------------
// Service health polling
// ---------------------------------------------------------------------------

async function waitForHealth(
  url: string,
  timeoutMs: number = 30_000
): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const resp = await net.fetch(url);
      if (resp.ok) return;
    } catch {
      // not ready yet
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`Service at ${url} did not become ready within ${timeoutMs}ms`);
}

// ---------------------------------------------------------------------------
// Child process management
// ---------------------------------------------------------------------------

function spawnFastApi(port: number): ChildProcess {
  const resourcePath = getResourcePath();
  const uvPath = resolveUvPath();

  const apiKey = getApiKey();
  const hfToken = getHfToken();

  const env: Record<string, string> = { ...process.env } as Record<
    string,
    string
  >;
  if (apiKey) env.ANTHROPIC_API_KEY = apiKey;
  if (hfToken) env.HF_TOKEN = hfToken;

  const child = spawn(
    uvPath,
    [
      "run",
      "uvicorn",
      "api.main:app",
      "--port",
      String(port),
      "--host",
      "127.0.0.1",
      "--no-access-log",
    ],
    {
      cwd: resourcePath,
      env,
      stdio: ["ignore", "pipe", "pipe"],
    }
  );

  child.stdout?.on("data", (data: Buffer) => {
    console.log(`[fastapi] ${data.toString().trimEnd()}`);
  });

  child.stderr?.on("data", (data: Buffer) => {
    console.error(`[fastapi] ${data.toString().trimEnd()}`);
  });

  child.on("error", (err) => {
    console.error("[fastapi] Failed to start:", err.message);
  });

  return child;
}

function killChildProcess(child: ChildProcess | null): Promise<void> {
  if (!child || child.killed) return Promise.resolve();

  return new Promise((resolve) => {
    const timeout = setTimeout(() => {
      try {
        child.kill("SIGKILL");
      } catch {
        // already dead
      }
      resolve();
    }, 5000);

    child.once("exit", () => {
      clearTimeout(timeout);
      resolve();
    });

    try {
      child.kill("SIGTERM");
    } catch {
      clearTimeout(timeout);
      resolve();
    }
  });
}

function spawnNextJs(port: number): ChildProcess {
  const resourcePath = getResourcePath();
  const webDir = nodePath.join(resourcePath, "web");

  const child = spawn(
    "npx",
    ["next", "dev", "--port", String(port)],
    {
      cwd: webDir,
      env: {
        ...process.env,
        NEXT_PUBLIC_API_URL: `http://127.0.0.1:${fastApiPort}`,
      } as Record<string, string>,
      stdio: ["ignore", "pipe", "pipe"],
      shell: true,
    }
  );

  child.stdout?.on("data", (data: Buffer) => {
    console.log(`[nextjs] ${data.toString().trimEnd()}`);
  });

  child.stderr?.on("data", (data: Buffer) => {
    // Next.js outputs normal startup info on stderr
    console.log(`[nextjs] ${data.toString().trimEnd()}`);
  });

  child.on("error", (err) => {
    console.error("[nextjs] Failed to start:", err.message);
  });

  return child;
}

// ---------------------------------------------------------------------------
// Window creation
// ---------------------------------------------------------------------------

function createMainWindow(url: string): BrowserWindow {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    titleBarStyle: "hiddenInset",
    trafficLightPosition: { x: 16, y: 16 },
    webPreferences: {
      preload: nodePath.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.loadURL(url);

  win.on("closed", () => {
    mainWindow = null;
  });

  return win;
}

function createSetupWindow(): BrowserWindow {
  const win = new BrowserWindow({
    width: 640,
    height: 520,
    resizable: false,
    titleBarStyle: "hiddenInset",
    trafficLightPosition: { x: 16, y: 16 },
    webPreferences: {
      preload: nodePath.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const setupPath = nodePath.join(__dirname, "..", "src", "pages", "setup.html");
  win.loadFile(setupPath);

  return win;
}

// ---------------------------------------------------------------------------
// IPC handlers
// ---------------------------------------------------------------------------

function registerIpcHandlers(): void {
  ipcMain.handle("get-settings", () => getSettings());

  ipcMain.handle(
    "save-settings",
    (_event, settings: Record<string, unknown>) => {
      if (typeof settings.apiKey === "string") saveApiKey(settings.apiKey);
      if (typeof settings.hfToken === "string") saveHfToken(settings.hfToken);
      if (typeof settings.provider === "string")
        setSetting("provider", settings.provider);
      if (typeof settings.ollamaModel === "string")
        setSetting("ollamaModel", settings.ollamaModel);
      if (settings.firstLaunch === false) markSetupComplete();
    }
  );

  ipcMain.handle("is-first-launch", () => isFirstLaunch());

  ipcMain.handle("get-ollama-status", async () => checkOllama());
}

// ---------------------------------------------------------------------------
// App startup
// ---------------------------------------------------------------------------

async function startApp(): Promise<void> {
  registerIpcHandlers();

  // First-launch setup flow
  if (isFirstLaunch()) {
    const setupWin = createSetupWindow();

    // Wait for setup to complete — the setup page calls save-settings
    // with firstLaunch: false, then we proceed.
    await new Promise<void>((resolve) => {
      const check = setInterval(() => {
        if (!isFirstLaunch()) {
          clearInterval(check);
          setupWin.close();
          resolve();
        }
      }, 500);

      setupWin.on("closed", () => {
        clearInterval(check);
        resolve();
      });
    });

    // If user closed setup without completing, quit
    if (isFirstLaunch()) {
      app.quit();
      return;
    }
  }

  // Find an available port for FastAPI
  try {
    fastApiPort = await findAvailablePort(8000);
  } catch (err) {
    dialog.showErrorBox(
      "Port Error",
      "Could not find an available port for the backend server."
    );
    app.quit();
    return;
  }

  // Spawn FastAPI
  fastApiProcess = spawnFastApi(fastApiPort);

  // Handle immediate crash
  const crashPromise = new Promise<"crashed">((resolve) => {
    fastApiProcess?.once("exit", (code) => {
      if (code !== null && code !== 0) resolve("crashed");
    });
  });

  // Wait for health check
  const healthUrl = `http://127.0.0.1:${fastApiPort}/health`;

  try {
    const result = await Promise.race([
      waitForHealth(healthUrl).then(() => "ready" as const),
      crashPromise,
    ]);

    if (result === "crashed") {
      throw new Error("FastAPI process exited unexpectedly");
    }
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Unknown error starting backend";

    const response = await dialog.showMessageBox({
      type: "error",
      title: "Backend Error",
      message: "Failed to start the analysis backend.",
      detail: `${message}\n\nMake sure Python and uv are installed.`,
      buttons: ["Quit", "Retry"],
      defaultId: 1,
    });

    if (response.response === 1) {
      await killChildProcess(fastApiProcess);
      fastApiProcess = null;
      return startApp();
    }

    app.quit();
    return;
  }

  // Start the Next.js frontend
  nextJsPort = await findAvailablePort(3000);
  nextJsProcess = spawnNextJs(nextJsPort);

  const frontendUrl = `http://localhost:${nextJsPort}`;

  try {
    await waitForHealth(frontendUrl, 60_000); // Next.js takes longer to start
  } catch {
    // If Next.js didn't start, try loading anyway — it may come up shortly
    console.warn("[nextjs] Health check timed out, loading anyway...");
  }

  mainWindow = createMainWindow(frontendUrl);
}

// ---------------------------------------------------------------------------
// App lifecycle
// ---------------------------------------------------------------------------

app.on("ready", () => {
  startApp().catch((err) => {
    console.error("Fatal startup error:", err);
    dialog.showErrorBox("Startup Error", String(err));
    app.quit();
  });
});

app.on("window-all-closed", () => {
  app.quit();
});

app.on("before-quit", async () => {
  await Promise.all([
    killChildProcess(fastApiProcess),
    killChildProcess(nextJsProcess),
  ]);
  fastApiProcess = null;
  nextJsProcess = null;
});

app.on("activate", () => {
  if (mainWindow === null && !isFirstLaunch()) {
    const frontendUrl = `http://localhost:${nextJsPort}`;
    mainWindow = createMainWindow(frontendUrl);
  }
});
