
# Python program to create a table
from tkinter import *

class TKTable:
    def __init__(self, root, rows, columns, table):
        self.root = root
        for j in range(columns):
            self.make_cell(j, 0, j+1)
        for i in range(rows):
            self.make_cell(i, i+1, 0)
            for j in range(columns):

                self.make_cell(str(table[i][j]), i+1, j+1, "blue")

    
    def make_cell(self, text, row, column, color="black"):
        self.e = Entry(self.root, width=15, fg=color, font=('Arial',10,'bold'))
        self.e.grid(row=row, column=column)
        self.e.insert(END, text)


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