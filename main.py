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
    color: str


def parse_date(s: str) -> datetime.date:
    return datetime.date.fromisoformat(s.strip())


def shift_month(y, m, delta):
    m += delta
    if m == 0:
        return y - 1, 12
    if m == 13:
        return y + 1, 1
    return y, m


class MonthView(tk.Canvas):
    def __init__(self, master, year, month, goals, on_goal_click, **kwargs):
        super().__init__(master, **kwargs)
        self.year = year
        self.month = month
        self.goals = goals
        self.on_goal_click = on_goal_click

        self.pad = 18
        self.weekday_h = 32
        self.cell_w = 120
        self.cell_h = 80

        self.goal_hitboxes = []
        self.bind("<Button-1>", self._handle_click)
        self.draw()

    def set_month(self, year, month):
        self.year = year
        self.month = month
        self.draw()

    def draw(self):
        self.delete("all")
        self.goal_hitboxes.clear()

        cal = calendar.Calendar(firstweekday=0)
        self.month_dates = list(cal.itermonthdates(self.year, self.month))[:42]

        width = self.pad * 2 + self.cell_w * 7
        height = self.pad * 2 + self.weekday_h + self.cell_h * 6
        self.config(width=width, height=height)

        # weekday header
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, wd in enumerate(weekdays):
            x0 = self.pad + i * self.cell_w
            x1 = x0 + self.cell_w
            y0 = self.pad
            y1 = y0 + self.weekday_h
            self.create_rectangle(x0, y0, x1, y1, fill="#eaeaea", outline="black")
            self.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=wd, font=("Arial", 12, "bold"))

        # grid
        self.grid_top = self.pad + self.weekday_h
        for idx, date in enumerate(self.month_dates):
            r, c = divmod(idx, 7)
            x0 = self.pad + c * self.cell_w
            y0 = self.grid_top + r * self.cell_h
            x1 = x0 + self.cell_w
            y1 = y0 + self.cell_h

            fill = "white" if date.month == self.month else "#f2f2f2"
            self.create_rectangle(x0, y0, x1, y1, fill=fill, outline="black")

            self.create_text(
                x0 + 6, y0 + 6,
                anchor="nw",
                text=str(date.day),
                font=("Arial", 11),
                fill="black" if date.month == self.month else "#888"
            )

        self._draw_goals()

    def _draw_goals(self):
        date_to_idx = {d: i for i, d in enumerate(self.month_dates)}
        visible_start, visible_end = self.month_dates[0], self.month_dates[-1]

        lane_h, lane_gap, base_y = 16, 4, 26
        lanes_per_row = {}

        # NOTE: current simple lane assignment (can be upgraded later)
        for goal in self.goals:
            s, e = max(goal.start, visible_start), min(goal.end, visible_end)
            if s > e:
                continue

            idxs = []
            cur = s
            while cur <= e:
                idxs.append(date_to_idx[cur])
                cur += datetime.timedelta(days=1)

            by_row = {}
            for idx in idxs:
                r, c = divmod(idx, 7)
                by_row.setdefault(r, []).append(c)

            for r, cols in by_row.items():
                cols.sort()
                start = prev = cols[0]

                for c in cols[1:] + [None]:
                    if c != prev + 1:
                        lanes_per_row.setdefault(r, [])
                        lane = len(lanes_per_row[r])
                        lanes_per_row[r].append(goal)

                        x0 = self.pad + start * self.cell_w
                        x1 = self.pad + (prev + 1) * self.cell_w
                        y0 = self.grid_top + r * self.cell_h

                        bar_y0 = y0 + base_y + lane * (lane_h + lane_gap)
                        bar_y1 = bar_y0 + lane_h

                        self.create_rectangle(x0 + 6, bar_y0, x1 - 6, bar_y1, fill=goal.color, outline="")
                        self.goal_hitboxes.append({
                            "x0": x0 + 6, "y0": bar_y0, "x1": x1 - 6, "y1": bar_y1,
                            "goal": goal
                        })

                        if start == cols[0]:
                            self.create_text(
                                x0 + 10, (bar_y0 + bar_y1) / 2,
                                text=goal.name,
                                anchor="w",
                                fill="white",
                                font=("Arial", 9, "bold")
                            )

                        start = c
                    prev = c

    def _handle_click(self, event):
        for hb in reversed(self.goal_hitboxes):
            if hb["x0"] <= event.x <= hb["x1"] and hb["y0"] <= event.y <= hb["y1"]:
                self.on_goal_click(hb["goal"])
                return


