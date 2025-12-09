import tkinter as tk
from tkinter import messagebox, filedialog


class SudokuApp:
    def __init__(self, root, solver_callback, ocr_callback):
        self.root = root
        self.root.title("Yapay Zeka Sudoku Çözücü")

        self.solver_callback = solver_callback
        self.ocr_callback = ocr_callback

        self.cells = {}
        self._setup_ui()

    def _setup_ui(self):
        top_frame = tk.Frame(self.root, pady=10)
        top_frame.pack()

        load_btn = tk.Button(
            top_frame,
            text="📁 SUDOKU RESMİ YÜKLE",
            command=self.load_image_action,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold")
        )
        load_btn.pack()

        grid_frame = tk.Frame(self.root, padx=10, pady=10)
        grid_frame.pack()

        for i in range(9):
            for j in range(9):
                pad_top = 5 if i % 3 == 0 and i != 0 else 1
                pad_left = 5 if j % 3 == 0 and j != 0 else 1

                cell = tk.Entry(
                    grid_frame,
                    width=3,
                    font=("Arial", 18),
                    justify="center"
                )
                cell.grid(row=i, column=j, padx=(pad_left, 1), pady=(pad_top, 1))
                self.cells[(i, j)] = cell

        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack()

        solve_btn = tk.Button(
            btn_frame,
            text="✅ SAT İLE ÇÖZ",
            command=self.solve_action,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold")
        )
        solve_btn.pack(side=tk.LEFT, padx=10)

        clear_btn = tk.Button(
            btn_frame,
            text="TEMİZLE",
            command=self.clear_grid,
            bg="#f44336",
            fg="white",
            font=("Arial", 12)
        )
        clear_btn.pack(side=tk.LEFT, padx=10)

    def load_image_action(self):
        file_path = filedialog.askopenfilename(
            title="Bir Sudoku Resmi Seçin",
            filetypes=[("Resim Dosyaları", "*.png *.jpg *.jpeg")]
        )

        if not file_path:
            return

        try:
            detected_grid = self.ocr_callback(file_path)
            self.clear_grid()
            self.update_grid(detected_grid)
            messagebox.showinfo("Başarılı", "Resim tarandı ve sayılar yerleştirildi!")
        except Exception as e:
            messagebox.showerror("OCR Hatası", str(e))

    def get_grid_values(self):
        grid = []
        for i in range(9):
            row = []
            for j in range(9):
                val = self.cells[(i, j)].get()
                row.append(int(val) if val.isdigit() else 0)
            grid.append(row)
        return grid

    def update_grid(self, grid_data):
        for i in range(9):
            for j in range(9):
                val = grid_data[i][j]
                cell = self.cells[(i, j)]

                cell.delete(0, tk.END)
                if val != 0:
                    cell.insert(0, str(val))
                    cell.config(fg="blue")
                else:
                    cell.config(fg="black")

    def clear_grid(self):
        for cell in self.cells.values():
            cell.delete(0, tk.END)
            cell.config(fg="black")

    def solve_action(self):
        try:
            current_grid = self.get_grid_values()
            solved_grid = self.solver_callback(current_grid)

            if solved_grid:
                self.update_grid(solved_grid)
            else:
                messagebox.showwarning("Sonuç", "Çözüm bulunamadı!")
        except Exception as e:
            messagebox.showerror("Hata", str(e))
