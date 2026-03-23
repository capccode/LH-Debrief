import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import OutputTree from "../OutputTree";

const testFiles = ["briefing.md", "analysis.json", "transcript.txt"];

describe("OutputTree", () => {
  it("shows empty state when no files", () => {
    render(<OutputTree files={[]} viewingFile={null} onSelectFile={vi.fn()} />);
    expect(screen.getByText("No output files yet")).toBeInTheDocument();
  });

  it("renders file list", () => {
    render(<OutputTree files={testFiles} viewingFile={null} onSelectFile={vi.fn()} />);
    expect(screen.getByText(/briefing\.md/)).toBeInTheDocument();
    expect(screen.getByText(/analysis\.json/)).toBeInTheDocument();
    expect(screen.getByText(/transcript\.txt/)).toBeInTheDocument();
  });

  it("clicking file calls onSelectFile", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<OutputTree files={testFiles} viewingFile={null} onSelectFile={onSelect} />);
    await user.click(screen.getByRole("button", { name: /briefing\.md/ }));
    expect(onSelect).toHaveBeenCalledWith("briefing.md");
  });

  it("active file is highlighted", () => {
    render(<OutputTree files={testFiles} viewingFile="briefing.md" onSelectFile={vi.fn()} />);
    const activeButton = screen.getByRole("button", { name: /briefing\.md/ });
    expect(activeButton.className).toContain("bg-accent");
  });

  it("non-active files have default styling", () => {
    render(<OutputTree files={testFiles} viewingFile="briefing.md" onSelectFile={vi.fn()} />);
    const otherButton = screen.getByRole("button", { name: /analysis\.json/ });
    expect(otherButton.className).toContain("text-slate-300");
  });

  it("shows correct icon for JSON files", () => {
    render(<OutputTree files={["data.json"]} viewingFile={null} onSelectFile={vi.fn()} />);
    expect(screen.getByText("📊")).toBeInTheDocument();
  });

  it("shows correct icon for markdown files", () => {
    render(<OutputTree files={["notes.md"]} viewingFile={null} onSelectFile={vi.fn()} />);
    expect(screen.getByText("📝")).toBeInTheDocument();
  });

  it("shows correct icon for other files", () => {
    render(<OutputTree files={["output.txt"]} viewingFile={null} onSelectFile={vi.fn()} />);
    expect(screen.getByText("📄")).toBeInTheDocument();
  });
});
