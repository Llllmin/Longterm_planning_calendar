import tkinter as tk

def main():
    root = tk.Tk()
    root.title("Long-term Planning Calendar")
    root.geometry("900x600")

    title = tk.Label(
        root,
        text="Long-term Planning Calendar",
        font=("Arial", 20)
    )
    title.pack(pady=20)

    subtitle = tk.Label(
        root,
        text="MVP v0.1 — window works ✅",
        font=("Arial", 14)
    )
    subtitle.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
