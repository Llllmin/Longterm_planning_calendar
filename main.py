import tkinter as tk
from tkinter import messagebox
import calendar
import datetime
from dataclasses import dataclass


@dataclass
class Goal:
    name: str
    start: datetime.date
    end: datetime.date
    color: str = "#7aa2f7"


class MonthView(tk.Canvas):
    def __init__(self, master, year: int, month: int, goals: list[Goal], **kwargs):
        super().__init__(master, **kwargs)
        self.year = year
        self.month = month
        self.goals = goals

        # layout
        self.pad = 20
        self.header_h = 50
        self.weekday_h = 30
        self.cell_w = 120
        self.cell_h = 70

        self.goal_hitboxes = []
        self.draw()
        self.bind("<Button-1>", self.on_click)

    def set_month(self, year: int, month: int):
        self.year = year
        self.month = month
        self.draw()

    def draw(self):
        self.delete("all")
        self.goal_hitboxes.clear()

        cal = calendar.Calendar(firstweekday=0)  # 0=Mon
        self.month_dates = list(cal.itermonthdates(self.year, self.month))[:42]

        width = self.pad * 2 + self.cell_w * 7
        height = self.pad * 2 + self.header_h + self.weekday_h + self.cell_h * 6
        self.config(width=width, height=height)

        title = f"{calendar.month_name[self.month]} {self.year}"
        self.create_text(width // 2, self.pad + self.header_h // 2, text=title, font=("Arial", 18, "bold"))

        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        top_y = self.pad + self.header_h
        for i, wd in enumerate(weekdays):
            x0 = self.pad + i * self.cell_w
            x1 = x0 + self.cell_w
            y0 = top_y
            y1 = y0 + self.weekday_h
            self.create_rectangle(x0, y0, x1, y1)
            self.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=wd, font=("Arial", 12, "bold"))

        self.grid_top = top_y + self.weekday_h
        for idx, date_obj in enumerate(self.month_dates):
            row = idx // 7
            col = idx % 7
            x0, y0, x1, y1 = self._cell_bounds(row, col)

            in_current_month = (date_obj.month == self.month)
            fill = "white" if in_current_month else "#f2f2f2"
            self.create_rectangle(x0, y0, x1, y1, fill=fill, outline="black")

            self.create_text(
                x0 + 10, y0 + 10,
                text=str(date_obj.day),
                anchor="nw",
                font=("Arial", 12),
                fill="black" if in_current_month else "#888888"
            )

        self._draw_goals()

    def _cell_bounds(self, row: int, col: int):
        x0 = self.pad + col * self.cell_w
        y0 = self.grid_top + row * self.cell_h
        x1 = x0 + self.cell_w
        y1 = y0 + self.cell_h
        return x0, y0, x1, y1

    def _draw_goals(self):
        date_to_idx = {d: i for i, d in enumerate(self.month_dates)}
        visible_start = self.month_dates[0]
        visible_end = self.month_dates[-1]

        bar_h = 18
        bar_pad_x = 6
        bar_y_offset = 28

        # NOTE: for now, all goals use the same vertical slot; later we can stack
        for goal in self.goals:
            s = max(goal.start, visible_start)
            e = min(goal.end, visible_end)
            if s > e:
                continue

            idxs = []
            cur = s
            while cur <= e:
                idxs.append(date_to_idx[cur])
                cur += datetime.timedelta(days=1)

            by_row = {}
            for idx in idxs:
                r = idx // 7
                c = idx % 7
                by_row.setdefault(r, []).append(c)

            segments = []
            for r, cols in by_row.items():
                cols.sort()
                start_c = cols[0]
                prev = cols[0]
                for c in cols[1:]:
                    if c == prev + 1:
                        prev = c
                    else:
                        segments.append((r, start_c, prev))
                        start_c = c
                        prev = c
                segments.append((r, start_c, prev))

            first_segment = True
            for (r, c0, c1) in sorted(segments):
                x0, y0, _, _ = self._cell_bounds(r, c0)
                _, _, x1, _ = self._cell_bounds(r, c1)

                bar_x0 = x0 + bar_pad_x
                bar_x1 = x1 - bar_pad_x
                bar_y0 = y0 + bar_y_offset
                bar_y1 = bar_y0 + bar_h

                self.create_rectangle(bar_x0, bar_y0, bar_x1, bar_y1, fill=goal.color, outline="")

                self.goal_hitboxes.append({
                    "x0": bar_x0, "y0": bar_y0, "x1": bar_x1, "y1": bar_y1,
                    "goal": goal
                })

                if first_segment:
                    self.create_text(
                        bar_x0 + 6, (bar_y0 + bar_y1) / 2,
                        text=goal.name,
                        anchor="w",
                        font=("Arial", 10, "bold"),
                        fill="white"
                    )
                    first_segment = False

    def on_click(self, event):
        x, y = event.x, event.y
        for hb in reversed(self.goal_hitboxes):
            if hb["x0"] <= x <= hb["x1"] and hb["y0"] <= y <= hb["y1"]:
                g: Goal = hb["goal"]
                messagebox.showinfo("Goal details", f"{g.name}\n{g.start.isoformat()} → {g.end.isoformat()}")
                return


