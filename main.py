import sys
import os

# ---------------------------------------------------------
# Proje kök klasörünü Python yoluna ekle
# ---------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Modülleri import et (Artık %100 bulunur)
from gui.gui import SudokuApp
from ocr.ocr_reader import sudoku_oku_openai
from sat.encoder import build_cnf_from_grid
from sat.solver import solve_cnf_with_openai, model_to_grid

import tkinter as tk
from tkinter import messagebox

# ---------------------------------------------------------
# OpenAI ile SAT çözme fonksiyonu
# ---------------------------------------------------------
def solve_with_sat(grid):
    try:
        print("Gelen grid:")
        for row in grid:
            print(row)

        clauses = build_cnf_from_grid(grid)
        print("Toplam clause sayısı:", len(clauses))

        API_KEY = "keyi buraya yaz"   # sadece imza için, solver kullanmıyor

        model = solve_cnf_with_openai(clauses, API_KEY)

        if model is None:
            messagebox.showwarning("Hata", "SAT çözümü bulunamadı (UNSAT).")
            return None

        solved_grid = model_to_grid(model)

        print("Çözülmüş grid:")
        for row in solved_grid:
            print(row)

        return solved_grid

    except Exception as e:
        messagebox.showerror("SAT Solver Hatası", str(e))
        return None


# ---------------------------------------------------------
# OCR ile sudoku okuma
# ---------------------------------------------------------
def read_sudoku_from_image(path):
    API_KEY = "keyi buraya yaz"   # <<<<<< BUNA DA AYNI KEYİ YAZ
    return sudoku_oku_openai(path, API_KEY)


# ---------------------------------------------------------
# GUI başlat
# ---------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuApp(
        root,
        solver_callback=solve_with_sat,
        ocr_callback=read_sudoku_from_image
    )
    root.mainloop()