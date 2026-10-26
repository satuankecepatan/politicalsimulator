"""Chronicle formatting and Markdown history export."""

from __future__ import annotations

from pathlib import Path
from polsim.history.log import HistoryLog


def export_markdown_chronicle(history: HistoryLog, title: str = "Historical Political Chronicle") -> str:
    """Generate a readable, formatted Markdown chronicle from simulation history."""
    lines: list[str] = [
        f"# {title}\n",
        "> Generated from simulation structured records.\n",
        "---\n",
    ]

    current_year: str | None = None

    for entry in history.entries:
        # Extract year
        year_part = entry.date.split()[-1] if " " in entry.date else entry.date
        if year_part != current_year:
            current_year = year_part
            lines.append(f"\n## Year {current_year}\n")

        lines.append(f"### {entry.date} — {entry.title}\n")
        if entry.prose:
            lines.append(f"*{entry.prose}*\n")

        d = entry.details
        if entry.entry_type == "election":
            lines.append("| Party | Seats Won | Vote Share |")
            lines.append("| :--- | :--- | :--- |")
            seats_dict = d.get("seats", {})
            shares_dict = d.get("shares", {})
            for p_id, seats in seats_dict.items():
                pct = shares_dict.get(p_id, 0.0) * 100.0
                lines.append(f"| **{p_id.upper()}** | {seats} | {pct:.1f}% |")
            lines.append("")

        elif entry.entry_type == "coalition":
            leader = d.get("leader", "")
            members = d.get("members", [])
            lines.append(f"- **Governing Coalition**: {', '.join(members)}")
            lines.append(f"- **Prime Minister**: {leader}\n")

        elif entry.entry_type == "event":
            if "description" in d:
                lines.append(f"> {d['description']}\n")

    return "\n".join(lines)


def save_markdown_chronicle(history: HistoryLog, path: str | Path, title: str = "Chronicle") -> None:
    text = export_markdown_chronicle(history, title=title)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