def parse_date(s: str) -> datetime.date:
    # Expect YYYY-MM-DD
    return datetime.date.fromisoformat(s.strip())


def main():
    root = tk.Tk()
    root.title("Long-term Planning Calendar")
    root.configure(bg="white")

    # ---- data ----
    goals: list[Goal] = [
        Goal("IB CS (core)", datetime.date(2026, 1, 5), datetime.date(2026, 2, 10), "#4f7cff"),
        Goal("Math HL", datetime.date(2025, 12, 20), datetime.date(2026, 1, 18), "#f28c28"),
    ]

    current_year = 2026
    current_month = 1

    # ---- layout: left calendar, right form ----
    container = tk.Frame(root, bg="white")
    container.pack(padx=12, pady=12)

    # calendar
    canvas = MonthView(container, current_year, current_month, goals, bg="white", highlightthickness=0)
    canvas.grid(row=0, column=0, padx=(0, 12), pady=0)

    # form panel
    panel = tk.Frame(container, bg="white")
    panel.grid(row=0, column=1, sticky="n")

    tk.Label(panel, text="Add a goal", font=("Arial", 14, "bold"), bg="white").pack(anchor="w", pady=(0, 10))

    # name
    tk.Label(panel, text="Name", bg="white").pack(anchor="w")
    name_var = tk.StringVar(value="New Goal")
    name_entry = tk.Entry(panel, textvariable=name_var, width=28)
    name_entry.pack(anchor="w", pady=(0, 10))

    # start
    tk.Label(panel, text="Start (YYYY-MM-DD)", bg="white").pack(anchor="w")
    start_var = tk.StringVar(value=f"{current_year}-{current_month:02d}-05")
    start_entry = tk.Entry(panel, textvariable=start_var, width=28)
    start_entry.pack(anchor="w", pady=(0, 10))

    # end
    tk.Label(panel, text="End (YYYY-MM-DD)", bg="white").pack(anchor="w")
    end_var = tk.StringVar(value=f"{current_year}-{current_month:02d}-20")
    end_entry = tk.Entry(panel, textvariable=end_var, width=28)
    end_entry.pack(anchor="w", pady=(0, 10))

    # color dropdown (simple & stable)
    tk.Label(panel, text="Color", bg="white").pack(anchor="w")
    color_map = {
        "Blue": "#4f7cff",
        "Orange": "#f28c28",
        "Green": "#2ea043",
        "Purple": "#a371f7",
        "Pink": "#ff6aa2",
        "Gray": "#6e7681",
    }
    color_name_var = tk.StringVar(value="Blue")
    color_menu = tk.OptionMenu(panel, color_name_var, *color_map.keys())
    color_menu.config(width=22)
    color_menu.pack(anchor="w", pady=(0, 12))

    def add_goal():
        try:
            name = name_var.get().strip()
            if not name:
                raise ValueError("Name cannot be empty.")

            start = parse_date(start_var.get())
            end = parse_date(end_var.get())
            if start > end:
                raise ValueError("Start date must be ≤ end date.")

            color = color_map[color_name_var.get()]
            goals.append(Goal(name, start, end, color))

            canvas.draw()  # redraw to show new goal immediately
        except Exception as e:
            messagebox.showerror("Invalid input", str(e))

    add_btn = tk.Button(panel, text="Add goal", command=add_goal)
    add_btn.pack(anchor="w", pady=(0, 8))

    tip = tk.Label(
        panel,
        text="Tip: click a bar to view details.",
        fg="#555555",
        bg="white"
    )
    tip.pack(anchor="w")

    root.mainloop()


if __name__ == "__main__":
    main()
