import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ProcessingLog from "../ProcessingLog";
import { mockLogs } from "@/test/mocks/fixtures";
import type { LogMessage } from "@/lib/types";

describe("ProcessingLog", () => {
  it("shows empty state when no logs", () => {
    render(<ProcessingLog logs={[]} />);
    expect(screen.getByText("Waiting for job to start...")).toBeInTheDocument();
  });

  it("renders log messages", () => {
    render(<ProcessingLog logs={mockLogs} />);
    expect(screen.getByText("Starting diarization")).toBeInTheDocument();
    expect(screen.getByText("Transcribing audio")).toBeInTheDocument();
    expect(screen.getByText("LLM call failed")).toBeInTheDocument();
  });

  it("shows stage labels in brackets", () => {
    render(<ProcessingLog logs={mockLogs} />);
    expect(screen.getByText("[diarize]")).toBeInTheDocument();
    expect(screen.getByText("[transcribe]")).toBeInTheDocument();
    expect(screen.getByText("[analyze]")).toBeInTheDocument();
  });

  it("done status shows green checkmark", () => {
    const log: LogMessage = { timestamp: "", stage: "test", message: "Done", status: "done" };
    render(<ProcessingLog logs={[log]} />);
    const icon = screen.getByText("✓");
    expect(icon).toHaveClass("text-green-400");
  });

  it("running status shows spinning indicator", () => {
    const log: LogMessage = { timestamp: "", stage: "test", message: "Working", status: "running" };
    render(<ProcessingLog logs={[log]} />);
    const icon = screen.getByText("⟳");
    expect(icon).toHaveClass("animate-spin");
  });

  it("error status shows red X and red message text", () => {
    const log: LogMessage = { timestamp: "", stage: "test", message: "Failed", status: "error" };
    render(<ProcessingLog logs={[log]} />);
    const icon = screen.getByText("✕");
    expect(icon).toHaveClass("text-red-400");
    const message = screen.getByText("Failed");
    expect(message).toHaveClass("text-red-400");
  });
});
