from tkinter import *

class TKTable:
    def __init__(self, root, rows, columns, table):
        self.root = root
        self.cells = []
        for j in range(columns):
            self.make_cell(j, 0, j+1)
        for i in range(rows):
            self.make_cell(i, i+1, 0)
            row_cells = []
            for j in range(i, columns):
                row_cells.append(
                    self.make_cell(str(table[i][j]), i+1, j+1, "blue")
                )
            self.cells.append(row_cells)

    def make_cell(self, text, row, column, color="black"):
        e = Entry(self.root, width=15, fg=color, font=('Arial',10,'bold'))
        e.grid(row=row, column=column)
        e.insert(END, text)
        return e
    
    def get_values(self):
        values = []
        for row in self.cells:
            current_row = []
            for cell in row:
                value = cell.get()
                try:
                    value = eval(value)
                    if value == "None":
                        value = None
                except Exception:
                    value = None
                current_row.append(value)
            values.append(current_row)
        return values


if __name__ == "__main__":
    table = [
        [None, (5, 6), None, None],
        [(5, 6), None, (7, 12), (8,9)],
        [None, (7, 12), None, (3, 15)],
        [None, (8, 9), (3, 15), None],
    ]
    total_rows = len(table)
    total_columns = len(table[0])
    # create root window
    root = Tk()
    t = TKTable(root, total_rows, total_columns, table)
    root.mainloop()