import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ProfileSelector from "../ProfileSelector";
import { fetchProfiles } from "@/lib/api";
import { mockProfiles } from "@/test/mocks/fixtures";

vi.mock("@/lib/api");

describe("ProfileSelector", () => {
  beforeEach(() => {
    vi.mocked(fetchProfiles).mockResolvedValue(mockProfiles);
  });

  it("renders 'None' default option", () => {
    render(<ProfileSelector selected={null} onSelect={vi.fn()} />);
    expect(screen.getByText("None (use blocks directly)")).toBeInTheDocument();
  });

  it("loads and displays profiles from API", async () => {
    render(<ProfileSelector selected={null} onSelect={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText("Business Meeting")).toBeInTheDocument();
    });
    expect(screen.getByText("Therapy Session")).toBeInTheDocument();
  });

  it("shows error on fetch failure", async () => {
    vi.mocked(fetchProfiles).mockRejectedValue(new Error("fail"));
    render(<ProfileSelector selected={null} onSelect={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText("Could not load profiles")).toBeInTheDocument();
    });
  });

  it("selecting a profile calls onSelect with profile object", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<ProfileSelector selected={null} onSelect={onSelect} />);
    await waitFor(() => {
      expect(screen.getByText("Business Meeting")).toBeInTheDocument();
    });
    await user.selectOptions(screen.getByRole("combobox"), "business");
    expect(onSelect).toHaveBeenCalledWith(mockProfiles[0]);
  });

  it("selecting 'None' calls onSelect with null", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<ProfileSelector selected={mockProfiles[0]} onSelect={onSelect} />);
    await waitFor(() => {
      expect(screen.getByText("Business Meeting")).toBeInTheDocument();
    });
    await user.selectOptions(screen.getByRole("combobox"), "");
    expect(onSelect).toHaveBeenCalledWith(null);
  });

  it("shows preview card when profile is selected", () => {
    render(<ProfileSelector selected={mockProfiles[0]} onSelect={vi.fn()} />);
    expect(screen.getByText("Business Meeting")).toBeInTheDocument();
    expect(screen.getByText("Analyze business meetings")).toBeInTheDocument();
    expect(screen.getByText(/Focus on action items/)).toBeInTheDocument();
    expect(screen.getByText("summary")).toBeInTheDocument();
    expect(screen.getByText("action_items")).toBeInTheDocument();
    expect(screen.getByText("decisions")).toBeInTheDocument();
  });

  it("hides preview card when no profile selected", () => {
    render(<ProfileSelector selected={null} onSelect={vi.fn()} />);
    expect(screen.queryByText("Context lens")).not.toBeInTheDocument();
    expect(screen.queryByText("Blocks")).not.toBeInTheDocument();
  });
});
