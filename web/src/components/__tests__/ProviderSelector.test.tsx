import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ProviderSelector from "../ProviderSelector";
import { fetchOllamaModels } from "@/lib/api";
import { mockOllamaModels } from "@/test/mocks/fixtures";

vi.mock("@/lib/api");

describe("ProviderSelector", () => {
  beforeEach(() => {
    vi.mocked(fetchOllamaModels).mockResolvedValue(mockOllamaModels);
  });

  it("renders Anthropic and Ollama radio buttons", () => {
    render(
      <ProviderSelector provider="anthropic" onProviderChange={vi.fn()} model="" onModelChange={vi.fn()} />
    );
    expect(screen.getByLabelText("Anthropic")).toBeInTheDocument();
    expect(screen.getByLabelText("Ollama")).toBeInTheDocument();
  });

  it("Anthropic is checked when provider is anthropic", () => {
    render(
      <ProviderSelector provider="anthropic" onProviderChange={vi.fn()} model="" onModelChange={vi.fn()} />
    );
    expect(screen.getByLabelText("Anthropic")).toBeChecked();
    expect(screen.getByLabelText("Ollama")).not.toBeChecked();
  });

  it("clicking Ollama calls onProviderChange", async () => {
    const user = userEvent.setup();
    const onProviderChange = vi.fn();
    render(
      <ProviderSelector provider="anthropic" onProviderChange={onProviderChange} model="" onModelChange={vi.fn()} />
    );
    await user.click(screen.getByLabelText("Ollama"));
    expect(onProviderChange).toHaveBeenCalledWith("ollama");
  });

  it("Ollama shows model dropdown when selected", async () => {
    render(
      <ProviderSelector provider="ollama" onProviderChange={vi.fn()} model="qwen3:8b" onModelChange={vi.fn()} />
    );
    await waitFor(() => {
      expect(screen.getByRole("combobox")).toBeInTheDocument();
    });
  });

  it("Ollama models populate dropdown", async () => {
    render(
      <ProviderSelector provider="ollama" onProviderChange={vi.fn()} model="qwen3:8b" onModelChange={vi.fn()} />
    );
    await waitFor(() => {
      expect(screen.getByText("qwen3:8b")).toBeInTheDocument();
    });
    expect(screen.getByText("llama3:8b")).toBeInTheDocument();
  });

  it("selecting Ollama model calls onModelChange", async () => {
    const user = userEvent.setup();
    const onModelChange = vi.fn();
    render(
      <ProviderSelector provider="ollama" onProviderChange={vi.fn()} model="qwen3:8b" onModelChange={onModelChange} />
    );
    await waitFor(() => {
      expect(screen.getByRole("combobox")).toBeInTheDocument();
    });
    await user.selectOptions(screen.getByRole("combobox"), "llama3:8b");
    expect(onModelChange).toHaveBeenCalledWith("llama3:8b");
  });

  it("shows 'Ollama not reachable' when fetch fails", async () => {
    vi.mocked(fetchOllamaModels).mockRejectedValue(new Error("fail"));
    render(
      <ProviderSelector provider="ollama" onProviderChange={vi.fn()} model="" onModelChange={vi.fn()} />
    );
    await waitFor(() => {
      expect(screen.getByText("Ollama not reachable")).toBeInTheDocument();
    });
  });

  it("shows green status dot when Ollama is available", async () => {
    render(
      <ProviderSelector provider="ollama" onProviderChange={vi.fn()} model="qwen3:8b" onModelChange={vi.fn()} />
    );
    await waitFor(() => {
      expect(screen.getByTitle("Connected")).toBeInTheDocument();
    });
    expect(screen.getByTitle("Connected").className).toContain("bg-green-500");
  });

  it("shows red status dot when Ollama is unavailable", async () => {
    vi.mocked(fetchOllamaModels).mockRejectedValue(new Error("fail"));
    render(
      <ProviderSelector provider="ollama" onProviderChange={vi.fn()} model="" onModelChange={vi.fn()} />
    );
    await waitFor(() => {
      expect(screen.getByTitle("Not available")).toBeInTheDocument();
    });
    expect(screen.getByTitle("Not available").className).toContain("bg-red-500");
  });

  it("Anthropic shows model override text input", () => {
    render(
      <ProviderSelector provider="anthropic" onProviderChange={vi.fn()} model="" onModelChange={vi.fn()} />
    );
    expect(screen.getByPlaceholderText("Default: claude-opus-4-5")).toBeInTheDocument();
  });

  it("Anthropic hides model dropdown", () => {
    render(
      <ProviderSelector provider="anthropic" onProviderChange={vi.fn()} model="" onModelChange={vi.fn()} />
    );
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });
});