def main():
    root = tk.Tk()
    root.title("Long-term Planning Calendar")

    goals = [
        Goal("IB CS", datetime.date(2026, 1, 5), datetime.date(2026, 2, 10), "#4f7cff"),
        Goal("Math HL", datetime.date(2025, 12, 20), datetime.date(2026, 1, 18), "#f28c28"),
        Goal("TOK Essay", datetime.date(2026, 1, 10), datetime.date(2026, 1, 25), "#2ea043"),
    ]

    year, month = 2026, 2

    # ===== Top bar: title + prev/next =====
    top = tk.Frame(root)
    top.pack(pady=(10, 6))

    title_var = tk.StringVar()

    def update_title():
        title_var.set(f"{calendar.month_name[month]} {year}")

    def prev_month():
        nonlocal year, month
        year, month = shift_month(year, month, -1)
        update_title()
        cal_view.set_month(year, month)

    def next_month():
        nonlocal year, month
        year, month = shift_month(year, month, 1)
        update_title()
        cal_view.set_month(year, month)

    tk.Button(top, text="← Prev", command=prev_month).pack(side="left", padx=8)
    tk.Label(top, textvariable=title_var, font=("Arial", 22, "bold")).pack(side="left", padx=14)
    tk.Button(top, text="Next →", command=next_month).pack(side="left", padx=8)
    update_title()

    # ===== Main area: calendar + right panel =====
    body = tk.Frame(root)
    body.pack(padx=12, pady=10)

    # colors for UI
    colors = {
        "Blue": "#4f7cff",
        "Orange": "#f28c28",
        "Green": "#2ea043",
        "Purple": "#a371f7",
        "Pink": "#ff6aa2",
        "Gray": "#6e7681",
    }
    # reverse map for dropdown default selection
    rev_colors = {v: k for k, v in colors.items()}

    def open_goal_editor(goal: Goal):
        win = tk.Toplevel(root)
        win.title("Edit goal")
        win.resizable(False, False)

        frm = tk.Frame(win, padx=12, pady=12)
        frm.pack()

        tk.Label(frm, text="Name").grid(row=0, column=0, sticky="w")
        name_var = tk.StringVar(value=goal.name)
        tk.Entry(frm, textvariable=name_var, width=28).grid(row=0, column=1, pady=4)

        tk.Label(frm, text="Start (YYYY-MM-DD)").grid(row=1, column=0, sticky="w")
        start_var = tk.StringVar(value=goal.start.isoformat())
        tk.Entry(frm, textvariable=start_var, width=28).grid(row=1, column=1, pady=4)

        tk.Label(frm, text="End (YYYY-MM-DD)").grid(row=2, column=0, sticky="w")
        end_var = tk.StringVar(value=goal.end.isoformat())
        tk.Entry(frm, textvariable=end_var, width=28).grid(row=2, column=1, pady=4)

        tk.Label(frm, text="Color").grid(row=3, column=0, sticky="w")
        color_name_var = tk.StringVar(value=rev_colors.get(goal.color, "Blue"))
        tk.OptionMenu(frm, color_name_var, *colors.keys()).grid(row=3, column=1, sticky="w", pady=4)

        def save_changes():
            try:
                new_name = name_var.get().strip()
                if not new_name:
                    raise ValueError("Name cannot be empty.")

                new_start = parse_date(start_var.get())
                new_end = parse_date(end_var.get())
                if new_start > new_end:
                    raise ValueError("Start date must be ≤ end date.")

                goal.name = new_name
                goal.start = new_start
                goal.end = new_end
                goal.color = colors[color_name_var.get()]

                cal_view.draw()
                win.destroy()
            except Exception as e:
                messagebox.showerror("Invalid input", str(e), parent=win)

        def delete_goal():
            # simple confirm
            if messagebox.askyesno("Delete", f"Delete '{goal.name}'?", parent=win):
                try:
                    goals.remove(goal)
                except ValueError:
                    pass
                cal_view.draw()
                win.destroy()

        btns = tk.Frame(frm)
        btns.grid(row=4, column=0, columnspan=2, pady=(10, 0), sticky="e")

        tk.Button(btns, text="Delete", command=delete_goal).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="Save changes", command=save_changes).pack(side="left")

    cal_view = MonthView(
        body, year, month, goals,
        on_goal_click=open_goal_editor,
        bg="white",
        highlightthickness=0
    )
    cal_view.grid(row=0, column=0, padx=(0, 14), pady=0)

    # ---- Right panel: add goals ----
    panel = tk.Frame(body)
    panel.grid(row=0, column=1, sticky="n")

    tk.Label(panel, text="Add goal", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 8))

    tk.Label(panel, text="Name").pack(anchor="w")
    name_entry = tk.Entry(panel, width=26)
    name_entry.insert(0, "New Goal")
    name_entry.pack(anchor="w", pady=(0, 10))

    tk.Label(panel, text="Start (YYYY-MM-DD)").pack(anchor="w")
    start_entry = tk.Entry(panel, width=26)
    start_entry.insert(0, f"{year}-{month:02d}-05")
    start_entry.pack(anchor="w", pady=(0, 10))

    tk.Label(panel, text="End (YYYY-MM-DD)").pack(anchor="w")
    end_entry = tk.Entry(panel, width=26)
    end_entry.insert(0, f"{year}-{month:02d}-20")
    end_entry.pack(anchor="w", pady=(0, 10))

    tk.Label(panel, text="Color").pack(anchor="w")
    color_name = tk.StringVar(value="Purple")
    tk.OptionMenu(panel, color_name, *colors.keys()).pack(anchor="w", pady=(0, 10))

    def add_goal():
        try:
            name = name_entry.get().strip()
            if not name:
                raise ValueError("Name cannot be empty.")

            start = parse_date(start_entry.get())
            end = parse_date(end_entry.get())
            if start > end:
                raise ValueError("Start date must be ≤ end date.")

            goals.append(Goal(name, start, end, colors[color_name.get()]))
            cal_view.draw()
        except Exception as e:
            messagebox.showerror("Invalid input", str(e))

    tk.Button(panel, text="Add", command=add_goal).pack(anchor="w", pady=(0, 6))
    tk.Label(panel, text="Tip: click a bar to edit / delete.", fg="#555").pack(anchor="w")

    root.mainloop()


if __name__ == "__main__":
    main()
