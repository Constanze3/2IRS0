import tkinter as tk

def routing_table_widget(root, node, destination, routing_table, fg="black", bg="black", header_color="gray60", cell_color="white") -> tk.Frame:
    frame = tk.Frame(root, width=200, bg=bg)
    frame.pack_propagate(False)

    label_text = f"{str(node)} >> {str(destination)}"
    label = tk.Label(frame, text=label_text, bg=bg, fg=cell_color, font=("Arial", 20))
    label.pack(side="top", pady=2)

    container = tk.Frame(frame)
    container.pack(padx=5, pady=2, anchor="nw", side="bottom", fill="both", expand=True)

    canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0, width=0)
    canvas.pack(side="left", fill="both", expand=True)

    gap = tk.Frame(container, width=5, bg=bg)
    gap.pack(side="left", fill="y")
    
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")

    table = tk.Frame(canvas)
    table.grid_columnconfigure(tuple(range(3)), weight=1)

    table_item = canvas.create_window((0,0), window=table, anchor="nw")

    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        # set the width of table to the same as the width of canvas
        canvas.itemconfig(table_item, width=event.width)

    canvas.configure(yscrollcommand=scrollbar.set) 
    canvas.bind('<Configure>', on_configure)

        
    def table_entry(column, row, text, color):
        entry = tk.Frame(table, bg=bg)
        entry.grid(column=column, row=row, sticky="nsew")

        label = tk.Label(entry, text=text, fg=fg, bg=color)
        label.pack(padx=2, pady=2, fill="x", expand=True)


    table_entry(0, 0, "d", header_color)
    table_entry(1, 0, "pi", header_color)
    table_entry(2, 0, "delta", header_color)

    for i, entry in enumerate(routing_table):
        i = i + 1
        d, pi, delta = entry

        table_entry(0, i, str(d), cell_color)
        table_entry(1, i, str(pi), cell_color)
        table_entry(2, i, str(delta), cell_color)

    
    return frame

def main():
    root = tk.Tk()
    root.title("Research")
    root.geometry("1200x600")

    frame = tk.Frame(root, bg="gray60")
    frame.pack(anchor="nw", fill="both", expand=True)
    frame.grid_rowconfigure(0, weight=1)

    test_routing_table = [(1, 2, 3)] * 100

    r1 = routing_table_widget(frame, 1, 2, test_routing_table)
    r1.grid(column=0, row=0, sticky="nsw", padx=5)

    r2 = routing_table_widget(frame, 5, 6, test_routing_table)
    r2.grid(column=1, row=0, sticky="nsw", padx=5)

    r3 = routing_table_widget(frame, 1, 5, test_routing_table)
    r3.grid(column=2, row=0, sticky="nsw", padx=5)

    # root.update()
    # input("Press Enter to continue...")

    root.mainloop()

main()