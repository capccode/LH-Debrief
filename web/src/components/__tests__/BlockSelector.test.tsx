import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import BlockSelector from "../BlockSelector";
import { fetchBlocks } from "@/lib/api";
import { mockBlocks } from "@/test/mocks/fixtures";

vi.mock("@/lib/api");

describe("BlockSelector", () => {
  beforeEach(() => {
    vi.mocked(fetchBlocks).mockResolvedValue(mockBlocks);
  });

  it("renders block checkboxes after loading", async () => {
    render(
      <BlockSelector selectedBlocks={[]} onBlocksChange={vi.fn()} profileBlocks={["summary"]} />
    );
    await waitFor(() => {
      expect(screen.getByText("Summary")).toBeInTheDocument();
    });
    expect(screen.getByText("Action Items")).toBeInTheDocument();
    expect(screen.getByText("Decisions")).toBeInTheDocument();
    expect(screen.getByText("Themes")).toBeInTheDocument();
    expect(screen.getByText("Emotions")).toBeInTheDocument();
  });

  it("profile blocks are checked and disabled", async () => {
    render(
      <BlockSelector selectedBlocks={[]} onBlocksChange={vi.fn()} profileBlocks={["summary"]} />
    );
    await waitFor(() => {
      expect(screen.getByText("Summary")).toBeInTheDocument();
    });
    const checkboxes = screen.getAllByRole("checkbox");
    // Summary is the first profile block
    const summaryCheckbox = checkboxes[0];
    expect(summaryCheckbox).toBeChecked();
    expect(summaryCheckbox).toBeDisabled();
  });

  it("non-profile blocks are unchecked and enabled", async () => {
    render(
      <BlockSelector selectedBlocks={[]} onBlocksChange={vi.fn()} profileBlocks={["summary"]} />
    );
    await waitFor(() => {
      expect(screen.getByText("Themes")).toBeInTheDocument();
    });
    // Themes is a non-profile block — find its checkbox
    const checkboxes = screen.getAllByRole("checkbox");
    // Profile block (summary) is first, then additional blocks (action_items, decisions, themes, emotions)
    const themesCheckbox = checkboxes[3]; // 0=summary, 1=action_items, 2=decisions, 3=themes
    expect(themesCheckbox).not.toBeChecked();
    expect(themesCheckbox).not.toBeDisabled();
  });

  it("clicking non-profile block calls onBlocksChange", async () => {
    const user = userEvent.setup();
    const onBlocksChange = vi.fn();
    render(
      <BlockSelector selectedBlocks={[]} onBlocksChange={onBlocksChange} profileBlocks={["summary"]} />
    );
    await waitFor(() => {
      expect(screen.getByText("Themes")).toBeInTheDocument();
    });
    // Click the "Themes" checkbox by clicking its label row
    const checkboxes = screen.getAllByRole("checkbox");
    const themesCheckbox = checkboxes[3];
    await user.click(themesCheckbox);
    expect(onBlocksChange).toHaveBeenCalledWith(["themes"]);
  });

  it("clicking selected block removes it", async () => {
    const user = userEvent.setup();
    const onBlocksChange = vi.fn();
    render(
      <BlockSelector selectedBlocks={["themes"]} onBlocksChange={onBlocksChange} profileBlocks={["summary"]} />
    );
    await waitFor(() => {
      expect(screen.getByText("Themes")).toBeInTheDocument();
    });
    const checkboxes = screen.getAllByRole("checkbox");
    const themesCheckbox = checkboxes[3];
    await user.click(themesCheckbox);
    expect(onBlocksChange).toHaveBeenCalledWith([]);
  });

  it("info button toggles expanded info panel", async () => {
    const user = userEvent.setup();
    render(
      <BlockSelector selectedBlocks={[]} onBlocksChange={vi.fn()} profileBlocks={["summary"]} />
    );
    await waitFor(() => {
      expect(screen.getByText("Summary")).toBeInTheDocument();
    });
    // Click the first info button (for Summary)
    const infoButtons = screen.getAllByTitle("Show block info");
    await user.click(infoButtons[0]);
    expect(screen.getByText("A concise summary of the conversation")).toBeInTheDocument();
    // Click again to collapse
    await user.click(infoButtons[0]);
    expect(screen.queryByText("A concise summary of the conversation")).not.toBeInTheDocument();
  });

  it("shows error on fetch failure", async () => {
    vi.mocked(fetchBlocks).mockRejectedValue(new Error("fail"));
    render(
      <BlockSelector selectedBlocks={[]} onBlocksChange={vi.fn()} profileBlocks={[]} />
    );
    await waitFor(() => {
      expect(screen.getByText("Could not load blocks")).toBeInTheDocument();
    });
  });
});
